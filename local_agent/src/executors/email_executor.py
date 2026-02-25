"""Email executor for local agent.

Executes approved email sends via Email MCP server.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any

from shared.base_executor import BaseExecutor
from shared.models.approval_request import ApprovalRequest, ApprovalType
from shared.models.log_entry import LogEntry, LogCategory as LogEntryCategory, LogLevel
from shared.utils.vault_manager import VaultManager
from shared.utils.logger import VaultLogger, LogCategory


logger = logging.getLogger(__name__)


class EmailExecutor(BaseExecutor):
    """Executes approved email sends.

    Communicates with Email MCP server to send emails via Gmail API.
    """

    def __init__(
        self,
        agent_id: str,
        vault_manager: VaultManager,
        vault_logger: VaultLogger,
        mcp_client: Any,
        dev_mode: bool = False,
        dry_run: bool = False,
    ):
        """Initialize email executor.

        Args:
            agent_id: Agent ID
            vault_manager: Vault manager instance
            vault_logger: Vault logger instance
            mcp_client: MCP client for email operations
            dev_mode: Development mode flag
            dry_run: Dry run mode flag
        """
        super().__init__(
            executor_id=f"{agent_id}_email_executor",
            executor_name="Email Executor",
            agent_id=agent_id,
            vault_manager=vault_manager,
            vault_logger=vault_logger,
            dev_mode=dev_mode,
            dry_run=dry_run,
        )

        self.mcp_client = mcp_client

        logger.info("Email executor initialized")

    def can_execute(self, approval: ApprovalRequest) -> bool:
        """Check if this executor can handle the approval request.

        Args:
            approval: Approval request

        Returns:
            True if can execute, False otherwise
        """
        return approval.approval_type == ApprovalType.EMAIL_SEND

    def execute(self, approval: ApprovalRequest) -> bool:
        """Execute approved email send.

        Args:
            approval: Approved email send request

        Returns:
            True if successful, False otherwise
        """
        try:
            self.vault_logger.info(
                LogCategory.EXECUTOR,
                f"Executing email send: {approval.approval_id}",
                details={
                    "approval_id": approval.approval_id,
                    "recipient": approval.target_id,
                }
            )

            # Extract email parameters
            recipient = approval.metadata.get("recipient")
            subject = approval.metadata.get("subject")
            body = approval.body
            thread_id = approval.metadata.get("thread_id")

            # Development/dry-run mode
            if self.dev_mode or self.dry_run:
                self.vault_logger.info(
                    LogCategory.EXECUTOR,
                    f"[DRY RUN] Would send email to {recipient}",
                    details={
                        "recipient": recipient,
                        "subject": subject,
                        "body_preview": body[:100],
                    }
                )
                return True

            # Send email via MCP
            result = self._send_email(
                recipient=recipient,
                subject=subject,
                body=body,
                thread_id=thread_id,
            )

            if result:
                self.vault_logger.info(
                    LogCategory.EXECUTOR,
                    f"Email sent successfully: {approval.approval_id}",
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
                    f"Failed to send email: {approval.approval_id}",
                    details={
                        "approval_id": approval.approval_id,
                        "recipient": recipient,
                    }
                )

                # Log to audit trail
                self._log_execution(approval, success=False, error="Email send failed")

                return False

        except Exception as e:
            self.vault_logger.error(
                LogCategory.EXECUTOR,
                f"Error executing email send: {e}",
                error_type=type(e).__name__,
                stack_trace=str(e),
            )

            # Log to audit trail
            self._log_execution(approval, success=False, error=str(e))

            return False

    def _send_email(
        self,
        recipient: str,
        subject: str,
        body: str,
        thread_id: Optional[str] = None,
    ) -> bool:
        """Send email via MCP server.

        Args:
            recipient: Recipient email address
            subject: Email subject
            body: Email body
            thread_id: Thread ID for reply

        Returns:
            True if successful, False otherwise
        """
        try:
            # For MVP, use simple implementation
            # TODO: Integrate with Email MCP server

            logger.info(f"Sending email to {recipient}: {subject}")

            # Simulate email send for MVP
            # In production, this would call the MCP server
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
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
                message=f"Email send {'succeeded' if success else 'failed'}: {approval.approval_id}",
                agent_id=self.agent_id,
                details={
                    "approval_id": approval.approval_id,
                    "subject": approval.metadata.get("subject"),
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
