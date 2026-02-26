"""Cloud agent main orchestrator for Platinum Tier AI Employee.

The cloud agent runs 24/7 on a cloud VM and is responsible for:
- Monitoring Gmail for new messages (via GmailWatcher)
- Drafting email responses, social posts, and accounting entries
- Writing drafts to Pending_Approval folders in the vault
- Syncing vault with local agent via Git/Syncthing

Security: Cloud agent can only draft, never execute sensitive actions.
All sensitive credentials remain local-only.
"""

import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.base_agent import BaseAgent
from shared.models.agent_state import AgentType
from shared.models.vault_config import VaultConfig
from shared.models.action_file import ActionFile, ActionStatus
from shared.utils.vault_manager import VaultManager
from shared.utils.logger import VaultLogger, LogCategory
from shared.sync_manager import SyncManager

from cloud_agent.watchers.gmail_watcher import GmailWatcher
from cloud_agent.src.drafters.email_drafter import EmailDrafter
from cloud_agent.src.config import CloudAgentConfig


logger = logging.getLogger(__name__)


class CloudAgent(BaseAgent):
    """Cloud agent orchestrator.

    Monitors external services and drafts responses for approval.
    Runs 24/7 on cloud VM.
    """

    def __init__(self, config: CloudAgentConfig):
        """Initialize cloud agent.

        Args:
            config: Cloud agent configuration
        """
        # Initialize vault config
        vault_config = VaultConfig(
            vault_root=config.vault_path,
            sync_method=config.sync_method
        )

        # Initialize base agent
        super().__init__(
            agent_id="cloud_agent",
            agent_type=AgentType.CLOUD,
            agent_name="Cloud Agent",
            vault_config=vault_config,
            config=config.to_dict(),
        )

        self.config = config

        # Initialize sync manager
        self.sync_manager = SyncManager(
            vault_config=vault_config,
            vault_logger=self.vault_logger,
        )

        # Watchers
        self.gmail_watcher: Optional[GmailWatcher] = None

        # Drafters
        self.email_drafter: Optional[EmailDrafter] = None

        logger.info(f"Cloud agent initialized (vault={config.vault_path})")

    def setup(self) -> None:
        """Setup cloud agent resources."""
        self.vault_logger.info(
            LogCategory.AGENT,
            "Setting up cloud agent",
            details={"vault_path": self.config.vault_path}
        )

        # Initialize Gmail watcher if enabled
        if self.config.gmail_enabled:
            self.gmail_watcher = GmailWatcher(
                agent_id=self.agent_id,
                vault_manager=self.vault_manager,
                vault_logger=self.vault_logger,
                credentials_path=self.config.gmail_credentials_path,
                token_path=self.config.gmail_token_path,
                check_interval_seconds=self.config.gmail_check_interval,
            )
            self.gmail_watcher.start()
            self.vault_logger.info(LogCategory.WATCHER, "Gmail watcher started")

        # Initialize email drafter
        self.email_drafter = EmailDrafter(
            agent_id=self.agent_id,
            vault_manager=self.vault_manager,
            vault_logger=self.vault_logger,
            claude_api_key=self.config.claude_api_key,
            company_handbook_path=self.config.company_handbook_path,
        )

        # Initial vault sync
        self._sync_vault()

        self.vault_logger.info(LogCategory.AGENT, "Cloud agent setup complete")

    def process_cycle(self) -> None:
        """Execute one processing cycle."""
        # Check watchers
        if self.gmail_watcher:
            self.gmail_watcher.check()

        # Process action files in Needs_Action
        self._process_needs_action()

        # Sync vault periodically
        self._sync_vault()

        # Sleep briefly
        time.sleep(5)

    def cleanup(self) -> None:
        """Cleanup cloud agent resources."""
        self.vault_logger.info(LogCategory.AGENT, "Cleaning up cloud agent")

        # Stop watchers
        if self.gmail_watcher:
            self.gmail_watcher.stop()

        # Final vault sync
        self._sync_vault()

        self.vault_logger.info(LogCategory.AGENT, "Cloud agent cleanup complete")

    def _process_needs_action(self) -> None:
        """Process action files in Needs_Action folders."""
        # Process email actions
        email_folder = "Needs_Action/email"
        email_files = self.vault_manager.list_files(email_folder, pattern="*.md")

        for file_path in email_files:
            try:
                # Load action file
                action = ActionFile.from_file(str(file_path))

                # Skip if already claimed
                if action.claimed_by:
                    continue

                # Claim action
                action.claimed_by = self.agent_id
                action.claimed_at = datetime.now()
                action.status = ActionStatus.IN_PROGRESS

                # Move to In_Progress
                in_progress_folder = f"In_Progress/{self.agent_type.value}"
                new_path = self.vault_manager.move_file(
                    file_path,
                    in_progress_folder
                )
                action.to_file(str(new_path))

                # Draft email response
                if self.email_drafter:
                    self.email_drafter.draft_response(action)

                # Move to Done
                done_folder = "Done"
                self.vault_manager.move_file(
                    new_path,
                    done_folder
                )

                self.vault_logger.info(
                    LogCategory.AGENT,
                    f"Processed email action: {action.action_id}",
                    details={"action_id": action.action_id}
                )

            except Exception as e:
                self.vault_logger.error(
                    LogCategory.AGENT,
                    f"Failed to process action file: {file_path}",
                    error_type=type(e).__name__,
                    stack_trace=str(e),
                )

    def _sync_vault(self) -> None:
        """Sync vault with remote."""
        try:
            # Pull changes from remote
            self.sync_manager.pull()

            # Push local changes
            self.sync_manager.push()

        except Exception as e:
            logger.error(f"Vault sync failed: {e}")


def main():
    """Main entry point for cloud agent."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Load configuration
    config = CloudAgentConfig.from_env()

    # Create and start agent
    agent = CloudAgent(config)

    try:
        agent.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
