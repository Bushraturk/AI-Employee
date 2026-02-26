"""ApprovalRequest model for actions requiring human approval."""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
import frontmatter


class ApprovalType(str, Enum):
    """Types of approval requests."""
    EMAIL_SEND = "email_send"
    SOCIAL_POST = "social_post"
    ACCOUNTING_ENTRY = "accounting_entry"
    WHATSAPP_SEND = "whatsapp_send"
    PAYMENT = "payment"


class ApprovalStatus(str, Enum):
    """Status of an approval request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class RiskLevel(str, Enum):
    """Risk level of an approval request."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalRequest(BaseModel):
    """Model for approval request files in the vault.

    Approval requests represent draft actions that require human approval.
    They follow the naming convention: {action_type}_{target_id}_{timestamp}.md
    """

    # Metadata
    approval_id: str = Field(..., description="Unique identifier for this approval request")
    approval_type: ApprovalType = Field(..., description="Type of approval")
    target_id: str = Field(..., description="Target identifier (e.g., recipient email)")
    timestamp: datetime = Field(..., description="When the request was created")
    status: ApprovalStatus = Field(default=ApprovalStatus.PENDING)

    # Risk assessment
    risk_level: RiskLevel = Field(..., description="Risk level of this action")
    risk_factors: List[str] = Field(default_factory=list, description="Identified risk factors")

    # Content
    title: str = Field(..., description="Human-readable title")
    summary: str = Field(..., description="Brief summary of the action")
    body: str = Field(..., description="Full draft content or action details")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    # Processing
    created_by: str = Field(..., description="Agent that created this request")
    approved_by: Optional[str] = Field(None, description="User who approved/rejected")
    approved_at: Optional[datetime] = Field(None, description="When the decision was made")
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection")

    # Relationships
    action_file_id: str = Field(..., description="Related action file ID")

    # Expiration
    expires_at: datetime = Field(..., description="When this request expires")

    @validator("approval_id")
    def validate_approval_id(cls, v: str) -> str:
        """Validate approval ID format."""
        if not v:
            raise ValueError("approval_id cannot be empty")
        return v

    @classmethod
    def from_file(cls, file_path: str) -> "ApprovalRequest":
        """Load ApprovalRequest from a markdown file with frontmatter.

        Args:
            file_path: Path to the markdown file

        Returns:
            ApprovalRequest instance

        Raises:
            ValueError: If file format is invalid
        """
        with open(file_path, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)

        # Extract frontmatter metadata
        metadata = dict(post.metadata)
        body = post.content

        # Parse datetime fields
        timestamp = datetime.fromisoformat(metadata.pop("timestamp"))
        expires_at = datetime.fromisoformat(metadata.pop("expires_at"))

        approved_at_str = metadata.pop("approved_at", None)
        approved_at = datetime.fromisoformat(approved_at_str) if approved_at_str else None

        return cls(
            approval_id=metadata.pop("approval_id"),
            approval_type=ApprovalType(metadata.pop("approval_type")),
            target_id=metadata.pop("target_id"),
            timestamp=timestamp,
            status=ApprovalStatus(metadata.pop("status", "pending")),
            risk_level=RiskLevel(metadata.pop("risk_level")),
            risk_factors=metadata.pop("risk_factors", []),
            title=metadata.pop("title"),
            summary=metadata.pop("summary"),
            body=body,
            metadata=metadata.pop("metadata", {}),
            created_by=metadata.pop("created_by"),
            approved_by=metadata.pop("approved_by", None),
            approved_at=approved_at,
            rejection_reason=metadata.pop("rejection_reason", None),
            action_file_id=metadata.pop("action_file_id"),
            expires_at=expires_at,
        )

    def to_file(self, file_path: str) -> None:
        """Save ApprovalRequest to a markdown file with frontmatter.

        Args:
            file_path: Path where the file should be saved
        """
        # Prepare frontmatter metadata
        metadata = {
            "approval_id": self.approval_id,
            "approval_type": self.approval_type.value,
            "target_id": self.target_id,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
            "risk_level": self.risk_level.value,
            "risk_factors": self.risk_factors,
            "title": self.title,
            "summary": self.summary,
            "metadata": self.metadata,
            "created_by": self.created_by,
            "action_file_id": self.action_file_id,
            "expires_at": self.expires_at.isoformat(),
        }

        # Add optional fields
        if self.approved_by:
            metadata["approved_by"] = self.approved_by
        if self.approved_at:
            metadata["approved_at"] = self.approved_at.isoformat()
        if self.rejection_reason:
            metadata["rejection_reason"] = self.rejection_reason

        # Create frontmatter post
        post = frontmatter.Post(self.body, **metadata)

        # Write to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

    def get_filename(self) -> str:
        """Generate filename for this approval request.

        Returns:
            Filename in format: {action_type}_{target_id}_{timestamp}.md
        """
        timestamp_str = self.timestamp.strftime("%Y%m%dT%H%M%SZ")
        # Sanitize target_id for filename
        safe_target = self.target_id.replace("@", "_at_").replace(".", "_")
        return f"{self.approval_type.value}_{safe_target}_{timestamp_str}.md"

    def is_expired(self) -> bool:
        """Check if this approval request has expired.

        Returns:
            True if expired, False otherwise
        """
        return datetime.now() > self.expires_at

    class Config:
        """Pydantic configuration."""
        use_enum_values = False
