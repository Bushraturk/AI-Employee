"""Base watcher framework for monitoring external services."""

import time
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging

from shared.models.watcher_state import WatcherState, WatcherStatus, WatcherType
from shared.models.action_file import ActionFile
from shared.utils.vault_manager import VaultManager
from shared.utils.logger import VaultLogger, LogCategory


logger = logging.getLogger(__name__)


class BaseWatcher(ABC):
    """Base class for watchers that monitor external services.

    Provides common functionality for polling, state management,
    and event detection.
    """

    def __init__(
        self,
        watcher_id: str,
        watcher_type: WatcherType,
        watcher_name: str,
        agent_id: str,
        vault_manager: VaultManager,
        vault_logger: VaultLogger,
        check_interval_seconds: int = 60,
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize base watcher.

        Args:
            watcher_id: Unique watcher identifier
            watcher_type: Type of watcher
            watcher_name: Human-readable watcher name
            agent_id: Agent that owns this watcher
            vault_manager: Vault manager instance
            vault_logger: Vault logger instance
            check_interval_seconds: Check interval in seconds
            config: Watcher-specific configuration
        """
        self.watcher_id = watcher_id
        self.watcher_type = watcher_type
        self.watcher_name = watcher_name
        self.agent_id = agent_id
        self.vault_manager = vault_manager
        self.vault_logger = vault_logger
        self.check_interval_seconds = check_interval_seconds
        self.config = config or {}

        # Watcher state
        now = datetime.now()
        self.state = WatcherState(
            watcher_id=watcher_id,
            watcher_type=watcher_type,
            watcher_name=watcher_name,
            agent_id=agent_id,
            status=WatcherStatus.STARTING,
            last_check=now,
            next_check=now + timedelta(seconds=check_interval_seconds),
            check_interval_seconds=check_interval_seconds,
            config=self.config,
        )

        logger.info(f"Initialized watcher: {watcher_name} (interval={check_interval_seconds}s)")

    @abstractmethod
    def check_for_events(self) -> List[ActionFile]:
        """Check for new events from the external service.

        Must be implemented by subclasses.

        Returns:
            List of detected action files
        """
        pass

    @abstractmethod
    def get_target_folder(self) -> str:
        """Get target vault folder for detected events.

        Must be implemented by subclasses.

        Returns:
            Folder path (e.g., "Needs_Action/email")
        """
        pass

    def start(self) -> None:
        """Start the watcher."""
        self.vault_logger.info(
            LogCategory.WATCHER,
            f"Starting watcher: {self.watcher_name}",
            watcher_id=self.watcher_id,
        )

        self.state.status = WatcherStatus.RUNNING
        self._save_state()

    def stop(self) -> None:
        """Stop the watcher."""
        self.vault_logger.info(
            LogCategory.WATCHER,
            f"Stopping watcher: {self.watcher_name}",
            watcher_id=self.watcher_id,
        )

        self.state.status = WatcherStatus.STOPPED
        self._save_state()

    def check(self) -> int:
        """Execute one check cycle.

        Returns:
            Number of events detected
        """
        now = datetime.now()

        # Check if it's time to run
        if now < self.state.next_check:
            return 0

        try:
            self.state.status = WatcherStatus.SYNCING
            self.state.last_check = now
            self.state.total_checks += 1
            self._save_state()

            self.vault_logger.debug(
                LogCategory.WATCHER,
                f"Checking {self.watcher_name}",
                watcher_id=self.watcher_id,
            )

            # Check for events
            events = self.check_for_events()

            # Write events to vault
            target_folder = self.get_target_folder()
            for event in events:
                self.vault_manager.write_action_file(event, target_folder)
                self.state.events_detected += 1

            # Update state
            self.state.events_processed += self.state.events_detected
            self.state.last_sync_at = now
            self.state.next_check = now + timedelta(seconds=self.check_interval_seconds)
            self.state.status = WatcherStatus.RUNNING
            self.state.consecutive_errors = 0  # Reset on success
            self._save_state()

            if events:
                self.vault_logger.info(
                    LogCategory.WATCHER,
                    f"{self.watcher_name} detected {len(events)} events",
                    watcher_id=self.watcher_id,
                    details={"event_count": len(events)},
                )

            return len(events)

        except Exception as e:
            self._handle_error(e)
            return 0

    def _handle_error(self, error: Exception) -> None:
        """Handle error during check.

        Args:
            error: Exception that occurred
        """
        self.state.errors_count += 1
        self.state.consecutive_errors += 1
        self.state.last_error = str(error)
        self.state.last_error_at = datetime.now()
        self.state.status = WatcherStatus.ERROR

        self.vault_logger.error(
            LogCategory.WATCHER,
            f"Error in {self.watcher_name}: {error}",
            watcher_id=self.watcher_id,
            error_type=type(error).__name__,
            stack_trace=str(error),
        )

        # Exponential backoff on consecutive errors
        backoff_multiplier = min(2 ** self.state.consecutive_errors, 16)
        self.state.next_check = datetime.now() + timedelta(
            seconds=self.check_interval_seconds * backoff_multiplier
        )

        self._save_state()

        # Reset status after delay
        time.sleep(5)
        self.state.status = WatcherStatus.RUNNING

    def _save_state(self) -> None:
        """Save watcher state to vault."""
        try:
            state_folder = f"In_Progress/{self.agent_id.split('_')[0]}"  # Extract agent type
            state_path = self.vault_manager.get_folder_path(state_folder) / self.state.get_filename()
            self.state.to_file(str(state_path))
        except Exception as e:
            logger.error(f"Failed to save watcher state: {e}")

    def is_healthy(self) -> bool:
        """Check if watcher is healthy.

        Returns:
            True if healthy, False otherwise
        """
        return self.state.is_healthy()

    def get_state_path(self) -> Path:
        """Get path to watcher state file.

        Returns:
            Path to watcher state file
        """
        state_folder = f"In_Progress/{self.agent_id.split('_')[0]}"
        return self.vault_manager.get_folder_path(state_folder) / self.state.get_filename()
