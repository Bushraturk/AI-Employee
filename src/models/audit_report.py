"""AuditReport entity model for Gold Tier.

Represents weekly business intelligence reports with financial, operational, and social metrics.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
import frontmatter
import uuid


class TrendDirection(Enum):
    """Trend direction types."""
    UP = "up"
    DOWN = "down"
    STABLE = "stable"


class AnomalySeverity(Enum):
    """Anomaly severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class FinancialSummary:
    """Financial metrics summary."""
    revenue: float = 0.0
    expenses: float = 0.0
    profit_loss: float = 0.0
    cash_flow: float = 0.0
    outstanding_invoices: int = 0
    outstanding_amount: float = 0.0
    expense_categories: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "revenue": self.revenue,
            "expenses": self.expenses,
            "profit_loss": self.profit_loss,
            "cash_flow": self.cash_flow,
            "outstanding_invoices": self.outstanding_invoices,
            "outstanding_amount": self.outstanding_amount,
            "expense_categories": self.expense_categories
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FinancialSummary":
        """Create from dictionary."""
        return cls(
            revenue=data.get("revenue", 0.0),
            expenses=data.get("expenses", 0.0),
            profit_loss=data.get("profit_loss", 0.0),
            cash_flow=data.get("cash_flow", 0.0),
            outstanding_invoices=data.get("outstanding_invoices", 0),
            outstanding_amount=data.get("outstanding_amount", 0.0),
            expense_categories=data.get("expense_categories", [])
        )


@dataclass
class OperationalMetrics:
    """Operational metrics summary."""
    tasks_completed: int = 0
    tasks_pending: int = 0
    average_response_time: float = 0.0  # seconds
    approval_rate: float = 0.0  # 0.0 to 1.0
    system_uptime: float = 0.0  # 0.0 to 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tasks_completed": self.tasks_completed,
            "tasks_pending": self.tasks_pending,
            "average_response_time": self.average_response_time,
            "approval_rate": self.approval_rate,
            "system_uptime": self.system_uptime
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OperationalMetrics":
        """Create from dictionary."""
        return cls(
            tasks_completed=data.get("tasks_completed", 0),
            tasks_pending=data.get("tasks_pending", 0),
            average_response_time=data.get("average_response_time", 0.0),
            approval_rate=data.get("approval_rate", 0.0),
            system_uptime=data.get("system_uptime", 0.0)
        )


@dataclass
class SocialMetrics:
    """Social media metrics summary."""
    total_posts: int = 0
    total_reach: int = 0
    total_engagement: int = 0
    engagement_rate: float = 0.0
    follower_growth: Dict[str, int] = field(default_factory=dict)
    top_performing_post: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_posts": self.total_posts,
            "total_reach": self.total_reach,
            "total_engagement": self.total_engagement,
            "engagement_rate": self.engagement_rate,
            "follower_growth": self.follower_growth,
            "top_performing_post": self.top_performing_post
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SocialMetrics":
        """Create from dictionary."""
        return cls(
            total_posts=data.get("total_posts", 0),
            total_reach=data.get("total_reach", 0),
            total_engagement=data.get("total_engagement", 0),
            engagement_rate=data.get("engagement_rate", 0.0),
            follower_growth=data.get("follower_growth", {}),
            top_performing_post=data.get("top_performing_post")
        )


@dataclass
class Trend:
    """Trend analysis entry."""
    metric: str
    direction: TrendDirection
    change_percent: float
    comparison: str  # e.g., "vs_previous_week"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metric": self.metric,
            "direction": self.direction.value,
            "change_percent": self.change_percent,
            "comparison": self.comparison
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Trend":
        """Create from dictionary."""
        return cls(
            metric=data["metric"],
            direction=TrendDirection(data["direction"]),
            change_percent=data["change_percent"],
            comparison=data["comparison"]
        )


@dataclass
class Anomaly:
    """Anomaly detection entry."""
    type: str  # financial, operational, social
    severity: AnomalySeverity
    description: str
    recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type,
            "severity": self.severity.value,
            "description": self.description,
            "recommendation": self.recommendation
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Anomaly":
        """Create from dictionary."""
        return cls(
            type=data["type"],
            severity=AnomalySeverity(data["severity"]),
            description=data["description"],
            recommendation=data["recommendation"]
        )


