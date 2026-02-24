"""Conflict Detection for Odoo Sync.

Detects conflicts when transactions are modified in both vault and Odoo.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
from decimal import Decimal

from src.models.odoo_transaction import OdooTransaction

logger = logging.getLogger(__name__)


class ConflictDetector:
    """Detects sync conflicts between vault and Odoo transactions.

    Conflict occurs when:
    - Transaction modified in vault after last sync (updated_at > last_synced_at)
    - Transaction modified in Odoo after last sync (write_date > last_synced_at)
    - Both modifications happened
    """

    @staticmethod
    def detect_conflict(vault_transaction: OdooTransaction,
                       odoo_record: Dict[str, Any]) -> Optional[str]:
        """Detect if transaction has sync conflict.

        Args:
            vault_transaction: Transaction from vault
            odoo_record: Record from Odoo

        Returns:
            Conflict description if conflict detected, None otherwise
        """
        if not vault_transaction.last_synced_at:
            # Never synced, no conflict possible
            return None

        try:
            # Parse Odoo write date
            odoo_write_date = datetime.strptime(
                odoo_record['write_date'],
                '%Y-%m-%d %H:%M:%S'
            )

            # Check if vault was modified after last sync
            vault_modified = vault_transaction.updated_at > vault_transaction.last_synced_at

            # Check if Odoo was modified after last sync
            odoo_modified = odoo_write_date > vault_transaction.last_synced_at

            if vault_modified and odoo_modified:
                # Both sides modified - conflict!
                conflict_details = ConflictDetector._build_conflict_details(
                    vault_transaction,
                    odoo_record,
                    odoo_write_date
                )
                return conflict_details

            return None

        except Exception as e:
            logger.error(f"Error detecting conflict: {e}")
            return None

    @staticmethod
    def _build_conflict_details(vault_transaction: OdooTransaction,
                               odoo_record: Dict[str, Any],
                               odoo_write_date: datetime) -> str:
        """Build detailed conflict description.

        Args:
            vault_transaction: Transaction from vault
            odoo_record: Record from Odoo
            odoo_write_date: Odoo modification timestamp

        Returns:
            Conflict description string
        """
        details = []

        # Compare amounts
        vault_amount = vault_transaction.amount
        odoo_amount = Decimal(str(odoo_record['amount_total']))

        if vault_amount != odoo_amount:
            details.append(
                f"Amount: Vault={vault_amount}, Odoo={odoo_amount}"
            )

        # Compare dates
        vault_date = vault_transaction.date
        odoo_date = datetime.strptime(odoo_record['invoice_date'], '%Y-%m-%d').date()

        if vault_date != odoo_date:
            details.append(
                f"Date: Vault={vault_date}, Odoo={odoo_date}"
            )

        # Compare customer/vendor
        vault_customer = vault_transaction.customer_vendor or "Unknown"
        odoo_customer = odoo_record['partner_id'][1] if isinstance(
            odoo_record['partner_id'], list
        ) else "Unknown"

        if vault_customer != odoo_customer:
            details.append(
                f"Customer: Vault={vault_customer}, Odoo={odoo_customer}"
            )

        # Build conflict message
        conflict_msg = (
            f"Transaction modified in both systems. "
            f"Vault modified: {vault_transaction.updated_at.strftime('%Y-%m-%d %H:%M:%S')}, "
            f"Odoo modified: {odoo_write_date.strftime('%Y-%m-%d %H:%M:%S')}. "
            f"Differences: {'; '.join(details) if details else 'Timestamps only'}"
        )

        return conflict_msg[:500]  # Truncate to 500 chars

    @staticmethod
    def resolve_conflict_with_vault(vault_transaction: OdooTransaction,
                                    odoo_client) -> bool:
        """Resolve conflict by using vault version (overwrite Odoo).

        Args:
            vault_transaction: Transaction from vault
            odoo_client: Odoo client instance

        Returns:
            True if resolution successful
        """
        try:
            if not vault_transaction.odoo_id:
                logger.error("Cannot resolve conflict: no Odoo ID")
                return False

            # Update Odoo record with vault values
            values = {
                'amount_total': float(vault_transaction.amount),
                'invoice_date': vault_transaction.date.isoformat(),
            }

            odoo_client.update_record(
                'account.move',
                vault_transaction.odoo_id,
                values
            )

            # Mark conflict as resolved
            vault_transaction.resolve_conflict()

            logger.info(
                f"Resolved conflict for transaction {vault_transaction.transaction_id} "
                f"using vault version"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to resolve conflict with vault version: {e}")
            return False

    @staticmethod
    def resolve_conflict_with_odoo(vault_transaction: OdooTransaction,
                                   odoo_record: Dict[str, Any]) -> bool:
        """Resolve conflict by using Odoo version (overwrite vault).

        Args:
            vault_transaction: Transaction from vault
            odoo_record: Record from Odoo

        Returns:
            True if resolution successful
        """
        try:
            # Update vault transaction with Odoo values
            vault_transaction.amount = Decimal(str(odoo_record['amount_total']))
            vault_transaction.date = datetime.strptime(
                odoo_record['invoice_date'],
                '%Y-%m-%d'
            ).date()

            partner_name = odoo_record['partner_id'][1] if isinstance(
                odoo_record['partner_id'], list
            ) else 'Unknown'
            vault_transaction.customer_vendor = partner_name

            # Mark conflict as resolved
            vault_transaction.resolve_conflict()

            logger.info(
                f"Resolved conflict for transaction {vault_transaction.transaction_id} "
                f"using Odoo version"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to resolve conflict with Odoo version: {e}")
            return False
