"""Dashboard Updater Extension for Gold Tier.

Extends dashboard with Gold Tier metrics:
- Odoo sync status
- Social media performance
- MCP server health
- Workflow executions
"""

import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timedelta

from src.models.odoo_transaction import OdooTransaction, SyncStatus
from src.models.social_media_post import SocialMediaPost, PostStatus
from src.models.workflow_execution import WorkflowExecution, ExecutionStatus
from src.orchestrator.mcp_server_orchestrator import MCPServerOrchestrator

logger = logging.getLogger(__name__)


class GoldTierDashboardUpdater:
    """Collects and formats Gold Tier metrics for dashboard display.

    Features:
    - Odoo sync status and transaction counts
    - Social media performance metrics
    - MCP server health monitoring
    - Workflow execution tracking
    """

    def __init__(self, vault_path: Path, mcp_orchestrator: MCPServerOrchestrator):
        """Initialize Gold Tier dashboard updater.

        Args:
            vault_path: Path to AI Employee vault
            mcp_orchestrator: MCP server orchestrator instance
        """
        self.vault_path = vault_path
        self.mcp_orchestrator = mcp_orchestrator
        self.dashboard_path = vault_path / "Dashboard.md"

    def collect_gold_tier_metrics(self) -> Dict[str, Any]:
        """Collect all Gold Tier metrics.

        Returns:
            Dictionary with Gold Tier metrics
        """
        try:
            return {
                "odoo": self._collect_odoo_metrics(),
                "social_media": self._collect_social_metrics(),
                "mcp_servers": self._collect_mcp_metrics(),
                "workflows": self._collect_workflow_metrics()
            }
        except Exception as e:
            logger.error(f"Failed to collect Gold Tier metrics: {e}")
            return {}

    def _collect_odoo_metrics(self) -> Dict[str, Any]:
        """Collect Odoo sync metrics.

        Returns:
            Odoo metrics dictionary
        """
        try:
            transactions_dir = self.vault_path / "Odoo_Transactions"

            if not transactions_dir.exists():
                return {
                    "total_transactions": 0,
                    "synced": 0,
                    "pending": 0,
                    "conflicts": 0,
                    "failed": 0
                }

            # Count transactions by status
            synced = 0
            pending = 0
            conflicts = 0
            failed = 0

            for tx_file in transactions_dir.glob("*.md"):
                try:
                    tx = OdooTransaction.load(self.vault_path, tx_file.stem)

                    if tx.sync_status == SyncStatus.SYNCED:
                        synced += 1
                    elif tx.sync_status == SyncStatus.PENDING:
                        pending += 1
                    elif tx.sync_status == SyncStatus.CONFLICT:
                        conflicts += 1
                    elif tx.sync_status == SyncStatus.FAILED:
                        failed += 1
                except Exception as e:
                    logger.warning(f"Failed to load transaction {tx_file.stem}: {e}")
                    continue

            total = synced + pending + conflicts + failed

            return {
                "total_transactions": total,
                "synced": synced,
                "pending": pending,
                "conflicts": conflicts,
                "failed": failed,
                "sync_rate": (synced / total * 100) if total > 0 else 0.0
            }

        except Exception as e:
            logger.error(f"Failed to collect Odoo metrics: {e}")
            return {}

    def _collect_social_metrics(self) -> Dict[str, Any]:
        """Collect social media performance metrics.

        Returns:
            Social media metrics dictionary
        """
        try:
            posts_dir = self.vault_path / "Social_Media_Posts"

            if not posts_dir.exists():
                return {
                    "total_posts": 0,
                    "posted": 0,
                    "pending_approval": 0,
                    "scheduled": 0,
                    "total_engagement": 0
                }

            # Count posts by status
            posted = 0
            pending_approval = 0
            scheduled = 0
            total_engagement = 0

            # Get posts from last 7 days
            cutoff_date = datetime.now() - timedelta(days=7)

            for post_file in posts_dir.glob("*.md"):
                try:
                    post = SocialMediaPost.load(self.vault_path, post_file.stem)

                    if post.status == PostStatus.POSTED:
                        posted += 1

                        # Calculate total engagement
                        if post.performance_metrics:
                            total_engagement += (
                                post.performance_metrics.likes +
                                post.performance_metrics.comments +
                                post.performance_metrics.shares
                            )
                    elif post.status == PostStatus.PENDING_APPROVAL:
                        pending_approval += 1
                    elif post.status == PostStatus.SCHEDULED:
                        scheduled += 1

                except Exception as e:
                    logger.warning(f"Failed to load post {post_file.stem}: {e}")
                    continue

            total = posted + pending_approval + scheduled

            return {
                "total_posts": total,
                "posted": posted,
                "pending_approval": pending_approval,
                "scheduled": scheduled,
                "total_engagement": total_engagement,
                "avg_engagement": (total_engagement / posted) if posted > 0 else 0.0
            }

        except Exception as e:
            logger.error(f"Failed to collect social metrics: {e}")
            return {}

    def _collect_mcp_metrics(self) -> Dict[str, Any]:
        """Collect MCP server health metrics.

        Returns:
            MCP server metrics dictionary
        """
        try:
            status = self.mcp_orchestrator.get_all_server_status()

            running = 0
            stopped = 0
            total_errors = 0
            total_restarts = 0

            for server_id, server_status in status.items():
                if not server_status:
                    continue

                if server_status["status"] == "running":
                    running += 1
                else:
                    stopped += 1

                total_errors += server_status.get("error_count", 0)
                total_restarts += server_status.get("restart_count", 0)

            total = running + stopped

            return {
                "total_servers": total,
                "running": running,
                "stopped": stopped,
                "total_errors": total_errors,
                "total_restarts": total_restarts,
                "health_rate": (running / total * 100) if total > 0 else 0.0
            }

        except Exception as e:
            logger.error(f"Failed to collect MCP metrics: {e}")
            return {}

    def _collect_workflow_metrics(self) -> Dict[str, Any]:
        """Collect workflow execution metrics.

        Returns:
            Workflow metrics dictionary
        """
        try:
            workflows_dir = self.vault_path / "Workflows" / "executions"

            if not workflows_dir.exists():
                return {
                    "total_workflows": 0,
                    "completed": 0,
                    "running": 0,
                    "paused": 0,
                    "failed": 0
                }

            # Count workflows by status
            completed = 0
            running = 0
            paused = 0
            failed = 0

            for workflow_file in workflows_dir.glob("*.md"):
                try:
                    workflow = WorkflowExecution.load(self.vault_path, workflow_file.stem)

                    if workflow.status == ExecutionStatus.COMPLETED:
                        completed += 1
                    elif workflow.status == ExecutionStatus.RUNNING:
                        running += 1
                    elif workflow.status == ExecutionStatus.PAUSED:
                        paused += 1
                    elif workflow.status == ExecutionStatus.FAILED:
                        failed += 1

                except Exception as e:
                    logger.warning(f"Failed to load workflow {workflow_file.stem}: {e}")
                    continue

            total = completed + running + paused + failed

            return {
                "total_workflows": total,
                "completed": completed,
                "running": running,
                "paused": paused,
                "failed": failed,
                "success_rate": (completed / total * 100) if total > 0 else 0.0
            }

        except Exception as e:
            logger.error(f"Failed to collect workflow metrics: {e}")
            return {}

    def update_dashboard_with_gold_metrics(self) -> bool:
        """Update dashboard with Gold Tier metrics section.

        Returns:
            True if update succeeded
        """
        try:
            # Collect metrics
            metrics = self.collect_gold_tier_metrics()

            if not metrics:
                logger.warning("No Gold Tier metrics collected")
                return False

            # Read existing dashboard
            if not self.dashboard_path.exists():
                logger.warning("Dashboard.md does not exist")
                return False

            content = self.dashboard_path.read_text(encoding="utf-8")

            # Generate Gold Tier section
            gold_section = self._generate_gold_tier_section(metrics)

            # Check if Gold Tier section already exists
            if "## Gold Tier Metrics" in content:
                # Replace existing section
                lines = content.split("\n")
                start_idx = None
                end_idx = None

                for i, line in enumerate(lines):
                    if line.startswith("## Gold Tier Metrics"):
                        start_idx = i
                    elif start_idx is not None and line.startswith("##"):
                        end_idx = i
                        break

                if start_idx is not None:
                    if end_idx is None:
                        # Section is at the end
                        lines = lines[:start_idx]
                    else:
                        # Section is in the middle
                        lines = lines[:start_idx] + lines[end_idx:]

                    content = "\n".join(lines)

            # Append Gold Tier section before the footer
            if "---" in content:
                parts = content.rsplit("---", 1)
                content = parts[0] + gold_section + "\n---" + parts[1]
            else:
                content += "\n" + gold_section

            # Write updated dashboard
            self.dashboard_path.write_text(content, encoding="utf-8")

            logger.info("Dashboard updated with Gold Tier metrics")
            return True

        except Exception as e:
            logger.error(f"Failed to update dashboard with Gold Tier metrics: {e}")
            return False

    def _generate_gold_tier_section(self, metrics: Dict[str, Any]) -> str:
        """Generate Gold Tier metrics section for dashboard.

        Args:
            metrics: Gold Tier metrics dictionary

        Returns:
            Markdown formatted Gold Tier section
        """
        odoo = metrics.get("odoo", {})
        social = metrics.get("social_media", {})
        mcp = metrics.get("mcp_servers", {})
        workflows = metrics.get("workflows", {})

        return f"""
## Gold Tier Metrics

### Odoo Integration
- **Total Transactions**: {odoo.get('total_transactions', 0)}
- **Synced**: {odoo.get('synced', 0)} ({odoo.get('sync_rate', 0):.1f}%)
- **Pending**: {odoo.get('pending', 0)}
- **Conflicts**: {odoo.get('conflicts', 0)}
- **Failed**: {odoo.get('failed', 0)}

### Social Media Performance
- **Total Posts (7d)**: {social.get('total_posts', 0)}
- **Posted**: {social.get('posted', 0)}
- **Pending Approval**: {social.get('pending_approval', 0)}
- **Scheduled**: {social.get('scheduled', 0)}
- **Total Engagement**: {social.get('total_engagement', 0)}
- **Avg Engagement/Post**: {social.get('avg_engagement', 0):.1f}

### MCP Server Health
- **Total Servers**: {mcp.get('total_servers', 0)}
- **Running**: {mcp.get('running', 0)} ({mcp.get('health_rate', 0):.1f}%)
- **Stopped**: {mcp.get('stopped', 0)}
- **Total Errors**: {mcp.get('total_errors', 0)}
- **Total Restarts**: {mcp.get('total_restarts', 0)}

### Workflow Executions
- **Total Workflows**: {workflows.get('total_workflows', 0)}
- **Completed**: {workflows.get('completed', 0)} ({workflows.get('success_rate', 0):.1f}%)
- **Running**: {workflows.get('running', 0)}
- **Paused**: {workflows.get('paused', 0)}
- **Failed**: {workflows.get('failed', 0)}
"""
