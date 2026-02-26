"""Vault manager for file operations and synchronization."""

import os
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from shared.models.vault_config import VaultConfig
from shared.models.action_file import ActionFile
from shared.models.approval_request import ApprovalRequest


logger = logging.getLogger(__name__)


class VaultManager:
    """Manages vault file operations and synchronization.

    Provides atomic file operations, folder management, and sync coordination.
    Implements the claim-by-move rule and single-writer pattern.
    """

    def __init__(self, config: VaultConfig):
        """Initialize vault manager.

        Args:
            config: Vault configuration
        """
        self.config = config
        self.vault_root = config.vault_root

        # Ensure required folders exist
        created = config.ensure_folders_exist()
        if created:
            logger.info(f"Created {len(created)} missing vault folders")

    def get_folder_path(self, folder: str) -> Path:
        """Get absolute path for a vault folder.

        Args:
            folder: Folder name (e.g., "Needs_Action/email")

        Returns:
            Absolute path to the folder
        """
        return self.config.get_folder_path(folder)

    def list_files(self, folder: str, pattern: Optional[str] = None) -> List[Path]:
        """List files in a vault folder.

        Args:
            folder: Folder name
            pattern: Optional glob pattern (e.g., "*.md")

        Returns:
            List of file paths
        """
        folder_path = self.get_folder_path(folder)
        if not folder_path.exists():
            return []

        if pattern:
            return list(folder_path.glob(pattern))
        else:
            return [f for f in folder_path.iterdir() if f.is_file()]

    def read_action_file(self, file_path: Path) -> ActionFile:
        """Read an action file from the vault.

        Args:
            file_path: Path to the action file

        Returns:
            ActionFile instance

        Raises:
            ValueError: If file format is invalid
        """
        return ActionFile.from_file(str(file_path))

    def write_action_file(self, action: ActionFile, folder: str) -> Path:
        """Write an action file to the vault.

        Args:
            action: ActionFile instance
            folder: Target folder (e.g., "Needs_Action/email")

        Returns:
            Path to the written file
        """
        folder_path = self.get_folder_path(folder)
        file_path = folder_path / action.get_filename()
        action.to_file(str(file_path))
        logger.debug(f"Wrote action file: {file_path}")
        return file_path

    def read_approval_request(self, file_path: Path) -> ApprovalRequest:
        """Read an approval request file from the vault.

        Args:
            file_path: Path to the approval request file

        Returns:
            ApprovalRequest instance

        Raises:
            ValueError: If file format is invalid
        """
        return ApprovalRequest.from_file(str(file_path))

    def write_approval_request(self, approval: ApprovalRequest, folder: str) -> Path:
        """Write an approval request file to the vault.

        Args:
            approval: ApprovalRequest instance
            folder: Target folder (e.g., "Pending_Approval/email")

        Returns:
            Path to the written file
        """
        folder_path = self.get_folder_path(folder)
        file_path = folder_path / approval.get_filename()
        approval.to_file(str(file_path))
        logger.debug(f"Wrote approval request: {file_path}")
        return file_path

    def move_file(self, source: Path, target_folder: str, max_retries: int = 3) -> Optional[Path]:
        """Move a file atomically (claim-by-move rule).

        Uses atomic rename operation. If the file doesn't exist, another agent
        claimed it first (race condition).

        Args:
            source: Source file path
            target_folder: Target folder name
            max_retries: Maximum retry attempts on race conditions

        Returns:
            Path to the moved file, or None if file was claimed by another agent
        """
        target_folder_path = self.get_folder_path(target_folder)
        target_path = target_folder_path / source.name

        for attempt in range(max_retries):
            try:
                # Check if source still exists (atomic check)
                if not source.exists():
                    logger.debug(f"File already claimed: {source}")
                    return None

                # Atomic rename (claim operation)
                shutil.move(str(source), str(target_path))
                logger.debug(f"Moved file: {source} -> {target_path}")
                return target_path

            except FileNotFoundError:
                # Another agent claimed it first
                logger.debug(f"Race condition: file claimed by another agent: {source}")
                return None

            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Move failed (attempt {attempt + 1}/{max_retries}): {e}")
                    continue
                else:
                    logger.error(f"Move failed after {max_retries} attempts: {e}")
                    raise

        return None

    def delete_file(self, file_path: Path) -> bool:
        """Delete a file from the vault.

        Args:
            file_path: Path to the file

        Returns:
            True if deleted, False if file didn't exist
        """
        try:
            if file_path.exists():
                file_path.unlink()
                logger.debug(f"Deleted file: {file_path}")
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            raise

    def archive_old_files(self, folder: str, retention_days: int) -> int:
        """Archive or delete old files based on retention policy.

        Args:
            folder: Folder name
            retention_days: Number of days to retain files

        Returns:
            Number of files archived/deleted
        """
        folder_path = self.get_folder_path(folder)
        if not folder_path.exists():
            return 0

        cutoff_time = datetime.now().timestamp() - (retention_days * 86400)
        archived_count = 0

        for file_path in folder_path.glob("*.md"):
            if file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    archived_count += 1
                    logger.debug(f"Archived old file: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to archive {file_path}: {e}")

        return archived_count

    def validate_structure(self) -> Dict[str, Any]:
        """Validate vault structure.

        Returns:
            Dictionary with validation results
        """
        return self.config.validate_structure()

    def get_stats(self) -> Dict[str, int]:
        """Get vault statistics.

        Returns:
            Dictionary with file counts per folder
        """
        stats = {}
        for folder in self.config.required_folders:
            folder_path = self.get_folder_path(folder)
            if folder_path.exists():
                file_count = len([f for f in folder_path.glob("*.md")])
                stats[folder] = file_count
            else:
                stats[folder] = 0
        return stats
