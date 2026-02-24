"""MCPServer entity model for Gold Tier.

Represents metadata for independent MCP server instances with health tracking,
rate limiting, and lifecycle management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional
import frontmatter
import uuid


class ServerDomain(Enum):
    """MCP server domain types."""
    ACCOUNTING = "accounting"
    SOCIAL = "social"
    COMMUNICATIONS = "communications"


class ServerStatus(Enum):
    """MCP server status states."""
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    CRASHED = "crashed"


@dataclass
class RateLimits:
    """Rate limit configuration for MCP server."""
    calls_per_minute: int = 60
    calls_per_hour: int = 1000
    concurrent_requests: int = 5


@dataclass
class MCPServer:
    """MCP Server entity for domain-separated action execution.

    Storage: AI_Employee_Vault/System/mcp_servers/{server_id}.md
    """

    server_id: str
    domain: ServerDomain
    status: ServerStatus
    available_tools: List[str]
    rate_limits: RateLimits
    error_count: int = 0
    restart_count: int = 0
    last_health_check: Optional[datetime] = None
    process_id: Optional[int] = None
    started_at: Optional[datetime] = None
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate entity after initialization."""
        if not self.available_tools:
            raise ValueError("available_tools must not be empty")

        if self.status == ServerStatus.RUNNING:
            if self.process_id is None or self.started_at is None:
                raise ValueError("Running server must have process_id and started_at")

        if self.status == ServerStatus.STOPPED:
            if self.process_id is not None:
                raise ValueError("Stopped server should not have process_id")

    @classmethod
    def create(cls, server_id: str, domain: ServerDomain, available_tools: List[str],
               rate_limits: Optional[RateLimits] = None) -> "MCPServer":
        """Create a new MCPServer entity."""
        return cls(
            server_id=server_id,
            domain=domain,
            status=ServerStatus.STOPPED,
            available_tools=available_tools,
            rate_limits=rate_limits or RateLimits(),
            error_count=0,
            restart_count=0
        )

    def start(self, process_id: int) -> None:
        """Mark server as started."""
        self.status = ServerStatus.RUNNING
        self.process_id = process_id
        self.started_at = datetime.now()
        self.error_count = 0
        self.updated_at = datetime.now()

    def stop(self) -> None:
        """Mark server as stopped."""
        self.status = ServerStatus.STOPPED
        self.process_id = None
        self.started_at = None
        self.updated_at = datetime.now()

    def mark_error(self) -> None:
        """Increment error count and update status."""
        self.error_count += 1
        self.status = ServerStatus.ERROR
        self.updated_at = datetime.now()

    def mark_crashed(self) -> None:
        """Mark server as crashed."""
        self.status = ServerStatus.CRASHED
        self.process_id = None
        self.updated_at = datetime.now()

    def restart(self, process_id: int) -> None:
        """Restart server with new process."""
        self.restart_count += 1
        self.start(process_id)

    def update_health_check(self) -> None:
        """Update last health check timestamp."""
        self.last_health_check = datetime.now()
        self.updated_at = datetime.now()

    def to_markdown(self) -> str:
        """Convert entity to Markdown format."""
        uptime = ""
        if self.status == ServerStatus.RUNNING and self.started_at:
            delta = datetime.now() - self.started_at
            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60
            uptime = f"{hours} hours {minutes} minutes"

        metadata = {
            "server_id": self.server_id,
            "domain": self.domain.value,
            "status": self.status.value,
            "process_id": self.process_id,
            "error_count": self.error_count,
            "restart_count": self.restart_count,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "updated_at": self.updated_at.isoformat(),
            "available_tools": self.available_tools,
            "rate_limits": {
                "calls_per_minute": self.rate_limits.calls_per_minute,
                "calls_per_hour": self.rate_limits.calls_per_hour,
                "concurrent_requests": self.rate_limits.concurrent_requests
            }
        }

        body = f"""# MCP Server: {self.server_id.title()}

**Domain**: {self.domain.value.title()}
**Status**: {self.status.value.title()}{f" (PID: {self.process_id})" if self.process_id else ""}
{f"**Uptime**: {uptime}" if uptime else ""}

## Available Tools
{chr(10).join(f"- {tool}" for tool in self.available_tools)}

## Health Status
- Last Health Check: {self.last_health_check.strftime("%Y-%m-%d %H:%M:%S") if self.last_health_check else "Never"}
- Error Count: {self.error_count}
- Restart Count: {self.restart_count}

## Rate Limits
- {self.rate_limits.calls_per_minute} calls/minute
- {self.rate_limits.calls_per_hour} calls/hour
- {self.rate_limits.concurrent_requests} concurrent requests
"""

        post = frontmatter.Post(body, **metadata)
        return frontmatter.dumps(post)

    @classmethod
    def from_markdown(cls, content: str) -> "MCPServer":
        """Parse MCPServer from Markdown file."""
        post = frontmatter.loads(content)

        return cls(
            server_id=post["server_id"],
            domain=ServerDomain(post["domain"]),
            status=ServerStatus(post["status"]),
            available_tools=post["available_tools"],
            rate_limits=RateLimits(**post["rate_limits"]),
            error_count=post["error_count"],
            restart_count=post["restart_count"],
            last_health_check=datetime.fromisoformat(post["last_health_check"]) if post.get("last_health_check") else None,
            process_id=post.get("process_id"),
            started_at=datetime.fromisoformat(post["started_at"]) if post.get("started_at") else None,
            updated_at=datetime.fromisoformat(post["updated_at"])
        )

    def save(self, vault_path: Path) -> Path:
        """Save entity to vault."""
        server_dir = vault_path / "System" / "mcp_servers"
        server_dir.mkdir(parents=True, exist_ok=True)

        file_path = server_dir / f"{self.server_id}.md"
        file_path.write_text(self.to_markdown(), encoding="utf-8")

        return file_path

    @classmethod
    def load(cls, vault_path: Path, server_id: str) -> "MCPServer":
        """Load entity from vault."""
        file_path = vault_path / "System" / "mcp_servers" / f"{server_id}.md"

        if not file_path.exists():
            raise FileNotFoundError(f"MCPServer {server_id} not found")

        content = file_path.read_text(encoding="utf-8")
        return cls.from_markdown(content)
