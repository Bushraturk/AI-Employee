"""Business auditor for analyzing business performance.

Analyzes business goals, completed tasks, and financial transactions
to generate insights and metrics.
"""

import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict

from shared.utils.vault_manager import VaultManager
from shared.models.log_entry import LogEntry


logger = logging.getLogger(__name__)


class BusinessAuditor:
    """Analyzes business performance and generates metrics."""

    def __init__(self, vault_manager: VaultManager):
        """Initialize business auditor.

        Args:
            vault_manager: Vault manager instance
        """
        self.vault_manager = vault_manager

    def analyze_period(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """Analyze business performance for a time period.

        Args:
            start_date: Period start date
            end_date: Period end date

        Returns:
            Dictionary with analysis results
        """
        logger.info(f"Analyzing period: {start_date} to {end_date}")

        # Read business goals
        goals = self._read_business_goals()

        # Analyze logs
        logs = self._read_logs(start_date, end_date)

        # Calculate metrics
        metrics = self._calculate_metrics(logs, goals)

        # Identify trends
        trends = self._identify_trends(logs, metrics)

        # Find bottlenecks
        bottlenecks = self._find_bottlenecks(logs)

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "goals": goals,
            "metrics": metrics,
            "trends": trends,
            "bottlenecks": bottlenecks,
        }

    def _read_business_goals(self) -> Dict[str, Any]:
        """Read business goals from vault.

        Returns:
            Dictionary with business goals
        """
        try:
            goals_path = self.vault_manager.vault_path / "Business_Goals.md"
            if not goals_path.exists():
                return {}

            with open(goals_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Simple parsing - extract key metrics
            goals = {
                "revenue_target": self._extract_number(content, "revenue"),
                "customer_target": self._extract_number(content, "customer"),
                "growth_target": self._extract_number(content, "growth"),
            }

            return goals

        except Exception as e:
            logger.error(f"Error reading business goals: {e}")
            return {}

    def _read_logs(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> List[LogEntry]:
        """Read log entries for period.

        Args:
            start_date: Period start
            end_date: Period end

        Returns:
            List of log entries
        """
        logs = []

        try:
            log_files = self.vault_manager.list_files("Logs", "*.md")

            for log_file in log_files:
                try:
                    log = LogEntry.from_file(str(log_file))
                    if start_date <= log.timestamp <= end_date:
                        logs.append(log)
                except Exception as e:
                    logger.warning(f"Error reading log {log_file}: {e}")

        except Exception as e:
            logger.error(f"Error reading logs: {e}")

        return logs

    def _calculate_metrics(
        self,
        logs: List[LogEntry],
        goals: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Calculate business metrics.

        Args:
            logs: Log entries
            goals: Business goals

        Returns:
            Dictionary with metrics
        """
        metrics = {
            "total_actions": len(logs),
            "emails_sent": 0,
            "social_posts": 0,
            "accounting_entries": 0,
            "whatsapp_messages": 0,
            "approvals_processed": 0,
            "errors": 0,
        }

        # Count by category
        for log in logs:
            if log.category == "email":
                metrics["emails_sent"] += 1
            elif log.category == "social":
                metrics["social_posts"] += 1
            elif log.category == "accounting":
                metrics["accounting_entries"] += 1
            elif log.category == "whatsapp":
                metrics["whatsapp_messages"] += 1
            elif log.category == "approval":
                metrics["approvals_processed"] += 1
            elif log.level == "error":
                metrics["errors"] += 1

        # Calculate success rate
        if metrics["total_actions"] > 0:
            metrics["success_rate"] = (
                (metrics["total_actions"] - metrics["errors"]) /
                metrics["total_actions"] * 100
            )
        else:
            metrics["success_rate"] = 0

        return metrics

    def _identify_trends(
        self,
        logs: List[LogEntry],
        metrics: Dict[str, Any],
    ) -> List[str]:
        """Identify trends in the data.

        Args:
            logs: Log entries
            metrics: Calculated metrics

        Returns:
            List of trend descriptions
        """
        trends = []

        # Activity trend
        if metrics["total_actions"] > 50:
            trends.append("High activity level - system is being actively used")
        elif metrics["total_actions"] < 10:
            trends.append("Low activity level - consider increasing automation")

        # Error trend
        if metrics["errors"] > metrics["total_actions"] * 0.1:
            trends.append("High error rate - investigate system issues")

        # Communication trend
        total_comms = (
            metrics["emails_sent"] +
            metrics["social_posts"] +
            metrics["whatsapp_messages"]
        )
        if total_comms > metrics["total_actions"] * 0.7:
            trends.append("Communication-heavy workload")

        return trends

    def _find_bottlenecks(self, logs: List[LogEntry]) -> List[Dict[str, Any]]:
        """Find bottlenecks in the workflow.

        Args:
            logs: Log entries

        Returns:
            List of bottleneck descriptions
        """
        bottlenecks = []

        # Group by category
        by_category = defaultdict(list)
        for log in logs:
            by_category[log.category].append(log)

        # Check for approval delays
        approval_logs = by_category.get("approval", [])
        if len(approval_logs) > 10:
            bottlenecks.append({
                "type": "approval_backlog",
                "severity": "medium",
                "description": f"{len(approval_logs)} pending approvals",
                "recommendation": "Review and process pending approvals",
            })

        # Check for error patterns
        error_logs = [log for log in logs if log.level == "error"]
        if len(error_logs) > 5:
            bottlenecks.append({
                "type": "recurring_errors",
                "severity": "high",
                "description": f"{len(error_logs)} errors detected",
                "recommendation": "Investigate and fix error sources",
            })

        return bottlenecks

    def _extract_number(self, text: str, keyword: str) -> Optional[float]:
        """Extract a number associated with a keyword.

        Args:
            text: Text to search
            keyword: Keyword to find

        Returns:
            Extracted number or None
        """
        import re

        # Simple pattern matching
        pattern = rf"{keyword}[:\s]+\$?(\d+(?:,\d+)*(?:\.\d+)?)"
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            number_str = match.group(1).replace(",", "")
            return float(number_str)

        return None
