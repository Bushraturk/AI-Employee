"""Logging utility for audit logging to vault."""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from shared.models.log_entry import LogEntry, LogLevel, LogCategory


class VaultLogger:
    """Logger that writes audit logs to the vault Logs/ folder.

    Writes logs as JSON lines to daily log files.
    Integrates with Python's logging module.
    """

    def __init__(self, vault_root: Path, agent_id: Optional[str] = None):
        """Initialize vault logger.

        Args:
            vault_root: Root path of the vault
            agent_id: Agent ID for this logger
        """
        self.vault_root = vault_root
        self.logs_folder = vault_root / "Logs"
        self.agent_id = agent_id

        # Ensure logs folder exists
        self.logs_folder.mkdir(parents=True, exist_ok=True)

        # Setup Python logger
        self.logger = logging.getLogger(f"vault.{agent_id or 'system'}")

    def _get_log_file_path(self, date: Optional[datetime] = None) -> Path:
        """Get log file path for a given date.

        Args:
            date: Date for the log file (defaults to today)

        Returns:
            Path to the log file
        """
        if date is None:
            date = datetime.now()
        filename = LogEntry.get_log_filename(date)
        return self.logs_folder / filename

    def _write_log_entry(self, entry: LogEntry) -> None:
        """Write a log entry to the appropriate log file.

        Args:
            entry: Log entry to write
        """
        log_file = self._get_log_file_path(entry.timestamp)

        # Append JSON line to log file
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry.to_json_line() + "\n")

    def log(
        self,
        level: LogLevel,
        category: LogCategory,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        watcher_id: Optional[str] = None,
        action_id: Optional[str] = None,
        approval_id: Optional[str] = None,
        error_type: Optional[str] = None,
        stack_trace: Optional[str] = None,
    ) -> None:
        """Write a log entry.

        Args:
            level: Log level
            category: Log category
            message: Log message
            details: Additional details
            watcher_id: Related watcher ID
            action_id: Related action ID
            approval_id: Related approval ID
            error_type: Error type (for error logs)
            stack_trace: Stack trace (for error logs)
        """
        entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            category=category,
            message=message,
            details=details or {},
            agent_id=self.agent_id,
            watcher_id=watcher_id,
            action_id=action_id,
            approval_id=approval_id,
            error_type=error_type,
            stack_trace=stack_trace,
        )

        self._write_log_entry(entry)

        # Also log to Python logger
        python_level = {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL,
        }[level]

        self.logger.log(python_level, f"[{category.value}] {message}")

    def debug(
        self,
        category: LogCategory,
        message: str,
        **kwargs
    ) -> None:
        """Write a debug log entry."""
        self.log(LogLevel.DEBUG, category, message, **kwargs)

    def info(
        self,
        category: LogCategory,
        message: str,
        **kwargs
    ) -> None:
        """Write an info log entry."""
        self.log(LogLevel.INFO, category, message, **kwargs)

    def warning(
        self,
        category: LogCategory,
        message: str,
        **kwargs
    ) -> None:
        """Write a warning log entry."""
        self.log(LogLevel.WARNING, category, message, **kwargs)

    def error(
        self,
        category: LogCategory,
        message: str,
        error_type: Optional[str] = None,
        stack_trace: Optional[str] = None,
        **kwargs
    ) -> None:
        """Write an error log entry."""
        self.log(
            LogLevel.ERROR,
            category,
            message,
            error_type=error_type,
            stack_trace=stack_trace,
            **kwargs
        )

    def critical(
        self,
        category: LogCategory,
        message: str,
        error_type: Optional[str] = None,
        stack_trace: Optional[str] = None,
        **kwargs
    ) -> None:
        """Write a critical log entry."""
        self.log(
            LogLevel.CRITICAL,
            category,
            message,
            error_type=error_type,
            stack_trace=stack_trace,
            **kwargs
        )

    def read_logs(
        self,
        date: Optional[datetime] = None,
        level: Optional[LogLevel] = None,
        category: Optional[LogCategory] = None,
    ) -> list[LogEntry]:
        """Read log entries from a log file.

        Args:
            date: Date to read logs from (defaults to today)
            level: Filter by log level
            category: Filter by category

        Returns:
            List of log entries
        """
        log_file = self._get_log_file_path(date)

        if not log_file.exists():
            return []

        entries = []
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = LogEntry.from_json_line(line)

                    # Apply filters
                    if level and entry.level != level:
                        continue
                    if category and entry.category != category:
                        continue

                    entries.append(entry)
                except Exception as e:
                    self.logger.error(f"Failed to parse log line: {e}")

        return entries
