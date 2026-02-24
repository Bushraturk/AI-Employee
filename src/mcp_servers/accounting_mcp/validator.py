"""Validation Logic for Odoo Transactions.

Validates transaction data before syncing to Odoo.
"""

import logging
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional

from src.models.odoo_transaction import OdooTransaction, TransactionType

logger = logging.getLogger(__name__)


class TransactionValidator:
    """Validates transaction data before syncing to Odoo.

    Validation rules:
    - Required fields must be present
    - Amounts must be positive
    - Dates must be valid (not in future)
    - Currency codes must be valid ISO 4217
    - Categories must be mapped
    """

    def __init__(self, category_mapper=None):
        """Initialize validator.

        Args:
            category_mapper: CategoryMapper instance for category validation
        """
        self.category_mapper = category_mapper

        # Valid ISO 4217 currency codes (common ones)
        self.valid_currencies = {
            'USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD',
            'CNY', 'INR', 'BRL', 'MXN', 'ZAR', 'SEK', 'NOK', 'DKK'
        }

    def validate_transaction(self, transaction: OdooTransaction) -> Dict[str, any]:
        """Validate a transaction before syncing.

        Args:
            transaction: Transaction to validate

        Returns:
            Dictionary with validation results:
            {
                "valid": bool,
                "errors": List[str],
                "warnings": List[str]
            }
        """
        errors = []
        warnings = []

        # Validate required fields
        if not transaction.transaction_id:
            errors.append("transaction_id is required")

        if not transaction.type:
            errors.append("type is required")

        if not transaction.amount:
            errors.append("amount is required")
        elif transaction.amount <= 0:
            errors.append("amount must be positive")

        if not transaction.currency:
            errors.append("currency is required")
        elif transaction.currency not in self.valid_currencies:
            warnings.append(f"currency '{transaction.currency}' may not be valid ISO 4217 code")

        if not transaction.date:
            errors.append("date is required")
        elif transaction.date > date.today():
            errors.append("date cannot be in future")

        if not transaction.category:
            errors.append("category is required")
        elif self.category_mapper and not self.category_mapper.validate_category(transaction.category):
            warnings.append(f"category '{transaction.category}' has no account mapping")

        # Validate customer/vendor for invoices and expenses
        if transaction.type in [TransactionType.INVOICE, TransactionType.EXPENSE]:
            if not transaction.customer_vendor:
                warnings.append("customer_vendor is recommended for invoices and expenses")

        # Validate sync status consistency
        if transaction.odoo_id and transaction.sync_status.value == "pending":
            errors.append("transaction with odoo_id cannot have pending sync status")

        # Validate conflict flag consistency
        if transaction.conflict_flag and not transaction.conflict_details:
            errors.append("conflict_flag requires conflict_details")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    def validate_amount(self, amount: Decimal) -> bool:
        """Validate transaction amount.

        Args:
            amount: Amount to validate

        Returns:
            True if valid
        """
        if amount <= 0:
            return False

        # Check decimal places (max 2)
        if amount.as_tuple().exponent < -2:
            return False

        return True

    def validate_date(self, transaction_date: date) -> bool:
        """Validate transaction date.

        Args:
            transaction_date: Date to validate

        Returns:
            True if valid
        """
        if transaction_date > date.today():
            return False

        # Check if date is too old (more than 10 years)
        from datetime import timedelta
        ten_years_ago = date.today() - timedelta(days=3650)

        if transaction_date < ten_years_ago:
            logger.warning(f"Transaction date is very old: {transaction_date}")

        return True

    def validate_currency(self, currency: str) -> bool:
        """Validate currency code.

        Args:
            currency: Currency code to validate

        Returns:
            True if valid
        """
        if len(currency) != 3:
            return False

        if not currency.isupper():
            return False

        if currency not in self.valid_currencies:
            logger.warning(f"Currency code may be invalid: {currency}")

        return True

    def validate_category(self, category: str) -> bool:
        """Validate category.

        Args:
            category: Category to validate

        Returns:
            True if valid
        """
        if not category:
            return False

        if len(category) > 200:
            return False

        if self.category_mapper:
            return self.category_mapper.validate_category(category)

        return True

    def validate_customer_vendor(self, customer_vendor: Optional[str]) -> bool:
        """Validate customer/vendor name.

        Args:
            customer_vendor: Customer/vendor name to validate

        Returns:
            True if valid
        """
        if customer_vendor is None:
            return True  # Optional field

        if len(customer_vendor) > 200:
            return False

        if len(customer_vendor.strip()) == 0:
            return False

        return True

    def get_validation_summary(self, transaction: OdooTransaction) -> str:
        """Get human-readable validation summary.

        Args:
            transaction: Transaction to validate

        Returns:
            Validation summary string
        """
        result = self.validate_transaction(transaction)

        if result["valid"]:
            summary = f"✓ Transaction {transaction.transaction_id} is valid"

            if result["warnings"]:
                summary += f"\n⚠ Warnings: {', '.join(result['warnings'])}"

            return summary
        else:
            summary = f"✗ Transaction {transaction.transaction_id} is invalid"
            summary += f"\n  Errors: {', '.join(result['errors'])}"

            if result["warnings"]:
                summary += f"\n  Warnings: {', '.join(result['warnings'])}"

            return summary
