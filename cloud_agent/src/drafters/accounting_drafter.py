"""Accounting drafter for cloud agent.

Analyzes bank transactions and drafts Odoo accounting entries.
Writes drafts to Pending_Approval/accounting/ for human review.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path
from decimal import Decimal

from shared.models.action_file import ActionFile
from shared.models.approval_request import ApprovalRequest, ApprovalType, ApprovalStatus, RiskLevel
from shared.utils.vault_manager import VaultManager
from shared.utils.logger import VaultLogger, LogCategory
from shared.risk_assessor import RiskAssessor
from src.models.odoo_transaction import OdooTransaction, TransactionType, SyncStatus


logger = logging.getLogger(__name__)


class AccountingDrafter:
    """Drafts accounting entries for Odoo integration.

    Analyzes bank transactions and generates appropriate Odoo entries
    based on company handbook and business rules.
    """

    def __init__(
        self,
        agent_id: str,
        vault_manager: VaultManager,
        vault_logger: VaultLogger,
        company_handbook_path: str,
    ):
        """Initialize accounting drafter.

        Args:
            agent_id: Agent ID
            vault_manager: Vault manager instance
            vault_logger: Vault logger instance
            company_handbook_path: Path to company handbook
        """
        self.agent_id = agent_id
        self.vault_manager = vault_manager
        self.vault_logger = vault_logger
        self.company_handbook_path = company_handbook_path

        # Initialize risk assessor
        self.risk_assessor = RiskAssessor()

        # Load company handbook
        self.company_handbook = self._load_company_handbook()

        # Load category mappings
        self.category_mappings = self._load_category_mappings()

        logger.info("Accounting drafter initialized")

    def _load_company_handbook(self) -> str:
        """Load company handbook content.

        Returns:
            Company handbook content
        """
        try:
            handbook_path = Path(self.company_handbook_path)
            if handbook_path.exists():
                with open(handbook_path, "r", encoding="utf-8") as f:
                    return f.read()
            else:
                logger.warning(f"Company handbook not found: {self.company_handbook_path}")
                return ""
        except Exception as e:
            logger.error(f"Failed to load company handbook: {e}")
            return ""

    def _load_category_mappings(self) -> Dict[str, str]:
        """Load category mappings from company handbook.

        Returns:
            Dictionary mapping transaction descriptions to categories
        """
        # Default category mappings
        # In production, these would be extracted from Company_Handbook
        return {
            "office supplies": "Office Expenses",
            "software": "Software & Subscriptions",
            "hosting": "Software & Subscriptions",
            "advertising": "Marketing & Advertising",
            "consulting": "Professional Services",
            "salary": "Payroll",
            "rent": "Rent & Utilities",
            "utilities": "Rent & Utilities",
            "travel": "Travel & Entertainment",
            "meals": "Travel & Entertainment",
            "insurance": "Insurance",
            "legal": "Legal & Compliance",
            "bank": "Bank Fees",
            "interest": "Interest Expense",
            "revenue": "Revenue",
            "sales": "Revenue",
            "payment": "Accounts Receivable",
        }

    def draft_entry(self, action: ActionFile) -> Optional[ApprovalRequest]:
        """Draft accounting entry for a transaction.

        Args:
            action: Action file representing bank transaction

        Returns:
            ApprovalRequest instance or None if drafting failed
        """
        try:
            self.vault_logger.info(
                LogCategory.AGENT,
                f"Drafting accounting entry for action: {action.action_id}",
                details={"action_id": action.action_id}
            )

            # Extract transaction metadata
            transaction_id = action.metadata.get("transaction_id")
            date = action.metadata.get("date")
            description = action.metadata.get("description", "")
            amount = Decimal(str(action.metadata.get("amount", 0)))
            currency = action.metadata.get("currency", "USD")
            transaction_type = action.metadata.get("type", "expense")
            customer_vendor = action.metadata.get("customer_vendor")

            # Categorize transaction
            category = self._categorize_transaction(description, transaction_type)

            # Match to existing invoices if applicable
            matched_invoice = self._match_to_invoice(description, amount, customer_vendor)

            # Create OdooTransaction entity
            odoo_transaction = OdooTransaction.create(
                type=self._map_transaction_type(transaction_type),
                amount=amount,
                currency=currency,
                date=datetime.fromisoformat(date).date() if isinstance(date, str) else date,
                category=category,
                customer_vendor=customer_vendor,
            )

            # Generate draft entry details
            draft_details = self._generate_draft_details(
                odoo_transaction,
                description,
                matched_invoice,
            )

            # Assess risk
            risk_level, risk_factors = self._assess_accounting_risk(
                odoo_transaction,
                matched_invoice,
            )

            # Create approval request
            approval_id = f"accounting_approval_{action.action_id}_{datetime.now().strftime('%Y%m%dT%H%M%SZ')}"

            approval = ApprovalRequest(
                approval_id=approval_id,
                approval_type=ApprovalType.ACCOUNTING_ENTRY,
                target_id=transaction_id,
                timestamp=datetime.now(),
                status=ApprovalStatus.PENDING,
                risk_level=risk_level,
                risk_factors=risk_factors,
                title=f"Accounting Entry: {category} - {currency} {amount:.2f}",
                summary=f"Draft Odoo entry for {transaction_type}: {description[:100]}",
                body=draft_details,
                metadata={
                    "transaction_id": transaction_id,
                    "odoo_transaction_id": odoo_transaction.transaction_id,
                    "date": date,
                    "description": description,
                    "amount": float(amount),
                    "currency": currency,
                    "type": transaction_type,
                    "category": category,
                    "customer_vendor": customer_vendor,
                    "matched_invoice": matched_invoice,
                },
                created_by=self.agent_id,
                action_file_id=action.action_id,
                expires_at=datetime.now() + timedelta(hours=48),  # 48 hours for accounting
            )

            # Save OdooTransaction to vault
            vault_path = Path(self.vault_manager.vault_root)
            odoo_transaction.save(vault_path)

            # Write approval request to vault
            approval_folder = "Pending_Approval/accounting"
            approval_path = self.vault_manager.get_folder_path(approval_folder) / approval.get_filename()
            approval.to_file(str(approval_path))

            self.vault_logger.info(
                LogCategory.AGENT,
                f"Created accounting approval request: {approval_id}",
                details={
                    "approval_id": approval_id,
                    "transaction_id": transaction_id,
                    "amount": float(amount),
                    "category": category,
                    "risk_level": risk_level.value,
                }
            )

            # Write update for dashboard
            self._write_dashboard_update(action, approval, odoo_transaction)

            return approval

        except Exception as e:
            self.vault_logger.error(
                LogCategory.AGENT,
                f"Failed to draft accounting entry: {e}",
                error_type=type(e).__name__,
                stack_trace=str(e),
            )
            return None

    def _categorize_transaction(self, description: str, transaction_type: str) -> str:
        """Categorize transaction based on description.

        Args:
            description: Transaction description
            transaction_type: Transaction type (expense, payment, etc.)

        Returns:
            Category name
        """
        description_lower = description.lower()

        # Check category mappings
        for keyword, category in self.category_mappings.items():
            if keyword in description_lower:
                return category

        # Default categories by type
        if transaction_type == "expense":
            return "General Expenses"
        elif transaction_type == "payment":
            return "Accounts Receivable"
        else:
            return "Uncategorized"

    def _match_to_invoice(
        self,
        description: str,
        amount: Decimal,
        customer_vendor: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        """Match transaction to existing invoice.

        Args:
            description: Transaction description
            amount: Transaction amount
            customer_vendor: Customer or vendor name

        Returns:
            Matched invoice details or None
        """
        # For MVP, return None
        # In production, this would search for matching invoices in Odoo
        # based on amount, customer/vendor, and date range
        return None

    def _map_transaction_type(self, transaction_type: str) -> TransactionType:
        """Map transaction type string to TransactionType enum.

        Args:
            transaction_type: Transaction type string

        Returns:
            TransactionType enum value
        """
        type_mapping = {
            "invoice": TransactionType.INVOICE,
            "expense": TransactionType.EXPENSE,
            "payment": TransactionType.PAYMENT,
            "journal_entry": TransactionType.JOURNAL_ENTRY,
        }

        return type_mapping.get(transaction_type, TransactionType.EXPENSE)

    def _generate_draft_details(
        self,
        odoo_transaction: OdooTransaction,
        description: str,
        matched_invoice: Optional[Dict[str, Any]],
    ) -> str:
        """Generate draft entry details for approval.

        Args:
            odoo_transaction: OdooTransaction entity
            description: Original transaction description
            matched_invoice: Matched invoice details if any

        Returns:
            Draft details as markdown
        """
        draft = f"""# Accounting Entry Draft

