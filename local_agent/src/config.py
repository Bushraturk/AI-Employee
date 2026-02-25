"""Local agent configuration."""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class LocalAgentConfig:
    """Configuration for local agent.

    Local agent runs on user's machine and handles:
    - Approval workflow monitoring
    - Action execution (email sends, social posts, payments)
    - WhatsApp and finance monitoring
    - Dashboard updates

    Security: Local agent has all sensitive credentials.
    Never syncs credentials to vault.
    """

    # Vault configuration
    vault_path: str
    sync_method: str = "git"  # "git" or "syncthing"
    git_remote: Optional[str] = None
    git_branch: str = "main"

    # MCP server configuration
    mcp_config_path: str = "config/mcp_config.json"

    # WhatsApp configuration
    whatsapp_enabled: bool = False
    whatsapp_session_path: Optional[str] = None
    whatsapp_check_interval: int = 30  # 30 seconds

    # Finance configuration
    finance_enabled: bool = False
    bank_api_token: Optional[str] = None
    finance_check_interval: int = 300  # 5 minutes

    # Rate limiting
    max_emails_per_hour: int = 10
    max_payments_per_hour: int = 3

    # Dashboard configuration
    dashboard_update_interval: int = 60  # 1 minute

    # Development mode
    dev_mode: bool = False
    dry_run: bool = False

    @classmethod
    def from_env(cls) -> "LocalAgentConfig":
        """Load configuration from environment variables.

        Returns:
            LocalAgentConfig instance
        """
        # Get absolute vault path
        vault_path = os.getenv("VAULT_PATH", "vault")
        if not os.path.isabs(vault_path):
            # Make it absolute relative to project root
            project_root = Path(__file__).parent.parent.parent
            vault_path = str(project_root / vault_path)

        return cls(
            # Vault
            vault_path=vault_path,
            sync_method=os.getenv("SYNC_METHOD", "git"),
            git_remote=os.getenv("GIT_REMOTE"),
            git_branch=os.getenv("GIT_BRANCH", "main"),

            # MCP
            mcp_config_path=os.getenv("MCP_CONFIG_PATH", "config/mcp_config.json"),

            # WhatsApp
            whatsapp_enabled=os.getenv("WHATSAPP_ENABLED", "false").lower() == "true",
            whatsapp_session_path=os.getenv("WHATSAPP_SESSION_PATH"),
            whatsapp_check_interval=int(os.getenv("WHATSAPP_CHECK_INTERVAL", "30")),

            # Finance
            finance_enabled=os.getenv("FINANCE_ENABLED", "false").lower() == "true",
            bank_api_token=os.getenv("BANK_API_TOKEN"),
            finance_check_interval=int(os.getenv("FINANCE_CHECK_INTERVAL", "300")),

            # Rate limiting
            max_emails_per_hour=int(os.getenv("MAX_EMAILS_PER_HOUR", "10")),
            max_payments_per_hour=int(os.getenv("MAX_PAYMENTS_PER_HOUR", "3")),

            # Dashboard
            dashboard_update_interval=int(os.getenv("DASHBOARD_UPDATE_INTERVAL", "60")),

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
            "whatsapp_enabled": self.whatsapp_enabled,
            "finance_enabled": self.finance_enabled,
            "max_emails_per_hour": self.max_emails_per_hour,
            "max_payments_per_hour": self.max_payments_per_hour,
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

        # Validate MCP config
        if not Path(self.mcp_config_path).exists():
            raise ValueError(f"MCP config not found: {self.mcp_config_path}")

        # Validate WhatsApp configuration
        if self.whatsapp_enabled and not self.whatsapp_session_path:
            raise ValueError("WHATSAPP_SESSION_PATH is required when WhatsApp is enabled")

        # Validate finance configuration
        if self.finance_enabled and not self.bank_api_token:
            raise ValueError("BANK_API_TOKEN is required when finance monitoring is enabled")

        # Validate sync configuration
        if self.sync_method == "git" and not self.git_remote:
            raise ValueError("GIT_REMOTE is required when sync_method is 'git'")