@dataclass
class AuditReport:
    """Audit report entity for weekly business intelligence.

    Storage: AI_Employee_Vault/Audits/weekly/{report_id}.md
    """

    report_id: str
    week_start_date: date
    week_end_date: date
    financial_summary: FinancialSummary
    operational_metrics: OperationalMetrics
    social_metrics: SocialMetrics
    trends: List[Trend]
    anomalies: List[Anomaly]
    recommendations: List[str]
    generated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate entity after initialization."""
        # Week end date must be 6 days after start date
        delta = (self.week_end_date - self.week_start_date).days
        if delta != 6:
            raise ValueError("week_end_date must be 6 days after week_start_date")

        # Week start date must be a Monday
        if self.week_start_date.weekday() != 0:
            raise ValueError("week_start_date must be a Monday")

        # Recommendations limit
        if len(self.recommendations) > 10:
            raise ValueError("Maximum 10 recommendations allowed")

    @classmethod
    def create(cls, week_start_date: date, financial_summary: FinancialSummary,
               operational_metrics: OperationalMetrics, social_metrics: SocialMetrics,
               trends: List[Trend], anomalies: List[Anomaly],
               recommendations: List[str]) -> "AuditReport":
        """Create a new AuditReport entity."""
        # Calculate week end date (6 days after start)
        from datetime import timedelta
        week_end_date = week_start_date + timedelta(days=6)

        return cls(
            report_id=str(uuid.uuid4()),
            week_start_date=week_start_date,
            week_end_date=week_end_date,
            financial_summary=financial_summary,
            operational_metrics=operational_metrics,
            social_metrics=social_metrics,
            trends=trends,
            anomalies=anomalies,
            recommendations=recommendations
        )

    def to_markdown(self) -> str:
        """Convert entity to Markdown format."""
        metadata = {
            "report_id": self.report_id,
            "week_start_date": self.week_start_date.isoformat(),
            "week_end_date": self.week_end_date.isoformat(),
            "generated_at": self.generated_at.isoformat()
        }

        # Build executive summary
        revenue_trend = next((t for t in self.trends if t.metric == "revenue"), None)
        revenue_change = f"{revenue_trend.change_percent:+.1f}%" if revenue_trend else "N/A"

        exec_summary = self._generate_executive_summary()

        # Build financial section
        financial_section = f"""## Financial Performance

- **Revenue**: ${self.financial_summary.revenue:,.2f} ({revenue_change} vs last week)
- **Expenses**: ${self.financial_summary.expenses:,.2f}
- **Profit/Loss**: ${self.financial_summary.profit_loss:,.2f}
- **Cash Flow**: ${self.financial_summary.cash_flow:,.2f}
- **Outstanding Invoices**: {self.financial_summary.outstanding_invoices} (${self.financial_summary.outstanding_amount:,.2f})

### Expense Breakdown
{chr(10).join(f"- {cat['category']}: ${cat['amount']:,.2f}" for cat in self.financial_summary.expense_categories)}
"""

        # Build operational section
        operational_section = f"""## Operational Metrics

- **Tasks Completed**: {self.operational_metrics.tasks_completed}
- **Tasks Pending**: {self.operational_metrics.tasks_pending}
- **Average Response Time**: {self.operational_metrics.average_response_time:.0f} seconds
- **Approval Rate**: {self.operational_metrics.approval_rate * 100:.1f}%
- **System Uptime**: {self.operational_metrics.system_uptime * 100:.1f}%
"""

        # Build social section
        social_section = f"""## Social Media Performance

- **Total Posts**: {self.social_metrics.total_posts}
- **Total Reach**: {self.social_metrics.total_reach:,}
- **Total Engagement**: {self.social_metrics.total_engagement:,}
- **Engagement Rate**: {self.social_metrics.engagement_rate:.1f}%
- **Follower Growth**: {sum(self.social_metrics.follower_growth.values())} total
"""

        if self.social_metrics.follower_growth:
            social_section += "\n### Platform Growth\n"
            for platform, growth in self.social_metrics.follower_growth.items():
                social_section += f"- {platform.title()}: +{growth}\n"

        # Build trends section
        trends_section = "## Trends\n\n"
        positive_trends = [t for t in self.trends if t.direction == TrendDirection.UP]
        negative_trends = [t for t in self.trends if t.direction == TrendDirection.DOWN]

        if positive_trends:
            trends_section += "📈 **Positive Trends**\n"
            for trend in positive_trends:
                trends_section += f"- {trend.metric.replace('_', ' ').title()} up {trend.change_percent:.1f}%\n"

        if negative_trends:
            trends_section += "\n📉 **Concerning Trends**\n"
            for trend in negative_trends:
                trends_section += f"- {trend.metric.replace('_', ' ').title()} down {abs(trend.change_percent):.1f}%\n"

        # Build anomalies section
        anomalies_section = ""
        if self.anomalies:
            anomalies_section = "\n## Anomalies Detected\n\n"
            for anomaly in self.anomalies:
                severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}[anomaly.severity.value]
                anomalies_section += f"{severity_icon} **{anomaly.severity.value.title()} Severity**\n"
                anomalies_section += f"- {anomaly.description}\n"
                anomalies_section += f"  - **Recommendation**: {anomaly.recommendation}\n\n"

        # Build recommendations section
        recommendations_section = "## Recommendations\n\n"
        for i, rec in enumerate(self.recommendations, 1):
            recommendations_section += f"{i}. {rec}\n"

        body = f"""# Weekly Business Audit: {self.week_start_date.strftime('%b %d')}-{self.week_end_date.strftime('%d, %Y')}

