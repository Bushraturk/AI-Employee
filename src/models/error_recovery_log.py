"""ErrorRecoveryLog entity model for Gold Tier.

Tracks error handling and recovery attempts across all external services.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Any
import frontmatter
import uuid


class ErrorType(Enum):
    """Error category types."""
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    VALIDATION = "validation"
    SYSTEM = "system"


class ServiceType(Enum):
    """External service types."""
    ODOO = "odoo"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    GMAIL = "gmail"
    WHATSAPP = "whatsapp"


class RecoveryStrategy(Enum):
    """Recovery strategy types."""
    RETRY = "retry"
    QUEUE = "queue"
    ESCALATE = "escalate"
    DEGRADE = "degrade"


class RecoveryOutcome(Enum):
    """Recovery result types."""
    RECOVERED = "recovered"
    ESCALATED = "escalated"
    QUEUED = "queued"


@dataclass
class ErrorRecoveryLog:
    """Error recovery log entity for comprehensive error tracking.

    Storage: AI_Employee_Vault/Logs/error_recovery/{error_id}.md
    """

    error_id: str
    error_type: ErrorType
    service: ServiceType
    error_message: str
    retry_count: int
    recovery_strategy: RecoveryStrategy
    outcome: RecoveryOutcome
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate entity after initialization."""
        if self.retry_count < 0 or self.retry_count > 3:
            raise ValueError("retry_count must be 0-3 (max 3 retries per FR-051)")

        if self.outcome == RecoveryOutcome.RECOVERED and self.retry_count == 0:
            raise ValueError("Recovered outcome requires retry_count > 0")

        if self.outcome == RecoveryOutcome.ESCALATED and self.retry_count != 3:
            raise ValueError("Escalated outcome requires retry_count = 3")

        if len(self.error_message) > 500:
            raise ValueError("error_message must be max 500 chars")

    @classmethod
    def create(cls, error_type: ErrorType, service: ServiceType, error_message: str,
               retry_count: int, recovery_strategy: RecoveryStrategy,
               outcome: RecoveryOutcome, context: Optional[Dict[str, Any]] = None) -> "ErrorRecoveryLog":
        """Create a new ErrorRecoveryLog entity."""
        return cls(
            error_id=str(uuid.uuid4()),
            error_type=error_type,
            service=service,
            error_message=error_message,
            retry_count=retry_count,
            recovery_strategy=recovery_strategy,
            outcome=outcome,
            timestamp=datetime.now(),
            context=context or {}
        )

    def to_markdown(self) -> str:
        """Convert entity to Markdown format."""
        metadata = {
            "error_id": self.error_id,
            "error_type": self.error_type.value,
            "service": self.service.value,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "recovery_strategy": self.recovery_strategy.value,
            "outcome": self.outcome.value,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context
        }

        # Build recovery timeline
        recovery_timeline = ""
        if "attempt_timestamps" in self.context:
            recovery_timeline = "\n## Recovery Strategy\n\n"
            if self.recovery_strategy == RecoveryStrategy.RETRY:
                recovery_timeline += "Exponential backoff retry:\n"
                for i, ts in enumerate(self.context["attempt_timestamps"], 1):
                    status = "Success" if i == len(self.context["attempt_timestamps"]) and self.outcome == RecoveryOutcome.RECOVERED else "Failed"
                    recovery_timeline += f"{i}. Attempt {i}: {status} ({ts})\n"

        # Build context section
        context_section = "\n## Context\n\n"
        for key, value in self.context.items():
            if key != "attempt_timestamps":
                context_section += f"- **{key.replace('_', ' ').title()}**: {value}\n"

        body = f"""# Error Recovery: {self.service.value.title()} {self.error_type.value.replace('_', ' ').title()}

**Service**: {self.service.value.title()}
**Error Type**: {self.error_type.value.replace('_', ' ').title()}
**Timestamp**: {self.timestamp.strftime("%Y-%m-%d %H:%M:%S")}
**Outcome**: {self.outcome.value.title()}{f" (after {self.retry_count} retries)" if self.retry_count > 0 else ""}

## Error Details

{self.error_message}
{recovery_timeline}
{context_section}
## Lessons Learned

{self._generate_lessons_learned()}
"""

        post = frontmatter.Post(body, **metadata)
        return frontmatter.dumps(post)

    def _generate_lessons_learned(self) -> str:
        """Generate lessons learned based on error pattern."""
        if self.error_type == ErrorType.NETWORK and self.outcome == RecoveryOutcome.RECOVERED:
            return "Network transient errors are common during peak hours. Exponential backoff with 3 retries is effective for recovery."
        elif self.error_type == ErrorType.RATE_LIMIT:
            return "Rate limit exceeded. Consider implementing request throttling or increasing time between API calls."
        elif self.error_type == ErrorType.AUTHENTICATION:
            return "Authentication failure. Verify credentials are up to date and tokens have not expired."
        elif self.outcome == RecoveryOutcome.ESCALATED:
            return "Multiple retry attempts failed. Manual intervention required to resolve underlying issue."
        else:
            return "Error pattern requires further investigation to identify root cause."

    @classmethod
    def from_markdown(cls, content: str) -> "ErrorRecoveryLog":
        """Parse ErrorRecoveryLog from Markdown file."""
        post = frontmatter.loads(content)

        return cls(
            error_id=post["error_id"],
            error_type=ErrorType(post["error_type"]),
            service=ServiceType(post["service"]),
            error_message=post["error_message"],
            retry_count=post["retry_count"],
            recovery_strategy=RecoveryStrategy(post["recovery_strategy"]),
            outcome=RecoveryOutcome(post["outcome"]),
            timestamp=datetime.fromisoformat(post["timestamp"]),
            context=post.get("context", {})
        )

    def save(self, vault_path: Path) -> Path:
        """Save entity to vault."""
        log_dir = vault_path / "Logs" / "error_recovery"
        log_dir.mkdir(parents=True, exist_ok=True)

        file_path = log_dir / f"{self.error_id}.md"
        file_path.write_text(self.to_markdown(), encoding="utf-8")

        return file_path

    @classmethod
    def load(cls, vault_path: Path, error_id: str) -> "ErrorRecoveryLog":
        """Load entity from vault."""
        file_path = vault_path / "Logs" / "error_recovery" / f"{error_id}.md"

        if not file_path.exists():
            raise FileNotFoundError(f"ErrorRecoveryLog {error_id} not found")

        content = file_path.read_text(encoding="utf-8")
        return cls.from_markdown(content)
