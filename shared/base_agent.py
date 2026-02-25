"""Base agent framework for cloud and local agents."""

import os
import time
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import logging

from shared.models.agent_state import AgentState, AgentStatus, AgentType
from shared.models.vault_config import VaultConfig
from shared.utils.vault_manager import VaultManager
from shared.utils.logger import VaultLogger, LogCategory


logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for cloud and local agents.

    Provides common functionality for agent lifecycle, state management,
    heartbeat, and error handling.
    """

    def __init__(
        self,
        agent_id: str,
        agent_type: AgentType,
        agent_name: str,
        vault_config: VaultConfig,
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize base agent.

        Args:
            agent_id: Unique agent identifier
            agent_type: Type of agent (cloud or local)
            agent_name: Human-readable agent name
            vault_config: Vault configuration
            config: Agent-specific configuration
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.agent_name = agent_name
        self.vault_config = vault_config
        self.config = config or {}

        # Initialize vault manager and logger
        self.vault_manager = VaultManager(vault_config)
        self.vault_logger = VaultLogger(vault_config.vault_root, agent_id)

        # Agent state
        self.state = AgentState(
            agent_id=agent_id,
            agent_type=agent_type,
            agent_name=agent_name,
            status=AgentStatus.STARTING,
            last_heartbeat=datetime.now(),
            started_at=datetime.now(),
            config=self.config,
        )

        # Runtime state
        self._running = False
        self._start_time = time.time()

        # Development mode
        self.dev_mode = os.getenv("DEVELOPMENT_MODE", "false").lower() == "true"
        self.dry_run = os.getenv("DRY_RUN_MODE", "false").lower() == "true"

        logger.info(f"Initialized {agent_type.value} agent: {agent_name} (dev_mode={self.dev_mode}, dry_run={self.dry_run})")

    @abstractmethod
    def setup(self) -> None:
        """Setup agent-specific resources.

        Called once during agent startup.
        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def process_cycle(self) -> None:
        """Execute one processing cycle.

        Called repeatedly while agent is running.
        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup agent-specific resources.

        Called once during agent shutdown.
        Must be implemented by subclasses.
        """
        pass

    def start(self) -> None:
        """Start the agent."""
        try:
            self.vault_logger.info(
                LogCategory.AGENT,
                f"Starting {self.agent_name}",
                details={"agent_id": self.agent_id, "agent_type": self.agent_type.value}
            )

            # Setup
            self.setup()

            # Update state
            self.state.status = AgentStatus.RUNNING
            self._running = True
            self._save_state()

            self.vault_logger.info(
                LogCategory.AGENT,
                f"{self.agent_name} started successfully"
            )

            # Main loop
            while self._running:
                try:
                    # Update heartbeat
                    self._heartbeat()

                    # Process one cycle
                    self.state.status = AgentStatus.BUSY
                    self._save_state()

                    self.process_cycle()

                    self.state.status = AgentStatus.IDLE
                    self._save_state()

                    # Sleep briefly
                    time.sleep(1)

                except KeyboardInterrupt:
                    logger.info("Received shutdown signal")
                    break

                except Exception as e:
                    self._handle_error(e)

        except Exception as e:
            self.vault_logger.error(
                LogCategory.AGENT,
                f"Fatal error in {self.agent_name}",
                error_type=type(e).__name__,
                stack_trace=str(e),
            )
            raise

        finally:
            self.stop()

    def stop(self) -> None:
        """Stop the agent."""
        if not self._running:
            return

        self.vault_logger.info(
            LogCategory.AGENT,
            f"Stopping {self.agent_name}"
        )

        self._running = False

        # Cleanup
        try:
            self.cleanup()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

        # Update state
        self.state.status = AgentStatus.STOPPED
        self._save_state()

        self.vault_logger.info(
            LogCategory.AGENT,
            f"{self.agent_name} stopped"
        )

    def _heartbeat(self) -> None:
        """Update heartbeat timestamp."""
        self.state.last_heartbeat = datetime.now()
        self.state.uptime_seconds = int(time.time() - self._start_time)

    def _save_state(self) -> None:
        """Save agent state to vault."""
        try:
            state_folder = f"In_Progress/{self.agent_type.value}"
            state_path = self.vault_manager.get_folder_path(state_folder) / "agent_state.md"
            self.state.to_file(str(state_path))
        except Exception as e:
            logger.error(f"Failed to save agent state: {e}")

    def _handle_error(self, error: Exception) -> None:
        """Handle error during processing.

        Args:
            error: Exception that occurred
        """
        self.state.error_count += 1
        self.state.last_error = str(error)
        self.state.last_error_at = datetime.now()
        self.state.status = AgentStatus.ERROR

        self.vault_logger.error(
            LogCategory.AGENT,
            f"Error in {self.agent_name}: {error}",
            error_type=type(error).__name__,
            stack_trace=str(error),
        )

        self._save_state()

        # Sleep before retrying
        time.sleep(5)

        # Reset status
        self.state.status = AgentStatus.RUNNING

    def is_running(self) -> bool:
        """Check if agent is running.

        Returns:
            True if running, False otherwise
        """
        return self._running

    def get_state_path(self) -> Path:
        """Get path to agent state file.

        Returns:
            Path to agent_state.md
        """
        state_folder = f"In_Progress/{self.agent_type.value}"
        return self.vault_manager.get_folder_path(state_folder) / "agent_state.md"
