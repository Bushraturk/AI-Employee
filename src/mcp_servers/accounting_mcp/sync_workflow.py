"""Transaction Sync Workflow for Odoo Integration.

Orchestrates the complete sync process: poll → detect changes → sync → handle conflicts.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from src.mcp_servers.accounting_mcp.odoo_client import OdooClient
from src.mcp_servers.accounting_mcp.polling_service import OdooPollingService
from src.mcp_servers.accounting_mcp.conflict_detector import ConflictDetector
from src.models.odoo_transaction import OdooTransaction, SyncStatus
from src.services.error_recovery import ErrorRecoveryService, ServiceType, ErrorType

logger = logging.getLogger(__name__)


class TransactionSyncWorkflow:
    """Orchestrates bidirectional transaction sync between vault and Odoo.

    Workflow steps:
    1. Poll Odoo for changes (new/modified transactions)
    2. Detect conflicts (modifications in both systems)
    3. Sync vault transactions to Odoo
    4. Handle conflicts (flag for manual resolution)
    5. Log all sync operations
    """

    def __init__(self, vault_path: Path):
        """Initialize sync workflow.

        Args:
            vault_path: Path to AI Employee vault
        """
        self.vault_path = vault_path
        self.odoo_client = OdooClient()
        self.polling_service = OdooPollingService(vault_path, self.odoo_client)
        self.error_recovery = ErrorRecoveryService(vault_path)

    def run_full_sync(self) -> Dict[str, Any]:
        """Run complete bidirectional sync workflow.

        Returns:
            Sync results dictionary
        """
        logger.info("Starting full transaction sync workflow")

        results = {
            "started_at": datetime.now().isoformat(),
            "odoo_to_vault": {},
            "vault_to_odoo": {},
            "conflicts": [],
            "errors": []
        }

        try:
            # Step 1: Poll Odoo for changes (Odoo → Vault)
            logger.info("Step 1: Polling Odoo for changes")
            poll_results = self.polling_service.poll_and_sync()
            results["odoo_to_vault"] = poll_results

            # Step 2: Sync pending vault transactions to Odoo (Vault → Odoo)
            logger.info("Step 2: Syncing vault transactions to Odoo")
            vault_sync_results = self._sync_vault_to_odoo()
            results["vault_to_odoo"] = vault_sync_results

            # Step 3: Detect and flag conflicts
            logger.info("Step 3: Detecting conflicts")
            conflicts = self._detect_all_conflicts()
            results["conflicts"] = conflicts

            results["completed_at"] = datetime.now().isoformat()
            results["success"] = True

            logger.info(
                f"Sync workflow complete: "
                f"{poll_results.get('new_count', 0)} new from Odoo, "
                f"{vault_sync_results.get('synced_count', 0)} synced to Odoo, "
                f"{len(conflicts)} conflicts detected"
            )

            return results

        except Exception as e:
            logger.error(f"Sync workflow failed: {e}")
            results["errors"].append(str(e))
            results["success"] = False
            results["completed_at"] = datetime.now().isoformat()
            return results

    def _sync_vault_to_odoo(self) -> Dict[str, Any]:
        """Sync pending vault transactions to Odoo.

        Returns:
            Sync results dictionary
        """
        results = {
            "synced_count": 0,
            "failed_count": 0,
            "skipped_count": 0
        }

        try:
            # Find all pending transactions in vault
            transaction_dir = self.vault_path / "Accounting" / "transactions"
            if not transaction_dir.exists():
                return results

            pending_transactions = []

            for transaction_file in transaction_dir.glob("*.md"):
                try:
                    transaction = OdooTransaction.load(
                        self.vault_path,
                        transaction_file.stem
                    )

                    if transaction.sync_status == SyncStatus.PENDING:
                        pending_transactions.append(transaction)

                except Exception as e:
                    logger.error(f"Failed to load transaction {transaction_file.stem}: {e}")

            logger.info(f"Found {len(pending_transactions)} pending transactions")

            # Connect to Odoo
            self.odoo_client.connect()

            # Sync each pending transaction
            for transaction in pending_transactions:
                try:
                    # Use error recovery wrapper
                    @self.error_recovery.with_retry(
                        service=ServiceType.ODOO,
                        error_type=ErrorType.NETWORK,
                        action_name="sync_transaction",
                        context={"transaction_id": transaction.transaction_id}
                    )
                    def sync_transaction():
                        return self._sync_single_transaction(transaction)

                    success = sync_transaction()

                    if success:
                        results["synced_count"] += 1
                    else:
                        results["failed_count"] += 1

                except Exception as e:
                    logger.error(
                        f"Failed to sync transaction {transaction.transaction_id}: {e}"
                    )
                    results["failed_count"] += 1

            # Disconnect from Odoo
            self.odoo_client.disconnect()

            return results

        except Exception as e:
            logger.error(f"Failed to sync vault to Odoo: {e}")
            return results

    def _sync_single_transaction(self, transaction: OdooTransaction) -> bool:
        """Sync a single transaction to Odoo.

        Args:
            transaction: Transaction to sync

        Returns:
            True if sync successful
        """
        try:
            if transaction.type.value == "invoice":
                # Get or create partner
                partner_id = self.odoo_client.get_or_create_partner(
                    transaction.customer_vendor or "Unknown",
                    is_customer=True
                )

                # Get currency ID
                currency_id = self.odoo_client.get_currency_id(transaction.currency)

                if not currency_id:
                    logger.error(f"Currency not found: {transaction.currency}")
                    transaction.mark_failed()
                    transaction.save(self.vault_path)
                    return False

                # Create invoice
                odoo_id = self.odoo_client.create_invoice(
                    partner_id=partner_id,
                    invoice_date=transaction.date.isoformat(),
                    amount=float(transaction.amount),
                    currency_id=currency_id,
                    description=f"Transaction {transaction.transaction_id}"
                )

                transaction.mark_synced(odoo_id)
                transaction.save(self.vault_path)

                logger.info(
                    f"Synced invoice {transaction.transaction_id} to Odoo (ID: {odoo_id})"
                )
                return True

            elif transaction.type.value == "expense":
                # Get or create partner
                partner_id = self.odoo_client.get_or_create_partner(
                    transaction.customer_vendor or "Unknown",
                    is_customer=False
                )

                # Get currency ID
                currency_id = self.odoo_client.get_currency_id(transaction.currency)

                if not currency_id:
                    logger.error(f"Currency not found: {transaction.currency}")
                    transaction.mark_failed()
                    transaction.save(self.vault_path)
                    return False

                # Note: Simplified - full implementation would use category mapper
                account_id = 1  # Placeholder

                # Create expense
                odoo_id = self.odoo_client.create_expense(
                    partner_id=partner_id,
                    expense_date=transaction.date.isoformat(),
                    amount=float(transaction.amount),
                    currency_id=currency_id,
                    account_id=account_id,
                    description=f"Transaction {transaction.transaction_id}"
                )

                transaction.mark_synced(odoo_id)
                transaction.save(self.vault_path)

                logger.info(
                    f"Synced expense {transaction.transaction_id} to Odoo (ID: {odoo_id})"
                )
                return True

            else:
                logger.warning(f"Unsupported transaction type: {transaction.type.value}")
                return False

        except Exception as e:
            logger.error(f"Failed to sync transaction {transaction.transaction_id}: {e}")
            transaction.mark_failed()
            transaction.save(self.vault_path)
            return False

    def _detect_all_conflicts(self) -> List[Dict[str, Any]]:
        """Detect conflicts for all synced transactions.

        Returns:
            List of conflict dictionaries
        """
        conflicts = []

        try:
            # Find all synced transactions in vault
            transaction_dir = self.vault_path / "Accounting" / "transactions"
            if not transaction_dir.exists():
                return conflicts

            # Connect to Odoo
            self.odoo_client.connect()

            for transaction_file in transaction_dir.glob("*.md"):
                try:
                    transaction = OdooTransaction.load(
                        self.vault_path,
                        transaction_file.stem
                    )

                    # Only check synced transactions
                    if transaction.sync_status != SyncStatus.SYNCED or not transaction.odoo_id:
                        continue

                    # Get Odoo record
                    odoo_record = self.odoo_client.get_invoice(transaction.odoo_id)

                    if not odoo_record:
                        logger.warning(
                            f"Transaction {transaction.transaction_id} not found in Odoo"
                        )
                        continue

                    # Detect conflict
                    conflict_details = ConflictDetector.detect_conflict(
                        transaction,
                        odoo_record
                    )

                    if conflict_details:
                        # Mark transaction as conflicted
                        transaction.mark_conflict(conflict_details)
                        transaction.save(self.vault_path)

                        conflicts.append({
                            "transaction_id": transaction.transaction_id,
                            "odoo_id": transaction.odoo_id,
                            "details": conflict_details
                        })

                        logger.warning(
                            f"Conflict detected for transaction {transaction.transaction_id}"
                        )

                except Exception as e:
                    logger.error(f"Failed to check transaction {transaction_file.stem}: {e}")

            # Disconnect from Odoo
            self.odoo_client.disconnect()

            return conflicts

        except Exception as e:
            logger.error(f"Failed to detect conflicts: {e}")
            return conflicts

    def resolve_conflict(self, transaction_id: str, use_vault_version: bool = True) -> bool:
        """Resolve a conflict for a specific transaction.

        Args:
            transaction_id: Transaction ID
            use_vault_version: If True, use vault version; if False, use Odoo version

        Returns:
            True if resolution successful
        """
        try:
            # Load transaction
            transaction = OdooTransaction.load(self.vault_path, transaction_id)

            if not transaction.conflict_flag:
                logger.warning(f"Transaction {transaction_id} has no conflict")
                return False

            if not transaction.odoo_id:
                logger.error(f"Transaction {transaction_id} has no Odoo ID")
                return False

            # Connect to Odoo
            self.odoo_client.connect()

            if use_vault_version:
                # Resolve with vault version
                success = ConflictDetector.resolve_conflict_with_vault(
                    transaction,
                    self.odoo_client
                )
            else:
                # Resolve with Odoo version
                odoo_record = self.odoo_client.get_invoice(transaction.odoo_id)

                if not odoo_record:
                    logger.error(f"Odoo record not found: {transaction.odoo_id}")
                    return False

                success = ConflictDetector.resolve_conflict_with_odoo(
                    transaction,
                    odoo_record
                )

            if success:
                transaction.save(self.vault_path)

            # Disconnect from Odoo
            self.odoo_client.disconnect()

            return success

        except Exception as e:
            logger.error(f"Failed to resolve conflict for {transaction_id}: {e}")
            return False
