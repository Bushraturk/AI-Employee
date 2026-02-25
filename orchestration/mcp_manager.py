"""MCP server lifecycle management."""

import os
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, Optional, List
import logging
import requests


logger = logging.getLogger(__name__)


class MCPServer:
    """Represents a single MCP server instance."""

    def __init__(
        self,
        name: str,
        command: str,
        args: List[str],
        env: Dict[str, str],
        port: int,
        auto_start: bool = True,
        restart_on_failure: bool = True,
        max_restarts: int = 3,
        restart_delay: int = 5000,
        local_only: bool = False,
    ):
        """Initialize MCP server configuration.

        Args:
            name: Server name
            command: Command to execute
            args: Command arguments
            env: Environment variables
            port: Server port
            auto_start: Whether to start automatically
            restart_on_failure: Whether to restart on failure
            max_restarts: Maximum restart attempts
            restart_delay: Delay between restarts (ms)
            local_only: Whether server should only run on local agent
        """
        self.name = name
        self.command = command
        self.args = args
        self.env = env
        self.port = port
        self.auto_start = auto_start
        self.restart_on_failure = restart_on_failure
        self.max_restarts = max_restarts
        self.restart_delay = restart_delay / 1000.0  # Convert to seconds
        self.local_only = local_only

        self.process: Optional[subprocess.Popen] = None
        self.restart_count = 0
        self.last_restart_time = 0.0

    def start(self) -> bool:
        """Start the MCP server.

        Returns:
            True if started successfully, False otherwise
        """
        if self.process and self.process.poll() is None:
            logger.warning(f"MCP server {self.name} is already running")
            return True

        try:
            logger.info(f"Starting MCP server: {self.name}")

            # Prepare environment
            env = os.environ.copy()
            env.update(self.env)

            # Start process
            self.process = subprocess.Popen(
                [self.command] + self.args,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Wait briefly and check if process started
            time.sleep(1)
            if self.process.poll() is not None:
                logger.error(f"MCP server {self.name} failed to start")
                return False

            logger.info(f"MCP server {self.name} started (PID={self.process.pid})")
            return True

        except Exception as e:
            logger.error(f"Failed to start MCP server {self.name}: {e}")
            return False

    def stop(self) -> bool:
        """Stop the MCP server.

        Returns:
            True if stopped successfully, False otherwise
        """
        if not self.process or self.process.poll() is not None:
            logger.warning(f"MCP server {self.name} is not running")
            return True

        try:
            logger.info(f"Stopping MCP server: {self.name}")

            # Terminate process
            self.process.terminate()

            # Wait for graceful shutdown
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning(f"MCP server {self.name} did not stop gracefully, killing")
                self.process.kill()
                self.process.wait()

            logger.info(f"MCP server {self.name} stopped")
            self.process = None
            return True

        except Exception as e:
            logger.error(f"Failed to stop MCP server {self.name}: {e}")
            return False

    def is_running(self) -> bool:
        """Check if server is running.

        Returns:
            True if running, False otherwise
        """
        return self.process is not None and self.process.poll() is None

    def is_healthy(self) -> bool:
        """Check if server is healthy (running and responding).

        Returns:
            True if healthy, False otherwise
        """
        if not self.is_running():
            return False

        try:
            # Try to connect to server port
            response = requests.get(f"http://localhost:{self.port}/health", timeout=2)
            return response.status_code == 200
        except Exception:
            return False

    def restart(self) -> bool:
        """Restart the MCP server.

        Returns:
            True if restarted successfully, False otherwise
        """
        # Check restart limits
        current_time = time.time()
        if current_time - self.last_restart_time < self.restart_delay:
            logger.warning(f"MCP server {self.name} restart delayed")
            return False

        if self.restart_count >= self.max_restarts:
            logger.error(f"MCP server {self.name} exceeded max restarts ({self.max_restarts})")
            return False

        logger.info(f"Restarting MCP server: {self.name}")

        # Stop and start
        self.stop()
        time.sleep(self.restart_delay)
        success = self.start()

        if success:
            self.restart_count += 1
            self.last_restart_time = current_time

        return success


class MCPManager:
    """Manages lifecycle of multiple MCP servers."""

    def __init__(self, config_path: Path, is_local_agent: bool = False):
        """Initialize MCP manager.

        Args:
            config_path: Path to MCP configuration file
            is_local_agent: Whether this is the local agent
        """
        self.config_path = config_path
        self.is_local_agent = is_local_agent
        self.servers: Dict[str, MCPServer] = {}

        # Load configuration
        self._load_config()

        logger.info(f"Initialized MCP manager with {len(self.servers)} servers")

    def _load_config(self) -> None:
        """Load MCP server configuration from file."""
        try:
            with open(self.config_path, "r") as f:
                config = json.load(f)

            for name, server_config in config.get("mcpServers", {}).items():
                # Skip local-only servers on cloud agent
                if server_config.get("localOnly", False) and not self.is_local_agent:
                    logger.info(f"Skipping local-only server {name} on cloud agent")
                    continue

                server = MCPServer(
                    name=name,
                    command=server_config["command"],
                    args=server_config.get("args", []),
                    env=server_config.get("env", {}),
                    port=server_config["port"],
                    auto_start=server_config.get("autoStart", True),
                    restart_on_failure=server_config.get("restartOnFailure", True),
                    max_restarts=server_config.get("maxRestarts", 3),
                    restart_delay=server_config.get("restartDelay", 5000),
                    local_only=server_config.get("localOnly", False),
                )

                self.servers[name] = server

        except Exception as e:
            logger.error(f"Failed to load MCP config: {e}")
            raise

    def start_all(self) -> Dict[str, bool]:
        """Start all MCP servers with auto_start enabled.

        Returns:
            Dictionary mapping server names to start success status
        """
        results = {}

        for name, server in self.servers.items():
            if server.auto_start:
                results[name] = server.start()
            else:
                logger.info(f"Skipping auto-start for {name}")
                results[name] = None

        return results

    def stop_all(self) -> Dict[str, bool]:
        """Stop all running MCP servers.

        Returns:
            Dictionary mapping server names to stop success status
        """
        results = {}

        for name, server in self.servers.items():
            results[name] = server.stop()

        return results

    def start_server(self, name: str) -> bool:
        """Start a specific MCP server.

        Args:
            name: Server name

        Returns:
            True if started successfully, False otherwise
        """
        if name not in self.servers:
            logger.error(f"Unknown MCP server: {name}")
            return False

        return self.servers[name].start()

    def stop_server(self, name: str) -> bool:
        """Stop a specific MCP server.

        Args:
            name: Server name

        Returns:
            True if stopped successfully, False otherwise
        """
        if name not in self.servers:
            logger.error(f"Unknown MCP server: {name}")
            return False

        return self.servers[name].stop()

    def restart_server(self, name: str) -> bool:
        """Restart a specific MCP server.

        Args:
            name: Server name

        Returns:
            True if restarted successfully, False otherwise
        """
        if name not in self.servers:
            logger.error(f"Unknown MCP server: {name}")
            return False

        return self.servers[name].restart()

    def health_check(self) -> Dict[str, bool]:
        """Check health of all MCP servers.

        Returns:
            Dictionary mapping server names to health status
        """
        results = {}

        for name, server in self.servers.items():
            results[name] = server.is_healthy()

        return results

    def monitor_and_restart(self) -> Dict[str, str]:
        """Monitor servers and restart failed ones.

        Returns:
            Dictionary mapping server names to status messages
        """
        results = {}

        for name, server in self.servers.items():
            if not server.is_running():
                if server.restart_on_failure:
                    logger.warning(f"MCP server {name} is down, attempting restart")
                    success = server.restart()
                    results[name] = "restarted" if success else "restart_failed"
                else:
                    results[name] = "down"
            elif not server.is_healthy():
                logger.warning(f"MCP server {name} is unhealthy")
                results[name] = "unhealthy"
            else:
                results[name] = "healthy"

        return results

    def get_status(self) -> Dict[str, Dict[str, any]]:
        """Get status of all MCP servers.

        Returns:
            Dictionary with server status information
        """
        status = {}

        for name, server in self.servers.items():
            status[name] = {
                "running": server.is_running(),
                "healthy": server.is_healthy(),
                "restart_count": server.restart_count,
                "port": server.port,
                "local_only": server.local_only,
            }

        return status
