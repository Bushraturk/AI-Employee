"""ActionFile model for representing detected events in the vault."""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
import frontmatter


class ActionType(str, Enum):
    """Types of actions that can be detected."""
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    TRANSACTION = "transaction"
    FILE_DROP = "file_drop"
    SOCIAL = "social"


class ActionStatus(str, Enum):
    """Status of an action file."""
    NEEDS_ACTION = "needs_action"
    IN_PROGRESS = "in_progress"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    DONE = "done"


class ActionFile(BaseModel):
    """Model for action files in the vault.

    Action files represent detected events that need processing.
    They follow the naming convention: {type}_{source_id}_{timestamp}.md
    """

    # Metadata
    action_id: str = Field(..., description="Unique identifier for this action")
    action_type: ActionType = Field(..., description="Type of action")
    source_id: str = Field(..., description="Source identifier (e.g., email message ID)")
    timestamp: datetime = Field(..., description="When the action was detected")
    status: ActionStatus = Field(default=ActionStatus.NEEDS_ACTION)

    # Content
    title: str = Field(..., description="Human-readable title")
    body: str = Field(..., description="Action body content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    # Processing
    claimed_by: Optional[str] = Field(None, description="Agent that claimed this action")
    claimed_at: Optional[datetime] = Field(None, description="When the action was claimed")
    completed_at: Optional[datetime] = Field(None, description="When the action was completed")

    # Relationships
    approval_request_id: Optional[str] = Field(None, description="Related approval request ID")
    parent_action_id: Optional[str] = Field(None, description="Parent action ID if this is a follow-up")

    @validator("action_id")
    def validate_action_id(cls, v: str) -> str:
        """Validate action ID format."""
        if not v:
            raise ValueError("action_id cannot be empty")
        return v

    @classmethod
    def from_file(cls, file_path: str) -> "ActionFile":
        """Load ActionFile from a markdown file with frontmatter.

        Args:
            file_path: Path to the markdown file

        Returns:
            ActionFile instance

        Raises:
            ValueError: If file format is invalid
        """
        with open(file_path, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)

        # Extract frontmatter metadata
        metadata = dict(post.metadata)
        body = post.content

        # Parse timestamp
        timestamp_str = metadata.pop("timestamp", None)
        timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.now()

        # Parse optional datetime fields
        claimed_at_str = metadata.pop("claimed_at", None)
        claimed_at = datetime.fromisoformat(claimed_at_str) if claimed_at_str else None

        completed_at_str = metadata.pop("completed_at", None)
        completed_at = datetime.fromisoformat(completed_at_str) if completed_at_str else None

        return cls(
            action_id=metadata.pop("action_id"),
            action_type=ActionType(metadata.pop("action_type")),
            source_id=metadata.pop("source_id"),
            timestamp=timestamp,
            status=ActionStatus(metadata.pop("status", "needs_action")),
            title=metadata.pop("title"),
            body=body,
            metadata=metadata.pop("metadata", {}),
            claimed_by=metadata.pop("claimed_by", None),
            claimed_at=claimed_at,
            completed_at=completed_at,
            approval_request_id=metadata.pop("approval_request_id", None),
            parent_action_id=metadata.pop("parent_action_id", None),
        )

    def to_file(self, file_path: str) -> None:
        """Save ActionFile to a markdown file with frontmatter.

        Args:
            file_path: Path where the file should be saved
        """
        # Prepare frontmatter metadata
        metadata = {
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "source_id": self.source_id,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
            "title": self.title,
            "metadata": self.metadata,
        }

        # Add optional fields
        if self.claimed_by:
            metadata["claimed_by"] = self.claimed_by
        if self.claimed_at:
            metadata["claimed_at"] = self.claimed_at.isoformat()
        if self.completed_at:
            metadata["completed_at"] = self.completed_at.isoformat()
        if self.approval_request_id:
            metadata["approval_request_id"] = self.approval_request_id
        if self.parent_action_id:
            metadata["parent_action_id"] = self.parent_action_id

        # Create frontmatter post
        post = frontmatter.Post(self.body, **metadata)

        # Write to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

    def get_filename(self) -> str:
        """Generate filename for this action file.

        Returns:
            Filename in format: {type}_{source_id}_{timestamp}.md
        """
        timestamp_str = self.timestamp.strftime("%Y%m%dT%H%M%SZ")
        return f"{self.action_type.value}_{self.source_id}_{timestamp_str}.md"

    class Config:
        """Pydantic configuration."""
        use_enum_values = False
