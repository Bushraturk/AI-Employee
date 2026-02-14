"""FileSystem Watcher - Monitors Inbox folder for new task files."""

from pathlib import Path
from typing import List, Dict, Any
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from watchers.base_watcher import BaseWatcher, WatcherStatus

logger = logging.getLogger(__name__)


class TaskFileHandler(FileSystemEventHandler):
    """Handles file system events for task files."""

    def __init__(self, watcher: 'FileSystemWatcher'):
        """Initialize handler with reference to parent watcher.

        Args:
            watcher: Parent FileSystemWatcher instance
        """
        self.watcher = watcher
        super().__init__()

    def on_created(self, event: FileCreatedEvent) -> None:
        """Handle file creation events.

        Args:
            event: File creation event
        """
        # Ignore directories
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Check if it's a markdown file
        if file_path.suffix.lower() in self.watcher.config.get('file_extensions', ['.md']):
            logger.info(f"Detected new task file: {file_path.name}")
            self.watcher._add_detected_task(file_path)


class FileSystemWatcher(BaseWatcher):
    """Watches filesystem for new task files in Inbox folder."""

    def __init__(self, vault_path: str, config: Dict[str, Any]):
        """Initialize FileSystem watcher.

        Args:
            vault_path: Path to the vault directory
            config: Configuration dictionary with:
                - inbox_folder: Name of inbox folder (default: 'Inbox')
                - file_extensions: List of file extensions to watch (default: ['.md'])
                - watch_recursive: Whether to watch subdirectories (default: False)
        """
        super().__init__(
            watcher_id='filesystem-watcher',
            watcher_type='filesystem',
            config=config
        )

        self.vault_path = Path(vault_path).resolve()
        self.inbox_path = self.vault_path / config.get('inbox_folder', 'Inbox')

        # Detected tasks queue
        self._detected_tasks: List[Dict[str, Any]] = []

        # Watchdog observer
        self._observer: Optional[Observer] = None
        self._event_handler: Optional[TaskFileHandler] = None

    def start(self) -> None:
        """Begin monitoring Inbox folder for new files."""
        try:
            # Validate inbox path exists
            if not self.inbox_path.exists():
                raise ValueError(f"Inbox folder does not exist: {self.inbox_path}")

            # Create event handler and observer
            self._event_handler = TaskFileHandler(self)
            self._observer = Observer()

            # Schedule observer
            recursive = self.config.get('watch_recursive', False)
            self._observer.schedule(
                self._event_handler,
                str(self.inbox_path),
                recursive=recursive
            )

            # Start observer
            self._observer.start()

            self.status = WatcherStatus.RUNNING
            self._reset_error_count()
            logger.info(f"FileSystem watcher started, monitoring: {self.inbox_path}")

        except Exception as e:
            self.status = WatcherStatus.ERROR
            self._increment_error_count()
            logger.error(f"Failed to start FileSystem watcher: {e}")
            raise

    def stop(self) -> None:
        """Gracefully shutdown filesystem monitoring."""
        try:
            if self._observer and self._observer.is_alive():
                self._observer.stop()
                self._observer.join(timeout=5.0)

            self.status = WatcherStatus.STOPPED
            logger.info("FileSystem watcher stopped")

        except Exception as e:
            logger.error(f"Error stopping FileSystem watcher: {e}")
            raise

    def get_new_tasks(self) -> List[Dict[str, Any]]:
        """Return list of newly detected tasks and clear the queue.

        Returns:
            List of task dictionaries with file_path and detected_at
        """
        self._update_last_check()

        # Get all detected tasks
        tasks = self._detected_tasks.copy()

        # Clear the queue
        self._detected_tasks.clear()

        logger.debug(f"Retrieved {len(tasks)} new tasks")
        return tasks

    def mark_processed(self, task_id: str) -> None:
        """Acknowledge that a task has been handled.

        For FileSystem watcher, this is a no-op since tasks are removed
        from the queue when retrieved.

        Args:
            task_id: Unique identifier of the processed task
        """
        logger.debug(f"Task marked as processed: {task_id}")

    def _add_detected_task(self, file_path: Path) -> None:
        """Add a detected task to the queue.

        Args:
            file_path: Path to the detected task file
        """
        from datetime import datetime

        task = {
            'file_path': str(file_path.resolve()),
            'detected_at': datetime.now().isoformat()
        }

        self._detected_tasks.append(task)
        logger.debug(f"Added task to queue: {file_path.name}")

    def scan_existing_files(self) -> int:
        """Scan Inbox for existing files and add them to queue.

        Useful for processing files that were added while system was offline.

        Returns:
            Number of files found and added to queue
        """
        try:
            file_extensions = self.config.get('file_extensions', ['.md'])
            count = 0

            for file_path in self.inbox_path.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in file_extensions:
                    self._add_detected_task(file_path)
                    count += 1

            logger.info(f"Scanned Inbox: found {count} existing files")
            return count

        except Exception as e:
            logger.error(f"Error scanning existing files: {e}")
            return 0
