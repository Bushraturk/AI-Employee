"""Log Rotation Service for Gold Tier.

Implements daily log rotation with 30-day retention.
"""

import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class LogRotator:
    """Rotates log files daily with configurable retention.

    Features:
    - Daily rotation at midnight
    - Configurable retention period (default: 30 days)
    - Automatic cleanup of old logs
    - Support for multiple log directories
    """

    def __init__(self, vault_path: Path, retention_days: int = 30):
        """Initialize log rotator.

        Args:
            vault_path: Path to AI Employee vault
            retention_days: Number of days to retain logs
        """
        self.vault_path = vault_path
        self.retention_days = retention_days

        # Log directories to rotate
        self.log_dirs = [
            vault_path / "Logs",
            vault_path / "Logs" / "error_recovery"
        ]

    def rotate_logs(self) -> Dict[str, Any]:
        """Rotate all log files.

        Returns:
            Rotation result dictionary
        """
        try:
            rotated_count = 0
            deleted_count = 0

            for log_dir in self.log_dirs:
                if not log_dir.exists():
                    continue

                # Rotate logs in this directory
                result = self._rotate_directory(log_dir)
                rotated_count += result["rotated"]
                deleted_count += result["deleted"]

            logger.info(
                f"Log rotation complete: {rotated_count} rotated, "
                f"{deleted_count} deleted"
            )

            return {
                "success": True,
                "rotated_count": rotated_count,
                "deleted_count": deleted_count
            }

        except Exception as e:
            logger.error(f"Log rotation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _rotate_directory(self, log_dir: Path) -> Dict[str, int]:
        """Rotate logs in a specific directory.

        Args:
            log_dir: Directory to rotate

        Returns:
            Dictionary with rotation counts
        """
        rotated = 0
        deleted = 0

        try:
            # Get all log files
            log_files = list(log_dir.glob("*.log"))

            # Rotate each log file
            for log_file in log_files:
                # Create rotated filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d")
                rotated_name = f"{log_file.stem}_{timestamp}.log"
                rotated_path = log_dir / rotated_name

                # Rename log file
                if not rotated_path.exists():
                    log_file.rename(rotated_path)
                    rotated += 1

            # Clean up old logs
            deleted = self._cleanup_old_logs(log_dir)

            return {
                "rotated": rotated,
                "deleted": deleted
            }

        except Exception as e:
            logger.error(f"Failed to rotate directory {log_dir}: {e}")
            return {
                "rotated": 0,
                "deleted": 0
            }

    def _cleanup_old_logs(self, log_dir: Path) -> int:
        """Delete logs older than retention period.

        Args:
            log_dir: Directory to clean

        Returns:
            Number of files deleted
        """
        deleted = 0

        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            cutoff_timestamp = cutoff_date.timestamp()

            # Find old log files
            for log_file in log_dir.glob("*.log"):
                if log_file.stat().st_mtime < cutoff_timestamp:
                    log_file.unlink()
                    deleted += 1

            return deleted

        except Exception as e:
            logger.error(f"Failed to cleanup old logs: {e}")
            return 0

    def get_log_statistics(self) -> Dict[str, Any]:
        """Get statistics about log files.

        Returns:
            Statistics dictionary
        """
        try:
            stats = {
                "total_logs": 0,
                "total_size_mb": 0.0,
                "by_directory": {}
            }

            for log_dir in self.log_dirs:
                if not log_dir.exists():
                    continue

                log_files = list(log_dir.glob("*.log"))
                total_size = sum(f.stat().st_size for f in log_files)

                stats["total_logs"] += len(log_files)
                stats["total_size_mb"] += total_size / (1024 * 1024)

                stats["by_directory"][str(log_dir)] = {
                    "count": len(log_files),
                    "size_mb": total_size / (1024 * 1024)
                }

            return stats

        except Exception as e:
            logger.error(f"Failed to get log statistics: {e}")
            return {}
