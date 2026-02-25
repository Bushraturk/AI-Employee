"""VaultConfig model for vault configuration and validation."""

from pathlib import Path
from typing import List, Dict, Any
from pydantic import BaseModel, Field, validator


class VaultConfig(BaseModel):
    """Model for vault configuration.

    Defines the vault structure, sync settings, and validation rules.
    """

    # Paths
    vault_root: Path = Field(..., description="Root path of the vault")

    # Required folders
    required_folders: List[str] = Field(
        default=[
            "Needs_Action",
            "Needs_Action/email",
            "Needs_Action/social",
            "Needs_Action/accounting",
            "Needs_Action/whatsapp",
            "In_Progress",
            "In_Progress/cloud",
            "In_Progress/local",
            "Pending_Approval",
            "Pending_Approval/email",
            "Pending_Approval/social",
            "Pending_Approval/accounting",
            "Pending_Approval/whatsapp",
            "Approved",
            "Rejected",
            "Done",
            "Logs",
            "Updates",
        ],
        description="List of required folders"
    )

    # Optional folders
    optional_folders: List[str] = Field(
        default=["Plans"],
        description="List of optional folders"
    )

    # Sync configuration
    sync_method: str = Field(..., description="Sync method: 'git' or 'syncthing'")
    sync_interval_seconds: int = Field(default=60, description="Sync interval in seconds")

    # Git configuration (if using git sync)
    git_remote: str = Field(default="", description="Git remote URL")
    git_branch: str = Field(default="main", description="Git branch name")

    # Syncthing configuration (if using syncthing sync)
    syncthing_folder_id: str = Field(default="", description="Syncthing folder ID")
    syncthing_api_key: str = Field(default="", description="Syncthing API key")
    syncthing_url: str = Field(default="http://localhost:8384", description="Syncthing URL")

    # File patterns
    action_file_pattern: str = Field(
        default=r"^(email|whatsapp|transaction|file_drop)_[a-zA-Z0-9]+_\d{8}T\d{6}Z\.md$",
        description="Regex pattern for action files"
    )
    approval_file_pattern: str = Field(
        default=r"^(email_send|social_post|accounting_entry|whatsapp_send|payment)_[a-zA-Z0-9@._-]+_\d{8}T\d{6}Z\.md$",
        description="Regex pattern for approval request files"
    )
    log_file_pattern: str = Field(
        default=r"^\d{4}-\d{2}-\d{2}\.md$",
        description="Regex pattern for log files"
    )

    # Retention policies
    rejected_retention_days: int = Field(default=90, description="Days to retain rejected actions")
    done_retention_days: int = Field(default=90, description="Days to retain completed actions")
    log_retention_days: int = Field(default=90, description="Days to retain logs")

    # Performance settings
    watch_debounce_ms: int = Field(default=100, description="File watch debounce in milliseconds")
    batch_sync_max_interval_seconds: int = Field(default=10, description="Max interval for batch sync")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @validator("vault_root")
    def validate_vault_root(cls, v: Path) -> Path:
        """Validate vault root path."""
        if not v.exists():
            raise ValueError(f"Vault root does not exist: {v}")
        if not v.is_dir():
            raise ValueError(f"Vault root is not a directory: {v}")
        return v

    @validator("sync_method")
    def validate_sync_method(cls, v: str) -> str:
        """Validate sync method."""
        if v not in ["git", "syncthing"]:
            raise ValueError(f"Invalid sync method: {v}. Must be 'git' or 'syncthing'")
        return v

    def get_folder_path(self, folder: str) -> Path:
        """Get absolute path for a vault folder.

        Args:
            folder: Folder name (e.g., "Needs_Action/email")

        Returns:
            Absolute path to the folder
        """
        return self.vault_root / folder

    def ensure_folders_exist(self) -> List[str]:
        """Ensure all required folders exist.

        Creates missing folders and returns list of created folders.

        Returns:
            List of folder paths that were created
        """
        created = []
        for folder in self.required_folders:
            folder_path = self.get_folder_path(folder)
            if not folder_path.exists():
                folder_path.mkdir(parents=True, exist_ok=True)
                created.append(str(folder_path))
        return created

    def validate_structure(self) -> Dict[str, Any]:
        """Validate vault structure.

        Returns:
            Dictionary with validation results
        """
        results = {
            "valid": True,
            "missing_folders": [],
            "warnings": [],
        }

        # Check required folders
        for folder in self.required_folders:
            folder_path = self.get_folder_path(folder)
            if not folder_path.exists():
                results["valid"] = False
                results["missing_folders"].append(folder)

        # Check optional folders
        for folder in self.optional_folders:
            folder_path = self.get_folder_path(folder)
            if not folder_path.exists():
                results["warnings"].append(f"Optional folder missing: {folder}")

        return results

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True
