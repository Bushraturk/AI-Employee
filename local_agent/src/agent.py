"""Local agent main orchestrator for Platinum Tier AI Employee.

The local agent runs on user's machine and is responsible for:
- Monitoring Approved folder for approved actions
- Executing approved actions (email sends, social posts, payments)
- Monitoring WhatsApp and finance (when enabled)
- Updating Dashboard.md with system status
- Syncing vault with cloud agent via Git/Syncthing

Security: Local agent has all sensitive credentials.
All execution happens locally, never on cloud.
"""

import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.base_agent import BaseAgent
from shared.models.agent_state import AgentType
from shared.models.vault_config import VaultConfig
from shared.models.approval_request import ApprovalRequest, ApprovalStatus
from shared.utils.vault_manager import VaultManager
from shared.utils.logger import VaultLogger, LogCategory
from shared.sync_manager import SyncManager

from local_agent.src.executors.email_executor import EmailExecutor
from local_agent.src.approval_handler import ApprovalHandler
from local_agent.src.dashboard_updater import DashboardUpdater
from local_agent.src.config import LocalAgentConfig


logger = logging.getLogger(__name__)


class LocalAgent(BaseAgent):
    """Local agent orchestrator.

    Monitors approvals and executes approved actions.
    Runs on user's local machine.
    """

    def __init__(self, config: LocalAgentConfig):
        """Initialize local agent.

        Args:
            config: Local agent configuration
        """
        # Initialize vault config
        vault_config = VaultConfig(
            vault_root=config.vault_path,
            sync_method=config.sync_method
        )

        # Initialize base agent
        super().__init__(
            agent_id="local_agent",
            agent_type=AgentType.LOCAL,
            agent_name="Local Agent",
            vault_config=vault_config,
            config=config.to_dict(),
        )

        self.config = config

        # Initialize sync manager
        self.sync_manager = SyncManager(
            vault_root=config.vault_path,
            sync_method=config.sync_method,
            git_remote=config.git_remote,
            git_branch=config.git_branch,
        )

        # Initialize executors
        self.email_executor: Optional[EmailExecutor] = None

        # Initialize approval handler
        self.approval_handler: Optional[ApprovalHandler] = None

        # Initialize dashboard updater
        self.dashboard_updater: Optional[DashboardUpdater] = None

        # Rate limiting
        self.email_count = 0
        self.email_count_reset_time = datetime.now()

        logger.info(f"Local agent initialized (vault={config.vault_path})")

    def setup(self) -> None:
        """Setup local agent resources."""
        self.vault_logger.info(
            LogCategory.AGENT,
            "Setting up local agent",
            details={"vault_path": self.config.vault_path}
        )

        # Initialize email executor
        self.email_executor = EmailExecutor(
            agent_id=self.agent_id,
            vault_manager=self.vault_manager,
            vault_logger=self.vault_logger,
            mcp_client=None,  # TODO: Initialize MCP client
            dev_mode=self.dev_mode,
            dry_run=self.dry_run,
        )

        # Initialize approval handler
        self.approval_handler = ApprovalHandler(
            agent_id=self.agent_id,
            vault_manager=self.vault_manager,
            vault_logger=self.vault_logger,
            executors=[self.email_executor],
        )

        # Initialize dashboard updater
        self.dashboard_updater = DashboardUpdater(
            agent_id=self.agent_id,
            vault_manager=self.vault_manager,
            vault_logger=self.vault_logger,
        )

        # Initial vault sync
        self._sync_vault()

        self.vault_logger.info(LogCategory.AGENT, "Local agent setup complete")

    def process_cycle(self) -> None:
        """Execute one processing cycle."""
        # Sync vault to get latest approvals from cloud agent
        self._sync_vault()

        # Process approved actions
        self._process_approved_actions()

        # Update dashboard
        if self.dashboard_updater:
            self.dashboard_updater.update_dashboard()

        # Sleep briefly
        time.sleep(5)

    def cleanup(self) -> None:
        """Cleanup local agent resources."""
        self.vault_logger.info(LogCategory.AGENT, "Cleaning up local agent")

        # Final dashboard update
        if self.dashboard_updater:
            self.dashboard_updater.update_dashboard()

        # Final vault sync
        self._sync_vault()

        self.vault_logger.info(LogCategory.AGENT, "Local agent cleanup complete")

    def _process_approved_actions(self) -> None:
        """Process approved actions in Approved folder."""
        if not self.approval_handler:
            return

        # List approved files
        approved_folder = "Approved"
        approved_files = self.vault_manager.list_files(approved_folder, pattern="*.md")

        for file_path in approved_files:
            try:
                # Load approval request
                approval = ApprovalRequest.from_file(str(file_path))

                # Check if expired
                if approval.is_expired():
                    self.vault_logger.warning(
                        LogCategory.AGENT,
                        f"Approval expired: {approval.approval_id}",
                        details={"approval_id": approval.approval_id}
                    )

                    # Move to Rejected folder
                    rejected_folder = "Rejected"
                    self.vault_manager.move_file(
                        str(file_path),
                        rejected_folder,
                        approval.get_filename()
                    )
                    continue

                # Check rate limits
                if not self._check_rate_limit(approval):
                    self.vault_logger.warning(
                        LogCategory.AGENT,
                        f"Rate limit exceeded for: {approval.approval_id}",
                        details={"approval_id": approval.approval_id}
                    )
                    continue

                # Execute approval
                success = self.approval_handler.execute_approval(approval)

                if success:
                    # Move to Done folder
                    done_folder = "Done"
                    self.vault_manager.move_file(
                        str(file_path),
                        done_folder,
                        approval.get_filename()
                    )

                    self.vault_logger.info(
                        LogCategory.AGENT,
                        f"Executed approval: {approval.approval_id}",
                        details={"approval_id": approval.approval_id}
                    )

                    # Update rate limit counter
                    self._update_rate_limit(approval)

                else:
                    self.vault_logger.error(
                        LogCategory.AGENT,
                        f"Failed to execute approval: {approval.approval_id}",
                        details={"approval_id": approval.approval_id}
                    )

            except Exception as e:
                self.vault_logger.error(
                    LogCategory.AGENT,
                    f"Failed to process approval file: {file_path}",
                    error_type=type(e).__name__,
                    stack_trace=str(e),
                )

    def _check_rate_limit(self, approval: ApprovalRequest) -> bool:
        """Check if rate limit allows this action.

        Args:
            approval: Approval request

        Returns:
            True if within rate limit, False otherwise
        """
        # Reset counter if hour has passed
        now = datetime.now()
        if (now - self.email_count_reset_time).total_seconds() > 3600:
            self.email_count = 0
            self.email_count_reset_time = now

        # Check email rate limit
        if approval.approval_type.value == "email_send":
            if self.email_count >= self.config.max_emails_per_hour:
                return False

        return True

    def _update_rate_limit(self, approval: ApprovalRequest) -> None:
        """Update rate limit counter after execution.

        Args:
            approval: Approval request
        """
        if approval.approval_type.value == "email_send":
            self.email_count += 1

    def _sync_vault(self) -> None:
        """Sync vault with remote."""
        try:
            # Pull changes from remote (cloud agent updates)
            self.sync_manager.pull()

            # Push local changes (executed actions, dashboard updates)
            self.sync_manager.push()

        except Exception as e:
            logger.error(f"Vault sync failed: {e}")


def main():
    """Main entry point for local agent."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Load configuration
    config = LocalAgentConfig.from_env()

    # Create and start agent
    agent = LocalAgent(config)

    try:
        agent.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
