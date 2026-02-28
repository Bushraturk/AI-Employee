"""Briefing generator for creating executive summaries.

Generates comprehensive business briefings with insights,
recommendations, and action items.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any

from shared.utils.vault_manager import VaultManager


logger = logging.getLogger(__name__)


class BriefingGenerator:
    """Generates executive briefings from audit data."""

    def __init__(self, vault_manager: VaultManager):
        """Initialize briefing generator.

        Args:
            vault_manager: Vault manager instance
        """
        self.vault_manager = vault_manager

    def generate_briefing(
        self,
        audit_data: Dict[str, Any],
        cost_analysis: Dict[str, Any],
    ) -> str:
        """Generate executive briefing.

        Args:
            audit_data: Audit analysis results
            cost_analysis: Cost optimization analysis

        Returns:
            Formatted briefing as markdown
        """
        logger.info("Generating executive briefing")

        # Build briefing sections
        sections = []

        # Header
        sections.append(self._generate_header(audit_data))

        # Executive summary
        sections.append(self._generate_executive_summary(audit_data))

        # Key metrics
        sections.append(self._generate_metrics_section(audit_data))

        # Trends and insights
        sections.append(self._generate_trends_section(audit_data))

        # Bottlenecks
        sections.append(self._generate_bottlenecks_section(audit_data))

        # Cost optimization
        sections.append(self._generate_cost_section(cost_analysis))

        # Recommendations
        sections.append(self._generate_recommendations(audit_data, cost_analysis))

        # Footer
        sections.append(self._generate_footer())

        return "\n\n".join(sections)

    def _generate_header(self, audit_data: Dict[str, Any]) -> str:
        """Generate briefing header."""
        period = audit_data.get("period", {})
        start = period.get("start", "")
        end = period.get("end", "")

        return f"""# Weekly Business Briefing

**Period**: {start} to {end}
**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Status**: Automated Analysis"""

    def _generate_executive_summary(self, audit_data: Dict[str, Any]) -> str:
        """Generate executive summary."""
        metrics = audit_data.get("metrics", {})
        trends = audit_data.get("trends", [])

        summary_points = []

        # Activity summary
        total_actions = metrics.get("total_actions", 0)
        success_rate = metrics.get("success_rate", 0)
        summary_points.append(
            f"Processed {total_actions} actions with {success_rate:.1f}% success rate"
        )

        # Communication summary
        emails = metrics.get("emails_sent", 0)
        posts = metrics.get("social_posts", 0)
        summary_points.append(
            f"Sent {emails} emails and published {posts} social media posts"
        )

        # Key trend
        if trends:
            summary_points.append(trends[0])

        summary = "## Executive Summary\n\n"
        for point in summary_points:
            summary += f"- {point}\n"

        return summary

    def _generate_metrics_section(self, audit_data: Dict[str, Any]) -> str:
        """Generate metrics section."""
        metrics = audit_data.get("metrics", {})

        section = "## Key Metrics\n\n"
        section += f"- **Total Actions**: {metrics.get('total_actions', 0)}\n"
        section += f"- **Emails Sent**: {metrics.get('emails_sent', 0)}\n"
        section += f"- **Social Posts**: {metrics.get('social_posts', 0)}\n"
        section += f"- **Accounting Entries**: {metrics.get('accounting_entries', 0)}\n"
        section += f"- **WhatsApp Messages**: {metrics.get('whatsapp_messages', 0)}\n"
        section += f"- **Approvals Processed**: {metrics.get('approvals_processed', 0)}\n"
        section += f"- **Success Rate**: {metrics.get('success_rate', 0):.1f}%\n"

        return section

    def _generate_trends_section(self, audit_data: Dict[str, Any]) -> str:
        """Generate trends section."""
        trends = audit_data.get("trends", [])

        if not trends:
            return "## Trends\n\nNo significant trends detected."

        section = "## Trends & Insights\n\n"
        for trend in trends:
            section += f"- {trend}\n"

        return section

    def _generate_bottlenecks_section(self, audit_data: Dict[str, Any]) -> str:
        """Generate bottlenecks section."""
        bottlenecks = audit_data.get("bottlenecks", [])

        if not bottlenecks:
            return "## Bottlenecks\n\nNo bottlenecks detected. System running smoothly."

        section = "## Bottlenecks & Issues\n\n"
        for bottleneck in bottlenecks:
            severity = bottleneck.get("severity", "medium").upper()
            description = bottleneck.get("description", "")
            recommendation = bottleneck.get("recommendation", "")

            section += f"### [{severity}] {description}\n"
            section += f"**Recommendation**: {recommendation}\n\n"

        return section

    def _generate_cost_section(self, cost_analysis: Dict[str, Any]) -> str:
        """Generate cost optimization section."""
        opportunities = cost_analysis.get("opportunities", [])

        if not opportunities:
            return "## Cost Optimization\n\nNo cost optimization opportunities identified."

        section = "## Cost Optimization Opportunities\n\n"
        total_savings = cost_analysis.get("total_potential_savings", 0)
        section += f"**Potential Monthly Savings**: ${total_savings:.2f}\n\n"

        for opp in opportunities:
            section += f"- **{opp.get('title', '')}**: ${opp.get('savings', 0):.2f}/month\n"
            section += f"  - {opp.get('description', '')}\n"

        return section

    def _generate_recommendations(
        self,
        audit_data: Dict[str, Any],
        cost_analysis: Dict[str, Any],
    ) -> str:
        """Generate recommendations section."""
        recommendations = []

        # Based on bottlenecks
        bottlenecks = audit_data.get("bottlenecks", [])
        for bottleneck in bottlenecks:
            recommendations.append(bottleneck.get("recommendation", ""))

        # Based on cost analysis
        opportunities = cost_analysis.get("opportunities", [])
        if opportunities:
            recommendations.append(
                f"Review {len(opportunities)} cost optimization opportunities"
            )

        # Based on metrics
        metrics = audit_data.get("metrics", {})
        if metrics.get("errors", 0) > 0:
            recommendations.append("Investigate and resolve system errors")

        if not recommendations:
            recommendations.append("Continue current operations")

        section = "## Recommendations\n\n"
        for i, rec in enumerate(recommendations, 1):
            section += f"{i}. {rec}\n"

        return section

    def _generate_footer(self) -> str:
        """Generate briefing footer."""
        return """---

*This briefing was automatically generated by the AI Employee system.*
*For questions or concerns, review the detailed logs in the vault.*"""

    def save_briefing(self, briefing: str, filename: Optional[str] = None) -> str:
        """Save briefing to vault.

        Args:
            briefing: Briefing content
            filename: Optional filename (defaults to timestamp)

        Returns:
            Path to saved briefing
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"briefing_{timestamp}.md"

        briefing_path = self.vault_manager.vault_path / "Plans" / filename

        with open(briefing_path, "w", encoding="utf-8") as f:
            f.write(briefing)

        logger.info(f"Saved briefing to {briefing_path}")
        return str(briefing_path)
