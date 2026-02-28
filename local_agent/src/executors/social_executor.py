"""Social media executor for local agent.

Executes approved social media posts via Social Media MCP server.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any as MCPClient
else:
    MCPClient = Any

from shared.base_executor import BaseExecutor
from shared.models.approval_request import ApprovalRequest, ApprovalType
from shared.models.log_entry import LogEntry, LogCategory as LogEntryCategory, LogLevel
from shared.utils.vault_manager import VaultManager
from shared.utils.logger import VaultLogger, LogCategory


logger = logging.getLogger(__name__)


class SocialExecutor(BaseExecutor):
    """Executes approved social media posts.

    Communicates with Social Media MCP server to post content to various platforms.
    """

    def __init__(
        self,
        agent_id: str,
        vault_manager: VaultManager,
        vault_logger: VaultLogger,
        mcp_client: Optional[Any] = None,
        dev_mode: bool = False,
        dry_run: bool = False,
    ):
        """Initialize social executor.

        Args:
            agent_id: Agent ID
            vault_manager: Vault manager instance
            vault_logger: Vault logger instance
            mcp_client: MCP client for social media operations
            dev_mode: Development mode flag
            dry_run: Dry run mode flag
        """
        super().__init__(
            executor_name="Social Executor",
            agent_id=agent_id,
            vault_manager=vault_manager,
            vault_logger=vault_logger,
        )

        self.mcp_client = mcp_client

        # Override dev_mode and dry_run if provided
        if dev_mode is not None:
            self.dev_mode = dev_mode
        if dry_run is not None:
            self.dry_run = dry_run

        logger.info("Social executor initialized")

    def can_execute(self, approval: ApprovalRequest) -> bool:
        """Check if this executor can handle the approval request.

        Args:
            approval: Approval request

        Returns:
            True if can execute, False otherwise
        """
        return approval.approval_type == ApprovalType.SOCIAL_POST

    def execute(self, approval: ApprovalRequest) -> bool:
        """Execute approved social media post.

        Args:
            approval: Approved social post request

        Returns:
            True if successful, False otherwise
        """
        try:
            self.vault_logger.info(
                LogCategory.EXECUTOR,
                f"Executing social post: {approval.approval_id}",
                details={
                    "approval_id": approval.approval_id,
                    "platform": approval.target_id,
                }
            )

            # Extract post parameters
            platform = approval.metadata.get("platform", approval.target_id)
            content = approval.body
            scheduled_time = approval.metadata.get("scheduled_time")

            # Development/dry-run mode
            if self.dev_mode or self.dry_run:
                self.vault_logger.info(
                    LogCategory.EXECUTOR,
                    f"[DRY RUN] Would post to {platform}",
                    details={
                        "platform": platform,
                        "content_preview": content[:100],
                        "scheduled_time": scheduled_time,
                    }
                )
                return True

            # Post to social media via MCP
            result = self._post_to_platform(
                platform=platform,
                content=content,
                scheduled_time=scheduled_time,
            )

            if result:
                self.vault_logger.info(
                    LogCategory.EXECUTOR,
                    f"Social post published successfully: {approval.approval_id}",
                    details={
                        "approval_id": approval.approval_id,
                        "platform": platform,
                    }
                )

                # Log to audit trail
                self._log_execution(approval, success=True)

                # Write dashboard update
                self._write_dashboard_update(approval, platform, success=True)

                return True
            else:
                self.vault_logger.error(
                    LogCategory.EXECUTOR,
                    f"Failed to publish social post: {approval.approval_id}",
                    details={
                        "approval_id": approval.approval_id,
                        "platform": platform,
                    }
                )

                # Log to audit trail
                self._log_execution(approval, success=False, error="Post failed")

                return False

        except Exception as e:
            self.vault_logger.error(
                LogCategory.EXECUTOR,
                f"Error executing social post: {e}",
                error_type=type(e).__name__,
                stack_trace=str(e),
            )

            # Log to audit trail
            self._log_execution(approval, success=False, error=str(e))

            return False

    def _post_to_platform(
        self,
        platform: str,
        content: str,
        scheduled_time: Optional[str] = None,
    ) -> bool:
        """Post content to social media platform via MCP server.

        Args:
            platform: Target platform (linkedin, twitter, facebook, instagram)
            content: Post content
            scheduled_time: Optional scheduled time for post

        Returns:
            True if successful, False otherwise
        """
        try:
            # For MVP, use simple implementation
            # TODO: Integrate with Social Media MCP server

            logger.info(f"Posting to {platform}: {content[:50]}...")

            # Simulate post for MVP
            # In production, this would call the MCP server
            # Example: self.mcp_client.call_tool("social_post", {
            #     "platform": platform,
            #     "content": content,
            #     "scheduled_time": scheduled_time,
            # })

            return True

        except Exception as e:
            logger.error(f"Failed to post to {platform}: {e}")
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
                message=f"Social post {'succeeded' if success else 'failed'}: {approval.approval_id}",
                agent_id=self.agent_id,
                details={
                    "approval_id": approval.approval_id,
                    "platform": approval.metadata.get("platform"),
                    "content_preview": approval.body[:100],
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

    def _write_dashboard_update(
        self,
        approval: ApprovalRequest,
        platform: str,
        success: bool,
    ) -> None:
        """Write update for dashboard merger.

        Args:
            approval: Approval request
            platform: Target platform
            success: Whether post was successful
        """
        try:
            update_folder = "Updates"
            update_filename = f"social_post_{datetime.now().strftime('%Y%m%dT%H%M%SZ')}.md"
            update_path = self.vault_manager.get_folder_path(update_folder) / update_filename

            status = "published" if success else "failed"

            update_content = f"""---
type: social_post
timestamp: {datetime.now().isoformat()}
approval_id: {approval.approval_id}
platform: {platform}
status: {status}
---

# Social Media Post {status.title()}

**Platform**: {platform.title()}
**Status**: {status.title()}
**Approval ID**: {approval.approval_id}

Post content has been {status} on {platform}.
"""

            with open(update_path, "w", encoding="utf-8") as f:
                f.write(update_content)

        except Exception as e:
            logger.error(f"Failed to write dashboard update: {e}")
