"""
WhatsApp Watcher Module

Monitors WhatsApp messages using Playwright web automation.
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import frontmatter
import uuid
import threading

from playwright.async_api import async_playwright, Browser, Page
from watchers.base_watcher import BaseWatcher, WatcherStatus

logger = logging.getLogger(__name__)


class WhatsAppWatcher(BaseWatcher):
    """WhatsApp watcher - monitors messages via web.whatsapp.com"""

    def __init__(self, vault_path: str, config: Dict[str, Any]):
        """
        Initialize WhatsApp watcher

        Args:
            vault_path: Path to vault directory
            config: Configuration with:
                - poll_interval_seconds: How often to check for new messages (default: 30)
                - session_path: Path to store browser session (default: 'whatsapp_session/')
                - monitor_groups: Whether to monitor group messages (default: True)
                - group_whitelist: List of group names to monitor (default: all)
        """
        super().__init__(
            watcher_id='whatsapp',
            watcher_type='whatsapp',
            config=config
        )

        self.vault_path = Path(vault_path)
        self.inbox_path = self.vault_path / 'Inbox'
        self.inbox_path.mkdir(parents=True, exist_ok=True)

        # Configuration
        self.poll_interval = config.get('poll_interval_seconds', 30)
        self.session_path = config.get('session_path', 'whatsapp_session/')
        self.monitor_groups = config.get('monitor_groups', True)
        self.group_whitelist = config.get('group_whitelist', [])

        # Playwright components
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.event_loop = None

        # State
        self.processed_message_ids = set()
        self.is_authenticated = False

    def start(self) -> None:
        """Start monitoring WhatsApp"""
        logger.info("Starting WhatsApp watcher...")

        # Create and start event loop in background thread
        self.event_loop = asyncio.new_event_loop()
        self.loop_thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.loop_thread.start()

        # Run async initialization in the background loop
        future = asyncio.run_coroutine_threadsafe(self._async_start(), self.event_loop)
        future.result()  # Wait for initialization to complete

        self.status = WatcherStatus.RUNNING
        logger.info("WhatsApp watcher started successfully")

    def _run_event_loop(self):
        """Run event loop in background thread"""
        asyncio.set_event_loop(self.event_loop)
        self.event_loop.run_forever()

    async def _async_start(self):
        """Async initialization of Playwright and WhatsApp Web"""
        try:
            # Launch Playwright
            self.playwright = await async_playwright().start()

            # Launch browser with persistent context (saves session)
            self.browser = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.session_path,
                headless=False,  # Must be False for QR code scan
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )

            # Get or create page
            if len(self.browser.pages) > 0:
                self.page = self.browser.pages[0]
            else:
                self.page = await self.browser.new_page()

            # Navigate to WhatsApp Web
            await self.page.goto('https://web.whatsapp.com')

            # Wait for authentication
            await self._wait_for_authentication()

            logger.info("WhatsApp Web authenticated successfully")
            self.is_authenticated = True

        except Exception as e:
            logger.error(f"Error starting WhatsApp watcher: {e}")
            raise

    async def _wait_for_authentication(self, timeout: int = 300):
        """
        Wait for user to scan QR code and authenticate

        Args:
            timeout: Maximum seconds to wait for authentication (default: 5 minutes)
        """
        logger.info("Waiting for WhatsApp authentication (scan QR code)...")
        logger.info("You have 5 minutes to scan the QR code")

        start_time = asyncio.get_event_loop().time()
        check_interval = 5  # Check every 5 seconds

        try:
            while (asyncio.get_event_loop().time() - start_time) < timeout:
                # Check multiple selectors that indicate successful authentication
                selectors_to_check = [
                    '[data-testid="chat-list"]',
                    '[data-testid="conversation-panel-wrapper"]',
                    '#pane-side',
                    '[aria-label="Chat list"]',
                    'div[data-testid="chatlist-panel"]'
                ]

                for selector in selectors_to_check:
                    try:
                        element = await self.page.query_selector(selector)
                        if element:
                            # Check if element is visible
                            is_visible = await element.is_visible()
                            if is_visible:
                                logger.info(f"WhatsApp authentication successful (detected: {selector})")
                                return
                    except Exception:
                        continue

                # Check if QR code is still present (means not authenticated yet)
                qr_code = await self.page.query_selector('[data-testid="qrcode"]')
                if qr_code:
                    logger.info("QR code still visible, waiting for scan...")
                else:
                    logger.info("QR code disappeared, waiting for chat list to load...")

                # Wait before next check
                await asyncio.sleep(check_interval)

            # Timeout reached
            raise TimeoutError(f"Authentication timeout after {timeout} seconds")

        except Exception as e:
            logger.error(f"WhatsApp authentication failed: {e}")
            logger.error("Please scan the QR code and wait for chats to load")
            raise

    def stop(self) -> None:
        """Stop monitoring WhatsApp"""
        logger.info("Stopping WhatsApp watcher...")

        # Run async cleanup in the background loop
        if self.event_loop and self.event_loop.is_running():
            future = asyncio.run_coroutine_threadsafe(self._async_stop(), self.event_loop)
            future.result(timeout=10)  # Wait up to 10 seconds

            # Stop the event loop
            self.event_loop.call_soon_threadsafe(self.event_loop.stop)

        self.status = WatcherStatus.STOPPED
        logger.info("WhatsApp watcher stopped")

    async def _async_stop(self):
        """Async cleanup of Playwright resources"""
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.error(f"Error stopping WhatsApp watcher: {e}")

    def get_new_tasks(self) -> List[Dict[str, Any]]:
        """
        Get new WhatsApp messages and convert to tasks

        Returns:
            List of task information dictionaries
        """
        if self.status != WatcherStatus.RUNNING or not self.is_authenticated:
            return []

        try:
            # Run async message fetching in the background loop
            if not self.event_loop or not self.event_loop.is_running():
                logger.error("Event loop not running, cannot fetch messages")
                return []

            future = asyncio.run_coroutine_threadsafe(
                self._async_get_new_messages(),
                self.event_loop
            )
            tasks = future.result(timeout=30)  # 30 second timeout

            self._update_last_check()
            self._reset_error_count()

            return tasks

        except Exception as e:
            logger.error(f"Error getting new tasks from WhatsApp: {e}")
            self._increment_error_count()
            if self.error_count >= 5:
                self.status = WatcherStatus.ERROR
            return []

    async def _async_get_new_messages(self) -> List[Dict[str, Any]]:
        """
        Fetch new WhatsApp messages

        Returns:
            List of task information dictionaries
        """
        tasks = []

        try:
            # Get all unread chats
            unread_chats = await self.page.query_selector_all('[data-testid="cell-frame-container"]')

            for chat in unread_chats[:10]:  # Limit to 10 chats per poll
                # Check if chat has unread indicator
                unread_indicator = await chat.query_selector('[data-testid="unread-count"]')
                if not unread_indicator:
                    continue

                # Click on chat to open
                await chat.click()
                await asyncio.sleep(1)  # Wait for messages to load

                # Extract messages
                messages = await self._extract_messages_from_chat()

                # Convert messages to tasks
                for msg_data in messages:
                    task_info = await self._message_to_task(msg_data)
                    if task_info:
                        tasks.append(task_info)

                # Go back to chat list
                await self.page.go_back()
                await asyncio.sleep(0.5)

        except Exception as e:
            logger.error(f"Error fetching WhatsApp messages: {e}")

        return tasks

    async def _extract_messages_from_chat(self) -> List[Dict[str, Any]]:
        """
        Extract messages from currently open chat

        Returns:
            List of message data dictionaries
        """
        messages = []

        try:
            # Get chat title (sender name or group name)
            chat_title_elem = await self.page.query_selector('[data-testid="conversation-header"]')
            chat_title = await chat_title_elem.inner_text() if chat_title_elem else "Unknown"

            # Get all message elements
            message_elems = await self.page.query_selector_all('[data-testid="msg-container"]')

            # Get last 5 unread messages
            for msg_elem in message_elems[-5:]:
                try:
                    # Extract message text
                    text_elem = await msg_elem.query_selector('[data-testid="msg-text"]')
                    if not text_elem:
                        continue

                    message_text = await text_elem.inner_text()

                    # Extract timestamp
                    time_elem = await msg_elem.query_selector('[data-testid="msg-time"]')
                    timestamp = await time_elem.inner_text() if time_elem else ""

                    # Check if message is from me (skip own messages)
                    is_from_me = await msg_elem.evaluate('(element) => element.classList.contains("message-out")')
                    if is_from_me:
                        continue

                    # Create message ID
                    msg_id = f"{chat_title}_{timestamp}_{message_text[:20]}"

                    # Skip if already processed
                    if msg_id in self.processed_message_ids:
                        continue

                    messages.append({
                        'message_id': msg_id,
                        'sender_name': chat_title,
                        'message_text': message_text,
                        'timestamp': timestamp,
                        'chat_type': 'group' if '@' in chat_title else 'direct'
                    })

                    self.processed_message_ids.add(msg_id)

                except Exception as e:
                    logger.error(f"Error extracting message: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error extracting messages from chat: {e}")

        return messages

    async def _message_to_task(self, msg_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert WhatsApp message to task format

        Args:
            msg_data: Message data dictionary

        Returns:
            Task information dictionary or None if conversion fails
        """
        try:
            # Create task file
            task_id = str(uuid.uuid4())
            task_file = self.inbox_path / f"{task_id}.md"

            # Create task metadata
            metadata = {
                'task_id': task_id,
                'title': f"WhatsApp: {msg_data['message_text'][:50]}...",
                'priority': 'P2',  # Default, will be classified by agent skill
                'status': 'inbox',
                'channel': 'whatsapp',
                'channel_metadata': {
                    'sender_name': msg_data['sender_name'],
                    'message_id': msg_data['message_id'],
                    'timestamp': msg_data['timestamp'],
                    'chat_type': msg_data['chat_type']
                },
                'created_at': datetime.now().isoformat(),
                'category': 'message'
            }

            # Create task content
            content = f"# WhatsApp Message from {msg_data['sender_name']}\n\n"
            content += f"**Chat Type**: {msg_data['chat_type']}\n\n"
            content += f"**Timestamp**: {msg_data['timestamp']}\n\n"
            content += f"**Message**:\n\n{msg_data['message_text']}\n\n"
            content += f"---\n\n"
            content += f"**Action Required**: Classify and process this message\n"

            # Write task file
            post = frontmatter.Post(content, **metadata)
            with open(task_file, 'w', encoding='utf-8') as f:
                f.write(frontmatter.dumps(post))

            logger.info(f"Created task from WhatsApp message: {msg_data['sender_name']}")

            return {
                'file_path': str(task_file),
                'task_id': task_id,
                'detected_at': datetime.now().isoformat(),
                'channel': 'whatsapp',
                'message_id': msg_data['message_id']
            }

        except Exception as e:
            logger.error(f"Error converting WhatsApp message to task: {e}")
            return None

    def mark_processed(self, task_id: str) -> None:
        """
        Mark message as processed

        Args:
            task_id: Task ID
        """
        # Message IDs are already tracked in processed_message_ids
        pass
