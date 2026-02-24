"""CLI commands for Gold Tier.

Provides command-line interface for Gold Tier features.
"""

import argparse
import sys
from pathlib import Path
from datetime import date, datetime

from src.services.audit_generator import AuditGeneratorService
from src.orchestrator.mcp_server_orchestrator import MCPServerOrchestrator
from src.orchestrator.approval_manager import ApprovalManager
from src.orchestrator.ralph_wiggum import RalphWiggumOrchestrator


def generate_audit_command(args):
    """Generate weekly audit report."""
    vault_path = Path(args.vault)

    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        return 1

    audit_service = AuditGeneratorService(vault_path)

    # Parse week start date if provided
    week_start_date = None
    if args.week_start:
        try:
            week_start_date = date.fromisoformat(args.week_start)
        except ValueError:
            print(f"Error: Invalid date format. Use YYYY-MM-DD")
            return 1

    print("Generating weekly audit report...")
    result = audit_service.generate_weekly_audit(week_start_date)

    if result.get("success"):
        print(f"✓ Audit report generated successfully")
        print(f"  Report ID: {result['report_id']}")
        print(f"  Week: {result['week_start_date']} to {result['week_end_date']}")
        print(f"  Path: {result['report_path']}")
        return 0
    else:
        print(f"✗ Failed to generate audit report: {result.get('error')}")
        return 1


def mcp_status_command(args):
    """Show MCP server status."""
    vault_path = Path(args.vault)

    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        return 1

    orchestrator = MCPServerOrchestrator(vault_path)
    status = orchestrator.get_all_server_status()

    print("\n=== MCP Server Status ===\n")

    for server_id, server_status in status.items():
        if not server_status:
            continue

        status_icon = "✓" if server_status["status"] == "running" else "✗"
        print(f"{status_icon} {server_id.upper()}")
        print(f"  Status: {server_status['status']}")
        print(f"  Domain: {server_status['domain']}")

        if server_status.get("process_id"):
            print(f"  PID: {server_status['process_id']}")

        print(f"  Error Count: {server_status['error_count']}")
        print(f"  Restart Count: {server_status['restart_count']}")

        if server_status.get("last_health_check"):
            print(f"  Last Health Check: {server_status['last_health_check']}")

        print(f"  Available Tools: {len(server_status['available_tools'])}")
        print()

    return 0


def approval_queue_command(args):
    """Show pending approvals."""
    vault_path = Path(args.vault)

    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        return 1

    approval_manager = ApprovalManager(vault_path)
    pending = approval_manager.get_pending_approvals()

    if not pending:
        print("No pending approvals")
        return 0

    print(f"\n=== Pending Approvals ({len(pending)}) ===\n")

    for item in pending:
        print(f"Post ID: {item['post_id']}")
        print(f"  Platforms: {', '.join(item['platforms'])}")
        print(f"  Content: {item['content_preview']}")
        print(f"  Requested: {item['requested_at']}")

        if item.get('cross_post_group_id'):
            print(f"  Cross-post Group: {item['cross_post_group_id']}")

        print()

    return 0


def approve_post_command(args):
    """Approve a social media post."""
    vault_path = Path(args.vault)

    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        return 1

    approval_manager = ApprovalManager(vault_path)
    result = approval_manager.approve_post(args.post_id, args.approved_by or "cli_user")

    if result.get("success"):
        print(f"✓ Post {args.post_id} approved")
        return 0
    else:
        print(f"✗ Failed to approve post: {result.get('error')}")
        return 1


def execute_workflow_command(args):
    """Execute autonomous workflow."""
    vault_path = Path(args.vault)

    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        return 1

    mcp_orchestrator = MCPServerOrchestrator(vault_path)
    ralph = RalphWiggumOrchestrator(vault_path, mcp_orchestrator)

    print(f"Executing workflow for task: {args.task_reference}")
    result = ralph.execute_workflow(args.task_reference)

    if result.get("success"):
        print(f"✓ Workflow executed successfully")
        print(f"  Execution ID: {result['execution_id']}")
        print(f"  Status: {result['status']}")
        print(f"  Steps Completed: {result['steps_completed']}/{result['total_steps']}")
        return 0
    else:
        print(f"✗ Workflow execution failed: {result.get('error')}")
        return 1


