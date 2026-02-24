"""MCP Server Orchestrator for Gold Tier.

Manages lifecycle of multiple independent MCP servers with health monitoring,
automatic restart, and action routing.
"""

import subprocess
import time
import json
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
import logging

from src.models.mcp_server import MCPServer, ServerDomain, ServerStatus, RateLimits

logger = logging.getLogger(__name__)


class MCPServerOrchestrator:
    """Orchestrates multiple independent MCP server processes.

    Responsibilities:
    - Start/stop/restart MCP servers as independent processes
    - Route actions to appropriate server based on action type
    - Monitor server health with automatic restart on failure
    - Persist server state to vault
    """

    def __init__(self, vault_path: Path, config_path: Optional[Path] = None):
        """Initialize orchestrator.

        Args:
            vault_path: Path to AI Employee vault
            config_path: Path to MCP server configuration file
        """
        self.vault_path = vault_path
        self.config_path = config_path or Path("config/mcp_servers.yaml")
        self.servers: Dict[str, MCPServer] = {}
        self.processes: Dict[str, subprocess.Popen] = {}

        # Action type to server domain mapping
        self.action_routing = {
            # Accounting actions
            "sync_odoo_transaction": ServerDomain.ACCOUNTING,
            "create_odoo_invoice": ServerDomain.ACCOUNTING,
            "create_odoo_expense": ServerDomain.ACCOUNTING,
            "create_odoo_customer": ServerDomain.ACCOUNTING,

            # Social media actions
            "post_facebook": ServerDomain.SOCIAL,
            "post_instagram": ServerDomain.SOCIAL,
            "post_twitter": ServerDomain.SOCIAL,
            "post_linkedin": ServerDomain.SOCIAL,
            "collect_social_metrics": ServerDomain.SOCIAL,

            # Communications actions
            "send_email": ServerDomain.COMMUNICATIONS,
            "send_whatsapp": ServerDomain.COMMUNICATIONS,
            "check_gmail": ServerDomain.COMMUNICATIONS,
            "check_whatsapp": ServerDomain.COMMUNICATIONS,
        }

        self._load_existing_servers()

    def _load_existing_servers(self) -> None:
        """Load existing server state from vault."""
        server_dir = self.vault_path / "System" / "mcp_servers"
        if not server_dir.exists():
            return

        for server_file in server_dir.glob("*.md"):
            try:
                server = MCPServer.load(self.vault_path, server_file.stem)
                self.servers[server.server_id] = server
                logger.info(f"Loaded server state: {server.server_id} ({server.status.value})")
            except Exception as e:
                logger.error(f"Failed to load server {server_file.stem}: {e}")

    def start_server(self, server_id: str) -> bool:
        """Start an MCP server as independent process.

        Args:
            server_id: Server identifier (accounting, social, communications)

        Returns:
            True if server started successfully
        """
        if server_id not in self.servers:
            logger.error(f"Server {server_id} not registered")
            return False

        server = self.servers[server_id]

        # Check if already running
        if server.status == ServerStatus.RUNNING:
            logger.warning(f"Server {server_id} is already running")
            return True

        try:
            # Construct server script path
            script_path = Path("src") / "mcp_servers" / f"{server_id}_mcp" / "server.py"

            if not script_path.exists():
                logger.error(f"Server script not found: {script_path}")
                return False

            # Start server process
            process = subprocess.Popen(
                ["python", str(script_path), "--vault", str(self.vault_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1
            )

            # Wait briefly to ensure process started
            time.sleep(0.5)

            if process.poll() is not None:
                # Process already terminated
                stderr = process.stderr.read() if process.stderr else ""
                logger.error(f"Server {server_id} failed to start: {stderr}")
                return False

            # Update server state
            server.start(process.pid)
            server.save(self.vault_path)

            # Store process reference
            self.processes[server_id] = process

            logger.info(f"Started server {server_id} (PID: {process.pid})")
            return True

        except Exception as e:
            logger.error(f"Failed to start server {server_id}: {e}")
            server.mark_error()
            server.save(self.vault_path)
            return False

    def stop_server(self, server_id: str, timeout: int = 10) -> bool:
        """Stop an MCP server gracefully.

        Args:
            server_id: Server identifier
            timeout: Seconds to wait for graceful shutdown

        Returns:
            True if server stopped successfully
        """
        if server_id not in self.servers:
            logger.error(f"Server {server_id} not registered")
            return False

        server = self.servers[server_id]

        if server.status == ServerStatus.STOPPED:
            logger.info(f"Server {server_id} is already stopped")
            return True

        try:
            process = self.processes.get(server_id)

            if process:
                # Try graceful shutdown
                process.terminate()

                try:
                    process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    # Force kill if graceful shutdown failed
                    logger.warning(f"Server {server_id} did not stop gracefully, forcing kill")
                    process.kill()
                    process.wait()

                # Remove process reference
                del self.processes[server_id]

            # Update server state
            server.stop()
            server.save(self.vault_path)

            logger.info(f"Stopped server {server_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to stop server {server_id}: {e}")
            return False

    def restart_server(self, server_id: str) -> bool:
        """Restart an MCP server.

        Args:
            server_id: Server identifier

        Returns:
            True if server restarted successfully
        """
        if server_id not in self.servers:
            logger.error(f"Server {server_id} not registered")
            return False

        server = self.servers[server_id]

        # Check restart limit
        if server.restart_count >= 3:
            logger.error(f"Server {server_id} has reached max restart limit (3)")
            server.mark_crashed()
            server.save(self.vault_path)
            return False

        logger.info(f"Restarting server {server_id} (attempt {server.restart_count + 1}/3)")

        # Stop if running
        if server.status == ServerStatus.RUNNING:
            self.stop_server(server_id)

        # Start again
        success = self.start_server(server_id)

        if success:
            server.restart_count += 1
            server.save(self.vault_path)

        return success

    def health_check(self, server_id: str) -> bool:
        """Check health of an MCP server.

        Args:
            server_id: Server identifier

        Returns:
            True if server is healthy
        """
        if server_id not in self.servers:
            logger.error(f"Server {server_id} not registered")
            return False

        server = self.servers[server_id]

        try:
            # Check if process is alive
            process = self.processes.get(server_id)

            if not process:
                logger.warning(f"Server {server_id} has no process reference")
                if server.status == ServerStatus.RUNNING:
                    server.mark_crashed()
                    server.save(self.vault_path)
                return False

            # Check if process is still running
            if process.poll() is not None:
                logger.error(f"Server {server_id} process has terminated")
                server.mark_crashed()
                server.save(self.vault_path)

                # Attempt automatic restart
                return self.restart_server(server_id)

            # Update health check timestamp
            server.update_health_check()
            server.save(self.vault_path)

            return True

        except Exception as e:
            logger.error(f"Health check failed for server {server_id}: {e}")
            server.mark_error()
            server.save(self.vault_path)
            return False

    def health_check_all(self) -> Dict[str, bool]:
        """Check health of all servers.

        Returns:
            Dictionary mapping server_id to health status
        """
        results = {}
        for server_id in self.servers:
            results[server_id] = self.health_check(server_id)
        return results

    def route_action(self, action_type: str) -> Optional[str]:
        """Route action to appropriate MCP server.

        Args:
            action_type: Type of action to execute

        Returns:
            Server ID that should handle this action, or None if no route found
        """
        domain = self.action_routing.get(action_type)

        if not domain:
            logger.warning(f"No routing found for action type: {action_type}")
            return None

        # Find server for this domain
        for server_id, server in self.servers.items():
            if server.domain == domain and server.status == ServerStatus.RUNNING:
                return server_id

        logger.error(f"No running server found for domain: {domain.value}")
        return None

    def register_server(self, server_id: str, domain: ServerDomain,
                       available_tools: List[str], rate_limits: Optional[RateLimits] = None) -> bool:
        """Register a new MCP server.

        Args:
            server_id: Server identifier
            domain: Server domain
            available_tools: List of tool names this server provides
            rate_limits: Rate limit configuration

        Returns:
            True if server registered successfully
        """
        try:
            server = MCPServer.create(server_id, domain, available_tools, rate_limits)
            server.save(self.vault_path)
            self.servers[server_id] = server

            logger.info(f"Registered server {server_id} for domain {domain.value}")
            return True

        except Exception as e:
            logger.error(f"Failed to register server {server_id}: {e}")
            return False

    def get_server_status(self, server_id: str) -> Optional[Dict]:
        """Get status information for a server.

        Args:
            server_id: Server identifier

        Returns:
            Dictionary with server status information
        """
        if server_id not in self.servers:
            return None

        server = self.servers[server_id]

        return {
            "server_id": server.server_id,
            "domain": server.domain.value,
            "status": server.status.value,
            "process_id": server.process_id,
            "error_count": server.error_count,
            "restart_count": server.restart_count,
            "last_health_check": server.last_health_check.isoformat() if server.last_health_check else None,
            "available_tools": server.available_tools,
            "rate_limits": {
                "calls_per_minute": server.rate_limits.calls_per_minute,
                "calls_per_hour": server.rate_limits.calls_per_hour,
                "concurrent_requests": server.rate_limits.concurrent_requests
            }
        }

    def get_all_server_status(self) -> Dict[str, Dict]:
        """Get status information for all servers.

        Returns:
            Dictionary mapping server_id to status information
        """
        return {
            server_id: self.get_server_status(server_id)
            for server_id in self.servers
        }

    def shutdown_all(self) -> None:
        """Shutdown all MCP servers gracefully."""
        logger.info("Shutting down all MCP servers")

        for server_id in list(self.servers.keys()):
            self.stop_server(server_id)

        logger.info("All MCP servers stopped")
