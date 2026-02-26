"""Dashboard updater for local agent.

Updates Dashboard.md with system status and pending approvals.
Implements single-writer rule (only local agent writes to Dashboard).
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from shared.models.vault_config import VaultConfig
from shared.utils.vault_manager import VaultManager
from shared.utils.logger import VaultLogger, LogCategory


logger = logging.getLogger(__name__)


class DashboardUpdater:
    """Updates Dashboard.md with system status.

    Single-writer rule: Only local agent writes to Dashboard.md.
    Cloud agent writes to Updates/ folder, which is merged here.
    """

    def __init__(
        self,
        agent_id: str,
        vault_manager: VaultManager,
        vault_logger: VaultLogger,
    ):
        """Initialize dashboard updater.

        Args:
            agent_id: Agent ID
            vault_manager: Vault manager instance
            vault_logger: Vault logger instance
        """
        self.agent_id = agent_id
        self.vault_manager = vault_manager
        self.vault_logger = vault_logger

        logger.info("Dashboard updater initialized")

    def update_dashboard(self) -> None:
        """Update Dashboard.md with current system status."""
        try:
            # Collect system status
            status = self._collect_status()

            # Merge updates from cloud agent
            updates = self._collect_updates()

            # Generate dashboard content
            dashboard_content = self._generate_dashboard(status, updates)

            # Write to Dashboard.md
            dashboard_path = self.vault_manager.vault_root / "Dashboard.md"
            with open(dashboard_path, "w", encoding="utf-8") as f:
                f.write(dashboard_content)

            self.vault_logger.debug(
                LogCategory.AGENT,
                "Dashboard updated",
                details={"pending_approvals": status["pending_approvals"]["total"]}
            )

        except Exception as e:
            self.vault_logger.error(
                LogCategory.AGENT,
                f"Failed to update dashboard: {e}",
                error_type=type(e).__name__,
                stack_trace=str(e),
            )

    def _collect_status(self) -> Dict[str, Any]:
        """Collect current system status.

        Returns:
            Status dictionary
        """
        # Count pending approvals
        pending_approvals = {
            "email": len(self.vault_manager.list_files("Pending_Approval/email", pattern="*.md")),
            "social": len(self.vault_manager.list_files("Pending_Approval/social", pattern="*.md")),
            "accounting": len(self.vault_manager.list_files("Pending_Approval/accounting", pattern="*.md")),
            "whatsapp": len(self.vault_manager.list_files("Pending_Approval/whatsapp", pattern="*.md")),
        }
        pending_approvals["total"] = sum(pending_approvals.values())

        # Check agent states
        cloud_agent_state = self._check_agent_state("cloud")
        local_agent_state = self._check_agent_state("local")

        return {
            "last_updated": datetime.now(),
            "updated_by": self.agent_id,
            "system_health": {
                "cloud_agent": cloud_agent_state,
                "local_agent": local_agent_state,
                "vault_sync": "synced",  # TODO: Check actual sync status
            },
            "pending_approvals": pending_approvals,
        }

    def _check_agent_state(self, agent_type: str) -> str:
        """Check agent state.

        Args:
            agent_type: Agent type (cloud or local)

        Returns:
            Agent status (running, stopped, error)
        """
        try:
            state_path = self.vault_manager.get_folder_path(f"In_Progress/{agent_type}") / "agent_state.md"
            if state_path.exists():
                # TODO: Parse agent state and check heartbeat
                return "running"
            else:
                return "stopped"
        except Exception:
            return "unknown"

    def _collect_updates(self) -> List[str]:
        """Collect updates from cloud agent.

        Returns:
            List of update messages
        """
        updates = []

        try:
            updates_folder = "Updates"
            update_files = self.vault_manager.list_files(updates_folder, pattern="*.md")

            for file_path in update_files:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        updates.append(content)

                    # Archive processed update
                    # TODO: Move to archive or delete after processing

                except Exception as e:
                    logger.error(f"Failed to read update file {file_path}: {e}")

        except Exception as e:
            logger.error(f"Failed to collect updates: {e}")

        return updates

    def _generate_dashboard(self, status: Dict[str, Any], updates: List[str]) -> str:
        """Generate dashboard content.

        Args:
            status: System status
            updates: Cloud agent updates

        Returns:
            Dashboard markdown content
        """
        content = f"""---
last_updated: {status['last_updated'].isoformat()}
updated_by: {status['updated_by']}
system_health:
  cloud_agent: {status['system_health']['cloud_agent']}
  local_agent: {status['system_health']['local_agent']}
  vault_sync: {status['system_health']['vault_sync']}
pending_approvals:
  email: {status['pending_approvals']['email']}
  social: {status['pending_approvals']['social']}
  accounting: {status['pending_approvals']['accounting']}
  whatsapp: {status['pending_approvals']['whatsapp']}
  total: {status['pending_approvals']['total']}
---

# AI Employee Dashboard

**Last Updated**: {status['last_updated'].strftime('%Y-%m-%d %H:%M:%S')}

## System Health

- **Cloud Agent**: {status['system_health']['cloud_agent'].upper()}
- **Local Agent**: {status['system_health']['local_agent'].upper()}
- **Vault Sync**: {status['system_health']['vault_sync'].upper()}

## Pending Approvals

**Total**: {status['pending_approvals']['total']} actions awaiting approval

- Email: {status['pending_approvals']['email']}
- Social Media: {status['pending_approvals']['social']}
- Accounting: {status['pending_approvals']['accounting']}
- WhatsApp: {status['pending_approvals']['whatsapp']}

## Recent Updates

"""

        # Add recent updates
        if updates:
            for update in updates[-10:]:  # Last 10 updates
                content += f"\n{update}\n---\n"
        else:
            content += "\nNo recent updates.\n"

        content += """
## Quick Actions

- Review pending approvals: Check `Pending_Approval/` folders
- View audit logs: Check `Logs/` folder
- Check agent status: Check `In_Progress/` folders

---

*This dashboard is automatically updated by the Local Agent.*
"""

        return content
