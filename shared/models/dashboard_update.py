"""DashboardUpdate model for cloud agent updates."""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import frontmatter


class UpdateType(str, Enum):
    """Type of dashboard update."""
    STATUS = "status"
    METRIC = "metric"
    ALERT = "alert"
    SUMMARY = "summary"


class UpdatePriority(str, Enum):
    """Priority of dashboard update."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class DashboardUpdate(BaseModel):
    """Model for dashboard update files in the vault.

    Dashboard updates are written by the cloud agent to the Updates/ folder.
    The local agent merges them into Dashboard.md and deletes the update files.
    """

    # Metadata
    update_id: str = Field(..., description="Unique identifier for this update")
    update_type: UpdateType = Field(..., description="Type of update")
    priority: UpdatePriority = Field(..., description="Priority of update")
    timestamp: datetime = Field(..., description="When the update was created")

    # Source
    agent_id: str = Field(..., description="Agent that created this update")
    watcher_id: Optional[str] = Field(None, description="Watcher that triggered this update")

    # Content
    title: str = Field(..., description="Update title")
    summary: str = Field(..., description="Brief summary")
    body: str = Field(..., description="Full update content")

    # Metrics (if update_type is METRIC)
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Metric values")

    # Context
    action_ids: List[str] = Field(default_factory=list, description="Related action IDs")
    approval_ids: List[str] = Field(default_factory=list, description="Related approval IDs")

    # Processing
    merged: bool = Field(default=False, description="Whether this update has been merged")
    merged_at: Optional[datetime] = Field(None, description="When the update was merged")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @classmethod
    def from_file(cls, file_path: str) -> "DashboardUpdate":
        """Load DashboardUpdate from a markdown file with frontmatter.

        Args:
            file_path: Path to the markdown file

        Returns:
            DashboardUpdate instance

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

        merged_at_str = metadata.pop("merged_at", None)
        merged_at = datetime.fromisoformat(merged_at_str) if merged_at_str else None

        return cls(
            update_id=metadata.pop("update_id"),
            update_type=UpdateType(metadata.pop("update_type")),
            priority=UpdatePriority(metadata.pop("priority")),
            timestamp=timestamp,
            agent_id=metadata.pop("agent_id"),
            watcher_id=metadata.pop("watcher_id", None),
            title=metadata.pop("title"),
            summary=metadata.pop("summary"),
            body=body,
            metrics=metadata.pop("metrics", {}),
            action_ids=metadata.pop("action_ids", []),
            approval_ids=metadata.pop("approval_ids", []),
            merged=metadata.pop("merged", False),
            merged_at=merged_at,
            metadata=metadata.pop("metadata", {}),
        )

    def to_file(self, file_path: str) -> None:
        """Save DashboardUpdate to a markdown file with frontmatter.

        Args:
            file_path: Path where the file should be saved
        """
        # Prepare frontmatter metadata
        metadata = {
            "update_id": self.update_id,
            "update_type": self.update_type.value,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat(),
            "agent_id": self.agent_id,
            "title": self.title,
            "summary": self.summary,
            "metrics": self.metrics,
            "action_ids": self.action_ids,
            "approval_ids": self.approval_ids,
            "merged": self.merged,
            "metadata": self.metadata,
        }

        # Add optional fields
        if self.watcher_id:
            metadata["watcher_id"] = self.watcher_id
        if self.merged_at:
            metadata["merged_at"] = self.merged_at.isoformat()

        # Create frontmatter post
        post = frontmatter.Post(self.body, **metadata)

        # Write to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

    def get_filename(self) -> str:
        """Generate filename for this dashboard update.

        Returns:
            Filename in format: {priority}_{type}_{timestamp}.md
        """
        timestamp_str = self.timestamp.strftime("%Y%m%dT%H%M%SZ")
        return f"{self.priority.value}_{self.update_type.value}_{timestamp_str}.md"

    def to_dashboard_section(self) -> str:
        """Convert update to a dashboard section.

        Returns:
            Markdown section for Dashboard.md
        """
        section = f"## {self.title}\n\n"
        section += f"**Priority**: {self.priority.value.upper()} | "
        section += f"**Type**: {self.update_type.value} | "
        section += f"**Time**: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        section += f"{self.summary}\n\n"

        if self.metrics:
            section += "### Metrics\n\n"
            for key, value in self.metrics.items():
                section += f"- **{key}**: {value}\n"
            section += "\n"

        section += f"{self.body}\n\n"

        if self.action_ids:
            section += f"**Related Actions**: {', '.join(self.action_ids)}\n\n"

        return section

    class Config:
        """Pydantic configuration."""
        use_enum_values = False
