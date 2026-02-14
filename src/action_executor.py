"""Action Executor - Safe file operations within vault boundaries."""

from pathlib import Path
from typing import Optional
import shutil
import logging
import os

logger = logging.getLogger(__name__)


class ActionExecutor:
    """Executes safe file operations within the vault directory."""

    def __init__(self, vault_path: str):
        """Initialize ActionExecutor with vault path.

        Args:
            vault_path: Absolute path to the vault directory
        """
        self.vault_path = Path(vault_path).resolve()

    def move_file(self, source: Path, destination: Path) -> bool:
        """Move a file from source to destination within vault.

        Args:
            source: Source file path
            destination: Destination file path

        Returns:
            True if move succeeded, False otherwise
        """
        try:
            # Validate both paths are within vault
            if not self.validate_vault_path(source):
                logger.error(f"Source path outside vault: {source}")
                return False

            if not self.validate_vault_path(destination):
                logger.error(f"Destination path outside vault: {destination}")
                return False

            # Check source exists
            if not source.exists():
                logger.error(f"Source file does not exist: {source}")
                return False

            # Create destination directory if needed
            destination.parent.mkdir(parents=True, exist_ok=True)

            # Use atomic move operation
            shutil.move(str(source), str(destination))

            logger.info(f"Moved file: {source.name} -> {destination.parent.name}/")
            return True

        except Exception as e:
            logger.error(f"Error moving file {source.name}: {e}")
            return False

    def atomic_write(self, file_path: Path, content: str) -> bool:
        """Write content to file atomically using temp file + rename.

        Args:
            file_path: Target file path
            content: Content to write

        Returns:
            True if write succeeded, False otherwise
        """
        try:
            # Validate path is within vault
            if not self.validate_vault_path(file_path):
                logger.error(f"File path outside vault: {file_path}")
                return False

            # Create parent directory if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write to temp file
            temp_path = file_path.with_suffix(file_path.suffix + '.tmp')
            temp_path.write_text(content, encoding='utf-8')

            # Atomic rename
            os.replace(str(temp_path), str(file_path))

            logger.debug(f"Atomic write completed: {file_path.name}")
            return True

        except Exception as e:
            logger.error(f"Error writing file {file_path.name}: {e}")
            # Clean up temp file if it exists
            if temp_path.exists():
                temp_path.unlink()
            return False

    def validate_vault_path(self, file_path: Path) -> bool:
        """Validate that file path is within vault boundary.

        Uses pathlib.resolve() to prevent directory traversal attacks.

        Args:
            file_path: Path to validate

        Returns:
            True if path is within vault, False otherwise
        """
        try:
            # Resolve both paths to absolute
            resolved_file = file_path.resolve()
            resolved_vault = self.vault_path.resolve()

            # Check if file path is relative to vault path
            return resolved_file.is_relative_to(resolved_vault)

        except (ValueError, RuntimeError):
            return False

    def check_disk_space(self, required_mb: int = 100) -> bool:
        """Check if sufficient disk space is available.

        Args:
            required_mb: Required space in megabytes

        Returns:
            True if sufficient space available, False otherwise
        """
        try:
            stat = shutil.disk_usage(self.vault_path)
            available_mb = stat.free / (1024 * 1024)

            if available_mb < required_mb:
                logger.warning(f"Low disk space: {available_mb:.1f}MB available, {required_mb}MB required")
                return False

            return True

        except Exception as e:
            logger.error(f"Error checking disk space: {e}")
            return False
