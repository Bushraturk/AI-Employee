"""Accounting executor for local agent.

Executes approved accounting entries via Accounting MCP server.
Posts transactions to Odoo and updates vault state.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
from decimal import Decimal

from shared.base_executor import BaseExecutor
from shared.models.approval_request import ApprovalRequest, ApprovalType
from shared.models.log_entry import LogEntry, LogCategory as LogEntryCategory, LogLevel
from shared.utils.vault_manager import VaultManager
from shared.utils.logger import VaultLogger, LogCategory
from src.models.odoo_transaction import OdooTransaction, SyncStatus


logger = logging.getLogger(__name__)


class AccountingExecutor(BaseExecutor):
    """Executes approved accounting entries.

    Communicates with Accounting MCP server to post entries to Odoo.
    Updates OdooTransaction entities in vault with sync status.
    """

    def __init__(
        self,
        agent_id: str,
        vault_manager: VaultManager,
        vault_logger: VaultLogger,
        mcp_client: Any,
        dev_mode: bool = False,
        dry_run: bool = False,
    ):
        """Initialize accounting executor.

        Args:
            agent_id: Agent ID
            vault_manager: Vault manager instance
            vault_logger: Vault logger instance
            mcp_client: MCP client for accounting operations
            dev_mode: Development mode flag
            dry_run: Dry run mode flag
        """
        super().__init__(
            executor_name="Accounting Executor",
            agent_id=agent_id,
            vault_manager=vault_manager,
            vault_logger=vault_logger,
        )

        self.mcp_client = mcp_client

        # Override dev_mode and dry_run if provided
        if dev_mode is not None:
            self.dev_mode = dev_mode
        if dry_run is not None:
            self.dry_run = dry_run

        logger.info("Accounting executor initialized")

    def can_execute(self, approval: ApprovalRequest) -> bool:
        """Check if this executor can handle the approval request.

        Args:
            approval: Approval request

        Returns:
            True if can execute, False otherwise
        """
        return approval.approval_type == ApprovalType.ACCOUNTING_ENTRY

    def execute(self, approval: ApprovalRequest) -> bool:
        """Execute approved accounting entry.

        Args:
            approval: Approved accounting entry request

        Returns:
            True if successful, False otherwise
        """
        try:
            self.vault_logger.info(
                LogCategory.EXECUTOR,
                f"Executing accounting entry: {approval.approval_id}",
                details={
                    "approval_id": approval.approval_id,
                    "transaction_id": approval.metadata.get("transaction_id"),
                }
            )

            # Extract accounting parameters
            odoo_transaction_id = approval.metadata.get("odoo_transaction_id")
            transaction_type = approval.metadata.get("type")
            amount = Decimal(str(approval.metadata.get("amount", 0)))
            category = approval.metadata.get("category")

            # Load OdooTransaction entity
            vault_path = Path(self.vault_manager.vault_root)
            odoo_transaction = OdooTransaction.load(vault_path, odoo_transaction_id)

            # Development/dry-run mode
            if self.dev_mode or self.dry_run:
                self.vault_logger.info(
                    LogCategory.EXECUTOR,
                    f"[DRY RUN] Would post accounting entry to Odoo",
                    details={
                        "transaction_id": odoo_transaction_id,
                        "type": transaction_type,
                        "amount": float(amount),
                        "category": category,
                    }
                )

                # Mark as synced with dummy Odoo ID
                odoo_transaction.mark_synced(odoo_id=99999)
                odoo_transaction.save(vault_path)

                return True

            # Post to Odoo via MCP
            result = self._post_to_odoo(
                odoo_transaction=odoo_transaction,
                approval=approval,
            )

            if result:
                odoo_id = result.get("odoo_id")

                # Update OdooTransaction entity
                odoo_transaction.mark_synced(odoo_id=odoo_id)
                odoo_transaction.save(vault_path)

                self.vault_logger.info(
                    LogCategory.EXECUTOR,
                    f"Accounting entry posted successfully: {approval.approval_id}",
                    details={
                        "approval_id": approval.approval_id,
                        "odoo_id": odoo_id,
                        "transaction_id": odoo_transaction_id,
                    }
                )

                # Log to audit trail
                self._log_execution(approval, odoo_transaction, success=True)

                return True
            else:
                # Mark as failed
                odoo_transaction.mark_failed()
                odoo_transaction.save(vault_path)

                self.vault_logger.error(
                    LogCategory.EXECUTOR,
                    f"Failed to post accounting entry: {approval.approval_id}",
                    details={
                        "approval_id": approval.approval_id,
                        "transaction_id": odoo_transaction_id,
                    }
                )

                # Log to audit trail
                self._log_execution(approval, odoo_transaction, success=False, error="Odoo post failed")

                return False

        except Exception as e:
            self.vault_logger.error(
                LogCategory.EXECUTOR,
                f"Error executing accounting entry: {e}",
                error_type=type(e).__name__,
                stack_trace=str(e),
            )

            # Try to mark transaction as failed
            try:
                vault_path = Path(self.vault_manager.vault_root)
                odoo_transaction_id = approval.metadata.get("odoo_transaction_id")
                odoo_transaction = OdooTransaction.load(vault_path, odoo_transaction_id)
                odoo_transaction.mark_failed()
                odoo_transaction.save(vault_path)
            except Exception:
                pass

            # Log to audit trail
            self._log_execution(approval, None, success=False, error=str(e))

            return False

    def _post_to_odoo(
        self,
        odoo_transaction: OdooTransaction,
        approval: ApprovalRequest,
    ) -> Optional[Dict[str, Any]]:
        """Post accounting entry to Odoo via MCP server.

        Args:
            odoo_transaction: OdooTransaction entity
            approval: Approval request with metadata

        Returns:
            Result dictionary with odoo_id or None if failed
        """
        try:
            # For MVP, use simple implementation
            # TODO: Integrate with Accounting MCP server

            logger.info(f"Posting accounting entry to Odoo: {odoo_transaction.transaction_id}")

            # Prepare entry data
            entry_data = {
                "type": odoo_transaction.type.value,
                "amount": float(odoo_transaction.amount),
                "currency": odoo_transaction.currency,
                "date": odoo_transaction.date.isoformat(),
                "category": odoo_transaction.category,
                "customer_vendor": odoo_transaction.customer_vendor,
                "description": approval.metadata.get("description", ""),
            }

            # In production, this would call the MCP server:
            # result = self.mcp_client.call_tool(
            #     server="accounting",
            #     tool="create_accounting_entry",
            #     arguments=entry_data
            # )

            # Simulate successful post for MVP
            # Return dummy Odoo ID
            return {
                "odoo_id": 12345,  # Would be real Odoo record ID
                "status": "posted",
            }

        except Exception as e:
            logger.error(f"Failed to post to Odoo: {e}")
            return None

    def _log_execution(
        self,
        approval: ApprovalRequest,
        odoo_transaction: Optional[OdooTransaction],
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """Log execution to audit trail.

        Args:
            approval: Approval request
            odoo_transaction: OdooTransaction entity (may be None if error)
            success: Whether execution was successful
            error: Error message if failed
        """
        try:
            log_entry = LogEntry(
                timestamp=datetime.now(),
                level=LogLevel.INFO if success else LogLevel.ERROR,
                category=LogEntryCategory.EXECUTOR,
                message=f"Accounting entry {'succeeded' if success else 'failed'}: {approval.approval_id}",
                agent_id=self.agent_id,
                details={
                    "approval_id": approval.approval_id,
                    "transaction_id": approval.metadata.get("transaction_id"),
                    "odoo_transaction_id": approval.metadata.get("odoo_transaction_id"),
                    "type": approval.metadata.get("type"),
                    "amount": approval.metadata.get("amount"),
                    "category": approval.metadata.get("category"),
                    "odoo_id": odoo_transaction.odoo_id if odoo_transaction else None,
                    "result": "success" if success else "failure",
                },
                approval_id=approval.approval_id,
                error_type=type(error).__name__ if error else None,
                stack_trace=str(error) if error else None,
            )

            # Write to daily log file
            log_folder = "Logs"
            log_filename = f"{datetime.now().strftime('%Y-%m-%d')}.md"
            log_path = self.vault_manager.get_folder_path(log_folder) / log_filename

            # Append to log file
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"{log_entry.to_json_line()}\n")

        except Exception as e:
            logger.error(f"Failed to log execution: {e}")
