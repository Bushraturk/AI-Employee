"""Approval handler for local agent.

Coordinates execution of approved actions across multiple executors.
"""

import logging
from typing import List, Optional, Any

from shared.models.approval_request import ApprovalRequest
from shared.utils.vault_manager import VaultManager
from shared.utils.logger import VaultLogger, LogCategory


logger = logging.getLogger(__name__)


class ApprovalHandler:
    """Handles execution of approved actions.

    Routes approval requests to appropriate executors.
    """

    def __init__(
        self,
        agent_id: str,
        vault_manager: VaultManager,
        vault_logger: VaultLogger,
        executors: List[Any],
    ):
        """Initialize approval handler.

        Args:
            agent_id: Agent ID
            vault_manager: Vault manager instance
            vault_logger: Vault logger instance
            executors: List of executor instances
        """
        self.agent_id = agent_id
        self.vault_manager = vault_manager
        self.vault_logger = vault_logger
        self.executors = executors

        logger.info(f"Approval handler initialized with {len(executors)} executors")

    def execute_approval(self, approval: ApprovalRequest) -> bool:
        """Execute an approved action.

        Args:
            approval: Approved action request

        Returns:
            True if successful, False otherwise
        """
        try:
            self.vault_logger.info(
                LogCategory.AGENT,
                f"Executing approval: {approval.approval_id}",
                details={
                    "approval_id": approval.approval_id,
                    "approval_type": approval.approval_type.value,
                    "target": approval.target_id,
                }
            )

            # Find executor for this approval type
            executor = self._find_executor(approval)

            if not executor:
                self.vault_logger.error(
                    LogCategory.AGENT,
                    f"No executor found for approval type: {approval.approval_type.value}",
                    details={"approval_id": approval.approval_id}
                )
                return False

            # Execute
            success = executor.execute(approval)

            if success:
                self.vault_logger.info(
                    LogCategory.AGENT,
                    f"Approval executed successfully: {approval.approval_id}",
                    details={"approval_id": approval.approval_id}
                )
            else:
                self.vault_logger.error(
                    LogCategory.AGENT,
                    f"Approval execution failed: {approval.approval_id}",
                    details={"approval_id": approval.approval_id}
                )

            return success

        except Exception as e:
            self.vault_logger.error(
                LogCategory.AGENT,
                f"Error executing approval: {e}",
                error_type=type(e).__name__,
                stack_trace=str(e),
            )
            return False

    def _find_executor(self, approval: ApprovalRequest) -> Optional[Any]:
        """Find executor for approval type.

        Args:
            approval: Approval request

        Returns:
            Executor instance or None
        """
        for executor in self.executors:
            if executor.can_execute(approval):
                return executor

        return None
