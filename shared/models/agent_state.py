"""AgentState model for tracking agent status and health."""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import frontmatter


class AgentStatus(str, Enum):
    """Status of an agent."""
    STARTING = "starting"
    RUNNING = "running"
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    STOPPED = "stopped"


class AgentType(str, Enum):
    """Type of agent."""
    CLOUD = "cloud"
    LOCAL = "local"


class AgentState(BaseModel):
    """Model for agent state files in the vault.

    Agent state files track the current status and health of agents.
    Located at: In_Progress/{agent}/agent_state.md
    """

    # Identity
    agent_id: str = Field(..., description="Unique identifier for this agent")
    agent_type: AgentType = Field(..., description="Type of agent")
    agent_name: str = Field(..., description="Human-readable agent name")

    # Status
    status: AgentStatus = Field(..., description="Current agent status")
    last_heartbeat: datetime = Field(..., description="Last heartbeat timestamp")
    started_at: datetime = Field(..., description="When the agent started")

    # Current work
    current_task: Optional[str] = Field(None, description="Current task description")
    current_action_id: Optional[str] = Field(None, description="Current action file ID")
    tasks_in_progress: List[str] = Field(default_factory=list, description="List of action IDs in progress")

    # Statistics
    tasks_completed: int = Field(default=0, description="Total tasks completed")
    tasks_failed: int = Field(default=0, description="Total tasks failed")
    approvals_created: int = Field(default=0, description="Total approval requests created")
    uptime_seconds: int = Field(default=0, description="Total uptime in seconds")

    # Health
    error_count: int = Field(default=0, description="Error count since last reset")
    last_error: Optional[str] = Field(None, description="Last error message")
    last_error_at: Optional[datetime] = Field(None, description="When the last error occurred")

    # Configuration
    config: Dict[str, Any] = Field(default_factory=dict, description="Agent configuration")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @classmethod
    def from_file(cls, file_path: str) -> "AgentState":
        """Load AgentState from a markdown file with frontmatter.

        Args:
            file_path: Path to the markdown file

        Returns:
            AgentState instance

        Raises:
            ValueError: If file format is invalid
        """
        with open(file_path, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)

        # Extract frontmatter metadata
        metadata = dict(post.metadata)

        # Parse datetime fields
        last_heartbeat = datetime.fromisoformat(metadata.pop("last_heartbeat"))
        started_at = datetime.fromisoformat(metadata.pop("started_at"))

        last_error_at_str = metadata.pop("last_error_at", None)
        last_error_at = datetime.fromisoformat(last_error_at_str) if last_error_at_str else None

        return cls(
            agent_id=metadata.pop("agent_id"),
            agent_type=AgentType(metadata.pop("agent_type")),
            agent_name=metadata.pop("agent_name"),
            status=AgentStatus(metadata.pop("status")),
            last_heartbeat=last_heartbeat,
            started_at=started_at,
            current_task=metadata.pop("current_task", None),
            current_action_id=metadata.pop("current_action_id", None),
            tasks_in_progress=metadata.pop("tasks_in_progress", []),
            tasks_completed=metadata.pop("tasks_completed", 0),
            tasks_failed=metadata.pop("tasks_failed", 0),
            approvals_created=metadata.pop("approvals_created", 0),
            uptime_seconds=metadata.pop("uptime_seconds", 0),
            error_count=metadata.pop("error_count", 0),
            last_error=metadata.pop("last_error", None),
            last_error_at=last_error_at,
            config=metadata.pop("config", {}),
            metadata=metadata.pop("metadata", {}),
        )

    def to_file(self, file_path: str) -> None:
        """Save AgentState to a markdown file with frontmatter.

        Args:
            file_path: Path where the file should be saved
        """
        # Prepare frontmatter metadata
        metadata = {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type.value,
            "agent_name": self.agent_name,
            "status": self.status.value,
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "started_at": self.started_at.isoformat(),
            "tasks_in_progress": self.tasks_in_progress,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "approvals_created": self.approvals_created,
            "uptime_seconds": self.uptime_seconds,
            "error_count": self.error_count,
            "config": self.config,
            "metadata": self.metadata,
        }

        # Add optional fields
        if self.current_task:
            metadata["current_task"] = self.current_task
        if self.current_action_id:
            metadata["current_action_id"] = self.current_action_id
        if self.last_error:
            metadata["last_error"] = self.last_error
        if self.last_error_at:
            metadata["last_error_at"] = self.last_error_at.isoformat()

        # Create body with current status summary
        body = f"""# Agent Status: {self.status.value.upper()}

**Current Task**: {self.current_task or "None"}
**Tasks In Progress**: {len(self.tasks_in_progress)}
**Tasks Completed**: {self.tasks_completed}
**Tasks Failed**: {self.tasks_failed}
**Uptime**: {self.uptime_seconds // 3600}h {(self.uptime_seconds % 3600) // 60}m

## Recent Activity
Last heartbeat: {self.last_heartbeat.strftime("%Y-%m-%d %H:%M:%S")}
"""

        if self.last_error:
            body += f"\n## Last Error\n{self.last_error}\n"
            if self.last_error_at:
                body += f"Occurred at: {self.last_error_at.strftime('%Y-%m-%d %H:%M:%S')}\n"

        # Create frontmatter post
        post = frontmatter.Post(body, **metadata)

        # Write to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

    def is_healthy(self, max_heartbeat_age_seconds: int = 300) -> bool:
        """Check if agent is healthy based on heartbeat.

        Args:
            max_heartbeat_age_seconds: Maximum age of heartbeat in seconds

        Returns:
            True if healthy, False otherwise
        """
        age = (datetime.now() - self.last_heartbeat).total_seconds()
        return age <= max_heartbeat_age_seconds and self.status != AgentStatus.ERROR

    class Config:
        """Pydantic configuration."""
        use_enum_values = False
