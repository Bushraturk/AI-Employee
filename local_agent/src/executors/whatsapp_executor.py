"""WhatsApp executor for local agent.

Executes approved WhatsApp message sends via Playwright automation.
"""

import asyncio
import logging
import threading
from datetime import datetime
from typing import Optional, Dict, Any

from playwright.async_api import async_playwright, Browser, Page

from shared.base_executor import BaseExecutor
from shared.models.approval_request import ApprovalRequest, ApprovalType
from shared.models.log_entry import LogEntry, LogCategory as LogEntryCategory, LogLevel
from shared.utils.vault_manager import VaultManager
from shared.utils.logger import VaultLogger, LogCategory


logger = logging.getLogger(__name__)


class WhatsAppExecutor(BaseExecutor):
    """Executes approved WhatsApp message sends.

    Uses Playwright to automate WhatsApp Web for sending messages.
    """

    def __init__(
        self,
        agent_id: str,
        vault_manager: VaultManager,
        vault_logger: VaultLogger,
        session_path: str = "whatsapp_session/",
        dev_mode: bool = False,
        dry_run: bool = False,
    ):
        """Initialize WhatsApp executor.

        Args:
            agent_id: Agent ID
            vault_manager: Vault manager instance
            vault_logger: Vault logger instance
            session_path: Path to browser session
            dev_mode: Development mode flag
            dry_run: Dry run mode flag
        """
        super().__init__(
            executor_name="WhatsApp Executor",
            agent_id=agent_id,
            vault_manager=vault_manager,
            vault_logger=vault_logger,
        )

        self.session_path = session_path

        # Override dev_mode and dry_run if provided
        if dev_mode is not None:
            self.dev_mode = dev_mode
        if dry_run is not None:
            self.dry_run = dry_run

        # Playwright components
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.event_loop = None
        self.loop_thread = None
        self.is_authenticated = False

        logger.info("WhatsApp executor initialized")

    def can_execute(self, approval: ApprovalRequest) -> bool:
        """Check if this executor can handle the approval request.

        Args:
            approval: Approval request

        Returns:
            True if can execute, False otherwise
        """
        return approval.approval_type == ApprovalType.WHATSAPP_SEND

    def execute(self, approval: ApprovalRequest) -> bool:
        """Execute approved WhatsApp message send.

        Args:
            approval: Approved WhatsApp send request

        Returns:
            True if successful, False otherwise
        """
        try:
            self.vault_logger.info(
                LogCategory.EXECUTOR,
                f"Executing WhatsApp send: {approval.approval_id}",
                details={
                    "approval_id": approval.approval_id,
                    "recipient": approval.target_id,
                }
            )

            # Extract message parameters
            recipient = approval.metadata.get("recipient")
            message = approval.body

            # Development/dry-run mode
            if self.dev_mode or self.dry_run:
                self.vault_logger.info(
                    LogCategory.EXECUTOR,
                    f"[DRY RUN] Would send WhatsApp to {recipient}",
                    details={
                        "recipient": recipient,
                        "message_preview": message[:100],
                    }
                )
                return True

            # Initialize browser if needed
            if not self.is_authenticated:
                self._initialize_browser()

            # Send message
            result = self._send_message(recipient=recipient, message=message)

            if result:
                self.vault_logger.info(
                    LogCategory.EXECUTOR,
                    f"WhatsApp message sent successfully: {approval.approval_id}",
                    details={
                        "approval_id": approval.approval_id,
                        "recipient": recipient,
                    }
                )

                # Log to audit trail
                self._log_execution(approval, success=True)

                return True
            else:
                self.vault_logger.error(
                    LogCategory.EXECUTOR,
                    f"Failed to send WhatsApp message: {approval.approval_id}",
                    details={
                        "approval_id": approval.approval_id,
                        "recipient": recipient,
                    }
                )

                # Log to audit trail
                self._log_execution(approval, success=False, error="Message send failed")

                return False

        except Exception as e:
            self.vault_logger.error(
                LogCategory.EXECUTOR,
                f"Error executing WhatsApp send: {e}",
                error_type=type(e).__name__,
                stack_trace=str(e),
            )

            # Log to audit trail
            self._log_execution(approval, success=False, error=str(e))

            return False

    def _initialize_browser(self) -> None:
        """Initialize Playwright browser for WhatsApp Web."""
        try:
            logger.info("Initializing WhatsApp browser session...")

            # Create event loop if needed
            if not self.event_loop or not self.event_loop.is_running():
                self.event_loop = asyncio.new_event_loop()
                self.loop_thread = threading.Thread(target=self._run_event_loop, daemon=True)
                self.loop_thread.start()

            # Run async initialization
            future = asyncio.run_coroutine_threadsafe(self._async_initialize(), self.event_loop)
            future.result(timeout=60)

            logger.info("WhatsApp browser session initialized")

        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise

    def _run_event_loop(self):
        """Run event loop in background thread."""
        asyncio.set_event_loop(self.event_loop)
        self.event_loop.run_forever()

    async def _async_initialize(self):
        """Async initialization of Playwright and WhatsApp Web."""
        try:
            # Launch Playwright
            self.playwright = await async_playwright().start()

            # Launch browser with persistent context
            self.browser = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.session_path,
                headless=False,
                args=["--no-sandbox", "--disable-setuid-sandbox"],
            )

            # Get or create page
            if len(self.browser.pages) > 0:
                self.page = self.browser.pages[0]
            else:
                self.page = await self.browser.new_page()

            # Navigate to WhatsApp Web if not already there
            if "web.whatsapp.com" not in self.page.url:
                await self.page.goto("https://web.whatsapp.com")

            # Validate session
            await self._validate_session()

            self.is_authenticated = True

        except Exception as e:
            logger.error(f"Error initializing WhatsApp: {e}")
            raise

    async def _validate_session(self, timeout: int = 30):
        """Validate WhatsApp Web session.

        Args:
            timeout: Maximum seconds to wait

        Raises:
            TimeoutError: If session validation fails
        """
        logger.info("Validating WhatsApp session...")

        start_time = asyncio.get_event_loop().time()

        while (asyncio.get_event_loop().time() - start_time) < timeout:
            # Check for chat list
            try:
                chat_list = await self.page.query_selector('[data-testid="chat-list"]')
                if chat_list and await chat_list.is_visible():
                    logger.info("WhatsApp session validated")
                    return
            except Exception:
                pass

            await asyncio.sleep(2)

        raise TimeoutError("WhatsApp session validation timeout")

    def _send_message(self, recipient: str, message: str) -> bool:
        """Send WhatsApp message.

        Args:
            recipient: Recipient name
            message: Message content

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.event_loop or not self.event_loop.is_running():
                logger.error("Event loop not running")
                return False

            future = asyncio.run_coroutine_threadsafe(
                self._async_send_message(recipient, message), self.event_loop
            )
            return future.result(timeout=30)

        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False

    async def _async_send_message(self, recipient: str, message: str) -> bool:
        """Async send WhatsApp message.

        Args:
            recipient: Recipient name
            message: Message content

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Sending WhatsApp message to {recipient}")

            # Search for contact
            search_box = await self.page.query_selector('[data-testid="chat-list-search"]')
            if not search_box:
                logger.error("Search box not found")
                return False

            await search_box.click()
            await search_box.fill(recipient)
            await asyncio.sleep(2)

            # Click on first result
            first_result = await self.page.query_selector('[data-testid="cell-frame-container"]')
            if not first_result:
                logger.error(f"Contact not found: {recipient}")
                return False

            await first_result.click()
            await asyncio.sleep(1)

            # Type message
            message_box = await self.page.query_selector('[data-testid="conversation-compose-box-input"]')
            if not message_box:
                logger.error("Message box not found")
                return False

            await message_box.click()
            await message_box.fill(message)
            await asyncio.sleep(0.5)

            # Send message
            send_button = await self.page.query_selector('[data-testid="send"]')
            if not send_button:
                # Try pressing Enter as fallback
                await self.page.keyboard.press("Enter")
            else:
                await send_button.click()

            await asyncio.sleep(1)

            logger.info(f"WhatsApp message sent to {recipient}")
            return True

        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            return False

    def _log_execution(
        self,
        approval: ApprovalRequest,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """Log execution to audit trail.

        Args:
            approval: Approval request
            success: Whether execution was successful
            error: Error message if failed
        """
        try:
            log_entry = LogEntry(
                timestamp=datetime.now(),
                level=LogLevel.INFO if success else LogLevel.ERROR,
                category=LogEntryCategory.EXECUTOR,
                message=f"WhatsApp send {'succeeded' if success else 'failed'}: {approval.approval_id}",
                agent_id=self.agent_id,
                details={
                    "approval_id": approval.approval_id,
                    "recipient": approval.metadata.get("recipient"),
                    "result": "success" if success else "failure",
                },
                approval_id=approval.approval_id,
                error_type=type(error).__name__ if error else None,
                stack_trace=str(error) if error else None,
            )

            # Write to daily log file
            log_folder = "Logs"
            log_filename = f"{datetime.now().strftime('%Y-%m-%d')}.md"
            log_path = self.vault_manager.get_folder_path(log_folder) / log_filename

            # Append to log file
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"{log_entry.to_json_line()}\n")

        except Exception as e:
            logger.error(f"Failed to log execution: {e}")

    def cleanup(self) -> None:
        """Cleanup Playwright resources."""
        try:
            if self.event_loop and self.event_loop.is_running():
                future = asyncio.run_coroutine_threadsafe(self._async_cleanup(), self.event_loop)
                future.result(timeout=10)

                self.event_loop.call_soon_threadsafe(self.event_loop.stop)

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def _async_cleanup(self):
        """Async cleanup of Playwright resources."""
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.error(f"Error cleaning up Playwright: {e}")
