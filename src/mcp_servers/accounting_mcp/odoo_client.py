"""Odoo Client wrapper for Gold Tier.

Provides high-level interface to Odoo Community Edition via JSON-RPC.
"""

import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from dotenv import load_dotenv

try:
    import odoorpc
except ImportError:
    odoorpc = None

logger = logging.getLogger(__name__)

load_dotenv()


class OdooConnectionError(Exception):
    """Raised when connection to Odoo fails."""
    pass


class OdooAuthenticationError(Exception):
    """Raised when authentication with Odoo fails."""
    pass


class OdooClient:
    """Wrapper for Odoo JSON-RPC communication.

    Features:
    - Connection management with automatic reconnection
    - Authentication handling
    - Error handling and logging
    - High-level API for common operations
    """

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None,
                 database: Optional[str] = None, username: Optional[str] = None,
                 password: Optional[str] = None):
        """Initialize Odoo client.

        Args:
            host: Odoo server host (default: from ODOO_HOST env var)
            port: Odoo server port (default: from ODOO_PORT env var)
            database: Odoo database name (default: from ODOO_DB env var)
            username: Odoo username (default: from ODOO_USER env var)
            password: Odoo password (default: from ODOO_PASSWORD env var)
        """
        if odoorpc is None:
            raise ImportError("odoorpc library not installed. Run: pip install odoorpc>=0.10.1")

        self.host = host or os.getenv('ODOO_HOST', 'localhost')
        self.port = port or int(os.getenv('ODOO_PORT', '8069'))
        self.database = database or os.getenv('ODOO_DB')
        self.username = username or os.getenv('ODOO_USER')
        self.password = password or os.getenv('ODOO_PASSWORD')

        if not all([self.database, self.username, self.password]):
            raise ValueError("Odoo credentials not configured. Set ODOO_DB, ODOO_USER, ODOO_PASSWORD")

        self.odoo: Optional[odoorpc.ODOO] = None
        self._connected = False

    def connect(self) -> bool:
        """Connect to Odoo server.

        Returns:
            True if connection successful

        Raises:
            OdooConnectionError: If connection fails
            OdooAuthenticationError: If authentication fails
        """
        try:
            logger.info(f"Connecting to Odoo at {self.host}:{self.port}")

            self.odoo = odoorpc.ODOO(self.host, port=self.port)

            logger.info(f"Authenticating with database: {self.database}")

            self.odoo.login(self.database, self.username, self.password)

            self._connected = True
            logger.info("Successfully connected to Odoo")

            return True

        except odoorpc.error.RPCError as e:
            logger.error(f"Odoo RPC error: {e}")
            raise OdooConnectionError(f"Failed to connect to Odoo: {e}")

        except Exception as e:
            logger.error(f"Unexpected error connecting to Odoo: {e}")
            raise OdooConnectionError(f"Unexpected error: {e}")

    def disconnect(self) -> None:
        """Disconnect from Odoo server."""
        if self.odoo:
            self.odoo.logout()
            self._connected = False
            logger.info("Disconnected from Odoo")

    def ensure_connected(self) -> None:
        """Ensure connection is active, reconnect if needed."""
        if not self._connected or not self.odoo:
            self.connect()

    def search_records(self, model: str, domain: List, fields: Optional[List[str]] = None,
                      limit: Optional[int] = None, offset: int = 0) -> List[Dict[str, Any]]:
        """Search for records in Odoo.

        Args:
            model: Odoo model name (e.g., 'account.move')
            domain: Search domain (e.g., [('state', '=', 'posted')])
            fields: Fields to retrieve (default: all)
            limit: Maximum number of records
            offset: Number of records to skip

        Returns:
            List of record dictionaries
        """
        self.ensure_connected()

        try:
            # Search for record IDs
            record_ids = self.odoo.env[model].search(domain, limit=limit, offset=offset)

            if not record_ids:
                return []

            # Read record data
            records = self.odoo.env[model].read(record_ids, fields or [])

            return records

        except Exception as e:
            logger.error(f"Failed to search records in {model}: {e}")
            raise

    def create_record(self, model: str, values: Dict[str, Any]) -> int:
        """Create a new record in Odoo.

        Args:
            model: Odoo model name
            values: Field values for new record

        Returns:
            ID of created record
        """
        self.ensure_connected()

        try:
            record_id = self.odoo.env[model].create(values)
            logger.info(f"Created record in {model}: ID {record_id}")
            return record_id

        except Exception as e:
            logger.error(f"Failed to create record in {model}: {e}")
            raise

    def update_record(self, model: str, record_id: int, values: Dict[str, Any]) -> bool:
        """Update an existing record in Odoo.

        Args:
            model: Odoo model name
            record_id: Record ID to update
            values: Field values to update

        Returns:
            True if update successful
        """
        self.ensure_connected()

        try:
            self.odoo.env[model].write([record_id], values)
            logger.info(f"Updated record in {model}: ID {record_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update record {record_id} in {model}: {e}")
            raise

    def delete_record(self, model: str, record_id: int) -> bool:
        """Delete a record from Odoo.

        Args:
            model: Odoo model name
            record_id: Record ID to delete

        Returns:
            True if deletion successful
        """
        self.ensure_connected()

        try:
            self.odoo.env[model].unlink([record_id])
            logger.info(f"Deleted record from {model}: ID {record_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete record {record_id} from {model}: {e}")
            raise

    def get_record(self, model: str, record_id: int, fields: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Get a single record by ID.

        Args:
            model: Odoo model name
            record_id: Record ID
            fields: Fields to retrieve (default: all)

        Returns:
            Record dictionary or None if not found
        """
        self.ensure_connected()

        try:
            records = self.odoo.env[model].read([record_id], fields or [])
            return records[0] if records else None

        except Exception as e:
            logger.error(f"Failed to get record {record_id} from {model}: {e}")
            return None

    def search_by_write_date(self, model: str, since: datetime,
                            fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Search for records modified since a given date.

        Args:
            model: Odoo model name
            since: Datetime to search from
            fields: Fields to retrieve

        Returns:
            List of modified records
        """
        domain = [('write_date', '>=', since.strftime('%Y-%m-%d %H:%M:%S'))]
        return self.search_records(model, domain, fields)

    def get_invoice(self, invoice_id: int) -> Optional[Dict[str, Any]]:
        """Get invoice by ID.

        Args:
            invoice_id: Invoice ID

        Returns:
            Invoice record or None
        """
        return self.get_record('account.move', invoice_id, [
            'name', 'partner_id', 'invoice_date', 'amount_total',
            'currency_id', 'state', 'move_type', 'write_date'
        ])

    def create_invoice(self, partner_id: int, invoice_date: str, amount: float,
                      currency_id: int, description: str) -> int:
        """Create a customer invoice.

        Args:
            partner_id: Customer partner ID
            invoice_date: Invoice date (YYYY-MM-DD)
            amount: Invoice amount
            currency_id: Currency ID
            description: Invoice description

        Returns:
            Created invoice ID
        """
        values = {
            'partner_id': partner_id,
            'invoice_date': invoice_date,
            'move_type': 'out_invoice',
            'currency_id': currency_id,
            'narration': description
        }

        return self.create_record('account.move', values)

    def create_expense(self, partner_id: int, expense_date: str, amount: float,
                      currency_id: int, account_id: int, description: str) -> int:
        """Create an expense entry.

        Args:
            partner_id: Vendor partner ID
            expense_date: Expense date (YYYY-MM-DD)
            amount: Expense amount
            currency_id: Currency ID
            account_id: Expense account ID
            description: Expense description

        Returns:
            Created expense ID
        """
        values = {
            'partner_id': partner_id,
            'date': expense_date,
            'move_type': 'in_invoice',
            'currency_id': currency_id,
            'narration': description
        }

        return self.create_record('account.move', values)

    def get_or_create_partner(self, name: str, is_customer: bool = True) -> int:
        """Get existing partner or create new one.

        Args:
            name: Partner name
            is_customer: True for customer, False for vendor

        Returns:
            Partner ID
        """
        # Search for existing partner
        partners = self.search_records('res.partner', [('name', '=', name)], limit=1)

        if partners:
            return partners[0]['id']

        # Create new partner
        values = {
            'name': name,
            'customer_rank': 1 if is_customer else 0,
            'supplier_rank': 0 if is_customer else 1
        }

        return self.create_record('res.partner', values)

    def get_currency_id(self, currency_code: str) -> Optional[int]:
        """Get currency ID by code.

        Args:
            currency_code: Currency code (e.g., 'USD', 'EUR')

        Returns:
            Currency ID or None if not found
        """
        currencies = self.search_records('res.currency', [('name', '=', currency_code)], limit=1)
        return currencies[0]['id'] if currencies else None

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
