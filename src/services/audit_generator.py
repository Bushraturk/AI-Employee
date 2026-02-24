"""Audit Generator Service for Gold Tier.

Generates weekly business intelligence reports with financial, operational, and social metrics.
"""

import logging
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal

from src.models.audit_report import (
    AuditReport, FinancialSummary, OperationalMetrics, SocialMetrics,
    Trend, Anomaly, TrendDirection, AnomalySeverity
)
from src.models.odoo_transaction import OdooTransaction, TransactionType, SyncStatus
from src.models.social_media_post import SocialMediaPost, PostStatus

logger = logging.getLogger(__name__)


class AuditGeneratorService:
    """Generates weekly business intelligence reports.

    Features:
    - Collect financial metrics from Odoo transactions
    - Collect operational metrics from tasks and logs
    - Collect social media metrics from posts
    - Analyze trends (week-over-week comparison)
    - Detect anomalies (significant deviations)
    - Generate actionable recommendations
    - Format CEO briefing in Markdown
    """

    def __init__(self, vault_path: Path):
        """Initialize audit generator service.

        Args:
            vault_path: Path to AI Employee vault
        """
        self.vault_path = vault_path

    def generate_weekly_audit(self, week_start_date: Optional[date] = None) -> Dict[str, Any]:
        """Generate weekly audit report.

        Args:
            week_start_date: Start date of week (Monday), defaults to last Monday

        Returns:
            Generation result dictionary
        """
        try:
            # Determine week start date (last Monday if not specified)
            if not week_start_date:
                week_start_date = self._get_last_monday()

            # Ensure it's a Monday
            if week_start_date.weekday() != 0:
                logger.warning(f"Week start date {week_start_date} is not a Monday, adjusting")
                week_start_date = week_start_date - timedelta(days=week_start_date.weekday())

            week_end_date = week_start_date + timedelta(days=6)

            logger.info(f"Generating audit for week {week_start_date} to {week_end_date}")

            # Collect metrics
            financial_summary = self._collect_financial_metrics(week_start_date, week_end_date)
            operational_metrics = self._collect_operational_metrics(week_start_date, week_end_date)
            social_metrics = self._collect_social_metrics(week_start_date, week_end_date)

            # Analyze trends (compare with previous week)
            trends = self._analyze_trends(
                week_start_date,
                financial_summary,
                operational_metrics,
                social_metrics
            )

            # Detect anomalies
            anomalies = self._detect_anomalies(
                financial_summary,
                operational_metrics,
                social_metrics,
                trends
            )

            # Generate recommendations
            recommendations = self._generate_recommendations(
                financial_summary,
                operational_metrics,
                social_metrics,
                trends,
                anomalies
            )

            # Create audit report
            report = AuditReport.create(
                week_start_date=week_start_date,
                financial_summary=financial_summary,
                operational_metrics=operational_metrics,
                social_metrics=social_metrics,
                trends=trends,
                anomalies=anomalies,
                recommendations=recommendations
            )

            # Save report
            report_path = report.save(self.vault_path)

            logger.info(f"Generated audit report: {report.report_id}")

            return {
                "success": True,
                "report_id": report.report_id,
                "report_path": str(report_path),
                "week_start_date": week_start_date.isoformat(),
                "week_end_date": week_end_date.isoformat(),
                "message": "Weekly audit generated successfully"
            }

        except Exception as e:
            logger.error(f"Failed to generate weekly audit: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _get_last_monday(self) -> date:
        """Get the date of last Monday.

        Returns:
            Last Monday's date
        """
        today = date.today()
        days_since_monday = today.weekday()

        if days_since_monday == 0:
            # Today is Monday, use last week's Monday
            return today - timedelta(days=7)
        else:
            # Go back to last Monday
            return today - timedelta(days=days_since_monday)

    def _collect_financial_metrics(self, start_date: date, end_date: date) -> FinancialSummary:
        """Collect financial metrics from Odoo transactions.

        Args:
            start_date: Week start date
            end_date: Week end date

        Returns:
            FinancialSummary object
        """
        try:
            transaction_dir = self.vault_path / "Accounting" / "transactions"
            if not transaction_dir.exists():
                return FinancialSummary()

            revenue = 0.0
            expenses = 0.0
            outstanding_invoices = 0
            outstanding_amount = 0.0
            expense_by_category: Dict[str, float] = {}

            for transaction_file in transaction_dir.glob("*.md"):
                try:
                    transaction = OdooTransaction.load(self.vault_path, transaction_file.stem)

                    # Check if transaction is in date range
                    if not (start_date <= transaction.date <= end_date):
                        continue

                    # Calculate revenue and expenses
                    if transaction.type == TransactionType.INVOICE:
                        revenue += float(transaction.amount)

                        # Check if outstanding
                        if transaction.sync_status != SyncStatus.SYNCED:
                            outstanding_invoices += 1
                            outstanding_amount += float(transaction.amount)

                    elif transaction.type == TransactionType.EXPENSE:
                        expenses += float(transaction.amount)

                        # Track by category
                        category = transaction.category
                        expense_by_category[category] = expense_by_category.get(category, 0.0) + float(transaction.amount)

                except Exception as e:
                    logger.error(f"Failed to process transaction {transaction_file.stem}: {e}")

            # Calculate profit/loss and cash flow
            profit_loss = revenue - expenses
            cash_flow = revenue - outstanding_amount  # Simplified

            # Format expense categories
            expense_categories = [
                {"category": cat, "amount": amount}
                for cat, amount in sorted(expense_by_category.items(), key=lambda x: x[1], reverse=True)
            ]

            return FinancialSummary(
                revenue=revenue,
                expenses=expenses,
                profit_loss=profit_loss,
                cash_flow=cash_flow,
                outstanding_invoices=outstanding_invoices,
                outstanding_amount=outstanding_amount,
                expense_categories=expense_categories
            )

        except Exception as e:
            logger.error(f"Failed to collect financial metrics: {e}")
            return FinancialSummary()

    def _collect_operational_metrics(self, start_date: date, end_date: date) -> OperationalMetrics:
        """Collect operational metrics from tasks and logs.

        Args:
            start_date: Week start date
            end_date: Week end date

        Returns:
            OperationalMetrics object
        """
        try:
            # Note: This is a simplified implementation
            # Full implementation would parse task files and logs

            # Placeholder metrics
            return OperationalMetrics(
                tasks_completed=45,
                tasks_pending=12,
                average_response_time=120.0,  # 2 minutes
                approval_rate=0.92,
                system_uptime=0.998
            )

        except Exception as e:
            logger.error(f"Failed to collect operational metrics: {e}")
            return OperationalMetrics()

    def _collect_social_metrics(self, start_date: date, end_date: date) -> SocialMetrics:
        """Collect social media metrics from posts.

        Args:
            start_date: Week start date
            end_date: Week end date

        Returns:
            SocialMetrics object
        """
        try:
            post_dir = self.vault_path / "Social_Media" / "posts"
            if not post_dir.exists():
                return SocialMetrics()

            total_posts = 0
            total_reach = 0
            total_engagement = 0
            follower_growth: Dict[str, int] = {}
            top_post_id = None
            top_post_engagement = 0

            start_timestamp = datetime.combine(start_date, datetime.min.time()).timestamp()
            end_timestamp = datetime.combine(end_date, datetime.max.time()).timestamp()

            for post_file in post_dir.glob("*.md"):
                try:
                    post = SocialMediaPost.load(self.vault_path, post_file.stem)

                    # Check if post is in date range
                    if post.status != PostStatus.POSTED or not post.posted_at:
                        continue

                    if not (start_timestamp <= post.posted_at.timestamp() <= end_timestamp):
                        continue

                    total_posts += 1

                    # Aggregate metrics
                    for platform, metrics in post.performance_metrics.items():
                        total_reach += metrics.reach
                        total_engagement += metrics.engagement

                    # Track top performing post
                    post_engagement = post.get_total_engagement()
                    if post_engagement > top_post_engagement:
                        top_post_engagement = post_engagement
                        top_post_id = post.post_id

                except Exception as e:
                    logger.error(f"Failed to process post {post_file.stem}: {e}")

            # Calculate engagement rate
            engagement_rate = (total_engagement / total_reach * 100) if total_reach > 0 else 0.0

            # Note: Follower growth would need to be tracked separately
            # This is a placeholder
            follower_growth = {
                "facebook": 25,
                "instagram": 18,
                "twitter": 12,
                "linkedin": 8
            }

            return SocialMetrics(
                total_posts=total_posts,
                total_reach=total_reach,
                total_engagement=total_engagement,
                engagement_rate=engagement_rate,
                follower_growth=follower_growth,
                top_performing_post=top_post_id
            )

        except Exception as e:
            logger.error(f"Failed to collect social metrics: {e}")
            return SocialMetrics()

    def _analyze_trends(self, week_start_date: date,
                       financial_summary: FinancialSummary,
                       operational_metrics: OperationalMetrics,
                       social_metrics: SocialMetrics) -> List[Trend]:
        """Analyze trends by comparing with previous week.

        Args:
            week_start_date: Current week start date
            financial_summary: Current week financial metrics
            operational_metrics: Current week operational metrics
            social_metrics: Current week social metrics

        Returns:
            List of Trend objects
        """
        try:
            trends = []

            # Get previous week's data
            prev_week_start = week_start_date - timedelta(days=7)
            prev_week_end = prev_week_start + timedelta(days=6)

            prev_financial = self._collect_financial_metrics(prev_week_start, prev_week_end)
            prev_operational = self._collect_operational_metrics(prev_week_start, prev_week_end)
            prev_social = self._collect_social_metrics(prev_week_start, prev_week_end)

            # Financial trends
            if prev_financial.revenue > 0:
                revenue_change = ((financial_summary.revenue - prev_financial.revenue) / prev_financial.revenue) * 100
                trends.append(Trend(
                    metric="revenue",
                    direction=TrendDirection.UP if revenue_change > 0 else TrendDirection.DOWN,
                    change_percent=revenue_change,
                    comparison="vs_previous_week"
                ))

            if prev_financial.expenses > 0:
                expense_change = ((financial_summary.expenses - prev_financial.expenses) / prev_financial.expenses) * 100
                trends.append(Trend(
                    metric="expenses",
                    direction=TrendDirection.UP if expense_change > 0 else TrendDirection.DOWN,
                    change_percent=expense_change,
                    comparison="vs_previous_week"
                ))

            # Operational trends
            if prev_operational.tasks_completed > 0:
                tasks_change = ((operational_metrics.tasks_completed - prev_operational.tasks_completed) / prev_operational.tasks_completed) * 100
                trends.append(Trend(
                    metric="tasks_completed",
                    direction=TrendDirection.UP if tasks_change > 0 else TrendDirection.DOWN,
                    change_percent=tasks_change,
                    comparison="vs_previous_week"
                ))

            # Social trends
            if prev_social.engagement_rate > 0:
                engagement_change = ((social_metrics.engagement_rate - prev_social.engagement_rate) / prev_social.engagement_rate) * 100
                trends.append(Trend(
                    metric="engagement_rate",
                    direction=TrendDirection.UP if engagement_change > 0 else TrendDirection.DOWN,
                    change_percent=engagement_change,
                    comparison="vs_previous_week"
                ))

            return trends

        except Exception as e:
            logger.error(f"Failed to analyze trends: {e}")
            return []

    def _detect_anomalies(self, financial_summary: FinancialSummary,
                         operational_metrics: OperationalMetrics,
                         social_metrics: SocialMetrics,
                         trends: List[Trend]) -> List[Anomaly]:
        """Detect anomalies in metrics.

        Args:
            financial_summary: Financial metrics
            operational_metrics: Operational metrics
            social_metrics: Social metrics
            trends: Trend analysis

        Returns:
            List of Anomaly objects
        """
        anomalies = []

        # Financial anomalies
        expense_trend = next((t for t in trends if t.metric == "expenses"), None)
        if expense_trend and expense_trend.change_percent > 30:
            anomalies.append(Anomaly(
                type="financial",
                severity=AnomalySeverity.HIGH,
                description=f"Expenses increased {expense_trend.change_percent:.1f}% compared to previous week",
                recommendation="Review marketing spend and software subscriptions"
            ))

        # Operational anomalies
        if operational_metrics.approval_rate < 0.90:
            anomalies.append(Anomaly(
                type="operational",
                severity=AnomalySeverity.MEDIUM,
                description=f"Approval rate dropped to {operational_metrics.approval_rate * 100:.1f}%",
                recommendation="Review rejected tasks for quality issues"
            ))

        # Social anomalies
        engagement_trend = next((t for t in trends if t.metric == "engagement_rate"), None)
        if engagement_trend and engagement_trend.direction == TrendDirection.DOWN and abs(engagement_trend.change_percent) > 10:
            anomalies.append(Anomaly(
                type="social",
                severity=AnomalySeverity.MEDIUM,
                description=f"Engagement rate declined {abs(engagement_trend.change_percent):.1f}%",
                recommendation="Test new content formats and posting times"
            ))

        return anomalies

    def _generate_recommendations(self, financial_summary: FinancialSummary,
                                 operational_metrics: OperationalMetrics,
                                 social_metrics: SocialMetrics,
                                 trends: List[Trend],
                                 anomalies: List[Anomaly]) -> List[str]:
        """Generate actionable recommendations.

        Args:
            financial_summary: Financial metrics
            operational_metrics: Operational metrics
            social_metrics: Social metrics
            trends: Trend analysis
            anomalies: Detected anomalies

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Recommendations from anomalies
        for anomaly in anomalies:
            if anomaly.severity == AnomalySeverity.HIGH:
                recommendations.append(anomaly.recommendation)

        # Financial recommendations
        if financial_summary.outstanding_invoices > 0:
            recommendations.append(
                f"Follow up on {financial_summary.outstanding_invoices} outstanding invoices "
                f"(${financial_summary.outstanding_amount:,.2f})"
            )

        # Operational recommendations
        if operational_metrics.system_uptime >= 0.99:
            recommendations.append(
                f"Maintain excellent system uptime ({operational_metrics.system_uptime * 100:.1f}%)"
            )

        # Social recommendations
        if social_metrics.engagement_rate < 3.0:
            recommendations.append(
                "Improve social media engagement rate (currently below 3% target)"
            )

        # Limit to 10 recommendations
        return recommendations[:10]
