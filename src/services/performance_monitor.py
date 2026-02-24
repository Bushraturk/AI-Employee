"""Performance Monitoring Service for Gold Tier.

Tracks system performance metrics:
- Resource usage (CPU, memory, disk)
- API response times
- MCP server performance
- Task processing times
- Error rates
"""

import logging
import psutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import time

logger = logging.getLogger(__name__)


@dataclass
class PerformanceSnapshot:
    """Single performance measurement snapshot.

    Attributes:
        timestamp: When measurement was taken
        cpu_percent: CPU usage percentage
        memory_percent: Memory usage percentage
        disk_usage_percent: Disk usage percentage
        api_response_times: Dict of API endpoint to response time (ms)
        task_processing_times: List of recent task processing times (seconds)
        error_count: Number of errors in measurement period
        active_mcp_servers: Number of running MCP servers
    """
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    api_response_times: Dict[str, float] = field(default_factory=dict)
    task_processing_times: List[float] = field(default_factory=list)
    error_count: int = 0
    active_mcp_servers: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "timestamp": self.timestamp.isoformat(),
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "disk_usage_percent": self.disk_usage_percent,
            "api_response_times": self.api_response_times,
            "task_processing_times": self.task_processing_times,
            "error_count": self.error_count,
            "active_mcp_servers": self.active_mcp_servers
        }