## Transaction Details

**Type**: {odoo_transaction.type.value.replace('_', ' ').title()}
**Amount**: {odoo_transaction.currency} {odoo_transaction.amount:,.2f}
**Date**: {odoo_transaction.date.isoformat()}
**Category**: {odoo_transaction.category}
**Customer/Vendor**: {odoo_transaction.customer_vendor or 'N/A'}

**Description**: {description}

## Odoo Entry

This transaction will be recorded in Odoo with the following details:

- **Account**: {self._get_account_for_category(odoo_transaction.category)}
- **Journal**: {self._get_journal_for_type(odoo_transaction.type)}
- **Reference**: {odoo_transaction.transaction_id}

"""

        if matched_invoice:
            draft += f"""## Matched Invoice

This transaction matches an existing invoice:

- **Invoice Number**: {matched_invoice.get('number')}
- **Invoice Amount**: {matched_invoice.get('amount')}
- **Customer**: {matched_invoice.get('customer')}

The payment will be automatically applied to this invoice.

"""

        draft += """## Action Required

Please review the transaction details and approve to post to Odoo.

**Note**: Once approved, this entry will be synced to your Odoo accounting system.
"""

        return draft

    def _get_account_for_category(self, category: str) -> str:
        """Get Odoo account code for category.

        Args:
            category: Transaction category

        Returns:
            Account code or description
        """
        # Default account mappings
        # In production, these would be loaded from Odoo chart of accounts
        account_mapping = {
            "Office Expenses": "6100 - Office Expenses",
            "Software & Subscriptions": "6200 - Software & IT",
            "Marketing & Advertising": "6300 - Marketing",
            "Professional Services": "6400 - Professional Fees",
            "Payroll": "6500 - Payroll Expenses",
            "Rent & Utilities": "6600 - Rent & Utilities",
            "Travel & Entertainment": "6700 - Travel & Entertainment",
            "Insurance": "6800 - Insurance",
            "Legal & Compliance": "6900 - Legal & Compliance",
            "Bank Fees": "7000 - Bank Charges",
            "Interest Expense": "7100 - Interest Expense",
            "Revenue": "4000 - Revenue",
            "Accounts Receivable": "1200 - Accounts Receivable",
            "General Expenses": "6000 - General Expenses",
            "Uncategorized": "6999 - Uncategorized",
        }

        return account_mapping.get(category, "6999 - Uncategorized")

    def _get_journal_for_type(self, transaction_type: TransactionType) -> str:
        """Get Odoo journal for transaction type.

        Args:
            transaction_type: Transaction type

        Returns:
            Journal name
        """
        journal_mapping = {
            TransactionType.INVOICE: "Sales Journal",
            TransactionType.EXPENSE: "Purchase Journal",
            TransactionType.PAYMENT: "Bank Journal",
            TransactionType.JOURNAL_ENTRY: "Miscellaneous Journal",
        }

        return journal_mapping.get(transaction_type, "General Journal")

    def _assess_accounting_risk(
        self,
        odoo_transaction: OdooTransaction,
        matched_invoice: Optional[Dict[str, Any]],
    ) -> tuple[RiskLevel, list[str]]:
        """Assess risk level for accounting entry.

        Args:
            odoo_transaction: OdooTransaction entity
            matched_invoice: Matched invoice details if any

        Returns:
            Tuple of (risk_level, risk_factors)
        """
        risk_factors = []
        risk_level = RiskLevel.LOW

        # High amount threshold
        if odoo_transaction.amount > Decimal("10000"):
            risk_factors.append("High transaction amount (>$10,000)")
            risk_level = RiskLevel.HIGH

        # Medium amount threshold
        elif odoo_transaction.amount > Decimal("1000"):
            risk_factors.append("Medium transaction amount (>$1,000)")
            risk_level = RiskLevel.MEDIUM

        # Uncategorized transactions
        if odoo_transaction.category in ["Uncategorized", "General Expenses"]:
            risk_factors.append("Transaction not automatically categorized")
            if risk_level == RiskLevel.LOW:
                risk_level = RiskLevel.MEDIUM

        # No matched invoice for payment
        if odoo_transaction.type == TransactionType.PAYMENT and not matched_invoice:
            risk_factors.append("Payment not matched to existing invoice")
            if risk_level == RiskLevel.LOW:
                risk_level = RiskLevel.MEDIUM

        # Missing customer/vendor
        if not odoo_transaction.customer_vendor:
            risk_factors.append("No customer/vendor specified")

        return risk_level, risk_factors

    def _write_dashboard_update(
        self,
        action: ActionFile,
        approval: ApprovalRequest,
        odoo_transaction: OdooTransaction,
    ) -> None:
        """Write update for dashboard merger.

        Args:
            action: Original action file
            approval: Created approval request
            odoo_transaction: Created OdooTransaction entity
        """
        try:
            update_folder = "Updates"
            update_filename = f"accounting_draft_{datetime.now().strftime('%Y%m%dT%H%M%SZ')}.md"
            update_path = self.vault_manager.get_folder_path(update_folder) / update_filename

            update_content = f"""---
type: accounting_draft
timestamp: {datetime.now().isoformat()}
action_id: {action.action_id}
approval_id: {approval.approval_id}
transaction_id: {odoo_transaction.transaction_id}
---

# Accounting Entry Draft Created

**Type**: {odoo_transaction.type.value.replace('_', ' ').title()}
**Amount**: {odoo_transaction.currency} {odoo_transaction.amount:,.2f}
**Category**: {odoo_transaction.category}
**Risk Level**: {approval.risk_level.value}

Draft accounting entry created and awaiting approval in `Pending_Approval/accounting/`.
"""

            with open(update_path, "w", encoding="utf-8") as f:
                f.write(update_content)

        except Exception as e:
            logger.error(f"Failed to write dashboard update: {e}")
