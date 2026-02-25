"""Vault synchronization manager for Git and Syncthing."""

import os
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
import logging
from datetime import datetime

from shared.models.vault_config import VaultConfig
from shared.utils.logger import VaultLogger, LogCategory


logger = logging.getLogger(__name__)


class SyncManager:
    """Manages vault synchronization using Git or Syncthing.

    Provides unified interface for both sync methods with automatic
    conflict resolution and error handling.
    """

    def __init__(
        self,
        vault_config: VaultConfig,
        vault_logger: Optional[VaultLogger] = None,
    ):
        """Initialize sync manager.

        Args:
            vault_config: Vault configuration
            vault_logger: Optional vault logger
        """
        self.config = vault_config
        self.vault_logger = vault_logger
        self.vault_root = vault_config.vault_root
        self.sync_method = vault_config.sync_method

        # Development mode
        self.dev_mode = os.getenv("DEVELOPMENT_MODE", "false").lower() == "true"
        self.dry_run = os.getenv("DRY_RUN_MODE", "false").lower() == "true"

        logger.info(f"Initialized sync manager: {self.sync_method} (dev_mode={self.dev_mode})")

    def sync(self) -> Dict[str, Any]:
        """Perform vault synchronization.

        Returns:
            Dictionary with sync results
        """
        if self.dev_mode:
            logger.info("[DEV MODE] Skipping vault sync")
            return {"success": True, "skipped": True, "reason": "Development mode"}

        if self.dry_run:
            logger.info("[DRY RUN] Would sync vault")
            return {"success": True, "dry_run": True}

        try:
            if self.sync_method == "git":
                return self._sync_git()
            elif self.sync_method == "syncthing":
                return self._sync_syncthing()
            else:
                raise ValueError(f"Unknown sync method: {self.sync_method}")

        except Exception as e:
            logger.error(f"Sync failed: {e}")
            if self.vault_logger:
                self.vault_logger.error(
                    LogCategory.SYNC,
                    f"Vault sync failed: {e}",
                    error_type=type(e).__name__,
                    stack_trace=str(e),
                )
            return {"success": False, "error": str(e)}

    def _sync_git(self) -> Dict[str, Any]:
        """Sync vault using Git.

        Returns:
            Dictionary with sync results
        """
        logger.info("Syncing vault with Git")

        # Check if git is initialized
        git_dir = self.vault_root / ".git"
        if not git_dir.exists():
            logger.info("Initializing Git repository")
            self._run_git_command(["init"])

            # Add remote if configured
            if self.config.git_remote:
                self._run_git_command(["remote", "add", "origin", self.config.git_remote])

        # Pull changes from remote
        if self.config.git_remote:
            try:
                logger.debug("Pulling changes from remote")
                self._run_git_command(["pull", "origin", self.config.git_branch, "--rebase"])
            except subprocess.CalledProcessError as e:
                logger.warning(f"Pull failed (may be first push): {e}")

        # Stage all changes
        self._run_git_command(["add", "-A"])

        # Check if there are changes to commit
        status_output = self._run_git_command(["status", "--porcelain"])
        if not status_output.strip():
            logger.debug("No changes to sync")
            return {"success": True, "changes": False}

        # Commit changes
        commit_message = f"Vault sync at {datetime.now().isoformat()}"
        self._run_git_command(["commit", "-m", commit_message])

        # Push to remote
        if self.config.git_remote:
            logger.debug("Pushing changes to remote")
            self._run_git_command(["push", "origin", self.config.git_branch])

        if self.vault_logger:
            self.vault_logger.info(
                LogCategory.SYNC,
                "Vault synced successfully (Git)",
                details={"method": "git", "branch": self.config.git_branch},
            )

        return {"success": True, "changes": True, "method": "git"}

    def _sync_syncthing(self) -> Dict[str, Any]:
        """Sync vault using Syncthing.

        Syncthing runs continuously in the background, so this just
        verifies the connection and folder status.

        Returns:
            Dictionary with sync results
        """
        logger.info("Checking Syncthing sync status")

        try:
            import requests

            # Check Syncthing API
            headers = {"X-API-Key": self.config.syncthing_api_key}
            response = requests.get(
                f"{self.config.syncthing_url}/rest/db/status",
                headers=headers,
                params={"folder": self.config.syncthing_folder_id},
                timeout=5,
            )
            response.raise_for_status()

            status = response.json()
            logger.debug(f"Syncthing status: {status}")

            if self.vault_logger:
                self.vault_logger.info(
                    LogCategory.SYNC,
                    "Vault sync verified (Syncthing)",
                    details={"method": "syncthing", "status": status},
                )

            return {
                "success": True,
                "method": "syncthing",
                "status": status,
            }

        except Exception as e:
            logger.error(f"Syncthing check failed: {e}")
            return {"success": False, "error": str(e)}

    def _run_git_command(self, args: list[str]) -> str:
        """Run a git command in the vault directory.

        Args:
            args: Git command arguments

        Returns:
            Command output

        Raises:
            subprocess.CalledProcessError: If command fails
        """
        cmd = ["git"] + args
        logger.debug(f"Running: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            cwd=str(self.vault_root),
            capture_output=True,
            text=True,
            check=True,
        )

        return result.stdout

    def pull(self) -> Dict[str, Any]:
        """Pull changes from remote (Git only).

        Returns:
            Dictionary with pull results
        """
        if self.sync_method != "git":
            return {"success": False, "error": "Pull only supported for Git"}

        if self.dev_mode or self.dry_run:
            return {"success": True, "skipped": True}

        try:
            logger.info("Pulling changes from remote")
            self._run_git_command(["pull", "origin", self.config.git_branch, "--rebase"])

            if self.vault_logger:
                self.vault_logger.info(
                    LogCategory.SYNC,
                    "Pulled changes from remote",
                )

            return {"success": True}

        except Exception as e:
            logger.error(f"Pull failed: {e}")
            return {"success": False, "error": str(e)}

    def push(self) -> Dict[str, Any]:
        """Push changes to remote (Git only).

        Returns:
            Dictionary with push results
        """
        if self.sync_method != "git":
            return {"success": False, "error": "Push only supported for Git"}

        if self.dev_mode or self.dry_run:
            return {"success": True, "skipped": True}

        try:
            logger.info("Pushing changes to remote")

            # Stage and commit any pending changes
            self._run_git_command(["add", "-A"])
            status_output = self._run_git_command(["status", "--porcelain"])

            if status_output.strip():
                commit_message = f"Vault sync at {datetime.now().isoformat()}"
                self._run_git_command(["commit", "-m", commit_message])

            # Push
            self._run_git_command(["push", "origin", self.config.git_branch])

            if self.vault_logger:
                self.vault_logger.info(
                    LogCategory.SYNC,
                    "Pushed changes to remote",
                )

            return {"success": True}

        except Exception as e:
            logger.error(f"Push failed: {e}")
            return {"success": False, "error": str(e)}
