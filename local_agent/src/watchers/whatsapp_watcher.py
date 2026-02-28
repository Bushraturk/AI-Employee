"""WhatsApp watcher for local agent.

Monitors WhatsApp Web for new messages using Playwright automation.
Detects keywords and creates action files for processing.
"""

import asyncio
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from playwright.async_api import async_playwright, Browser, Page

from shared.base_watcher import BaseWatcher
from shared.models.watcher_state import WatcherType
from shared.models.action_file import ActionFile, ActionType, ActionStatus
from shared.utils.vault_manager import VaultManager
from shared.utils.logger import VaultLogger


logger = logging.getLogger(__name__)


class WhatsAppWatcher(BaseWatcher):
    """WhatsApp watcher - monitors messages via web.whatsapp.com"""

    # Keywords that trigger action creation
    KEYWORDS = ["invoice", "payment", "urgent", "asap", "help"]

    def __init__(
        self,
        agent_id: str,
        vault_manager: VaultManager,
        vault_logger: VaultLogger,
        session_path: str = "whatsapp_session/",
        check_interval_seconds: int = 30,
        monitor_groups: bool = True,
    ):
        """Initialize WhatsApp watcher.

        Args:
            agent_id: Agent ID
            vault_manager: Vault manager instance
            vault_logger: Vault logger instance
            session_path: Path to store browser session
            check_interval_seconds: Check interval (default: 30)
            monitor_groups: Whether to monitor group messages
        """
        super().__init__(
            watcher_id="whatsapp_watcher",
            watcher_type=WatcherType.WHATSAPP,
            watcher_name="WhatsApp Watcher",
            agent_id=agent_id,
            vault_manager=vault_manager,
            vault_logger=vault_logger,
            check_interval_seconds=check_interval_seconds,
            config={
                "session_path": session_path,
                "monitor_groups": monitor_groups,
            },
        )

        self.session_path = session_path
        self.monitor_groups = monitor_groups

        # Playwright components
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.event_loop = None
        self.loop_thread = None

        # State
        self.processed_message_ids = set()
        self.is_authenticated = False

    def start(self) -> None:
        """Start monitoring WhatsApp."""
        logger.info("Starting WhatsApp watcher...")

        # Create and start event loop in background thread
        self.event_loop = asyncio.new_event_loop()
        self.loop_thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.loop_thread.start()

        # Run async initialization
        future = asyncio.run_coroutine_threadsafe(self._async_start(), self.event_loop)
        try:
            future.result(timeout=300)  # 5 minute timeout for QR scan
        except Exception as e:
            logger.error(f"Failed to start WhatsApp watcher: {e}")
            raise

        # Call parent start
        super().start()
        logger.info("WhatsApp watcher started successfully")

    def _run_event_loop(self):
        """Run event loop in background thread."""
        asyncio.set_event_loop(self.event_loop)
        self.event_loop.run_forever()

    async def _async_start(self):
        """Async initialization of Playwright and WhatsApp Web."""
        try:
            # Launch Playwright
            self.playwright = await async_playwright().start()

            # Launch browser with persistent context
            self.browser = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.session_path,
                headless=False,  # Must be False for QR code scan
                args=["--no-sandbox", "--disable-setuid-sandbox"],
            )

            # Get or create page
            if len(self.browser.pages) > 0:
                self.page = self.browser.pages[0]
            else:
                self.page = await self.browser.new_page()

            # Navigate to WhatsApp Web
            await self.page.goto("https://web.whatsapp.com")

            # Wait for authentication
            await self._wait_for_authentication()

            logger.info("WhatsApp Web authenticated successfully")
            self.is_authenticated = True

        except Exception as e:
            logger.error(f"Error starting WhatsApp watcher: {e}")
            raise

    async def _wait_for_authentication(self, timeout: int = 300):
        """Wait for user to scan QR code and authenticate.

        Args:
            timeout: Maximum seconds to wait (default: 5 minutes)
        """
        logger.info("Waiting for WhatsApp authentication (scan QR code)...")
        logger.info("You have 5 minutes to scan the QR code")

        start_time = asyncio.get_event_loop().time()
        check_interval = 5

        try:
            while (asyncio.get_event_loop().time() - start_time) < timeout:
                # Check for chat list (indicates successful auth)
                selectors_to_check = [
                    '[data-testid="chat-list"]',
                    '[data-testid="conversation-panel-wrapper"]',
                    "#pane-side",
                ]

                for selector in selectors_to_check:
                    try:
                        element = await self.page.query_selector(selector)
                        if element and await element.is_visible():
                            logger.info(f"Authentication successful (detected: {selector})")
                            return
                    except Exception:
                        continue

                await asyncio.sleep(check_interval)

            raise TimeoutError(f"Authentication timeout after {timeout} seconds")

        except Exception as e:
            logger.error(f"WhatsApp authentication failed: {e}")
            raise

    def stop(self) -> None:
        """Stop monitoring WhatsApp."""
        logger.info("Stopping WhatsApp watcher...")

        # Run async cleanup
        if self.event_loop and self.event_loop.is_running():
            future = asyncio.run_coroutine_threadsafe(self._async_stop(), self.event_loop)
            try:
                future.result(timeout=10)
            except Exception as e:
                logger.error(f"Error during async cleanup: {e}")

            # Stop the event loop
            self.event_loop.call_soon_threadsafe(self.event_loop.stop)

        # Call parent stop
        super().stop()
        logger.info("WhatsApp watcher stopped")

    async def _async_stop(self):
        """Async cleanup of Playwright resources."""
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.error(f"Error stopping WhatsApp watcher: {e}")

    def check_for_events(self) -> List[ActionFile]:
        """Check for new WhatsApp messages.

        Returns:
            List of detected action files
        """
        if not self.is_authenticated:
            logger.warning("WhatsApp not authenticated, skipping check")
            return []

        try:
            # Run async message fetching
            if not self.event_loop or not self.event_loop.is_running():
                logger.error("Event loop not running")
                return []

            future = asyncio.run_coroutine_threadsafe(
                self._async_get_new_messages(), self.event_loop
            )
            action_files = future.result(timeout=30)

            return action_files

        except Exception as e:
            logger.error(f"Error checking for WhatsApp messages: {e}")
            return []

    async def _async_get_new_messages(self) -> List[ActionFile]:
        """Fetch new WhatsApp messages.

        Returns:
            List of action files
        """
        action_files = []

        try:
            # Get all unread chats
            unread_chats = await self.page.query_selector_all(
                '[data-testid="cell-frame-container"]'
            )

            for chat in unread_chats[:10]:  # Limit to 10 chats per poll
                # Check if chat has unread indicator
                unread_indicator = await chat.query_selector('[data-testid="unread-count"]')
                if not unread_indicator:
                    continue

                # Click on chat to open
                await chat.click()
                await asyncio.sleep(1)

                # Extract messages
                messages = await self._extract_messages_from_chat()

                # Convert messages to action files
                for msg_data in messages:
                    action_file = self._message_to_action(msg_data)
                    if action_file:
                        action_files.append(action_file)

                # Go back to chat list
                await self.page.keyboard.press("Escape")
                await asyncio.sleep(0.5)

        except Exception as e:
            logger.error(f"Error fetching WhatsApp messages: {e}")

        return action_files

    async def _extract_messages_from_chat(self) -> List[Dict[str, Any]]:
        """Extract messages from currently open chat.

        Returns:
            List of message data dictionaries
        """
        messages = []

        try:
            # Get chat title
            chat_title_elem = await self.page.query_selector(
                '[data-testid="conversation-header"]'
            )
            chat_title = await chat_title_elem.inner_text() if chat_title_elem else "Unknown"

            # Get all message elements
            message_elems = await self.page.query_selector_all('[data-testid="msg-container"]')

            # Get last 5 unread messages
            for msg_elem in message_elems[-5:]:
                try:
                    # Extract message text
                    text_elem = await msg_elem.query_selector('.copyable-text')
                    if not text_elem:
                        continue

                    message_text = await text_elem.inner_text()

                    # Check if message contains keywords
                    if not self._contains_keyword(message_text):
                        continue

                    # Extract timestamp
                    time_elem = await msg_elem.query_selector('[data-testid="msg-meta"]')
                    timestamp = await time_elem.inner_text() if time_elem else ""

                    # Check if message is from me
                    is_from_me = await msg_elem.evaluate(
                        '(element) => element.classList.contains("message-out")'
                    )
                    if is_from_me:
                        continue

                    # Create message ID
                    msg_id = f"{chat_title}_{timestamp}_{message_text[:20]}"

                    # Skip if already processed
                    if msg_id in self.processed_message_ids:
                        continue

                    messages.append(
                        {
                            "message_id": msg_id,
                            "sender_name": chat_title,
                            "message_text": message_text,
                            "timestamp": timestamp,
                            "chat_type": "group" if "@" in chat_title else "direct",
                        }
                    )

                    self.processed_message_ids.add(msg_id)

                except Exception as e:
                    logger.error(f"Error extracting message: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error extracting messages from chat: {e}")

        return messages

    def _contains_keyword(self, text: str) -> bool:
        """Check if text contains any keywords.

        Args:
            text: Message text

        Returns:
            True if contains keyword, False otherwise
        """
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.KEYWORDS)

    def _message_to_action(self, msg_data: Dict[str, Any]) -> Optional[ActionFile]:
        """Convert WhatsApp message to action file.

        Args:
            msg_data: Message data dictionary

        Returns:
            ActionFile instance or None
        """
        try:
            # Create action ID
            action_id = f"whatsapp_{msg_data['message_id']}_{datetime.now().strftime('%Y%m%dT%H%M%SZ')}"

            # Create action file
            action = ActionFile(
                action_id=action_id,
                action_type=ActionType.WHATSAPP,
                source_id=msg_data["message_id"],
                timestamp=datetime.now(),
                status=ActionStatus.NEEDS_ACTION,
                title=f"WhatsApp: {msg_data['message_text'][:50]}...",
                body=f"""# WhatsApp Message from {msg_data['sender_name']}

**Chat Type**: {msg_data['chat_type']}
**Timestamp**: {msg_data['timestamp']}

**Message**:

{msg_data['message_text']}

---

**Action Required**: Draft response for this WhatsApp message
""",
                metadata={
                    "sender_name": msg_data["sender_name"],
                    "message_id": msg_data["message_id"],
                    "timestamp": msg_data["timestamp"],
                    "chat_type": msg_data["chat_type"],
                    "message_text": msg_data["message_text"],
                },
            )

            logger.info(f"Created action from WhatsApp message: {msg_data['sender_name']}")
            return action

        except Exception as e:
            logger.error(f"Error converting WhatsApp message to action: {e}")
            return None

    def get_target_folder(self) -> str:
        """Get target vault folder for detected events.

        Returns:
            Folder path
        """
        return "Needs_Action/whatsapp"
