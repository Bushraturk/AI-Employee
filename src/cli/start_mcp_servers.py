"""MCP Server Startup Script for Gold Tier.

Launches all MCP servers with proper configuration.
"""

import sys
import logging
from pathlib import Path
from typing import List

from src.orchestrator.mcp_server_orchestrator import MCPServerOrchestrator
from src.models.mcp_server import ServerDomain, RateLimits

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def start_all_mcp_servers(vault_path: Path) -> bool:
    """Start all MCP servers.

    Args:
        vault_path: Path to AI Employee vault

    Returns:
        True if all servers started successfully
    """
    orchestrator = MCPServerOrchestrator(vault_path)

    # Register servers
    servers = [
        {
            "server_id": "accounting",
            "domain": ServerDomain.ACCOUNTING,
            "tools": [
                "sync_odoo_transaction",
                "create_odoo_invoice",
                "create_odoo_expense",
                "create_odoo_customer"
            ],
            "rate_limits": RateLimits(
                calls_per_minute=60,
                calls_per_hour=1000,
                concurrent_requests=5
            )
        },
        {
            "server_id": "social",
            "domain": ServerDomain.SOCIAL,
            "tools": [
                "post_facebook",
                "post_instagram",
                "post_twitter",
                "post_linkedin",
                "collect_social_metrics"
            ],
            "rate_limits": RateLimits(
                calls_per_minute=50,
                calls_per_hour=500,
                concurrent_requests=3
            )
        },
        {
            "server_id": "communications",
            "domain": ServerDomain.COMMUNICATIONS,
            "tools": [
                "send_email",
                "send_whatsapp",
                "check_gmail",
                "check_whatsapp"
            ],
            "rate_limits": RateLimits(
                calls_per_minute=30,
                calls_per_hour=300,
                concurrent_requests=2
            )
        }
    ]

    # Register all servers
    for server_config in servers:
        success = orchestrator.register_server(
            server_id=server_config["server_id"],
            domain=server_config["domain"],
            available_tools=server_config["tools"],
            rate_limits=server_config["rate_limits"]
        )

        if not success:
            logger.error(f"Failed to register server: {server_config['server_id']}")
            return False

    # Start all servers
    all_started = True
    for server_config in servers:
        server_id = server_config["server_id"]
        logger.info(f"Starting {server_id} MCP server...")

        success = orchestrator.start_server(server_id)

        if success:
            logger.info(f"✓ {server_id} server started")
        else:
            logger.error(f"✗ {server_id} server failed to start")
            all_started = False

    return all_started


def stop_all_mcp_servers(vault_path: Path) -> None:
    """Stop all MCP servers.

    Args:
        vault_path: Path to AI Employee vault
    """
    orchestrator = MCPServerOrchestrator(vault_path)
    orchestrator.shutdown_all()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="MCP Server Startup Script")
    parser.add_argument("--vault", type=str, default="AI_Employee_Vault",
                       help="Path to AI Employee vault")
    parser.add_argument("--stop", action="store_true",
                       help="Stop all servers instead of starting")

    args = parser.parse_args()

    vault_path = Path(args.vault)

    if not vault_path.exists():
        logger.error(f"Vault path does not exist: {vault_path}")
        return 1

    if args.stop:
        logger.info("Stopping all MCP servers...")
        stop_all_mcp_servers(vault_path)
        logger.info("All servers stopped")
        return 0

    logger.info("Starting all MCP servers...")
    success = start_all_mcp_servers(vault_path)

    if success:
        logger.info("✓ All MCP servers started successfully")
        logger.info("Servers are running. Press Ctrl+C to stop.")

        try:
            # Keep script running
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\nShutting down...")
            stop_all_mcp_servers(vault_path)
            logger.info("All servers stopped")

        return 0
    else:
        logger.error("✗ Some servers failed to start")
        return 1


if __name__ == "__main__":
    sys.exit(main())
