"""Odoo Polling Service for Gold Tier.

Polls Odoo for changes every 5 minutes and syncs to vault.
"""

import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any
from decimal import Decimal

from src.mcp_servers.accounting_mcp.odoo_client import OdooClient
from src.models.odoo_transaction import OdooTransaction, TransactionType, SyncStatus

logger = logging.getLogger(__name__)


class OdooPollingService:
    """Service for polling Odoo for transaction changes.

    Features:
    - Poll Odoo every 5 minutes for changes
    - Detect new transactions in Odoo
    - Detect modifications to existing transactions
    - Sync changes to vault
    - Track last poll timestamp
    """

    def __init__(self, vault_path: Path, odoo_client: OdooClient):
        """Initialize polling service.

        Args:
            vault_path: Path to AI Employee vault
            odoo_client: Odoo client instance
        """
        self.vault_path = vault_path
        self.odoo_client = odoo_client
        self.last_poll_file = vault_path / "System" / "odoo_last_poll.txt"

    def get_last_poll_time(self) -> datetime:
        """Get timestamp of last successful poll.

        Returns:
            Last poll timestamp, or 7 days ago if never polled
        """
        if self.last_poll_file.exists():
            try:
                timestamp_str = self.last_poll_file.read_text().strip()
                return datetime.fromisoformat(timestamp_str)
            except Exception as e:
                logger.error(f"Failed to read last poll time: {e}")

        # Default to 7 days ago for first poll
        return datetime.now() - timedelta(days=7)

    def update_last_poll_time(self, timestamp: datetime) -> None:
        """Update last poll timestamp.

        Args:
            timestamp: Timestamp to save
        """
        try:
            self.last_poll_file.parent.mkdir(parents=True, exist_ok=True)
            self.last_poll_file.write_text(timestamp.isoformat())
        except Exception as e:
            logger.error(f"Failed to update last poll time: {e}")

    def poll_odoo_changes(self) -> Dict[str, Any]:
        """Poll Odoo for changes since last poll.

        Returns:
            Dictionary with poll results
        """
        try:
            last_poll = self.get_last_poll_time()
            current_time = datetime.now()

            logger.info(f"Polling Odoo for changes since {last_poll.isoformat()}")

            # Connect to Odoo
            self.odoo_client.connect()

            # Search for modified invoices (customer invoices)
            invoices = self.odoo_client.search_by_write_date(
                model='account.move',
                since=last_poll,
                fields=['name', 'partner_id', 'invoice_date', 'amount_total',
                       'currency_id', 'state', 'move_type', 'write_date', 'id']
            )

            # Filter for customer invoices only
            customer_invoices = [
                inv for inv in invoices
                if inv.get('move_type') == 'out_invoice'
            ]

            # Filter for vendor bills (expenses)
            vendor_bills = [
                inv for inv in invoices
                if inv.get('move_type') == 'in_invoice'
            ]

            # Process new/modified invoices
            new_count = 0
            updated_count = 0

            for invoice in customer_invoices:
                result = self._process_invoice(invoice)
                if result == 'new':
                    new_count += 1
                elif result == 'updated':
                    updated_count += 1

            for bill in vendor_bills:
                result = self._process_expense(bill)
                if result == 'new':
                    new_count += 1
                elif result == 'updated':
                    updated_count += 1

            # Update last poll time
            self.update_last_poll_time(current_time)

            # Disconnect from Odoo
            self.odoo_client.disconnect()

            logger.info(
                f"Poll complete: {new_count} new, {updated_count} updated, "
                f"{len(customer_invoices) + len(vendor_bills)} total records"
            )

            return {
                "success": True,
                "new_count": new_count,
                "updated_count": updated_count,
                "total_records": len(customer_invoices) + len(vendor_bills),
                "poll_time": current_time.isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to poll Odoo: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _process_invoice(self, odoo_invoice: Dict[str, Any]) -> str:
        """Process an invoice from Odoo.

        Args:
            odoo_invoice: Invoice record from Odoo

        Returns:
            'new' if created, 'updated' if modified, 'skipped' if no action
        """
        try:
            odoo_id = odoo_invoice['id']

            # Check if transaction already exists in vault
            existing = OdooTransaction.find_by_odoo_id(self.vault_path, odoo_id)

            if existing:
                # Check if modified (conflict detection handled separately)
                odoo_write_date = datetime.strptime(
                    odoo_invoice['write_date'],
                    '%Y-%m-%d %H:%M:%S'
                )

                if existing.last_synced_at and odoo_write_date > existing.last_synced_at:
                    # Transaction was modified in Odoo after last sync
                    # Update vault transaction
                    existing.amount = Decimal(str(odoo_invoice['amount_total']))
                    existing.date = datetime.strptime(
                        odoo_invoice['invoice_date'],
                        '%Y-%m-%d'
                    ).date()
                    existing.last_synced_at = datetime.now()
                    existing.updated_at = datetime.now()
                    existing.save(self.vault_path)

                    logger.info(f"Updated transaction from Odoo: {existing.transaction_id}")
                    return 'updated'

                return 'skipped'

            else:
                # New transaction from Odoo, create in vault
                partner_name = odoo_invoice['partner_id'][1] if isinstance(
                    odoo_invoice['partner_id'], list
                ) else 'Unknown'

                currency_code = odoo_invoice['currency_id'][1] if isinstance(
                    odoo_invoice['currency_id'], list
                ) else 'USD'

                transaction = OdooTransaction.create(
                    type=TransactionType.INVOICE,
                    amount=Decimal(str(odoo_invoice['amount_total'])),
                    currency=currency_code[:3].upper(),  # Extract currency code
                    date=datetime.strptime(odoo_invoice['invoice_date'], '%Y-%m-%d').date(),
                    category="Revenue - Consulting",  # Default category
                    customer_vendor=partner_name
                )

                transaction.mark_synced(odoo_id)
                transaction.save(self.vault_path)

                logger.info(f"Created new transaction from Odoo: {transaction.transaction_id}")
                return 'new'

        except Exception as e:
            logger.error(f"Failed to process invoice {odoo_invoice.get('id')}: {e}")
            return 'skipped'

    def _process_expense(self, odoo_bill: Dict[str, Any]) -> str:
        """Process a vendor bill (expense) from Odoo.

        Args:
            odoo_bill: Vendor bill record from Odoo

        Returns:
            'new' if created, 'updated' if modified, 'skipped' if no action
        """
        try:
            odoo_id = odoo_bill['id']

            # Check if transaction already exists in vault
            existing = OdooTransaction.find_by_odoo_id(self.vault_path, odoo_id)

            if existing:
                # Check if modified
                odoo_write_date = datetime.strptime(
                    odoo_bill['write_date'],
                    '%Y-%m-%d %H:%M:%S'
                )

                if existing.last_synced_at and odoo_write_date > existing.last_synced_at:
                    # Transaction was modified in Odoo after last sync
                    existing.amount = Decimal(str(odoo_bill['amount_total']))
                    existing.date = datetime.strptime(
                        odoo_bill['invoice_date'],
                        '%Y-%m-%d'
                    ).date()
                    existing.last_synced_at = datetime.now()
                    existing.updated_at = datetime.now()
                    existing.save(self.vault_path)

                    logger.info(f"Updated expense from Odoo: {existing.transaction_id}")
                    return 'updated'

                return 'skipped'

            else:
                # New expense from Odoo, create in vault
                partner_name = odoo_bill['partner_id'][1] if isinstance(
                    odoo_bill['partner_id'], list
                ) else 'Unknown'

                currency_code = odoo_bill['currency_id'][1] if isinstance(
                    odoo_bill['currency_id'], list
                ) else 'USD'

                transaction = OdooTransaction.create(
                    type=TransactionType.EXPENSE,
                    amount=Decimal(str(odoo_bill['amount_total'])),
                    currency=currency_code[:3].upper(),
                    date=datetime.strptime(odoo_bill['invoice_date'], '%Y-%m-%d').date(),
                    category="Expenses - General",  # Default category
                    customer_vendor=partner_name
                )

                transaction.mark_synced(odoo_id)
                transaction.save(self.vault_path)

                logger.info(f"Created new expense from Odoo: {transaction.transaction_id}")
                return 'new'

        except Exception as e:
            logger.error(f"Failed to process expense {odoo_bill.get('id')}: {e}")
            return 'skipped'

    def poll_and_sync(self) -> Dict[str, Any]:
        """Poll Odoo and sync changes (main entry point for scheduled job).

        Returns:
            Poll results dictionary
        """
        return self.poll_odoo_changes()
