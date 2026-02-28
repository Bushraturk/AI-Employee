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
from cloud_agent.src.drafters.social_drafter import SocialDrafter
from cloud_agent.src.drafters.whatsapp_drafter import WhatsAppDrafter
from cloud_agent.src.drafters.accounting_drafter import AccountingDrafter
from cloud_agent.src.config import CloudAgentConfig
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger


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
        self.accounting_drafter: Optional[AccountingDrafter] = None
        self.social_drafter: Optional[SocialDrafter] = None
        self.whatsapp_drafter: Optional[WhatsAppDrafter] = None

        # Scheduler for periodic tasks
        self.scheduler: Optional[BackgroundScheduler] = None

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

        # Initialize WhatsApp drafter
        self.whatsapp_drafter = WhatsAppDrafter(
            agent_id=self.agent_id,
            vault_manager=self.vault_manager,
            vault_logger=self.vault_logger,
            claude_api_key=self.config.claude_api_key,
            company_handbook_path=self.config.company_handbook_path,
        )
        self.vault_logger.info(LogCategory.AGENT, "WhatsApp drafter initialized")

        # Initialize accounting drafter if enabled
        if getattr(self.config, 'accounting_enabled', False):
            self.accounting_drafter = AccountingDrafter(
                agent_id=self.agent_id,
                vault_manager=self.vault_manager,
                vault_logger=self.vault_logger,
                company_handbook_path=self.config.company_handbook_path,
            )
            self.vault_logger.info(LogCategory.AGENT, "Accounting drafter initialized")

        # Initialize social drafter if enabled
        if self.config.social_enabled:
            self.social_drafter = SocialDrafter(
                agent_id=self.agent_id,
                vault_manager=self.vault_manager,
                vault_logger=self.vault_logger,
                claude_api_key=self.config.claude_api_key,
                business_goals_path=self.config.business_goals_path,
            )
            self.vault_logger.info(LogCategory.AGENT, "Social drafter initialized")

            # Setup scheduler for social media posts
            self._setup_scheduler()

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

    def _process_needs_action(self) -> None:
        """Process action files in Needs_Action folders."""
        # Process email actions
        self._process_email_actions()

        # Process accounting actions
        self._process_accounting_actions()

    def _process_email_actions(self) -> None:
        """Process email action files."""
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
                    f"Failed to process email action file: {file_path}",
                    error_type=type(e).__name__,
                    stack_trace=str(e),
                )

    def _process_accounting_actions(self) -> None:
        """Process accounting action files."""
        if not self.accounting_drafter:
            return

        accounting_folder = "Needs_Action/accounting"
        accounting_files = self.vault_manager.list_files(accounting_folder, pattern="*.md")

        for file_path in accounting_files:
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

                # Draft accounting entry
                self.accounting_drafter.draft_entry(action)

                # Move to Done
                done_folder = "Done"
                self.vault_manager.move_file(
                    new_path,
                    done_folder
                )

                self.vault_logger.info(
                    LogCategory.AGENT,
                    f"Processed accounting action: {action.action_id}",
                    details={"action_id": action.action_id}
                )

            except Exception as e:
                self.vault_logger.error(
                    LogCategory.AGENT,
                    f"Failed to process accounting action file: {file_path}",
                    error_type=type(e).__name__,
                    stack_trace=str(e),
                )

    def cleanup(self) -> None:
        """Cleanup cloud agent resources."""
        self.vault_logger.info(LogCategory.AGENT, "Cleaning up cloud agent")

        # Stop scheduler
        if self.scheduler:
            self.scheduler.shutdown()

        # Stop watchers
        if self.gmail_watcher:
            self.gmail_watcher.stop()

        # Final vault sync
        self._sync_vault()

        self.vault_logger.info(LogCategory.AGENT, "Cloud agent cleanup complete")

    def _process_needs_action(self) -> None:
        """Process action files in Needs_Action folders."""
        # Process email actions
        self._process_action_folder("Needs_Action/email", self.email_drafter)

        # Process WhatsApp actions
        self._process_action_folder("Needs_Action/whatsapp", self.whatsapp_drafter)

    def _process_action_folder(self, folder: str, drafter: Any) -> None:
        """Process action files in a specific folder.

        Args:
            folder: Folder path to process
            drafter: Drafter instance to use
        """
        if not drafter:
            return

        action_files = self.vault_manager.list_files(folder, pattern="*.md")

        for file_path in action_files:
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

                # Draft response
                drafter.draft_response(action)

                # Move to Done
                done_folder = "Done"
                self.vault_manager.move_file(
                    new_path,
                    done_folder
                )

                self.vault_logger.info(
                    LogCategory.AGENT,
                    f"Processed action: {action.action_id}",
                    details={"action_id": action.action_id, "type": action.action_type.value}
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

    def _setup_scheduler(self) -> None:
        """Setup APScheduler for periodic social media post generation."""
        try:
            self.scheduler = BackgroundScheduler()

            # Schedule social media posts
            # Monday, Wednesday, Friday at 10:00 AM
            self.scheduler.add_job(
                func=self._generate_social_post,
                trigger=CronTrigger(day_of_week='mon,wed,fri', hour=10, minute=0),
                id='social_post_generation',
                name='Generate social media posts',
                replace_existing=True,
            )

            self.scheduler.start()
            self.vault_logger.info(
                LogCategory.AGENT,
                "Scheduler started for social media post generation"
            )

        except Exception as e:
            self.vault_logger.error(
                LogCategory.AGENT,
                f"Failed to setup scheduler: {e}",
                error_type=type(e).__name__,
                stack_trace=str(e),
            )

    def _generate_social_post(self) -> None:
        """Generate social media post (scheduled task)."""
        try:
            if not self.social_drafter:
                return

            self.vault_logger.info(
                LogCategory.AGENT,
                "Generating scheduled social media post"
            )

            # Generate posts for different platforms
            platforms = ['linkedin', 'twitter', 'facebook']

            for platform in platforms:
                try:
                    self.social_drafter.draft_post(
                        platform=platform,
                        content_type='update',
                    )
                    self.vault_logger.info(
                        LogCategory.AGENT,
                        f"Generated social post for {platform}"
                    )
                except Exception as e:
                    self.vault_logger.error(
                        LogCategory.AGENT,
                        f"Failed to generate post for {platform}: {e}",
                        error_type=type(e).__name__,
                        stack_trace=str(e),
                    )

        except Exception as e:
            self.vault_logger.error(
                LogCategory.AGENT,
                f"Failed to generate social posts: {e}",
                error_type=type(e).__name__,
                stack_trace=str(e),
            )


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
