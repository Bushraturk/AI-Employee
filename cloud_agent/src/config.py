"""Cloud agent configuration."""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class CloudAgentConfig:
    """Configuration for cloud agent.

    Cloud agent runs 24/7 on cloud VM and handles:
    - Gmail monitoring
    - Email/social/accounting draft generation
    - Vault synchronization

    Security: Cloud agent has read-only Gmail credentials only.
    No sensitive credentials (WhatsApp, banking, payment) on cloud.
    """

    # Vault configuration
    vault_path: str
    sync_method: str = "git"  # "git" or "syncthing"
    git_remote: Optional[str] = None
    git_branch: str = "main"

    # Gmail configuration
    gmail_enabled: bool = True
    gmail_credentials_path: str = "credentials/gmail_credentials.json"
    gmail_token_path: str = "credentials/gmail_token.json"
    gmail_check_interval: int = 120  # 2 minutes

    # Claude API configuration (for drafting)
    claude_api_key: Optional[str] = None

    # Business context
    company_handbook_path: str = "vault/Company_Handbook.md"
    business_goals_path: str = "vault/Business_Goals.md"

    # Odoo configuration (for accounting drafts)
    odoo_enabled: bool = False
    odoo_url: Optional[str] = None
    odoo_database: Optional[str] = None
    odoo_username: Optional[str] = None
    odoo_api_key: Optional[str] = None

    # Social media configuration (for social drafts)
    social_enabled: bool = False

    # Development mode
    dev_mode: bool = False
    dry_run: bool = False

    @classmethod
    def from_env(cls) -> "CloudAgentConfig":
        """Load configuration from environment variables.

        Returns:
            CloudAgentConfig instance
        """
        # Get absolute vault path
        vault_path = os.getenv("VAULT_PATH", "vault")
        project_root = Path(__file__).parent.parent.parent
        if not os.path.isabs(vault_path):
            vault_path = str(project_root / vault_path)

        # Resolve company handbook path
        company_handbook_path = os.getenv("COMPANY_HANDBOOK_PATH", "vault/Company_Handbook.md")
        if not os.path.isabs(company_handbook_path):
            company_handbook_path = str(project_root / company_handbook_path)

        # Resolve business goals path
        business_goals_path = os.getenv("BUSINESS_GOALS_PATH", "vault/Business_Goals.md")
        if not os.path.isabs(business_goals_path):
            business_goals_path = str(project_root / business_goals_path)

        return cls(
            # Vault
            vault_path=vault_path,
            sync_method=os.getenv("SYNC_METHOD", "git"),
            git_remote=os.getenv("GIT_REMOTE"),
            git_branch=os.getenv("GIT_BRANCH", "main"),

            # Gmail
            gmail_enabled=os.getenv("GMAIL_ENABLED", "true").lower() == "true",
            gmail_credentials_path=os.getenv("GMAIL_CREDENTIALS_PATH", "credentials/gmail_credentials.json"),
            gmail_token_path=os.getenv("GMAIL_TOKEN_PATH", "credentials/gmail_token.json"),
            gmail_check_interval=int(os.getenv("GMAIL_CHECK_INTERVAL", "120")),

            # Claude API
            claude_api_key=os.getenv("CLAUDE_API_KEY"),

            # Business context
            company_handbook_path=company_handbook_path,
            business_goals_path=business_goals_path,

            # Odoo
            odoo_enabled=os.getenv("ODOO_ENABLED", "false").lower() == "true",
            odoo_url=os.getenv("ODOO_URL"),
            odoo_database=os.getenv("ODOO_DATABASE"),
            odoo_username=os.getenv("ODOO_USERNAME"),
            odoo_api_key=os.getenv("ODOO_API_KEY"),

            # Social media
            social_enabled=os.getenv("SOCIAL_ENABLED", "false").lower() == "true",

            # Development
            dev_mode=os.getenv("DEVELOPMENT_MODE", "false").lower() == "true",
            dry_run=os.getenv("DRY_RUN_MODE", "false").lower() == "true",
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.

        Returns:
            Configuration as dictionary
        """
        return {
            "vault_path": self.vault_path,
            "sync_method": self.sync_method,
            "git_remote": self.git_remote,
            "git_branch": self.git_branch,
            "gmail_enabled": self.gmail_enabled,
            "gmail_check_interval": self.gmail_check_interval,
            "odoo_enabled": self.odoo_enabled,
            "social_enabled": self.social_enabled,
            "dev_mode": self.dev_mode,
            "dry_run": self.dry_run,
        }

    def validate(self) -> None:
        """Validate configuration.

        Raises:
            ValueError: If configuration is invalid
        """
        # Validate vault path
        if not self.vault_path:
            raise ValueError("vault_path is required")

        # Validate Gmail configuration
        if self.gmail_enabled:
            if not Path(self.gmail_credentials_path).exists():
                raise ValueError(f"Gmail credentials not found: {self.gmail_credentials_path}")

        # Validate Claude API key
        if not self.claude_api_key:
            raise ValueError("CLAUDE_API_KEY environment variable is required for drafting")

        # Validate sync configuration
        if self.sync_method == "git" and not self.git_remote:
            raise ValueError("GIT_REMOTE is required when sync_method is 'git'")
