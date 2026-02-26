"""WatcherState model for tracking watcher status and last sync."""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import frontmatter


class WatcherStatus(str, Enum):
    """Status of a watcher."""
    STARTING = "starting"
    RUNNING = "running"
    IDLE = "idle"
    SYNCING = "syncing"
    ERROR = "error"
    STOPPED = "stopped"


class WatcherType(str, Enum):
    """Type of watcher."""
    GMAIL = "gmail"
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"
    TWITTER = "twitter"
    WHATSAPP = "whatsapp"
    BANK = "bank"
    FILE_DROP = "file_drop"


class WatcherState(BaseModel):
    """Model for watcher state files in the vault.

    Watcher state files track the current status and last sync position.
    Located at: In_Progress/{agent}/watcher_{source}.md
    """

    # Identity
    watcher_id: str = Field(..., description="Unique identifier for this watcher")
    watcher_type: WatcherType = Field(..., description="Type of watcher")
    watcher_name: str = Field(..., description="Human-readable watcher name")
    agent_id: str = Field(..., description="Agent that owns this watcher")

    # Status
    status: WatcherStatus = Field(..., description="Current watcher status")
    last_check: datetime = Field(..., description="Last check timestamp")
    next_check: datetime = Field(..., description="Next scheduled check")
    check_interval_seconds: int = Field(..., description="Check interval in seconds")

    # Sync position
    last_sync_token: Optional[str] = Field(None, description="Last sync token/cursor")
    last_message_id: Optional[str] = Field(None, description="Last processed message ID")
    last_sync_at: Optional[datetime] = Field(None, description="When last sync completed")

    # Statistics
    total_checks: int = Field(default=0, description="Total checks performed")
    events_detected: int = Field(default=0, description="Total events detected")
    events_processed: int = Field(default=0, description="Total events processed")
    errors_count: int = Field(default=0, description="Error count since last reset")

    # Health
    consecutive_errors: int = Field(default=0, description="Consecutive errors")
    last_error: Optional[str] = Field(None, description="Last error message")
    last_error_at: Optional[datetime] = Field(None, description="When the last error occurred")

    # Configuration
    config: Dict[str, Any] = Field(default_factory=dict, description="Watcher configuration")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @classmethod
    def from_file(cls, file_path: str) -> "WatcherState":
        """Load WatcherState from a markdown file with frontmatter.

        Args:
            file_path: Path to the markdown file

        Returns:
            WatcherState instance

        Raises:
            ValueError: If file format is invalid
        """
        with open(file_path, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)

        # Extract frontmatter metadata
        metadata = dict(post.metadata)

        # Parse datetime fields
        last_check = datetime.fromisoformat(metadata.pop("last_check"))
        next_check = datetime.fromisoformat(metadata.pop("next_check"))

        last_sync_at_str = metadata.pop("last_sync_at", None)
        last_sync_at = datetime.fromisoformat(last_sync_at_str) if last_sync_at_str else None

        last_error_at_str = metadata.pop("last_error_at", None)
        last_error_at = datetime.fromisoformat(last_error_at_str) if last_error_at_str else None

        return cls(
            watcher_id=metadata.pop("watcher_id"),
            watcher_type=WatcherType(metadata.pop("watcher_type")),
            watcher_name=metadata.pop("watcher_name"),
            agent_id=metadata.pop("agent_id"),
            status=WatcherStatus(metadata.pop("status")),
            last_check=last_check,
            next_check=next_check,
            check_interval_seconds=metadata.pop("check_interval_seconds"),
            last_sync_token=metadata.pop("last_sync_token", None),
            last_message_id=metadata.pop("last_message_id", None),
            last_sync_at=last_sync_at,
            total_checks=metadata.pop("total_checks", 0),
            events_detected=metadata.pop("events_detected", 0),
            events_processed=metadata.pop("events_processed", 0),
            errors_count=metadata.pop("errors_count", 0),
            consecutive_errors=metadata.pop("consecutive_errors", 0),
            last_error=metadata.pop("last_error", None),
            last_error_at=last_error_at,
            config=metadata.pop("config", {}),
            metadata=metadata.pop("metadata", {}),
        )

    def to_file(self, file_path: str) -> None:
        """Save WatcherState to a markdown file with frontmatter.

        Args:
            file_path: Path where the file should be saved
        """
        # Prepare frontmatter metadata
        metadata = {
            "watcher_id": self.watcher_id,
            "watcher_type": self.watcher_type.value,
            "watcher_name": self.watcher_name,
            "agent_id": self.agent_id,
            "status": self.status.value,
            "last_check": self.last_check.isoformat(),
            "next_check": self.next_check.isoformat(),
            "check_interval_seconds": self.check_interval_seconds,
            "total_checks": self.total_checks,
            "events_detected": self.events_detected,
            "events_processed": self.events_processed,
            "errors_count": self.errors_count,
            "consecutive_errors": self.consecutive_errors,
            "config": self.config,
            "metadata": self.metadata,
        }

        # Add optional fields
        if self.last_sync_token:
            metadata["last_sync_token"] = self.last_sync_token
        if self.last_message_id:
            metadata["last_message_id"] = self.last_message_id
        if self.last_sync_at:
            metadata["last_sync_at"] = self.last_sync_at.isoformat()
        if self.last_error:
            metadata["last_error"] = self.last_error
        if self.last_error_at:
            metadata["last_error_at"] = self.last_error_at.isoformat()

        # Create body with current status summary
        body = f"""# Watcher Status: {self.status.value.upper()}

**Type**: {self.watcher_type.value}
**Check Interval**: {self.check_interval_seconds}s
**Last Check**: {self.last_check.strftime("%Y-%m-%d %H:%M:%S")}
**Next Check**: {self.next_check.strftime("%Y-%m-%d %H:%M:%S")}

## Statistics
- Total Checks: {self.total_checks}
- Events Detected: {self.events_detected}
- Events Processed: {self.events_processed}
- Error Count: {self.errors_count}
- Consecutive Errors: {self.consecutive_errors}

## Sync Position
"""

        if self.last_sync_token:
            body += f"- Last Sync Token: {self.last_sync_token}\n"
        if self.last_message_id:
            body += f"- Last Message ID: {self.last_message_id}\n"
        if self.last_sync_at:
            body += f"- Last Sync: {self.last_sync_at.strftime('%Y-%m-%d %H:%M:%S')}\n"

        if self.last_error:
            body += f"\n## Last Error\n{self.last_error}\n"
            if self.last_error_at:
                body += f"Occurred at: {self.last_error_at.strftime('%Y-%m-%d %H:%M:%S')}\n"

        # Create frontmatter post
        post = frontmatter.Post(body, **metadata)

        # Write to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

    def is_healthy(self) -> bool:
        """Check if watcher is healthy.

        Returns:
            True if healthy, False otherwise
        """
        return (
            self.status != WatcherStatus.ERROR
            and self.consecutive_errors < 5
        )

    def get_filename(self) -> str:
        """Generate filename for this watcher state.

        Returns:
            Filename in format: watcher_{source}.md
        """
        return f"watcher_{self.watcher_type.value}.md"

    class Config:
        """Pydantic configuration."""
        use_enum_values = False
