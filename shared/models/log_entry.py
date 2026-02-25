"""LogEntry model for audit logging."""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import json


class LogLevel(str, Enum):
    """Log level."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogCategory(str, Enum):
    """Log category."""
    AGENT = "agent"
    WATCHER = "watcher"
    EXECUTOR = "executor"
    SYNC = "sync"
    APPROVAL = "approval"
    SYSTEM = "system"


class LogEntry(BaseModel):
    """Model for audit log entries.

    Log entries are written to daily log files in the Logs/ folder.
    Each entry is a single line of JSON.
    """

    # Metadata
    timestamp: datetime = Field(..., description="When the event occurred")
    level: LogLevel = Field(..., description="Log level")
    category: LogCategory = Field(..., description="Log category")

    # Source
    agent_id: Optional[str] = Field(None, description="Agent that generated this log")
    watcher_id: Optional[str] = Field(None, description="Watcher that generated this log")

    # Content
    message: str = Field(..., description="Log message")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional details")

    # Context
    action_id: Optional[str] = Field(None, description="Related action ID")
    approval_id: Optional[str] = Field(None, description="Related approval ID")

    # Error tracking
    error_type: Optional[str] = Field(None, description="Error type if this is an error log")
    stack_trace: Optional[str] = Field(None, description="Stack trace if this is an error log")

    def to_json_line(self) -> str:
        """Convert log entry to a single line of JSON.

        Returns:
            JSON string (single line, no newline)
        """
        data = {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "category": self.category.value,
            "message": self.message,
            "details": self.details,
        }

        # Add optional fields
        if self.agent_id:
            data["agent_id"] = self.agent_id
        if self.watcher_id:
            data["watcher_id"] = self.watcher_id
        if self.action_id:
            data["action_id"] = self.action_id
        if self.approval_id:
            data["approval_id"] = self.approval_id
        if self.error_type:
            data["error_type"] = self.error_type
        if self.stack_trace:
            data["stack_trace"] = self.stack_trace

        return json.dumps(data, ensure_ascii=False)

    @classmethod
    def from_json_line(cls, line: str) -> "LogEntry":
        """Parse log entry from a JSON line.

        Args:
            line: JSON string (single line)

        Returns:
            LogEntry instance

        Raises:
            ValueError: If JSON is invalid
        """
        data = json.loads(line)

        # Parse timestamp
        timestamp = datetime.fromisoformat(data.pop("timestamp"))

        return cls(
            timestamp=timestamp,
            level=LogLevel(data.pop("level")),
            category=LogCategory(data.pop("category")),
            message=data.pop("message"),
            details=data.pop("details", {}),
            agent_id=data.pop("agent_id", None),
            watcher_id=data.pop("watcher_id", None),
            action_id=data.pop("action_id", None),
            approval_id=data.pop("approval_id", None),
            error_type=data.pop("error_type", None),
            stack_trace=data.pop("stack_trace", None),
        )

    @staticmethod
    def get_log_filename(date: datetime) -> str:
        """Get log filename for a given date.

        Args:
            date: Date for the log file

        Returns:
            Filename in format: YYYY-MM-DD.md
        """
        return date.strftime("%Y-%m-%d.md")

    class Config:
        """Pydantic configuration."""
        use_enum_values = False
