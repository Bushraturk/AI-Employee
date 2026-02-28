"""Odoo MCP Server

Provides Odoo ERP operations via Model Context Protocol (MCP).
Supports invoice creation, payment registration, and expense tracking.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
import odoorpc
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OdooMCPServer:
    """MCP server for Odoo integration."""

    def __init__(self):
        """Initialize Odoo MCP server."""
        self.odoo_url = os.getenv("ODOO_URL", "http://localhost:8069")
        self.odoo_db = os.getenv("ODOO_DB", "odoo")
        self.odoo_username = os.getenv("ODOO_USERNAME")
        self.odoo_password = os.getenv("ODOO_PASSWORD")

        self.odoo: Optional[odoorpc.ODOO] = None
        self._connect()

    def _connect(self) -> None:
        """Connect to Odoo instance."""
        try:
            # Parse URL
            url_parts = self.odoo_url.replace("http://", "").replace("https://", "").split(":")
            host = url_parts[0]
            port = int(url_parts[1]) if len(url_parts) > 1 else 8069
            protocol = "jsonrpc+ssl" if "https" in self.odoo_url else "jsonrpc"

            logger.info(f"Connecting to Odoo at {host}:{port}")

            self.odoo = odoorpc.ODOO(host, protocol=protocol, port=port)
            self.odoo.login(self.odoo_db, self.odoo_username, self.odoo_password)

            logger.info("Connected to Odoo successfully")

        except Exception as e:
            logger.error(f"Failed to connect to Odoo: {e}")
            raise

    def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools."""
        return [
            {
                "name": "create_invoice",
                "description": "Create a customer invoice in Odoo",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "partner_name": {
                            "type": "string",
                            "description": "Customer name",
                        },
                        "partner_email": {
                            "type": "string",
                            "description": "Customer email",
                        },
                        "invoice_lines": {
                            "type": "array",
                            "description": "Invoice line items",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "product_name": {"type": "string"},
                                    "quantity": {"type": "number"},
                                    "price_unit": {"type": "number"},
                                    "description": {"type": "string"},
                                },
                                "required": ["product_name", "quantity", "price_unit"],
                            },
                        },
                    },
                    "required": ["partner_name", "invoice_lines"],
                },
            },
            {
                "name": "register_payment",
                "description": "Register a payment for an invoice",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "invoice_id": {
                            "type": "integer",
                            "description": "Invoice ID",
                        },
                        "amount": {
                            "type": "number",
                            "description": "Payment amount",
                        },
                        "payment_date": {
                            "type": "string",
                            "description": "Payment date (YYYY-MM-DD)",
                        },
                        "journal_name": {
                            "type": "string",
                            "description": "Payment journal name (e.g., 'Bank')",
                        },
                    },
                    "required": ["invoice_id", "amount"],
                },
            },
            {
                "name": "create_expense",
                "description": "Create an expense entry in Odoo",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Expense description",
                        },
                        "amount": {
                            "type": "number",
                            "description": "Expense amount",
                        },
                        "date": {
                            "type": "string",
                            "description": "Expense date (YYYY-MM-DD)",
                        },
                        "category": {
                            "type": "string",
                            "description": "Expense category",
                        },
                    },
                    "required": ["name", "amount"],
                },
            },
            {
                "name": "get_partner",
                "description": "Get partner (customer/supplier) by name or email",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Partner name",
                        },
                        "email": {
                            "type": "string",
                            "description": "Partner email",
                        },
                    },
                },
            },
            {
                "name": "list_invoices",
                "description": "List invoices with optional filters",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "state": {
                            "type": "string",
                            "description": "Invoice state (draft, posted, cancel)",
                        },
                        "partner_name": {
                            "type": "string",
                            "description": "Filter by partner name",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                        },
                    },
                },
            },
        ]

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool by name."""
        try:
            if name == "create_invoice":
                return self.create_invoice(arguments)
            elif name == "register_payment":
                return self.register_payment(arguments)
            elif name == "create_expense":
                return self.create_expense(arguments)
            elif name == "get_partner":
                return self.get_partner(arguments)
            elif name == "list_invoices":
                return self.list_invoices(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")

        except Exception as e:
            logger.error(f"Error calling tool {name}: {e}")
            return {
                "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                "isError": True,
            }

    def create_invoice(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a customer invoice."""
        partner_name = args["partner_name"]
        partner_email = args.get("partner_email")
        invoice_lines = args["invoice_lines"]

        # Find or create partner
        Partner = self.odoo.env["res.partner"]
        partner_ids = Partner.search([("name", "=", partner_name)])

        if not partner_ids:
            # Create partner
            partner_id = Partner.create({
                "name": partner_name,
                "email": partner_email,
                "customer_rank": 1,
            })
        else:
            partner_id = partner_ids[0]

        # Create invoice
        Invoice = self.odoo.env["account.move"]

        # Prepare invoice lines
        line_data = []
        for line in invoice_lines:
            line_data.append((0, 0, {
                "name": line.get("description", line["product_name"]),
                "quantity": line["quantity"],
                "price_unit": line["price_unit"],
            }))

        invoice_id = Invoice.create({
            "partner_id": partner_id,
            "move_type": "out_invoice",
            "invoice_line_ids": line_data,
        })

        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "invoice_id": invoice_id,
                    "partner_id": partner_id,
                    "message": "Invoice created successfully",
                }),
            }],
        }

    def register_payment(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Register a payment for an invoice."""
        invoice_id = args["invoice_id"]
        amount = args["amount"]
        payment_date = args.get("payment_date")
        journal_name = args.get("journal_name", "Bank")

        # Get invoice
        Invoice = self.odoo.env["account.move"]
        invoice = Invoice.browse(invoice_id)

        # Find journal
        Journal = self.odoo.env["account.journal"]
        journal_ids = Journal.search([("name", "=", journal_name), ("type", "=", "bank")])

        if not journal_ids:
            raise ValueError(f"Journal '{journal_name}' not found")

        # Register payment
        Payment = self.odoo.env["account.payment"]
        payment_id = Payment.create({
            "payment_type": "inbound",
            "partner_type": "customer",
            "partner_id": invoice.partner_id.id,
            "amount": amount,
            "journal_id": journal_ids[0],
            "date": payment_date,
            "ref": f"Payment for {invoice.name}",
        })

        # Reconcile with invoice
        Payment.browse(payment_id).action_post()

        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "payment_id": payment_id,
                    "message": "Payment registered successfully",
                }),
            }],
        }

    def create_expense(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create an expense entry."""
        name = args["name"]
        amount = args["amount"]
        date = args.get("date")
        category = args.get("category", "General")

        # Create expense (using account.move for vendor bill)
        Invoice = self.odoo.env["account.move"]

        # Find or create expense partner
        Partner = self.odoo.env["res.partner"]
        partner_ids = Partner.search([("name", "=", "Expenses")])

        if not partner_ids:
            partner_id = Partner.create({
                "name": "Expenses",
                "supplier_rank": 1,
            })
        else:
            partner_id = partner_ids[0]

        expense_id = Invoice.create({
            "partner_id": partner_id,
            "move_type": "in_invoice",
            "invoice_date": date,
            "invoice_line_ids": [(0, 0, {
                "name": f"{category}: {name}",
                "quantity": 1,
                "price_unit": amount,
            })],
        })

        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "expense_id": expense_id,
                    "message": "Expense created successfully",
                }),
            }],
        }

    def get_partner(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get partner by name or email."""
        name = args.get("name")
        email = args.get("email")

        Partner = self.odoo.env["res.partner"]
        domain = []

        if name:
            domain.append(("name", "ilike", name))
        if email:
            domain.append(("email", "=", email))

        partner_ids = Partner.search(domain, limit=10)
        partners = Partner.read(partner_ids, ["name", "email", "phone"])

        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "partners": partners,
                }),
            }],
        }

    def list_invoices(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List invoices with filters."""
        state = args.get("state")
        partner_name = args.get("partner_name")
        limit = args.get("limit", 10)

        Invoice = self.odoo.env["account.move"]
        domain = [("move_type", "in", ["out_invoice", "in_invoice"])]

        if state:
            domain.append(("state", "=", state))
        if partner_name:
            domain.append(("partner_id.name", "ilike", partner_name))

        invoice_ids = Invoice.search(domain, limit=limit)
        invoices = Invoice.read(invoice_ids, ["name", "partner_id", "amount_total", "state", "invoice_date"])

        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "invoices": invoices,
                }),
            }],
        }


def main():
    """Main entry point."""
    import sys

    server = OdooMCPServer()

    # Simple stdio-based MCP protocol
    for line in sys.stdin:
        try:
            request = json.loads(line)
            method = request.get("method")
            params = request.get("params", {})

            if method == "tools/list":
                response = {"tools": server.list_tools()}
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                response = server.call_tool(tool_name, arguments)
            else:
                response = {"error": f"Unknown method: {method}"}

            print(json.dumps(response))
            sys.stdout.flush()

        except Exception as e:
            logger.error(f"Error processing request: {e}")
            print(json.dumps({"error": str(e)}))
            sys.stdout.flush()


if __name__ == "__main__":
    main()
