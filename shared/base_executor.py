"""Base executor framework for executing approved actions."""

import os
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import logging

from shared.models.approval_request import ApprovalRequest
from shared.utils.vault_manager import VaultManager
from shared.utils.logger import VaultLogger, LogCategory


logger = logging.getLogger(__name__)


class BaseExecutor(ABC):
    """Base class for executors that perform approved actions.

    Provides common functionality for action execution, error handling,
    and development mode checks.
    """

    def __init__(
        self,
        executor_name: str,
        agent_id: str,
        vault_manager: VaultManager,
        vault_logger: VaultLogger,
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize base executor.

        Args:
            executor_name: Human-readable executor name
            agent_id: Agent that owns this executor
            vault_manager: Vault manager instance
            vault_logger: Vault logger instance
            config: Executor-specific configuration
        """
        self.executor_name = executor_name
        self.agent_id = agent_id
        self.vault_manager = vault_manager
        self.vault_logger = vault_logger
        self.config = config or {}

        # Development mode flags
        self.dev_mode = os.getenv("DEVELOPMENT_MODE", "false").lower() == "true"
        self.dry_run = os.getenv("DRY_RUN_MODE", "false").lower() == "true"

        logger.info(f"Initialized executor: {executor_name} (dev_mode={self.dev_mode}, dry_run={self.dry_run})")

    @abstractmethod
    def execute(self, approval: ApprovalRequest) -> Dict[str, Any]:
        """Execute an approved action.

        Must be implemented by subclasses.

        Args:
            approval: Approval request to execute

        Returns:
            Dictionary with execution results
        """
        pass

    def execute_with_checks(self, approval: ApprovalRequest) -> Dict[str, Any]:
        """Execute an approved action with development mode checks.

        Args:
            approval: Approval request to execute

        Returns:
            Dictionary with execution results
        """
        # Development mode check
        if self.dev_mode:
            self.vault_logger.warning(
                LogCategory.EXECUTOR,
                f"[DEV MODE] Skipping execution: {approval.title}",
                approval_id=approval.approval_id,
            )
            return {
                "success": True,
                "skipped": True,
                "reason": "Development mode enabled",
            }

        # Dry-run mode check
        if self.dry_run:
            self.vault_logger.info(
                LogCategory.EXECUTOR,
                f"[DRY RUN] Would execute: {approval.title}",
                approval_id=approval.approval_id,
                details={"approval_type": approval.approval_type.value},
            )
            return {
                "success": True,
                "dry_run": True,
                "message": f"Dry-run: {approval.title}",
            }

        # Execute
        try:
            self.vault_logger.info(
                LogCategory.EXECUTOR,
                f"Executing: {approval.title}",
                approval_id=approval.approval_id,
            )

            result = self.execute(approval)

            self.vault_logger.info(
                LogCategory.EXECUTOR,
                f"Execution completed: {approval.title}",
                approval_id=approval.approval_id,
                details=result,
            )

            return result

        except Exception as e:
            self.vault_logger.error(
                LogCategory.EXECUTOR,
                f"Execution failed: {approval.title}",
                approval_id=approval.approval_id,
                error_type=type(e).__name__,
                stack_trace=str(e),
            )

            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
            }

    def validate_approval(self, approval: ApprovalRequest) -> bool:
        """Validate approval request before execution.

        Args:
            approval: Approval request to validate

        Returns:
            True if valid, False otherwise
        """
        # Check if expired
        if approval.is_expired():
            self.vault_logger.warning(
                LogCategory.EXECUTOR,
                f"Approval expired: {approval.title}",
                approval_id=approval.approval_id,
            )
            return False

        # Check if already approved
        if approval.status.value != "approved":
            self.vault_logger.warning(
                LogCategory.EXECUTOR,
                f"Approval not in approved status: {approval.title}",
                approval_id=approval.approval_id,
                details={"status": approval.status.value},
            )
            return False

        return True
