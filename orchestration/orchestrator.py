"""Main orchestrator for Platinum tier dual-agent system.

Coordinates folder watching, task scheduling, and process management.
"""

import os
import time
import logging
from pathlib import Path
from typing import Dict, Optional, Callable
from datetime import datetime

from orchestration.scheduler import TaskScheduler
from orchestration.mcp_manager import MCPManager
from orchestration.dashboard_merger import DashboardMerger
from shared.utils.vault_manager import VaultManager
from shared.utils.logger import VaultLogger, LogCategory
from shared.approval_workflow import ApprovalWorkflow


logger = logging.getLogger(__name__)


class Orchestrator:
    """Main orchestrator for the Platinum tier system.

    Responsibilities:
    - Monitor vault folders for new files
    - Schedule periodic tasks (audits, health checks)
    - Coordinate MCP server lifecycle
    - Trigger agent processing
    """

    def __init__(
        self,
        vault_path: Path,
        config_path: Path,
        is_local_agent: bool = False,
        agent_id: str = "orchestrator",
    ):
        """Initialize orchestrator.

        Args:
            vault_path: Path to vault directory
            config_path: Path to MCP configuration file
            is_local_agent: Whether this is the local agent
            agent_id: Agent identifier
        """
        self.vault_path = vault_path
        self.is_local_agent = is_local_agent
        self.agent_id = agent_id
        self._running = False
        self._stop_requested = False

        # Initialize components
        self.vault_manager = VaultManager(vault_path)
        self.vault_logger = VaultLogger(vault_path)
        self.mcp_manager = MCPManager(config_path, is_local_agent)
        self.scheduler = TaskScheduler(
            job_store_path=str(vault_path / ".scheduler.db")
        )
        self.approval_workflow = ApprovalWorkflow(
            self.vault_manager,
            self.vault_logger,
        )

        # Dashboard merger (local agent only)
        if is_local_agent:
            self.dashboard_merger = DashboardMerger(
                self.vault_manager,
                self.vault_logger,
            )
        else:
            self.dashboard_merger = None

        # Folder watch state
        self._last_check_times: Dict[str, float] = {}
        self._processed_files: Dict[str, set] = {}

        logger.info(f"Initialized orchestrator (agent={agent_id}, local={is_local_agent})")

    def start(self) -> None:
        """Start the orchestrator."""
        if self._running:
            logger.warning("Orchestrator is already running")
            return

        logger.info("Starting orchestrator...")

        try:
            # Start MCP servers
            logger.info("Starting MCP servers...")
            results = self.mcp_manager.start_all()
            for name, success in results.items():
                if success:
                    logger.info(f"MCP server started: {name}")
                elif success is False:
                    logger.error(f"Failed to start MCP server: {name}")

            # Start scheduler
            logger.info("Starting task scheduler...")
            self.scheduler.start()

            # Schedule periodic tasks
            self._schedule_periodic_tasks()

            self._running = True
            self._stop_requested = False

            self.vault_logger.info(
                LogCategory.SYSTEM,
                f"Orchestrator started (agent={self.agent_id})",
            )

            logger.info("Orchestrator started successfully")

        except Exception as e:
            logger.error(f"Failed to start orchestrator: {e}")
            raise

    def stop(self) -> None:
        """Stop the orchestrator."""
        if not self._running:
            logger.warning("Orchestrator is not running")
            return

        logger.info("Stopping orchestrator...")

        self._stop_requested = True

        try:
            # Stop scheduler
            logger.info("Stopping task scheduler...")
            self.scheduler.stop()

            # Stop MCP servers
            logger.info("Stopping MCP servers...")
            results = self.mcp_manager.stop_all()
            for name, success in results.items():
                if success:
                    logger.info(f"MCP server stopped: {name}")
                else:
                    logger.error(f"Failed to stop MCP server: {name}")

            self._running = False

            self.vault_logger.info(
                LogCategory.SYSTEM,
                f"Orchestrator stopped (agent={self.agent_id})",
            )

            logger.info("Orchestrator stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping orchestrator: {e}")
            raise

    def run(self) -> None:
        """Run the orchestrator main loop.

        This is a blocking call that runs until stop() is called.
        """
        if not self._running:
            self.start()

        logger.info("Entering orchestrator main loop...")

        try:
            while not self._stop_requested:
                # Monitor folders
                self._check_folders()

                # Check MCP server health
                self._check_mcp_health()

                # Merge dashboard updates (local agent only)
                if self.is_local_agent and self.dashboard_merger:
                    self._merge_dashboard_updates()

                # Check for expired approvals
                self._check_expired_approvals()

                # Sleep briefly
                time.sleep(5)

        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Error in orchestrator main loop: {e}")
            raise
        finally:
            self.stop()

    def _schedule_periodic_tasks(self) -> None:
        """Schedule periodic tasks."""
        # Check expired approvals every 5 minutes
        self.scheduler.add_interval_job(
            func=self._check_expired_approvals,
            seconds=300,
            job_id="check_expired_approvals",
        )

        # Health check MCP servers every 30 seconds
        self.scheduler.add_interval_job(
            func=self._check_mcp_health,
            seconds=30,
            job_id="mcp_health_check",
        )

        # Merge dashboard updates every 10 seconds (local agent only)
        if self.is_local_agent and self.dashboard_merger:
            self.scheduler.add_interval_job(
                func=self._merge_dashboard_updates,
                seconds=10,
                job_id="merge_dashboard_updates",
            )

        logger.info("Scheduled periodic tasks")

    def _check_folders(self) -> None:
        """Check vault folders for new files."""
        # Folders to monitor
        folders = ["Needs_Action", "Approved"]

        for folder in folders:
            try:
                files = self.vault_manager.list_files(folder, "*.md")

                # Initialize processed set for this folder
                if folder not in self._processed_files:
                    self._processed_files[folder] = set()

                # Check for new files
                for file_path in files:
                    file_str = str(file_path)
                    if file_str not in self._processed_files[folder]:
                        logger.info(f"New file detected in {folder}: {file_path.name}")
                        self._processed_files[folder].add(file_str)

                        # Trigger processing callback
                        self._on_new_file(folder, file_path)

            except Exception as e:
                logger.error(f"Error checking folder {folder}: {e}")

    def _on_new_file(self, folder: str, file_path: Path) -> None:
        """Handle new file detection.

        Args:
            folder: Folder name
            file_path: Path to new file
        """
        self.vault_logger.info(
            LogCategory.SYSTEM,
            f"New file in {folder}: {file_path.name}",
            details={"folder": folder, "file": file_path.name},
        )

        # Note: Actual processing is done by agents, not orchestrator
        # Orchestrator just detects and logs new files

    def _check_mcp_health(self) -> None:
        """Check health of MCP servers and restart if needed."""
        try:
            results = self.mcp_manager.monitor_and_restart()

            for name, status in results.items():
                if status == "restart_failed":
                    self.vault_logger.error(
                        LogCategory.SYSTEM,
                        f"MCP server restart failed: {name}",
                    )
                elif status == "restarted":
                    self.vault_logger.warning(
                        LogCategory.SYSTEM,
                        f"MCP server restarted: {name}",
                    )
                elif status == "unhealthy":
                    self.vault_logger.warning(
                        LogCategory.SYSTEM,
                        f"MCP server unhealthy: {name}",
                    )

        except Exception as e:
            logger.error(f"Error checking MCP health: {e}")

    def _merge_dashboard_updates(self) -> None:
        """Merge dashboard updates (local agent only)."""
        if not self.dashboard_merger:
            return

        try:
            count = self.dashboard_merger.merge_updates()
            if count > 0:
                logger.debug(f"Merged {count} dashboard updates")
        except Exception as e:
            logger.error(f"Error merging dashboard updates: {e}")

    def _check_expired_approvals(self) -> None:
        """Check for and handle expired approvals."""
        try:
            count = self.approval_workflow.check_expired_approvals()
            if count > 0:
                logger.info(f"Processed {count} expired approvals")
        except Exception as e:
            logger.error(f"Error checking expired approvals: {e}")

    def is_running(self) -> bool:
        """Check if orchestrator is running.

        Returns:
            True if running, False otherwise
        """
        return self._running

    def get_status(self) -> Dict[str, any]:
        """Get orchestrator status.

        Returns:
            Dictionary with status information
        """
        return {
            "running": self._running,
            "agent_id": self.agent_id,
            "is_local_agent": self.is_local_agent,
            "scheduler_running": self.scheduler.is_running(),
            "mcp_servers": self.mcp_manager.get_status(),
        }
