"""Finance Watcher for local agent.

Monitors bank transactions and creates action files for processing.
Runs every 5 minutes to check for new financial transactions.
"""

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from decimal import Decimal

from shared.models.action_file import ActionFile, ActionType, ActionStatus
from shared.utils.vault_manager import VaultManager
from shared.utils.logger import VaultLogger, LogCategory


logger = logging.getLogger(__name__)


class FinanceWatcher:
    """Monitors bank transactions and creates action files.

    This watcher checks for new bank transactions (from CSV imports, API feeds, etc.)
    and creates action files for the cloud agent to process.
    """

    def __init__(
        self,
        agent_id: str,
        vault_manager: VaultManager,
        vault_logger: VaultLogger,
        check_interval_seconds: int = 300,  # 5 minutes
    ):
        """Initialize finance watcher.

        Args:
            agent_id: Agent ID
            vault_manager: Vault manager instance
            vault_logger: Vault logger instance
            check_interval_seconds: How often to check for new transactions (default: 300s = 5 min)
        """
        self.agent_id = agent_id
        self.vault_manager = vault_manager
        self.vault_logger = vault_logger
        self.check_interval_seconds = check_interval_seconds

        self.is_running = False
        self.last_check_time: Optional[datetime] = None
        self.processed_transaction_ids: set = set()

        logger.info("Finance watcher initialized")

    def start(self) -> None:
        """Start monitoring bank transactions."""
        self.vault_logger.info(
            LogCategory.WATCHER,
            "Starting finance watcher",
            details={"check_interval": self.check_interval_seconds}
        )

        self.is_running = True
        self.last_check_time = datetime.now()

        logger.info("Finance watcher started")

    def stop(self) -> None:
        """Stop monitoring bank transactions."""
        self.vault_logger.info(LogCategory.WATCHER, "Stopping finance watcher")

        self.is_running = False

        logger.info("Finance watcher stopped")

    def check(self) -> None:
        """Check for new bank transactions and create action files."""
        if not self.is_running:
            return

        try:
            # Check if it's time to poll
            now = datetime.now()
            if self.last_check_time:
                elapsed = (now - self.last_check_time).total_seconds()
                if elapsed < self.check_interval_seconds:
                    return

            self.vault_logger.info(
                LogCategory.WATCHER,
                "Checking for new bank transactions"
            )

            # Get new transactions
            new_transactions = self._fetch_new_transactions()

            # Create action files for each transaction
            for transaction in new_transactions:
                self._create_action_file(transaction)

            self.last_check_time = now

            if new_transactions:
                self.vault_logger.info(
                    LogCategory.WATCHER,
                    f"Found {len(new_transactions)} new bank transactions",
                    details={"count": len(new_transactions)}
                )

        except Exception as e:
            self.vault_logger.error(
                LogCategory.WATCHER,
                f"Error checking bank transactions: {e}",
                error_type=type(e).__name__,
                stack_trace=str(e),
            )

    def _fetch_new_transactions(self) -> List[Dict[str, Any]]:
        """Fetch new bank transactions from monitoring sources.

        This method checks for:
        1. New CSV files in Accounting/bank_imports/
        2. Transactions from bank API (if configured)
        3. Manual transaction entries in Accounting/pending/

        Returns:
            List of transaction dictionaries
        """
        transactions = []

        # Check for CSV imports
        transactions.extend(self._check_csv_imports())

        # Check for manual entries
        transactions.extend(self._check_manual_entries())

        # Filter out already processed transactions
        new_transactions = [
            t for t in transactions
            if t["transaction_id"] not in self.processed_transaction_ids
        ]

        return new_transactions

    def _check_csv_imports(self) -> List[Dict[str, Any]]:
        """Check for new CSV bank statement imports.

        Returns:
            List of transaction dictionaries from CSV files
        """
        transactions = []

        try:
            import_folder = "Accounting/bank_imports"
            csv_files = self.vault_manager.list_files(import_folder, pattern="*.csv")

            for csv_path in csv_files:
                # Parse CSV and extract transactions
                # For MVP, we'll create a simple parser
                # In production, this would handle various bank CSV formats

                try:
                    import csv
                    with open(csv_path, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            transaction = self._parse_csv_row(row, csv_path)
                            if transaction:
                                transactions.append(transaction)

                    # Move processed CSV to archive
                    archive_folder = "Accounting/bank_imports/processed"
                    self.vault_manager.move_file(csv_path, archive_folder)

                except Exception as e:
                    logger.error(f"Failed to parse CSV {csv_path}: {e}")

        except Exception as e:
            logger.error(f"Failed to check CSV imports: {e}")

        return transactions

    def _check_manual_entries(self) -> List[Dict[str, Any]]:
        """Check for manual transaction entries.

        Returns:
            List of transaction dictionaries from manual entries
        """
        transactions = []

        try:
            pending_folder = "Accounting/pending"
            pending_files = self.vault_manager.list_files(pending_folder, pattern="*.md")

            for file_path in pending_files:
                try:
                    # Parse manual entry markdown file
                    transaction = self._parse_manual_entry(file_path)
                    if transaction:
                        transactions.append(transaction)

                        # Move to processed
                        processed_folder = "Accounting/pending/processed"
                        self.vault_manager.move_file(file_path, processed_folder)

                except Exception as e:
                    logger.error(f"Failed to parse manual entry {file_path}: {e}")

        except Exception as e:
            logger.error(f"Failed to check manual entries: {e}")

        return transactions

    def _parse_csv_row(self, row: Dict[str, str], source_file: Path) -> Optional[Dict[str, Any]]:
        """Parse a CSV row into a transaction dictionary.

        Args:
            row: CSV row as dictionary
            source_file: Source CSV file path

        Returns:
            Transaction dictionary or None if invalid
        """
        try:
            # Common CSV column mappings (adjust based on bank format)
            # This is a simplified parser - production would handle multiple formats

            transaction_id = row.get("Transaction ID") or str(uuid.uuid4())
            date_str = row.get("Date") or row.get("Transaction Date")
            description = row.get("Description") or row.get("Memo", "")
            amount_str = row.get("Amount") or row.get("Debit") or row.get("Credit", "0")

            # Parse amount (handle negative for debits)
            amount = Decimal(amount_str.replace(",", "").replace("$", ""))

            # Determine transaction type
            if amount < 0:
                transaction_type = "expense"
                amount = abs(amount)
            else:
                transaction_type = "payment"  # Incoming payment

            return {
                "transaction_id": transaction_id,
                "date": date_str,
                "description": description,
                "amount": float(amount),
                "currency": "USD",  # Default, should be configurable
                "type": transaction_type,
                "source": "csv_import",
                "source_file": str(source_file),
            }

        except Exception as e:
            logger.error(f"Failed to parse CSV row: {e}")
            return None

    def _parse_manual_entry(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Parse a manual transaction entry file.

        Args:
            file_path: Path to manual entry markdown file

        Returns:
            Transaction dictionary or None if invalid
        """
        try:
            import frontmatter

            with open(file_path, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)

            metadata = post.metadata

            return {
                "transaction_id": metadata.get("transaction_id", str(uuid.uuid4())),
                "date": metadata.get("date"),
                "description": metadata.get("description", ""),
                "amount": float(metadata.get("amount", 0)),
                "currency": metadata.get("currency", "USD"),
                "type": metadata.get("type", "expense"),
                "category": metadata.get("category", "Uncategorized"),
                "customer_vendor": metadata.get("customer_vendor"),
                "source": "manual_entry",
                "source_file": str(file_path),
            }

        except Exception as e:
            logger.error(f"Failed to parse manual entry: {e}")
            return None

    def _create_action_file(self, transaction: Dict[str, Any]) -> None:
        """Create action file for a bank transaction.

        Args:
            transaction: Transaction dictionary
        """
        try:
            action_id = f"accounting_{transaction['transaction_id']}_{datetime.now().strftime('%Y%m%dT%H%M%SZ')}"

            # Create action file
            action = ActionFile(
                action_id=action_id,
                action_type=ActionType.ACCOUNTING_ENTRY,
                status=ActionStatus.NEEDS_ACTION,
                title=f"Bank Transaction: {transaction['description'][:50]}",
                description=f"Process bank transaction: {transaction['type']} of {transaction['currency']} {transaction['amount']:.2f}",
                metadata={
                    "transaction_id": transaction["transaction_id"],
                    "date": transaction["date"],
                    "description": transaction["description"],
                    "amount": transaction["amount"],
                    "currency": transaction["currency"],
                    "type": transaction["type"],
                    "category": transaction.get("category", "Uncategorized"),
                    "customer_vendor": transaction.get("customer_vendor"),
                    "source": transaction["source"],
                    "source_file": transaction.get("source_file"),
                },
                created_by=self.agent_id,
                created_at=datetime.now(),
            )

            # Write to Needs_Action/accounting
            action_folder = "Needs_Action/accounting"
            action_path = self.vault_manager.get_folder_path(action_folder) / action.get_filename()
            action.to_file(str(action_path))

            # Mark as processed
            self.processed_transaction_ids.add(transaction["transaction_id"])

            self.vault_logger.info(
                LogCategory.WATCHER,
                f"Created action file for transaction: {transaction['transaction_id']}",
                details={
                    "action_id": action_id,
                    "transaction_id": transaction["transaction_id"],
                    "amount": transaction["amount"],
                }
            )

        except Exception as e:
            self.vault_logger.error(
                LogCategory.WATCHER,
                f"Failed to create action file for transaction: {e}",
                error_type=type(e).__name__,
                stack_trace=str(e),
            )