**Generated**: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

{exec_summary}

{financial_section}

{operational_section}

{social_section}

{trends_section}

{anomalies_section}

{recommendations_section}

## Next Week Focus

{self._generate_next_week_focus()}
"""

        post = frontmatter.Post(body, **metadata)
        return frontmatter.dumps(post)

    def _generate_executive_summary(self) -> str:
        """Generate executive summary based on metrics."""
        summary_parts = []

        # Financial summary
        if self.financial_summary.profit_loss > 0:
            summary_parts.append(f"Strong week with ${self.financial_summary.profit_loss:,.2f} profit")
        else:
            summary_parts.append(f"Loss of ${abs(self.financial_summary.profit_loss):,.2f} this week")

        # Operational summary
        if self.operational_metrics.approval_rate >= 0.95:
            summary_parts.append("excellent operational performance")
        elif self.operational_metrics.approval_rate >= 0.90:
            summary_parts.append("solid operational performance")
        else:
            summary_parts.append("operational performance needs improvement")

        # Social summary
        if self.social_metrics.engagement_rate >= 5.0:
            summary_parts.append("strong social media engagement")
        elif self.social_metrics.engagement_rate >= 3.0:
            summary_parts.append("moderate social media engagement")
        else:
            summary_parts.append("social media engagement below target")

        # Anomalies
        high_severity = [a for a in self.anomalies if a.severity == AnomalySeverity.HIGH]
        if high_severity:
            summary_parts.append(f"{len(high_severity)} high-priority issues require attention")

        return ". ".join(summary_parts).capitalize() + "."

    def _generate_next_week_focus(self) -> str:
        """Generate next week focus areas."""
        focus_areas = []

        # Based on anomalies
        for anomaly in self.anomalies:
            if anomaly.severity == AnomalySeverity.HIGH:
                focus_areas.append(f"- Address: {anomaly.description}")

        # Based on trends
        negative_trends = [t for t in self.trends if t.direction == TrendDirection.DOWN and abs(t.change_percent) > 10]
        for trend in negative_trends[:2]:  # Top 2 negative trends
            focus_areas.append(f"- Improve {trend.metric.replace('_', ' ')}")

        # Default focus if none identified
        if not focus_areas:
            focus_areas.append("- Maintain current performance levels")
            focus_areas.append("- Continue monitoring key metrics")

        return "\n".join(focus_areas)

    @classmethod
    def from_markdown(cls, content: str) -> "AuditReport":
        """Parse AuditReport from Markdown file."""
        post = frontmatter.loads(content)

        # Note: This is a simplified version
        # Full implementation would parse all sections from markdown body
        return cls(
            report_id=post["report_id"],
            week_start_date=date.fromisoformat(post["week_start_date"]),
            week_end_date=date.fromisoformat(post["week_end_date"]),
            financial_summary=FinancialSummary(),  # Would parse from body
            operational_metrics=OperationalMetrics(),  # Would parse from body
            social_metrics=SocialMetrics(),  # Would parse from body
            trends=[],  # Would parse from body
            anomalies=[],  # Would parse from body
            recommendations=[],  # Would parse from body
            generated_at=datetime.fromisoformat(post["generated_at"])
        )

    def save(self, vault_path: Path) -> Path:
        """Save entity to vault."""
        report_dir = vault_path / "Audits" / "weekly"
        report_dir.mkdir(parents=True, exist_ok=True)

        file_path = report_dir / f"{self.report_id}.md"
        file_path.write_text(self.to_markdown(), encoding="utf-8")

        return file_path

    @classmethod
    def load(cls, vault_path: Path, report_id: str) -> "AuditReport":
        """Load entity from vault."""
        file_path = vault_path / "Audits" / "weekly" / f"{report_id}.md"

        if not file_path.exists():
            raise FileNotFoundError(f"AuditReport {report_id} not found")

        content = file_path.read_text(encoding="utf-8")
        return cls.from_markdown(content)