def workflow_status_command(args):
    """Show workflow execution status."""
    vault_path = Path(args.vault)

    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        return 1

    mcp_orchestrator = MCPServerOrchestrator(vault_path)
    ralph = RalphWiggumOrchestrator(vault_path, mcp_orchestrator)

    result = ralph.get_workflow_status(args.execution_id)

    if result.get("success"):
        print(f"\n=== Workflow Status ===\n")
        print(f"Execution ID: {result['execution_id']}")
        print(f"Status: {result['status']}")
        print(f"Progress: {result['progress']:.0f}%")
        print(f"Current Step: {result['current_step']}/{result['total_steps']}")
        print(f"Started: {result['started_at']}")
        if result.get('completed_at'):
            print(f"Completed: {result['completed_at']}")
        return 0
    else:
        print(f"✗ Failed to get workflow status: {result.get('error')}")
        return 1


def pause_workflow_command(args):
    """Pause workflow execution."""
    vault_path = Path(args.vault)

    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        return 1

    mcp_orchestrator = MCPServerOrchestrator(vault_path)
    ralph = RalphWiggumOrchestrator(vault_path, mcp_orchestrator)

    result = ralph.pause_workflow(args.execution_id)

    if result.get("success"):
        print(f"✓ Workflow {args.execution_id} paused")
        return 0
    else:
        print(f"✗ Failed to pause workflow: {result.get('error')}")
        return 1


def resume_workflow_command(args):
    """Resume workflow execution."""
    vault_path = Path(args.vault)

    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        return 1

    mcp_orchestrator = MCPServerOrchestrator(vault_path)
    ralph = RalphWiggumOrchestrator(vault_path, mcp_orchestrator)

    print(f"Resuming workflow: {args.execution_id}")
    result = ralph.resume_workflow(args.execution_id)

    if result.get("success"):
        print(f"✓ Workflow resumed")
        return 0
    else:
        print(f"✗ Failed to resume workflow: {result.get('error')}")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="AI Employee Gold Tier CLI")
    parser.add_argument("--vault", type=str, default="AI_Employee_Vault",
                       help="Path to AI Employee vault")

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Generate audit command
    audit_parser = subparsers.add_parser("generate-audit",
                                        help="Generate weekly audit report")
    audit_parser.add_argument("--week-start", type=str,
                             help="Week start date (YYYY-MM-DD), defaults to last Monday")
    audit_parser.set_defaults(func=generate_audit_command)

    # MCP status command
    mcp_parser = subparsers.add_parser("mcp-status",
                                       help="Show MCP server status")
    mcp_parser.set_defaults(func=mcp_status_command)

    # Approval queue command
    queue_parser = subparsers.add_parser("approval-queue",
                                        help="Show pending approvals")
    queue_parser.set_defaults(func=approval_queue_command)

    # Approve post command
    approve_parser = subparsers.add_parser("approve-post",
                                          help="Approve a social media post")
    approve_parser.add_argument("post_id", help="Post ID to approve")
    approve_parser.add_argument("--approved-by", type=str,
                               help="User who approved (default: cli_user)")
    approve_parser.set_defaults(func=approve_post_command)

    # Execute workflow command
    workflow_parser = subparsers.add_parser("execute-workflow",
                                           help="Execute autonomous workflow")
    workflow_parser.add_argument("task_reference", help="Path to task file")
    workflow_parser.set_defaults(func=execute_workflow_command)

    # Workflow status command
    status_parser = subparsers.add_parser("workflow-status",
                                         help="Show workflow execution status")
    status_parser.add_argument("execution_id", help="Workflow execution ID")
    status_parser.set_defaults(func=workflow_status_command)

    # Pause workflow command
    pause_parser = subparsers.add_parser("pause-workflow",
                                        help="Pause workflow execution")
    pause_parser.add_argument("execution_id", help="Workflow execution ID")
    pause_parser.set_defaults(func=pause_workflow_command)

    # Resume workflow command
    resume_parser = subparsers.add_parser("resume-workflow",
                                         help="Resume workflow execution")
    resume_parser.add_argument("execution_id", help="Workflow execution ID")
    resume_parser.set_defaults(func=resume_workflow_command)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
