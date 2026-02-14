"""Base Watcher - Abstract interface for all input source watchers."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime
from enum import Enum


class WatcherStatus(Enum):
    """Watcher operational status."""
    STOPPED = "stopped"
    RUNNING = "running"
    ERROR = "error"


class BaseWatcher(ABC):
    """Abstract base class for all watchers (FileSystem, Gmail, WhatsApp)."""

    def __init__(self, watcher_id: str, watcher_type: str, config: Dict[str, Any]):
        """Initialize base watcher.

        Args:
            watcher_id: Unique identifier for this watcher instance
            watcher_type: Type of watcher (filesystem, gmail, whatsapp)
            config: Watcher-specific configuration dictionary
        """
        self.watcher_id = watcher_id
        self.watcher_type = watcher_type
        self.config = config
        self.status = WatcherStatus.STOPPED
        self.last_check_at = None
        self.error_count = 0

    @abstractmethod
    def start(self) -> None:
        """Begin monitoring input source.

        Must be implemented by concrete watcher classes.
        Should set status to RUNNING on success.

        Raises:
            Exception: If watcher fails to start
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """Gracefully shutdown monitoring.

        Must be implemented by concrete watcher classes.
        Should set status to STOPPED on success.
        Should complete any in-flight operations before stopping.
        """
        pass

    @abstractmethod
    def get_new_tasks(self) -> List[Dict[str, Any]]:
        """Return list of newly detected tasks.

        Must be implemented by concrete watcher classes.

        Returns:
            List of task dictionaries with at minimum:
            - file_path: Path to task file
            - detected_at: Timestamp when task was detected

        Raises:
            Exception: If task retrieval fails
        """
        pass

    @abstractmethod
    def mark_processed(self, task_id: str) -> None:
        """Acknowledge that a task has been handled.

        Must be implemented by concrete watcher classes.

        Args:
            task_id: Unique identifier of the processed task

        Raises:
            Exception: If marking fails
        """
        pass

    def get_status(self) -> Dict[str, Any]:
        """Get current watcher status.

        Returns:
            Dictionary with watcher status information
        """
        return {
            'watcher_id': self.watcher_id,
            'watcher_type': self.watcher_type,
            'status': self.status.value,
            'last_check_at': self.last_check_at.isoformat() if self.last_check_at else None,
            'error_count': self.error_count
        }

    def _update_last_check(self) -> None:
        """Update last check timestamp to current time."""
        self.last_check_at = datetime.now()

    def _increment_error_count(self) -> None:
        """Increment error counter."""
        self.error_count += 1

    def _reset_error_count(self) -> None:
        """Reset error counter to zero."""
        self.error_count = 0
