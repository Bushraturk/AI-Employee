"""Dashboard merger for combining cloud agent updates into Dashboard.md."""

import re
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import logging

from shared.models.dashboard_update import DashboardUpdate
from shared.utils.vault_manager import VaultManager
from shared.utils.logger import VaultLogger, LogCategory


logger = logging.getLogger(__name__)


class DashboardMerger:
    """Merges cloud agent updates into the main Dashboard.md file.

    The cloud agent writes updates to the Updates/ folder.
    The local agent periodically merges these updates into Dashboard.md
    and deletes the processed update files.
    """

    def __init__(
        self,
        vault_manager: VaultManager,
        vault_logger: Optional[VaultLogger] = None,
    ):
        """Initialize dashboard merger.

        Args:
            vault_manager: Vault manager instance
            vault_logger: Optional vault logger
        """
        self.vault_manager = vault_manager
        self.vault_logger = vault_logger
        self.dashboard_path = vault_manager.get_folder_path("") / "Dashboard.md"

    def merge_updates(self) -> int:
        """Merge all pending updates into Dashboard.md.

        Returns:
            Number of updates merged
        """
        # Get all update files
        update_files = self.vault_manager.list_files("Updates", "*.md")

        if not update_files:
            logger.debug("No updates to merge")
            return 0

        # Sort by priority and timestamp
        updates = []
        for file_path in update_files:
            try:
                update = DashboardUpdate.from_file(str(file_path))
                updates.append((update, file_path))
            except Exception as e:
                logger.error(f"Failed to read update {file_path}: {e}")

        # Sort: URGENT first, then by timestamp (newest first)
        updates.sort(
            key=lambda x: (
                0 if x[0].priority.value == "urgent" else 1,
                -x[0].timestamp.timestamp()
            )
        )

        # Read current dashboard
        dashboard_content = self._read_dashboard()

        # Merge updates
        merged_count = 0
        for update, file_path in updates:
            try:
                dashboard_content = self._merge_update(dashboard_content, update)

                # Mark as merged
                update.merged = True
                update.merged_at = datetime.now()

                # Delete update file
                self.vault_manager.delete_file(file_path)

                merged_count += 1

                if self.vault_logger:
                    self.vault_logger.info(
                        LogCategory.SYSTEM,
                        f"Merged dashboard update: {update.title}",
                        details={"update_id": update.update_id},
                    )

            except Exception as e:
                logger.error(f"Failed to merge update {update.update_id}: {e}")

        # Write updated dashboard
        if merged_count > 0:
            self._write_dashboard(dashboard_content)
            logger.info(f"Merged {merged_count} dashboard updates")

        return merged_count

    def _read_dashboard(self) -> str:
        """Read current Dashboard.md content.

        Returns:
            Dashboard content
        """
        if not self.dashboard_path.exists():
            # Create initial dashboard
            return self._create_initial_dashboard()

        with open(self.dashboard_path, "r", encoding="utf-8") as f:
            return f.read()

    def _write_dashboard(self, content: str) -> None:
        """Write Dashboard.md content.

        Args:
            content: Dashboard content
        """
        with open(self.dashboard_path, "w", encoding="utf-8") as f:
            f.write(content)

    def _create_initial_dashboard(self) -> str:
        """Create initial Dashboard.md structure.

        Returns:
            Initial dashboard content
        """
        now = datetime.now()
        return f"""# AI Employee Dashboard

**Last Updated**: {now.strftime("%Y-%m-%d %H:%M:%S")}

## System Status

- **Cloud Agent**: Starting
- **Local Agent**: Starting
- **Vault Sync**: OK

## Recent Activity

No activity yet.

## Pending Approvals

No pending approvals.

## Statistics

- **Tasks Completed**: 0
- **Approvals Processed**: 0
- **Errors**: 0

---
*This dashboard is automatically updated by the AI Employee system.*
"""

    def _merge_update(self, dashboard: str, update: DashboardUpdate) -> str:
        """Merge a single update into the dashboard.

        Args:
            dashboard: Current dashboard content
            update: Update to merge

        Returns:
            Updated dashboard content
        """
        # Update timestamp
        now = datetime.now()
        dashboard = re.sub(
            r"\*\*Last Updated\*\*: .*",
            f"**Last Updated**: {now.strftime('%Y-%m-%d %H:%M:%S')}",
            dashboard
        )

        # Handle different update types
        if update.update_type.value == "status":
            dashboard = self._merge_status_update(dashboard, update)
        elif update.update_type.value == "metric":
            dashboard = self._merge_metric_update(dashboard, update)
        elif update.update_type.value == "alert":
            dashboard = self._merge_alert_update(dashboard, update)
        elif update.update_type.value == "summary":
            dashboard = self._merge_summary_update(dashboard, update)

        return dashboard

    def _merge_status_update(self, dashboard: str, update: DashboardUpdate) -> str:
        """Merge a status update.

        Args:
            dashboard: Current dashboard content
            update: Status update

        Returns:
            Updated dashboard content
        """
        # Update System Status section
        section_pattern = r"## System Status\n\n(.*?)\n\n##"
        match = re.search(section_pattern, dashboard, re.DOTALL)

        if match:
            # Replace status section
            new_status = f"## System Status\n\n{update.body}\n\n##"
            dashboard = re.sub(section_pattern, new_status, dashboard, flags=re.DOTALL)

        return dashboard

    def _merge_metric_update(self, dashboard: str, update: DashboardUpdate) -> str:
        """Merge a metric update.

        Args:
            dashboard: Current dashboard content
            update: Metric update

        Returns:
            Updated dashboard content
        """
        # Update Statistics section
        section_pattern = r"## Statistics\n\n(.*?)\n\n---"
        match = re.search(section_pattern, dashboard, re.DOTALL)

        if match:
            # Update metrics
            stats_section = match.group(1)
            for key, value in update.metrics.items():
                metric_pattern = rf"- \*\*{re.escape(key)}\*\*: .*"
                replacement = f"- **{key}**: {value}"
                if re.search(metric_pattern, stats_section):
                    stats_section = re.sub(metric_pattern, replacement, stats_section)
                else:
                    stats_section += f"\n{replacement}"

            new_stats = f"## Statistics\n\n{stats_section}\n\n---"
            dashboard = re.sub(section_pattern, new_stats, dashboard, flags=re.DOTALL)

        return dashboard

    def _merge_alert_update(self, dashboard: str, update: DashboardUpdate) -> str:
        """Merge an alert update.

        Args:
            dashboard: Current dashboard content
            update: Alert update

        Returns:
            Updated dashboard content
        """
        # Add to Recent Activity section
        section_pattern = r"## Recent Activity\n\n(.*?)\n\n##"
        match = re.search(section_pattern, dashboard, re.DOTALL)

        if match:
            activity_section = match.group(1)

            # Add new alert at the top
            alert_entry = f"- **[ALERT]** {update.summary} ({update.timestamp.strftime('%H:%M:%S')})"

            if "No activity yet." in activity_section:
                activity_section = alert_entry
            else:
                # Keep only last 10 entries
                entries = activity_section.split("\n")
                entries = [alert_entry] + entries[:9]
                activity_section = "\n".join(entries)

            new_activity = f"## Recent Activity\n\n{activity_section}\n\n##"
            dashboard = re.sub(section_pattern, new_activity, dashboard, flags=re.DOTALL)

        return dashboard

    def _merge_summary_update(self, dashboard: str, update: DashboardUpdate) -> str:
        """Merge a summary update.

        Args:
            dashboard: Current dashboard content
            update: Summary update

        Returns:
            Updated dashboard content
        """
        # Add to Recent Activity section
        section_pattern = r"## Recent Activity\n\n(.*?)\n\n##"
        match = re.search(section_pattern, dashboard, re.DOTALL)

        if match:
            activity_section = match.group(1)

            # Add new summary at the top
            summary_entry = f"- {update.summary} ({update.timestamp.strftime('%H:%M:%S')})"

            if "No activity yet." in activity_section:
                activity_section = summary_entry
            else:
                # Keep only last 10 entries
                entries = activity_section.split("\n")
                entries = [summary_entry] + entries[:9]
                activity_section = "\n".join(entries)

            new_activity = f"## Recent Activity\n\n{activity_section}\n\n##"
            dashboard = re.sub(section_pattern, new_activity, dashboard, flags=re.DOTALL)

        return dashboard
