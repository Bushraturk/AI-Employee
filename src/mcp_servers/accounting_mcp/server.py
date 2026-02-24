"""Accounting MCP Server for Gold Tier.

Provides Odoo integration tools via JSON-RPC interface.
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.mcp_servers.accounting_mcp.odoo_client import OdooClient
from src.models.odoo_transaction import OdooTransaction
from src.services.error_recovery import ErrorRecoveryService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AccountingMCPServer:
    """MCP Server for Odoo accounting integration.

    Provides tools:
    - sync_odoo_transaction: Bidirectional transaction sync
    - create_odoo_invoice: Create customer invoice
    - create_odoo_expense: Record expense
    - create_odoo_customer: Create customer/partner
    """

    def __init__(self, vault_path: Path):
        """Initialize accounting MCP server.

        Args:
            vault_path: Path to AI Employee vault
        """
        self.vault_path = vault_path
        self.odoo_client = OdooClient()
        self.error_recovery = ErrorRecoveryService(vault_path)

        # Tool registry
        self.tools = {
            "sync_odoo_transaction": self.sync_odoo_transaction,
            "create_odoo_invoice": self.create_odoo_invoice,
            "create_odoo_expense": self.create_odoo_expense,
            "create_odoo_customer": self.create_odoo_customer,
        }

        logger.info("Accounting MCP Server initialized")

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming JSON-RPC request.

        Args:
            request: JSON-RPC request dictionary

        Returns:
            JSON-RPC response dictionary
        """
        try:
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")

            if method not in self.tools:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }

            # Execute tool
            result = self.tools[method](**params)

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }

        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }

    def sync_odoo_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """Sync transaction bidirectionally with Odoo.

        Args:
            transaction_id: Transaction ID to sync

        Returns:
            Sync result dictionary
        """
        try:
            # Load transaction from vault
            transaction = OdooTransaction.load(self.vault_path, transaction_id)

            # Connect to Odoo
            with self.odoo_client as odoo:
                if transaction.odoo_id:
                    # Transaction already synced, check for conflicts
                    odoo_record = odoo.get_invoice(transaction.odoo_id)

                    if not odoo_record:
                        transaction.mark_failed()
                        transaction.save(self.vault_path)
                        return {
                            "success": False,
                            "error": "Transaction not found in Odoo"
                        }

                    # Check for modifications (conflict detection)
                    # This is a simplified version - full implementation in T029
                    if transaction.last_synced_at:
                        odoo_write_date = odoo_record.get('write_date')
                        # Conflict detection logic would go here

                else:
                    # New transaction, create in Odoo
                    if transaction.type.value == "invoice":
                        # Get or create partner
                        partner_id = odoo.get_or_create_partner(
                            transaction.customer_vendor or "Unknown",
                            is_customer=True
                        )

                        # Get currency ID
                        currency_id = odoo.get_currency_id(transaction.currency)

                        if not currency_id:
                            raise ValueError(f"Currency not found: {transaction.currency}")

                        # Create invoice
                        odoo_id = odoo.create_invoice(
                            partner_id=partner_id,
                            invoice_date=transaction.date.isoformat(),
                            amount=float(transaction.amount),
                            currency_id=currency_id,
                            description=f"Transaction {transaction.transaction_id}"
                        )

                        transaction.mark_synced(odoo_id)
                        transaction.save(self.vault_path)

                        return {
                            "success": True,
                            "odoo_id": odoo_id,
                            "message": "Transaction synced to Odoo"
                        }

                    elif transaction.type.value == "expense":
                        # Similar logic for expenses
                        partner_id = odoo.get_or_create_partner(
                            transaction.customer_vendor or "Unknown",
                            is_customer=False
                        )

                        currency_id = odoo.get_currency_id(transaction.currency)

                        if not currency_id:
                            raise ValueError(f"Currency not found: {transaction.currency}")

                        # Note: Simplified - full implementation would map category to account_id
                        account_id = 1  # Placeholder

                        odoo_id = odoo.create_expense(
                            partner_id=partner_id,
                            expense_date=transaction.date.isoformat(),
                            amount=float(transaction.amount),
                            currency_id=currency_id,
                            account_id=account_id,
                            description=f"Transaction {transaction.transaction_id}"
                        )

                        transaction.mark_synced(odoo_id)
                        transaction.save(self.vault_path)

                        return {
                            "success": True,
                            "odoo_id": odoo_id,
                            "message": "Expense synced to Odoo"
                        }

            return {
                "success": False,
                "error": "Unsupported transaction type"
            }

        except Exception as e:
            logger.error(f"Failed to sync transaction {transaction_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def create_odoo_invoice(self, customer_name: str, amount: float,
                           currency: str, date: str, description: str) -> Dict[str, Any]:
        """Create customer invoice in Odoo.

        Args:
            customer_name: Customer name
            amount: Invoice amount
            currency: Currency code
            date: Invoice date (YYYY-MM-DD)
            description: Invoice description

        Returns:
            Creation result dictionary
        """
        try:
            with self.odoo_client as odoo:
                # Get or create partner
                partner_id = odoo.get_or_create_partner(customer_name, is_customer=True)

                # Get currency ID
                currency_id = odoo.get_currency_id(currency)

                if not currency_id:
                    raise ValueError(f"Currency not found: {currency}")

                # Create invoice
                odoo_id = odoo.create_invoice(
                    partner_id=partner_id,
                    invoice_date=date,
                    amount=amount,
                    currency_id=currency_id,
                    description=description
                )

                return {
                    "success": True,
                    "odoo_id": odoo_id,
                    "message": f"Invoice created in Odoo: ID {odoo_id}"
                }

        except Exception as e:
            logger.error(f"Failed to create invoice: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def create_odoo_expense(self, vendor_name: str, amount: float,
                           currency: str, date: str, category: str,
                           description: str) -> Dict[str, Any]:
        """Record expense in Odoo.

        Args:
            vendor_name: Vendor name
            amount: Expense amount
            currency: Currency code
            date: Expense date (YYYY-MM-DD)
            category: Expense category
            description: Expense description

        Returns:
            Creation result dictionary
        """
        try:
            with self.odoo_client as odoo:
                # Get or create partner
                partner_id = odoo.get_or_create_partner(vendor_name, is_customer=False)

                # Get currency ID
                currency_id = odoo.get_currency_id(currency)

                if not currency_id:
                    raise ValueError(f"Currency not found: {currency}")

                # Note: Simplified - full implementation would map category to account_id
                account_id = 1  # Placeholder

                # Create expense
                odoo_id = odoo.create_expense(
                    partner_id=partner_id,
                    expense_date=date,
                    amount=amount,
                    currency_id=currency_id,
                    account_id=account_id,
                    description=description
                )

                return {
                    "success": True,
                    "odoo_id": odoo_id,
                    "message": f"Expense created in Odoo: ID {odoo_id}"
                }

        except Exception as e:
            logger.error(f"Failed to create expense: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def create_odoo_customer(self, name: str, is_customer: bool = True) -> Dict[str, Any]:
        """Create customer/partner in Odoo.

        Args:
            name: Customer/vendor name
            is_customer: True for customer, False for vendor

        Returns:
            Creation result dictionary
        """
        try:
            with self.odoo_client as odoo:
                partner_id = odoo.get_or_create_partner(name, is_customer)

                return {
                    "success": True,
                    "partner_id": partner_id,
                    "message": f"Partner created/found in Odoo: ID {partner_id}"
                }

        except Exception as e:
            logger.error(f"Failed to create customer: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def run(self) -> None:
        """Run MCP server (read from stdin, write to stdout)."""
        logger.info("Accounting MCP Server started")

        try:
            while True:
                # Read JSON-RPC request from stdin
                line = sys.stdin.readline()

                if not line:
                    break

                try:
                    request = json.loads(line)
                    response = self.handle_request(request)

                    # Write JSON-RPC response to stdout
                    sys.stdout.write(json.dumps(response) + "\n")
                    sys.stdout.flush()

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        }
                    }
                    sys.stdout.write(json.dumps(error_response) + "\n")
                    sys.stdout.flush()

        except KeyboardInterrupt:
            logger.info("Accounting MCP Server stopped")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Accounting MCP Server")
    parser.add_argument("--vault", type=str, required=True, help="Path to AI Employee vault")
    args = parser.parse_args()

    vault_path = Path(args.vault)

    if not vault_path.exists():
        logger.error(f"Vault path does not exist: {vault_path}")
        sys.exit(1)

    server = AccountingMCPServer(vault_path)
    server.run()


if __name__ == "__main__":
    main()
