"""Logger - Append-only audit logging for all system actions."""

from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)


class ActionType:
    """Action types for audit logging."""
    FILE_DETECTED = "FILE_DETECTED"
    FILE_MOVED = "FILE_MOVED"
    TASK_PARSED = "TASK_PARSED"
    TASK_PROCESSED = "TASK_PROCESSED"
    DASHBOARD_UPDATED = "DASHBOARD_UPDATED"
    LOG_WRITTEN = "LOG_WRITTEN"
    ERROR = "ERROR"
    SYSTEM_STARTED = "SYSTEM_STARTED"
    SYSTEM_STOPPED = "SYSTEM_STOPPED"


class AuditLogger:
    """Manages append-only audit logs in Markdown format."""

    def __init__(self, vault_path: str):
        """Initialize AuditLogger with vault path.

        Args:
            vault_path: Absolute path to the vault directory
        """
        self.vault_path = Path(vault_path).resolve()
        self.logs_path = self.vault_path / 'Logs'

        # Ensure logs directory exists
        self.logs_path.mkdir(parents=True, exist_ok=True)

    def log_action(
        self,
        action_type: str,
        result: str = "success",
        task_reference: Optional[str] = None,
        details: Optional[str] = None,
        duration_ms: Optional[int] = None
    ) -> bool:
        """Log an action to today's log file.

        Args:
            action_type: Type of action (use ActionType constants)
            result: Action result (success/failure/partial)
            task_reference: Related task ID (if applicable)
            details: Additional context or error message
            duration_ms: Action execution time in milliseconds

        Returns:
            True if logging succeeded, False otherwise
        """
        try:
            # Generate action ID
            action_id = str(uuid.uuid4())

            # Get current timestamp
            timestamp = datetime.now()
            time_str = timestamp.strftime('%H:%M:%S')

            # Get today's log file
            log_file = self._get_todays_log_file()

            # Format log entry
            entry = self._format_log_entry(
                action_id=action_id,
                action_type=action_type,
                timestamp=time_str,
                result=result,
                task_reference=task_reference,
                details=details,
                duration_ms=duration_ms
            )

            # Append to log file
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(entry)
                f.write('\n')

            logger.debug(f"Logged action: {action_type} ({result})")
            return True

        except Exception as e:
            logger.error(f"Error logging action: {e}")
            return False

    def _get_todays_log_file(self) -> Path:
        """Get path to today's log file.

        Returns:
            Path to log file (YYYY-MM-DD.md)
        """
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = self.logs_path / f'{today}.md'

        # Create file with header if it doesn't exist
        if not log_file.exists():
            header = f"""# Audit Log: {today}

**Created**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

"""
            log_file.write_text(header, encoding='utf-8')

        return log_file

    def _format_log_entry(
        self,
        action_id: str,
        action_type: str,
        timestamp: str,
        result: str,
        task_reference: Optional[str],
        details: Optional[str],
        duration_ms: Optional[int]
    ) -> str:
        """Format a log entry in Markdown.

        Args:
            action_id: Unique action identifier
            action_type: Type of action
            timestamp: Time string (HH:MM:SS)
            result: Action result
            task_reference: Related task ID
            details: Additional details
            duration_ms: Duration in milliseconds

        Returns:
            Formatted Markdown log entry
        """
        entry = f"""## {timestamp} - {action_type}

- **Action ID**: {action_id}
- **Result**: {result}"""

        if task_reference:
            entry += f"\n- **Task Reference**: {task_reference}"

        if details:
            entry += f"\n- **Details**: {details}"

        if duration_ms is not None:
            entry += f"\n- **Duration**: {duration_ms}ms"

        entry += "\n\n---\n"

        return entry

    def get_todays_log_path(self) -> Path:
        """Get path to today's log file.

        Returns:
            Path to today's log file
        """
        return self._get_todays_log_file()

    def get_recent_errors(self, count: int = 10) -> list:
        """Get recent error entries from logs.

        Args:
            count: Number of recent errors to retrieve

        Returns:
            List of error log entries
        """
        try:
            log_file = self._get_todays_log_file()
            if not log_file.exists():
                return []

            content = log_file.read_text(encoding='utf-8')
            errors = []

            # Simple parsing - look for ERROR action types
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if '- ERROR' in line:
                    # Get context (5 lines)
                    start = max(0, i - 2)
                    end = min(len(lines), i + 3)
                    error_context = '\n'.join(lines[start:end])
                    errors.append(error_context)

            return errors[-count:]

        except Exception as e:
            logger.error(f"Error getting recent errors: {e}")
            return []
