"""File watcher utility for monitoring vault folders."""

import time
from pathlib import Path
from typing import Callable, List, Optional, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
import logging


logger = logging.getLogger(__name__)


class VaultFileHandler(FileSystemEventHandler):
    """File system event handler for vault folders."""

    def __init__(
        self,
        on_created: Optional[Callable[[Path], None]] = None,
        on_modified: Optional[Callable[[Path], None]] = None,
        on_deleted: Optional[Callable[[Path], None]] = None,
        on_moved: Optional[Callable[[Path, Path], None]] = None,
        file_pattern: str = "*.md",
        debounce_ms: int = 100,
    ):
        """Initialize file handler.

        Args:
            on_created: Callback for file creation events
            on_modified: Callback for file modification events
            on_deleted: Callback for file deletion events
            on_moved: Callback for file move events (src, dest)
            file_pattern: File pattern to watch (e.g., "*.md")
            debounce_ms: Debounce delay in milliseconds
        """
        super().__init__()
        self.on_created_callback = on_created
        self.on_modified_callback = on_modified
        self.on_deleted_callback = on_deleted
        self.on_moved_callback = on_moved
        self.file_pattern = file_pattern
        self.debounce_seconds = debounce_ms / 1000.0

        # Debouncing state
        self._last_event_time: dict[str, float] = {}
        self._processed_events: Set[str] = set()

    def _should_process(self, file_path: Path) -> bool:
        """Check if file should be processed based on pattern and debouncing.

        Args:
            file_path: Path to the file

        Returns:
            True if should process, False otherwise
        """
        # Check file pattern
        if not file_path.match(self.file_pattern):
            return False

        # Check debouncing
        file_key = str(file_path)
        current_time = time.time()
        last_time = self._last_event_time.get(file_key, 0)

        if current_time - last_time < self.debounce_seconds:
            return False

        self._last_event_time[file_key] = current_time
        return True

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation event.

        Args:
            event: File system event
        """
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        if self._should_process(file_path) and self.on_created_callback:
            try:
                logger.debug(f"File created: {file_path}")
                self.on_created_callback(file_path)
            except Exception as e:
                logger.error(f"Error processing created file {file_path}: {e}")

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification event.

        Args:
            event: File system event
        """
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        if self._should_process(file_path) and self.on_modified_callback:
            try:
                logger.debug(f"File modified: {file_path}")
                self.on_modified_callback(file_path)
            except Exception as e:
                logger.error(f"Error processing modified file {file_path}: {e}")

    def on_deleted(self, event: FileSystemEvent) -> None:
        """Handle file deletion event.

        Args:
            event: File system event
        """
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        if self.on_deleted_callback:
            try:
                logger.debug(f"File deleted: {file_path}")
                self.on_deleted_callback(file_path)
            except Exception as e:
                logger.error(f"Error processing deleted file {file_path}: {e}")

    def on_moved(self, event: FileSystemEvent) -> None:
        """Handle file move event.

        Args:
            event: File system event
        """
        if event.is_directory:
            return

        src_path = Path(event.src_path)
        dest_path = Path(event.dest_path)

        if self.on_moved_callback:
            try:
                logger.debug(f"File moved: {src_path} -> {dest_path}")
                self.on_moved_callback(src_path, dest_path)
            except Exception as e:
                logger.error(f"Error processing moved file {src_path} -> {dest_path}: {e}")


class FileWatcher:
    """File watcher for monitoring vault folders."""

    def __init__(self, debounce_ms: int = 100):
        """Initialize file watcher.

        Args:
            debounce_ms: Debounce delay in milliseconds
        """
        self.observer = Observer()
        self.debounce_ms = debounce_ms
        self.handlers: List[VaultFileHandler] = []
        self._running = False

    def watch_folder(
        self,
        folder_path: Path,
        on_created: Optional[Callable[[Path], None]] = None,
        on_modified: Optional[Callable[[Path], None]] = None,
        on_deleted: Optional[Callable[[Path], None]] = None,
        on_moved: Optional[Callable[[Path, Path], None]] = None,
        file_pattern: str = "*.md",
        recursive: bool = False,
    ) -> None:
        """Watch a folder for file system events.

        Args:
            folder_path: Path to the folder to watch
            on_created: Callback for file creation events
            on_modified: Callback for file modification events
            on_deleted: Callback for file deletion events
            on_moved: Callback for file move events
            file_pattern: File pattern to watch
            recursive: Whether to watch subdirectories
        """
        if not folder_path.exists():
            logger.warning(f"Folder does not exist: {folder_path}")
            return

        handler = VaultFileHandler(
            on_created=on_created,
            on_modified=on_modified,
            on_deleted=on_deleted,
            on_moved=on_moved,
            file_pattern=file_pattern,
            debounce_ms=self.debounce_ms,
        )

        self.handlers.append(handler)
        self.observer.schedule(handler, str(folder_path), recursive=recursive)
        logger.info(f"Watching folder: {folder_path} (recursive={recursive})")

    def start(self) -> None:
        """Start the file watcher."""
        if not self._running:
            self.observer.start()
            self._running = True
            logger.info("File watcher started")

    def stop(self) -> None:
        """Stop the file watcher."""
        if self._running:
            self.observer.stop()
            self.observer.join()
            self._running = False
            logger.info("File watcher stopped")

    def is_running(self) -> bool:
        """Check if file watcher is running.

        Returns:
            True if running, False otherwise
        """
        return self._running
