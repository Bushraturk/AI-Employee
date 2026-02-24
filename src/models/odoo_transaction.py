"""OdooTransaction entity model for Gold Tier.

Represents financial records synced bidirectionally with Odoo accounting system.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Optional
import frontmatter
import uuid


class TransactionType(Enum):
    """Transaction type categories."""
    INVOICE = "invoice"
    EXPENSE = "expense"
    PAYMENT = "payment"
    JOURNAL_ENTRY = "journal_entry"


class SyncStatus(Enum):
    """Sync status states."""
    PENDING = "pending"
    SYNCED = "synced"
    CONFLICT = "conflict"
    FAILED = "failed"


@dataclass
class OdooTransaction:
    """Odoo transaction entity for bidirectional financial sync.

    Storage: AI_Employee_Vault/Accounting/transactions/{transaction_id}.md
    """

    transaction_id: str
    type: TransactionType
    amount: Decimal
    currency: str
    date: date
    category: str
    sync_status: SyncStatus
    conflict_flag: bool = False
    customer_vendor: Optional[str] = None
    odoo_id: Optional[int] = None
    last_synced_at: Optional[datetime] = None
    conflict_details: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate entity after initialization."""
        # Amount must be positive
        if self.amount <= 0:
            raise ValueError("Amount must be positive")

        # Date cannot be in future
        if self.date > date.today():
            raise ValueError("Date cannot be in future")

        # If odoo_id is set, sync_status cannot be pending
        if self.odoo_id is not None and self.sync_status == SyncStatus.PENDING:
            raise ValueError("If odoo_id is set, sync_status cannot be pending")

        # If conflict_flag is true, conflict_details must be set
        if self.conflict_flag and not self.conflict_details:
            raise ValueError("If conflict_flag is true, conflict_details must be set")

        # Validate currency code (ISO 4217)
        if len(self.currency) != 3 or not self.currency.isupper():
            raise ValueError("Currency must be 3-letter ISO 4217 code (e.g., USD, EUR)")

        # Validate customer_vendor length
        if self.customer_vendor and len(self.customer_vendor) > 200:
            raise ValueError("customer_vendor must be max 200 chars")

        # Validate conflict_details length
        if self.conflict_details and len(self.conflict_details) > 500:
            raise ValueError("conflict_details must be max 500 chars")

    @classmethod
    def create(cls, type: TransactionType, amount: Decimal, currency: str,
               date: date, category: str, customer_vendor: Optional[str] = None) -> "OdooTransaction":
        """Create a new OdooTransaction entity."""
        return cls(
            transaction_id=str(uuid.uuid4()),
            type=type,
            amount=amount,
            currency=currency,
            date=date,
            category=category,
            customer_vendor=customer_vendor,
            sync_status=SyncStatus.PENDING,
            conflict_flag=False
        )

    def mark_synced(self, odoo_id: int) -> None:
        """Mark transaction as synced to Odoo."""
        self.sync_status = SyncStatus.SYNCED
        self.odoo_id = odoo_id
        self.last_synced_at = datetime.now()
        self.updated_at = datetime.now()

    def mark_conflict(self, conflict_details: str) -> None:
        """Mark transaction as having sync conflict."""
        self.sync_status = SyncStatus.CONFLICT
        self.conflict_flag = True
        self.conflict_details = conflict_details[:500]  # Truncate to 500 chars
        self.updated_at = datetime.now()

    def mark_failed(self) -> None:
        """Mark transaction sync as failed."""
        self.sync_status = SyncStatus.FAILED
        self.updated_at = datetime.now()

    def resolve_conflict(self) -> None:
        """Resolve conflict and mark as synced."""
        self.sync_status = SyncStatus.SYNCED
        self.conflict_flag = False
        self.conflict_details = None
        self.last_synced_at = datetime.now()
        self.updated_at = datetime.now()

    def to_markdown(self) -> str:
        """Convert entity to Markdown format."""
        metadata = {
            "transaction_id": self.transaction_id,
            "type": self.type.value,
            "amount": float(self.amount),
            "currency": self.currency,
            "date": self.date.isoformat(),
            "customer_vendor": self.customer_vendor,
            "category": self.category,
            "odoo_id": self.odoo_id,
            "sync_status": self.sync_status.value,
            "last_synced_at": self.last_synced_at.isoformat() if self.last_synced_at else None,
            "conflict_flag": self.conflict_flag,
            "conflict_details": self.conflict_details,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

        # Build title based on transaction type
        if self.type == TransactionType.INVOICE:
            title = f"Invoice: {self.customer_vendor or 'Unknown'}"
        elif self.type == TransactionType.EXPENSE:
            title = f"Expense: {self.category}"
        elif self.type == TransactionType.PAYMENT:
            title = f"Payment: {self.customer_vendor or 'Unknown'}"
        else:
            title = f"Journal Entry: {self.category}"

        # Build sync history
        sync_history = "## Sync History\n"
        if self.last_synced_at:
            sync_history += f"- {self.last_synced_at.strftime('%Y-%m-%d %H:%M:%S')} - Synced to Odoo successfully\n"
        sync_history += f"- {self.created_at.strftime('%Y-%m-%d %H:%M:%S')} - Created in vault\n"

        # Build conflict section if applicable
        conflict_section = ""
        if self.conflict_flag and self.conflict_details:
            conflict_section = f"\n## Conflict Details\n\n⚠️ **Sync Conflict Detected**\n\n{self.conflict_details}\n"

        body = f"""# {title}

**Amount**: {self.currency} {self.amount:,.2f}
**Date**: {self.date.isoformat()}
**Status**: {self.sync_status.value.title()}{f" (Odoo ID: {self.odoo_id})" if self.odoo_id else ""}
**Category**: {self.category}
{f"**Customer/Vendor**: {self.customer_vendor}" if self.customer_vendor else ""}

## Description

{self.type.value.replace('_', ' ').title()} transaction for {self.currency} {self.amount:,.2f}.
{conflict_section}
{sync_history}
"""

        post = frontmatter.Post(body, **metadata)
        return frontmatter.dumps(post)

    @classmethod
    def from_markdown(cls, content: str) -> "OdooTransaction":
        """Parse OdooTransaction from Markdown file."""
        post = frontmatter.loads(content)

        return cls(
            transaction_id=post["transaction_id"],
            type=TransactionType(post["type"]),
            amount=Decimal(str(post["amount"])),
            currency=post["currency"],
            date=date.fromisoformat(post["date"]),
            customer_vendor=post.get("customer_vendor"),
            category=post["category"],
            odoo_id=post.get("odoo_id"),
            sync_status=SyncStatus(post["sync_status"]),
            last_synced_at=datetime.fromisoformat(post["last_synced_at"]) if post.get("last_synced_at") else None,
            conflict_flag=post["conflict_flag"],
            conflict_details=post.get("conflict_details"),
            created_at=datetime.fromisoformat(post["created_at"]),
            updated_at=datetime.fromisoformat(post["updated_at"])
        )

    def save(self, vault_path: Path) -> Path:
        """Save entity to vault."""
        transaction_dir = vault_path / "Accounting" / "transactions"
        transaction_dir.mkdir(parents=True, exist_ok=True)

        file_path = transaction_dir / f"{self.transaction_id}.md"
        file_path.write_text(self.to_markdown(), encoding="utf-8")

        return file_path

    @classmethod
    def load(cls, vault_path: Path, transaction_id: str) -> "OdooTransaction":
        """Load entity from vault."""
        file_path = vault_path / "Accounting" / "transactions" / f"{transaction_id}.md"

        if not file_path.exists():
            raise FileNotFoundError(f"OdooTransaction {transaction_id} not found")

        content = file_path.read_text(encoding="utf-8")
        return cls.from_markdown(content)

    @classmethod
    def find_by_odoo_id(cls, vault_path: Path, odoo_id: int) -> Optional["OdooTransaction"]:
        """Find transaction by Odoo ID.

        Args:
            vault_path: Path to vault
            odoo_id: Odoo record ID

        Returns:
            OdooTransaction if found, None otherwise
        """
        transaction_dir = vault_path / "Accounting" / "transactions"
        if not transaction_dir.exists():
            return None

        for transaction_file in transaction_dir.glob("*.md"):
            try:
                content = transaction_file.read_text(encoding="utf-8")
                post = frontmatter.loads(content)

                if post.get("odoo_id") == odoo_id:
                    return cls.from_markdown(content)

            except Exception:
                continue

        return None
