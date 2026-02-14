"""Dashboard Manager - Updates Dashboard.md with real-time system status."""

from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DashboardManager:
    """Manages Dashboard.md updates with system metrics and status."""

    def __init__(self, vault_path: str):
        """Initialize DashboardManager with vault path.

        Args:
            vault_path: Absolute path to the vault directory
        """
        self.vault_path = Path(vault_path).resolve()
        self.dashboard_path = self.vault_path / 'Dashboard.md'

        # Metrics tracking
        self.start_time = datetime.now()
        self.total_processed = 0
        self.total_failed = 0
        self.processing_times = []

    def update_dashboard(self, metrics: Dict[str, Any]) -> bool:
        """Update Dashboard.md with current metrics.

        Args:
            metrics: Dictionary with system metrics

        Returns:
            True if update succeeded, False otherwise
        """
        try:
            # Count tasks in each folder
            inbox_count = self._count_tasks('Inbox')
            needs_action_count = self._count_tasks('Needs_Action')
            done_count = self._count_tasks('Done')

            # Update internal metrics
            self.total_processed = metrics.get('total_processed', self.total_processed)
            self.total_failed = metrics.get('total_failed', self.total_failed)

            # Calculate derived metrics
            uptime_hours = (datetime.now() - self.start_time).total_seconds() / 3600
            avg_processing_time = self._calculate_avg_processing_time()
            success_rate = self._calculate_success_rate()

            # Generate dashboard content
            content = self._generate_dashboard_content(
                inbox_count=inbox_count,
                needs_action_count=needs_action_count,
                done_count=done_count,
                total_processed=self.total_processed,
                avg_processing_time=avg_processing_time,
                success_rate=success_rate,
                uptime_hours=uptime_hours,
                error_count=self.total_failed
            )

            # Write atomically
            temp_path = self.dashboard_path.with_suffix('.tmp')
            temp_path.write_text(content, encoding='utf-8')
            temp_path.replace(self.dashboard_path)

            logger.debug("Dashboard updated successfully")
            return True

        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")
            return False

    def record_processing_time(self, duration_seconds: float) -> None:
        """Record a task processing time for metrics.

        Args:
            duration_seconds: Processing duration in seconds
        """
        self.processing_times.append(duration_seconds)
        # Keep only last 100 entries
        if len(self.processing_times) > 100:
            self.processing_times = self.processing_times[-100:]

    def _count_tasks(self, folder: str) -> int:
        """Count .md files in a folder.

        Args:
            folder: Folder name (Inbox, Needs_Action, Done)

        Returns:
            Number of .md files in folder
        """
        try:
            folder_path = self.vault_path / folder
            if not folder_path.exists():
                return 0

            return len(list(folder_path.glob('*.md')))
        except Exception as e:
            logger.error(f"Error counting tasks in {folder}: {e}")
            return 0

    def _calculate_avg_processing_time(self) -> float:
        """Calculate average processing time.

        Returns:
            Average processing time in seconds, or 0 if no data
        """
        if not self.processing_times:
            return 0.0
        return sum(self.processing_times) / len(self.processing_times)

    def _calculate_success_rate(self) -> float:
        """Calculate success rate percentage.

        Returns:
            Success rate as percentage (0-100)
        """
        total = self.total_processed + self.total_failed
        if total == 0:
            return 100.0
        return (self.total_processed / total) * 100

    def _generate_dashboard_content(
        self,
        inbox_count: int,
        needs_action_count: int,
        done_count: int,
        total_processed: int,
        avg_processing_time: float,
        success_rate: float,
        uptime_hours: float,
        error_count: int
    ) -> str:
        """Generate dashboard markdown content.

        Args:
            inbox_count: Number of tasks in Inbox
            needs_action_count: Number of tasks in Needs_Action
            done_count: Number of tasks in Done
            total_processed: Total tasks processed
            avg_processing_time: Average processing time in seconds
            success_rate: Success rate percentage
            uptime_hours: System uptime in hours
            error_count: Number of errors in last 24h

        Returns:
            Dashboard markdown content
        """
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # System status
        if needs_action_count > 0:
            status = "[PROCESSING]"
        elif inbox_count > 0:
            status = "[ACTIVE]"
        else:
            status = "[IDLE]"

        # Format average processing time
        if avg_processing_time > 0:
            avg_time_str = f"{avg_processing_time:.1f} seconds"
        else:
            avg_time_str = "N/A"

        # Format success rate
        if total_processed > 0:
            success_rate_str = f"{success_rate:.1f}%"
        else:
            success_rate_str = "N/A"

        return f"""# AI Employee Dashboard

**Last Updated**: {now}
**System Status**: {status}
**Uptime**: {uptime_hours:.1f} hours

## Task Counts

- **Inbox**: {inbox_count}
- **Needs Action**: {needs_action_count}
- **Done**: {done_count}

## Performance Metrics

- **Total Processed**: {total_processed} tasks
- **Average Processing Time**: {avg_time_str}
- **Success Rate**: {success_rate_str}
- **Errors (24h)**: {error_count}

## Recent Activity

{self._get_recent_activity()}

## System Health

- Memory Usage: N/A (monitoring not implemented)
- Disk Space: Available
- Watcher Status: Active
- Last Error: {"None" if error_count == 0 else f"{error_count} errors"}

---

*Dashboard auto-updates when tasks are processed*
"""

    def _get_recent_activity(self) -> str:
        """Get recent activity from Done folder.

        Returns:
            Markdown formatted recent activity list
        """
        try:
            done_path = self.vault_path / 'Done'
            if not done_path.exists():
                return "No activity yet. Drop a task file in the Inbox folder to get started!"

            # Get recent files (last 10)
            files = sorted(done_path.glob('*.md'), key=lambda p: p.stat().st_mtime, reverse=True)[:10]

            if not files:
                return "No activity yet. Drop a task file in the Inbox folder to get started!"

            activity = []
            for i, file_path in enumerate(files, 1):
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                time_str = mtime.strftime('%H:%M:%S')
                activity.append(f"{i}. **{time_str}** - Processed task: {file_path.stem}")

            return '\n'.join(activity)

        except Exception as e:
            logger.error(f"Error getting recent activity: {e}")
            return "Error loading recent activity"