class PerformanceMonitor:
    """Monitors system performance and tracks metrics.

    Features:
    - Real-time resource monitoring
    - API response time tracking
    - Task processing time tracking
    - Error rate monitoring
    - Performance trend analysis
    - Alert generation for anomalies
    """

    def __init__(self, vault_path: Path):
        """Initialize performance monitor.

        Args:
            vault_path: Path to AI Employee vault
        """
        self.vault_path = vault_path
        self.snapshots: List[PerformanceSnapshot] = []
        self.max_snapshots = 1000  # Keep last 1000 snapshots

        # Performance tracking
        self.api_timings: Dict[str, List[float]] = {}
        self.task_timings: List[float] = []
        self.error_counts: List[int] = []

        # Alert thresholds
        self.cpu_threshold = 80.0  # %
        self.memory_threshold = 85.0  # %
        self.disk_threshold = 90.0  # %
        self.api_response_threshold = 5000.0  # ms

        # Metrics directory
        self.metrics_dir = vault_path / "System" / "performance_metrics"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

    def capture_snapshot(self,
                        api_times: Optional[Dict[str, float]] = None,
                        task_times: Optional[List[float]] = None,
                        error_count: int = 0,
                        mcp_server_count: int = 0) -> PerformanceSnapshot:
        """Capture current performance snapshot.

        Args:
            api_times: Recent API response times (endpoint -> ms)
            task_times: Recent task processing times (seconds)
            error_count: Number of errors since last snapshot
            mcp_server_count: Number of active MCP servers

        Returns:
            Performance snapshot
        """
        try:
            # Capture system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage(str(self.vault_path))

            snapshot = PerformanceSnapshot(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_usage_percent=disk.percent,
                api_response_times=api_times or {},
                task_processing_times=task_times or [],
                error_count=error_count,
                active_mcp_servers=mcp_server_count
            )

            # Store snapshot
            self.snapshots.append(snapshot)

            # Trim old snapshots
            if len(self.snapshots) > self.max_snapshots:
                self.snapshots = self.snapshots[-self.max_snapshots:]

            # Check for alerts
            self._check_alerts(snapshot)

            # Persist snapshot
            self._persist_snapshot(snapshot)

            return snapshot

        except Exception as e:
            logger.error(f"Failed to capture performance snapshot: {e}")
            raise

    def record_api_call(self, endpoint: str, duration_ms: float) -> None:
        """Record API call timing.

        Args:
            endpoint: API endpoint name
            duration_ms: Response time in milliseconds
        """
        if endpoint not in self.api_timings:
            self.api_timings[endpoint] = []

        self.api_timings[endpoint].append(duration_ms)

        # Keep only last 100 timings per endpoint
        if len(self.api_timings[endpoint]) > 100:
            self.api_timings[endpoint] = self.api_timings[endpoint][-100:]

    def record_task_processing(self, duration_seconds: float) -> None:
        """Record task processing time.

        Args:
            duration_seconds: Processing duration in seconds
        """
        self.task_timings.append(duration_seconds)

        # Keep only last 100 timings
        if len(self.task_timings) > 100:
            self.task_timings = self.task_timings[-100:]

    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for specified time period.

        Args:
            hours: Number of hours to analyze

        Returns:
            Performance summary dictionary
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)

            # Filter snapshots within time period
            recent_snapshots = [
                s for s in self.snapshots
                if s.timestamp >= cutoff_time
            ]

            if not recent_snapshots:
                return {
                    "period_hours": hours,
                    "snapshot_count": 0,
                    "message": "No performance data available"
                }

            # Calculate averages
            avg_cpu = sum(s.cpu_percent for s in recent_snapshots) / len(recent_snapshots)
            avg_memory = sum(s.memory_percent for s in recent_snapshots) / len(recent_snapshots)
            avg_disk = sum(s.disk_usage_percent for s in recent_snapshots) / len(recent_snapshots)

            # Calculate API response time averages
            api_averages = {}
            for endpoint, timings in self.api_timings.items():
                if timings:
                    api_averages[endpoint] = sum(timings) / len(timings)

            # Calculate task processing average
            avg_task_time = 0.0
            if self.task_timings:
                avg_task_time = sum(self.task_timings) / len(self.task_timings)

            # Calculate total errors
            total_errors = sum(s.error_count for s in recent_snapshots)

            return {
                "period_hours": hours,
                "snapshot_count": len(recent_snapshots),
                "avg_cpu_percent": round(avg_cpu, 2),
                "avg_memory_percent": round(avg_memory, 2),
                "avg_disk_percent": round(avg_disk, 2),
                "api_response_times": {
                    k: round(v, 2) for k, v in api_averages.items()
                },
                "avg_task_processing_seconds": round(avg_task_time, 2),
                "total_errors": total_errors,
                "error_rate": round(total_errors / hours, 2)
            }

        except Exception as e:
            logger.error(f"Failed to generate performance summary: {e}")
            return {}

    def get_performance_trends(self) -> Dict[str, Any]:
        """Analyze performance trends.

        Returns:
            Trend analysis dictionary
        """
        try:
            if len(self.snapshots) < 10:
                return {
                    "message": "Insufficient data for trend analysis",
                    "snapshot_count": len(self.snapshots)
                }

            # Split snapshots into two halves for comparison
            mid_point = len(self.snapshots) // 2
            first_half = self.snapshots[:mid_point]
            second_half = self.snapshots[mid_point:]

            # Calculate averages for each half
            first_cpu = sum(s.cpu_percent for s in first_half) / len(first_half)
            second_cpu = sum(s.cpu_percent for s in second_half) / len(second_half)

            first_memory = sum(s.memory_percent for s in first_half) / len(first_half)
            second_memory = sum(s.memory_percent for s in second_half) / len(second_half)

            # Calculate trends
            cpu_trend = "increasing" if second_cpu > first_cpu else "decreasing"
            memory_trend = "increasing" if second_memory > first_memory else "decreasing"

            cpu_change = ((second_cpu - first_cpu) / first_cpu * 100) if first_cpu > 0 else 0
            memory_change = ((second_memory - first_memory) / first_memory * 100) if first_memory > 0 else 0

            return {
                "snapshot_count": len(self.snapshots),
                "cpu_trend": cpu_trend,
                "cpu_change_percent": round(cpu_change, 2),
                "memory_trend": memory_trend,
                "memory_change_percent": round(memory_change, 2),
                "analysis_period": f"{self.snapshots[0].timestamp.isoformat()} to {self.snapshots[-1].timestamp.isoformat()}"
            }

        except Exception as e:
            logger.error(f"Failed to analyze performance trends: {e}")
            return {}

    def _check_alerts(self, snapshot: PerformanceSnapshot) -> None:
        """Check snapshot for alert conditions.

        Args:
            snapshot: Performance snapshot to check
        """
        alerts = []

        # Check CPU threshold
        if snapshot.cpu_percent > self.cpu_threshold:
            alerts.append(f"High CPU usage: {snapshot.cpu_percent:.1f}%")

        # Check memory threshold
        if snapshot.memory_percent > self.memory_threshold:
            alerts.append(f"High memory usage: {snapshot.memory_percent:.1f}%")

        # Check disk threshold
        if snapshot.disk_usage_percent > self.disk_threshold:
            alerts.append(f"High disk usage: {snapshot.disk_usage_percent:.1f}%")

        # Check API response times
        for endpoint, response_time in snapshot.api_response_times.items():
            if response_time > self.api_response_threshold:
                alerts.append(f"Slow API response ({endpoint}): {response_time:.0f}ms")

        # Log alerts
        if alerts:
            for alert in alerts:
                logger.warning(f"Performance alert: {alert}")

            # Write alerts to file
            self._persist_alerts(snapshot.timestamp, alerts)

    def _persist_snapshot(self, snapshot: PerformanceSnapshot) -> None:
        """Persist snapshot to disk.

        Args:
            snapshot: Snapshot to persist
        """
        try:
            # Create daily snapshot file
            date_str = snapshot.timestamp.strftime("%Y-%m-%d")
            snapshot_file = self.metrics_dir / f"snapshots_{date_str}.md"

            # Append snapshot to file
            snapshot_line = (
                f"- **{snapshot.timestamp.strftime('%H:%M:%S')}** | "
                f"CPU: {snapshot.cpu_percent:.1f}% | "
                f"Memory: {snapshot.memory_percent:.1f}% | "
                f"Disk: {snapshot.disk_usage_percent:.1f}% | "
                f"Errors: {snapshot.error_count} | "
                f"MCP Servers: {snapshot.active_mcp_servers}\n"
            )

            # Create file with header if it doesn't exist
            if not snapshot_file.exists():
                header = f"# Performance Snapshots - {date_str}\n\n"
                snapshot_file.write_text(header + snapshot_line, encoding="utf-8")
            else:
                with open(snapshot_file, "a", encoding="utf-8") as f:
                    f.write(snapshot_line)

        except Exception as e:
            logger.error(f"Failed to persist snapshot: {e}")

    def _persist_alerts(self, timestamp: datetime, alerts: List[str]) -> None:
        """Persist performance alerts to disk.

        Args:
            timestamp: Alert timestamp
            alerts: List of alert messages
        """
        try:
            alerts_file = self.metrics_dir / "performance_alerts.md"

            # Create file with header if it doesn't exist
            if not alerts_file.exists():
                header = "# Performance Alerts\n\n"
                alerts_file.write_text(header, encoding="utf-8")

            # Append alerts
            alert_block = f"\n## {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            for alert in alerts:
                alert_block += f"- ⚠️ {alert}\n"

            with open(alerts_file, "a", encoding="utf-8") as f:
                f.write(alert_block)

        except Exception as e:
            logger.error(f"Failed to persist alerts: {e}")


class APITimer:
    """Context manager for timing API calls.

    Usage:
        with APITimer(monitor, "odoo_sync") as timer:
            # API call here
            pass
    """

    def __init__(self, monitor: PerformanceMonitor, endpoint: str):
        """Initialize API timer.

        Args:
            monitor: Performance monitor instance
            endpoint: API endpoint name
        """
        self.monitor = monitor
        self.endpoint = endpoint
        self.start_time = None

    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and record."""
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000
            self.monitor.record_api_call(self.endpoint, duration_ms)
