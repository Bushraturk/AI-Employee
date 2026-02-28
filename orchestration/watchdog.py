"""Watchdog for monitoring and restarting failed processes.

Implements health monitoring with exponential backoff for process restarts.
"""

import os
import time
import logging
import subprocess
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field


logger = logging.getLogger(__name__)


@dataclass
class ProcessConfig:
    """Configuration for a monitored process."""

    name: str
    command: str
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    working_dir: Optional[str] = None
    auto_start: bool = True
    restart_on_failure: bool = True
    max_restarts: int = 5
    restart_window_seconds: int = 300  # 5 minutes
    health_check_interval: int = 30  # seconds
    startup_grace_period: int = 10  # seconds


@dataclass
class ProcessState:
    """Runtime state of a monitored process."""

    process: Optional[subprocess.Popen] = None
    restart_count: int = 0
    restart_times: List[datetime] = field(default_factory=list)
    last_health_check: Optional[datetime] = None
    last_restart_time: Optional[datetime] = None
    consecutive_failures: int = 0
    is_healthy: bool = False
    start_time: Optional[datetime] = None


class Watchdog:
    """Monitors and restarts failed processes with exponential backoff.

    Features:
    - Health monitoring with configurable intervals
    - Automatic restart on failure
    - Exponential backoff for repeated failures
    - Restart rate limiting (max restarts per time window)
    - Graceful shutdown handling
    """

    def __init__(self, config_file: Optional[Path] = None):
        """Initialize watchdog.

        Args:
            config_file: Optional path to process configuration file
        """
        self.processes: Dict[str, ProcessConfig] = {}
        self.states: Dict[str, ProcessState] = {}
        self._running = False
        self._stop_requested = False

        if config_file:
            self._load_config(config_file)

        logger.info(f"Initialized watchdog with {len(self.processes)} processes")

    def add_process(self, config: ProcessConfig) -> None:
        """Add a process to monitor.

        Args:
            config: Process configuration
        """
        self.processes[config.name] = config
        self.states[config.name] = ProcessState()
        logger.info(f"Added process to watchdog: {config.name}")

    def start(self) -> None:
        """Start the watchdog."""
        if self._running:
            logger.warning("Watchdog is already running")
            return

        logger.info("Starting watchdog...")

        # Start all auto-start processes
        for name, config in self.processes.items():
            if config.auto_start:
                self._start_process(name)

        self._running = True
        self._stop_requested = False

        logger.info("Watchdog started")

    def stop(self) -> None:
        """Stop the watchdog and all monitored processes."""
        if not self._running:
            logger.warning("Watchdog is not running")
            return

        logger.info("Stopping watchdog...")

        self._stop_requested = True

        # Stop all processes
        for name in self.processes.keys():
            self._stop_process(name)

        self._running = False

        logger.info("Watchdog stopped")

    def run(self) -> None:
        """Run the watchdog main loop.

        This is a blocking call that runs until stop() is called.
        """
        if not self._running:
            self.start()

        logger.info("Entering watchdog main loop...")

        try:
            while not self._stop_requested:
                # Check health of all processes
                for name in self.processes.keys():
                    self._check_process_health(name)

                # Sleep briefly
                time.sleep(5)

        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Error in watchdog main loop: {e}")
            raise
        finally:
            self.stop()

    def _start_process(self, name: str) -> bool:
        """Start a monitored process.

        Args:
            name: Process name

        Returns:
            True if started successfully, False otherwise
        """
        if name not in self.processes:
            logger.error(f"Unknown process: {name}")
            return False

        config = self.processes[name]
        state = self.states[name]

        # Check if already running
        if state.process and state.process.poll() is None:
            logger.warning(f"Process {name} is already running")
            return True

        try:
            logger.info(f"Starting process: {name}")

            # Prepare environment
            env = os.environ.copy()
            env.update(config.env)

            # Start process
            state.process = subprocess.Popen(
                [config.command] + config.args,
                env=env,
                cwd=config.working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            state.start_time = datetime.now()
            state.is_healthy = False  # Will be checked after grace period

            # Wait for startup grace period
            time.sleep(min(config.startup_grace_period, 2))

            # Check if process started
            if state.process.poll() is not None:
                logger.error(f"Process {name} failed to start")
                state.consecutive_failures += 1
                return False

            logger.info(f"Process {name} started (PID={state.process.pid})")
            return True

        except Exception as e:
            logger.error(f"Failed to start process {name}: {e}")
            state.consecutive_failures += 1
            return False

    def _stop_process(self, name: str) -> bool:
        """Stop a monitored process.

        Args:
            name: Process name

        Returns:
            True if stopped successfully, False otherwise
        """
        if name not in self.processes:
            logger.error(f"Unknown process: {name}")
            return False

        state = self.states[name]

        if not state.process or state.process.poll() is not None:
            logger.warning(f"Process {name} is not running")
            return True

        try:
            logger.info(f"Stopping process: {name}")

            # Terminate process
            state.process.terminate()

            # Wait for graceful shutdown
            try:
                state.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.warning(f"Process {name} did not stop gracefully, killing")
                state.process.kill()
                state.process.wait()

            logger.info(f"Process {name} stopped")
            state.process = None
            state.is_healthy = False

            return True

        except Exception as e:
            logger.error(f"Failed to stop process {name}: {e}")
            return False

    def _check_process_health(self, name: str) -> None:
        """Check health of a process and restart if needed.

        Args:
            name: Process name
        """
        if name not in self.processes:
            return

        config = self.processes[name]
        state = self.states[name]

        # Skip if health check interval not elapsed
        now = datetime.now()
        if state.last_health_check:
            elapsed = (now - state.last_health_check).total_seconds()
            if elapsed < config.health_check_interval:
                return

        state.last_health_check = now

        # Check if process is running
        if not state.process or state.process.poll() is not None:
            logger.warning(f"Process {name} is not running")
            state.is_healthy = False

            # Attempt restart if enabled
            if config.restart_on_failure:
                self._restart_process(name)
            return

        # Check if still in startup grace period
        if state.start_time:
            elapsed = (now - state.start_time).total_seconds()
            if elapsed < config.startup_grace_period:
                logger.debug(f"Process {name} in startup grace period")
                return

        # Process is running
        state.is_healthy = True
        state.consecutive_failures = 0

    def _restart_process(self, name: str) -> bool:
        """Restart a failed process with exponential backoff.

        Args:
            name: Process name

        Returns:
            True if restarted successfully, False otherwise
        """
        if name not in self.processes:
            return False

        config = self.processes[name]
        state = self.states[name]

        now = datetime.now()

        # Check restart rate limiting
        window_start = now - timedelta(seconds=config.restart_window_seconds)
        recent_restarts = [
            t for t in state.restart_times
            if t > window_start
        ]

        if len(recent_restarts) >= config.max_restarts:
            logger.error(
                f"Process {name} exceeded max restarts "
                f"({config.max_restarts} in {config.restart_window_seconds}s)"
            )
            return False

        # Calculate exponential backoff delay
        backoff_delay = min(2 ** state.consecutive_failures, 60)  # Max 60 seconds

        # Check if enough time has passed since last restart
        if state.last_restart_time:
            elapsed = (now - state.last_restart_time).total_seconds()
            if elapsed < backoff_delay:
                logger.debug(
                    f"Process {name} restart delayed "
                    f"(backoff={backoff_delay}s, elapsed={elapsed:.1f}s)"
                )
                return False

        logger.info(
            f"Restarting process {name} "
            f"(attempt {len(recent_restarts) + 1}/{config.max_restarts})"
        )

        # Stop process if still running
        self._stop_process(name)

        # Wait for backoff delay
        if backoff_delay > 0:
            time.sleep(backoff_delay)

        # Start process
        success = self._start_process(name)

        if success:
            state.restart_count += 1
            state.restart_times.append(now)
            state.last_restart_time = now
            logger.info(f"Process {name} restarted successfully")
        else:
            logger.error(f"Failed to restart process {name}")

        return success

    def _load_config(self, config_file: Path) -> None:
        """Load process configuration from YAML file.

        Args:
            config_file: Path to configuration file
        """
        try:
            import yaml

            with open(config_file, "r") as f:
                config_data = yaml.safe_load(f)

            for name, proc_config in config_data.get("processes", {}).items():
                config = ProcessConfig(
                    name=name,
                    command=proc_config["command"],
                    args=proc_config.get("args", []),
                    env=proc_config.get("env", {}),
                    working_dir=proc_config.get("working_dir"),
                    auto_start=proc_config.get("auto_start", True),
                    restart_on_failure=proc_config.get("restart_on_failure", True),
                    max_restarts=proc_config.get("max_restarts", 5),
                    restart_window_seconds=proc_config.get("restart_window_seconds", 300),
                    health_check_interval=proc_config.get("health_check_interval", 30),
                    startup_grace_period=proc_config.get("startup_grace_period", 10),
                )

                self.add_process(config)

            logger.info(f"Loaded {len(self.processes)} processes from config")

        except Exception as e:
            logger.error(f"Failed to load config from {config_file}: {e}")
            raise

    def get_status(self) -> Dict[str, Dict[str, any]]:
        """Get status of all monitored processes.

        Returns:
            Dictionary with process status information
        """
        status = {}

        for name in self.processes.keys():
            state = self.states[name]
            status[name] = {
                "running": state.process is not None and state.process.poll() is None,
                "healthy": state.is_healthy,
                "restart_count": state.restart_count,
                "consecutive_failures": state.consecutive_failures,
                "pid": state.process.pid if state.process else None,
            }

        return status

    def is_running(self) -> bool:
        """Check if watchdog is running.

        Returns:
            True if running, False otherwise
        """
        return self._running
