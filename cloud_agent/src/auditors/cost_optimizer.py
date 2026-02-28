"""Cost optimizer for identifying cost savings opportunities.

Analyzes subscriptions, resource usage, and spending patterns
to identify potential cost optimizations.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import defaultdict

from shared.utils.vault_manager import VaultManager


logger = logging.getLogger(__name__)


class CostOptimizer:
    """Identifies cost optimization opportunities."""

    def __init__(self, vault_manager: VaultManager):
        """Initialize cost optimizer.

        Args:
            vault_manager: Vault manager instance
        """
        self.vault_manager = vault_manager

    def analyze_costs(self) -> Dict[str, Any]:
        """Analyze costs and identify optimization opportunities.

        Returns:
            Dictionary with cost analysis results
        """
        logger.info("Analyzing costs for optimization opportunities")

        opportunities = []

        # Check for unused subscriptions
        unused_subs = self._detect_unused_subscriptions()
        opportunities.extend(unused_subs)

        # Check for inefficient resource usage
        inefficiencies = self._detect_inefficiencies()
        opportunities.extend(inefficiencies)

        # Calculate total potential savings
        total_savings = sum(opp.get("savings", 0) for opp in opportunities)

        return {
            "opportunities": opportunities,
            "total_potential_savings": total_savings,
            "analysis_date": datetime.now().isoformat(),
        }

    def _detect_unused_subscriptions(self) -> List[Dict[str, Any]]:
        """Detect unused or underutilized subscriptions.

        Returns:
            List of unused subscription opportunities
        """
        opportunities = []

        # Common subscription patterns to check
        subscriptions = [
            {
                "name": "Email Marketing Tool",
                "cost": 29.99,
                "usage_threshold": 5,  # emails per month
                "category": "marketing",
            },
            {
                "name": "Social Media Scheduler",
                "cost": 19.99,
                "usage_threshold": 10,  # posts per month
                "category": "social",
            },
            {
                "name": "Cloud Storage",
                "cost": 9.99,
                "usage_threshold": 1,  # GB used
                "category": "storage",
            },
        ]

        # Check usage patterns
        for sub in subscriptions:
            usage = self._check_subscription_usage(sub["category"])

            if usage < sub["usage_threshold"]:
                opportunities.append({
                    "type": "unused_subscription",
                    "title": f"Underutilized: {sub['name']}",
                    "description": (
                        f"Only {usage} {sub['category']} actions this month. "
                        f"Consider canceling or downgrading."
                    ),
                    "savings": sub["cost"],
                    "priority": "medium",
                })

        return opportunities

    def _detect_inefficiencies(self) -> List[Dict[str, Any]]:
        """Detect operational inefficiencies.

        Returns:
            List of inefficiency opportunities
        """
        opportunities = []

        # Check for duplicate tools
        tools_used = self._analyze_tool_usage()

        if len(tools_used.get("email", [])) > 1:
            opportunities.append({
                "type": "duplicate_tools",
                "title": "Multiple Email Tools",
                "description": (
                    "Using multiple email tools. Consolidate to one platform."
                ),
                "savings": 15.00,
                "priority": "low",
            })

        # Check for manual processes that could be automated
        manual_tasks = self._detect_manual_tasks()

        if manual_tasks > 10:
            time_saved_hours = manual_tasks * 0.5  # 30 min per task
            cost_per_hour = 50  # Assumed hourly rate
            savings = time_saved_hours * cost_per_hour

            opportunities.append({
                "type": "automation_opportunity",
                "title": "Automate Manual Tasks",
                "description": (
                    f"{manual_tasks} manual tasks detected. "
                    f"Automation could save {time_saved_hours:.1f} hours/month."
                ),
                "savings": savings,
                "priority": "high",
            })

        return opportunities

    def _check_subscription_usage(self, category: str) -> int:
        """Check usage for a subscription category.

        Args:
            category: Subscription category

        Returns:
            Usage count
        """
        try:
            # Count actions in the last 30 days
            thirty_days_ago = datetime.now() - timedelta(days=30)

            log_files = self.vault_manager.list_files("Logs", "*.md")
            usage_count = 0

            for log_file in log_files:
                try:
                    # Simple check - count files with category in name
                    if category.lower() in str(log_file).lower():
                        usage_count += 1
                except Exception:
                    pass

            return usage_count

        except Exception as e:
            logger.error(f"Error checking subscription usage: {e}")
            return 0

    def _analyze_tool_usage(self) -> Dict[str, List[str]]:
        """Analyze which tools are being used.

        Returns:
            Dictionary mapping categories to tool names
        """
        tools = defaultdict(list)

        # This would analyze actual tool usage from logs
        # For now, return empty to avoid false positives
        return dict(tools)

    def _detect_manual_tasks(self) -> int:
        """Detect number of manual tasks.

        Returns:
            Count of manual tasks
        """
        try:
            # Count approval requests as proxy for manual tasks
            approval_files = self.vault_manager.list_files("Pending_Approval", "*.md")
            return len(approval_files)

        except Exception as e:
            logger.error(f"Error detecting manual tasks: {e}")
            return 0

    def generate_cost_report(self, analysis: Dict[str, Any]) -> str:
        """Generate cost optimization report.

        Args:
            analysis: Cost analysis results

        Returns:
            Formatted report as markdown
        """
        opportunities = analysis.get("opportunities", [])
        total_savings = analysis.get("total_potential_savings", 0)

        report = "# Cost Optimization Report\n\n"
        report += f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"**Potential Monthly Savings**: ${total_savings:.2f}\n\n"

        if not opportunities:
            report += "No cost optimization opportunities identified at this time.\n"
            return report

        # Group by priority
        by_priority = defaultdict(list)
        for opp in opportunities:
            priority = opp.get("priority", "medium")
            by_priority[priority].append(opp)

        # High priority first
        for priority in ["high", "medium", "low"]:
            opps = by_priority.get(priority, [])
            if not opps:
                continue

            report += f"## {priority.capitalize()} Priority\n\n"

            for opp in opps:
                report += f"### {opp.get('title', '')}\n"
                report += f"**Savings**: ${opp.get('savings', 0):.2f}/month\n"
                report += f"{opp.get('description', '')}\n\n"

        return report
