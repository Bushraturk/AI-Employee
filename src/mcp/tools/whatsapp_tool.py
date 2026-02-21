"""
WhatsApp MCP Tool

Implements WhatsApp message sending via Playwright automation with rate limiting.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path
from collections import deque

logger = logging.getLogger(__name__)


class WhatsAppTool:
    """WhatsApp tool for sending messages via web automation"""

    def __init__(self, vault_path: str = "vault", session_path: str = "whatsapp_session"):
        """
        Initialize WhatsApp tool

        Args:
            vault_path: Path to vault directory
            session_path: Path to WhatsApp session data
        """
        self.vault_path = Path(vault_path)
        self.session_path = Path(session_path)
        self.browser = None
        self.context = None
        self.page = None

        # Rate limiting: max 5 messages per minute
        self.rate_limit = 5
        self.rate_window = 60  # seconds
        self.message_timestamps = deque(maxlen=self.rate_limit)

    async def _initialize_browser(self):
        """Initialize Playwright browser with persistent session"""
        try:
            from playwright.async_api import async_playwright

            if self.browser:
                return True

            playwright = await async_playwright().start()

            # Create session directory
            self.session_path.mkdir(parents=True, exist_ok=True)

            # Launch browser with persistent context
            self.context = await playwright.chromium.launch_persistent_context(
                str(self.session_path),
                headless=False,  # WhatsApp Web requires visible browser for QR scan
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )

            self.page = await self.context.new_page()

            # Navigate to WhatsApp Web
            await self.page.goto('https://web.whatsapp.com')

            # Wait for WhatsApp to load (either QR code or chat list)
            try:
                await self.page.wait_for_selector('[data-testid="chat-list"]', timeout=60000)
                logger.info("WhatsApp Web loaded successfully")
                return True
            except Exception as e:
                logger.warning(f"WhatsApp Web not fully loaded: {e}")
                logger.info("Please scan QR code if this is first time setup")
                return False

        except ImportError as e:
            logger.error(f"Playwright not installed: {e}")
            logger.error("Install with: pip install playwright && playwright install chromium")
            return False
        except Exception as e:
            logger.error(f"Error initializing browser: {e}")
            return False

    async def _check_rate_limit(self) -> bool:
        """
        Check if rate limit allows sending message

        Returns:
            True if message can be sent, False if rate limit exceeded
        """
        now = datetime.now()

        # Remove timestamps older than rate window
        while self.message_timestamps and (now - self.message_timestamps[0]).total_seconds() > self.rate_window:
            self.message_timestamps.popleft()

        # Check if we can send
        if len(self.message_timestamps) >= self.rate_limit:
            oldest = self.message_timestamps[0]
            wait_time = self.rate_window - (now - oldest).total_seconds()
            logger.warning(f"Rate limit exceeded. Wait {wait_time:.1f} seconds")
            return False

        return True

    async def send_message(
        self,
        phone_number: str,
        message: str,
        verify_delivery: bool = True
    ) -> Dict[str, Any]:
        """
        Send a WhatsApp message via web automation

        Args:
            phone_number: Recipient phone number (with country code, e.g., +923001234567)
            message: Message text to send
            verify_delivery: Whether to verify message delivery (default: True)

        Returns:
            Result dictionary with status and delivery info
        """
        # Check rate limit
        if not await self._check_rate_limit():
            return {
                'success': False,
                'error': 'Rate limit exceeded. Max 5 messages per minute.'
            }

        # Initialize browser if needed
        if not self.page:
            initialized = await self._initialize_browser()
            if not initialized:
                return {
                    'success': False,
                    'error': 'Failed to initialize WhatsApp Web. Please scan QR code.'
                }

        try:
            # Navigate to chat using phone number
            # WhatsApp Web URL format: https://web.whatsapp.com/send?phone=PHONENUMBER
            chat_url = f"https://web.whatsapp.com/send?phone={phone_number.replace('+', '')}"
            await self.page.goto(chat_url)

            # Wait for chat to load
            await self.page.wait_for_selector('[data-testid="conversation-compose-box-input"]', timeout=10000)

            # Type message
            message_box = await self.page.query_selector('[data-testid="conversation-compose-box-input"]')
            await message_box.click()
            await message_box.type(message)

            # Click send button
            send_button = await self.page.query_selector('[data-testid="send"]')
            await send_button.click()

            # Record timestamp for rate limiting
            self.message_timestamps.append(datetime.now())

            # Verify delivery if requested
            delivery_status = 'sent'
            if verify_delivery:
                try:
                    # Wait for message to appear with checkmarks
                    await self.page.wait_for_selector('[data-testid="msg-dblcheck"]', timeout=5000)
                    delivery_status = 'delivered'
                except:
                    # Single check means sent but not delivered yet
                    try:
                        await self.page.wait_for_selector('[data-testid="msg-check"]', timeout=2000)
                        delivery_status = 'sent'
                    except:
                        delivery_status = 'unknown'

            logger.info(f"WhatsApp message sent to {phone_number}: {delivery_status}")

            return {
                'success': True,
                'phone_number': phone_number,
                'delivery_status': delivery_status,
                'sent_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def send_message_to_contact(
        self,
        contact_name: str,
        message: str,
        verify_delivery: bool = True
    ) -> Dict[str, Any]:
        """
        Send a WhatsApp message to a saved contact by name

        Args:
            contact_name: Contact name as saved in WhatsApp
            message: Message text to send
            verify_delivery: Whether to verify message delivery (default: True)

        Returns:
            Result dictionary with status and delivery info
        """
        # Check rate limit
        if not await self._check_rate_limit():
            return {
                'success': False,
                'error': 'Rate limit exceeded. Max 5 messages per minute.'
            }

        # Initialize browser if needed
        if not self.page:
            initialized = await self._initialize_browser()
            if not initialized:
                return {
                    'success': False,
                    'error': 'Failed to initialize WhatsApp Web. Please scan QR code.'
                }

        try:
            # Search for contact
            search_box = await self.page.query_selector('[data-testid="chat-list-search"]')
            await search_box.click()
            await search_box.type(contact_name)

            # Wait for search results
            await asyncio.sleep(1)

            # Click first result
            first_result = await self.page.query_selector('[data-testid="cell-frame-container"]')
            if not first_result:
                return {
                    'success': False,
                    'error': f'Contact not found: {contact_name}'
                }

            await first_result.click()

            # Wait for chat to load
            await self.page.wait_for_selector('[data-testid="conversation-compose-box-input"]', timeout=10000)

            # Type message
            message_box = await self.page.query_selector('[data-testid="conversation-compose-box-input"]')
            await message_box.click()
            await message_box.type(message)

            # Click send button
            send_button = await self.page.query_selector('[data-testid="send"]')
            await send_button.click()

            # Record timestamp for rate limiting
            self.message_timestamps.append(datetime.now())

            # Verify delivery if requested
            delivery_status = 'sent'
            if verify_delivery:
                try:
                    await self.page.wait_for_selector('[data-testid="msg-dblcheck"]', timeout=5000)
                    delivery_status = 'delivered'
                except:
                    try:
                        await self.page.wait_for_selector('[data-testid="msg-check"]', timeout=2000)
                        delivery_status = 'sent'
                    except:
                        delivery_status = 'unknown'

            logger.info(f"WhatsApp message sent to {contact_name}: {delivery_status}")

            return {
                'success': True,
                'contact_name': contact_name,
                'delivery_status': delivery_status,
                'sent_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def close(self):
        """Close browser and cleanup"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            logger.info("WhatsApp tool closed successfully")
        except Exception as e:
            logger.error(f"Error closing WhatsApp tool: {e}")
