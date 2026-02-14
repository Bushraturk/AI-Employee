"""Vault Manager - Initializes and manages AI Employee Vault structure."""

from pathlib import Path
from datetime import datetime
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class VaultManager:
    """Manages the AI Employee Vault structure and initialization."""

    REQUIRED_FOLDERS = [
        'Inbox',
        'Needs_Action',
        'Done',
        'Logs',
        'Company_Handbook'
    ]

    def __init__(self, vault_path: str):
        """Initialize VaultManager with vault path.

        Args:
            vault_path: Absolute path to the vault directory
        """
        self.vault_path = Path(vault_path).resolve()

    def initialize_vault(self) -> Dict[str, List[str]]:
        """Create vault structure if missing, preserve existing files.

        Returns:
            Dictionary with 'created' and 'validated' lists

        Raises:
            ValueError: If vault path doesn't exist or isn't writable
        """
        # Validate vault path exists
        if not self.vault_path.exists():
            raise ValueError(f"Vault path does not exist: {self.vault_path}")

        # Check write permissions
        if not self._check_write_permission():
            raise ValueError(f"No write permission for vault path: {self.vault_path}")

        created = []
        validated = []

        # Create required folders
        for folder in self.REQUIRED_FOLDERS:
            folder_path = self.vault_path / folder
            if not folder_path.exists():
                folder_path.mkdir(parents=True, exist_ok=True)
                created.append(folder)
                logger.info(f"Created folder: {folder}")
            else:
                validated.append(folder)
                logger.debug(f"Validated existing folder: {folder}")

        # Create Dashboard.md if missing
        dashboard_path = self.vault_path / 'Dashboard.md'
        if not dashboard_path.exists():
            dashboard_path.write_text(self._get_initial_dashboard_template(), encoding='utf-8')
            created.append('Dashboard.md')
            logger.info("Created Dashboard.md")
        else:
            validated.append('Dashboard.md')
            logger.debug("Validated existing Dashboard.md")

        return {
            'created': created,
            'validated': validated
        }

    def validate_vault_structure(self) -> bool:
        """Validate that all required folders and files exist.

        Returns:
            True if vault structure is valid, False otherwise
        """
        # Check all required folders
        for folder in self.REQUIRED_FOLDERS:
            folder_path = self.vault_path / folder
            if not folder_path.exists() or not folder_path.is_dir():
                logger.error(f"Missing or invalid folder: {folder}")
                return False

        # Check Dashboard.md
        dashboard_path = self.vault_path / 'Dashboard.md'
        if not dashboard_path.exists() or not dashboard_path.is_file():
            logger.error("Missing or invalid Dashboard.md")
            return False

        return True

    def _check_write_permission(self) -> bool:
        """Check if vault path is writable.

        Returns:
            True if writable, False otherwise
        """
        try:
            test_file = self.vault_path / '.write_test'
            test_file.touch()
            test_file.unlink()
            return True
        except (PermissionError, OSError):
            return False

    def _get_initial_dashboard_template(self) -> str:
        """Get initial Dashboard.md template.

        Returns:
            Dashboard markdown content
        """
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        return f"""# AI Employee Dashboard

**Last Updated**: {now}
**System Status**: [NOT STARTED]
**Uptime**: 0.0 hours

## Task Counts

- **Inbox**: 0
- **Needs Action**: 0
- **Done**: 0

## Performance Metrics

- **Total Processed**: 0 tasks
- **Average Processing Time**: N/A
- **Success Rate**: N/A
- **Errors (24h)**: 0

## Recent Activity

No activity yet. Drop a task file in the Inbox folder to get started!

## System Health

- Memory Usage: N/A
- Disk Space: N/A
- Watcher Status: Not Started
- Last Error: None

---

*Dashboard auto-updates when tasks are processed*
"""
