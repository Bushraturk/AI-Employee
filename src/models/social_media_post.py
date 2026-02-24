"""SocialMediaPost entity model for Gold Tier.

Represents content published across social media platforms with performance tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
import frontmatter
import uuid


class PostStatus(Enum):
    """Post status states."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    POSTED = "posted"
    FAILED = "failed"


class Platform(Enum):
    """Social media platform types."""
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"


@dataclass
class PerformanceMetrics:
    """Performance metrics for a specific platform."""
    reach: int = 0
    impressions: int = 0
    engagement: int = 0
    clicks: int = 0
    last_updated: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "reach": self.reach,
            "impressions": self.impressions,
            "engagement": self.engagement,
            "clicks": self.clicks,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PerformanceMetrics":
        """Create from dictionary."""
        return cls(
            reach=data.get("reach", 0),
            impressions=data.get("impressions", 0),
            engagement=data.get("engagement", 0),
            clicks=data.get("clicks", 0),
            last_updated=datetime.fromisoformat(data["last_updated"]) if data.get("last_updated") else None
        )


@dataclass
class ApprovalMetadata:
    """Approval tracking metadata."""
    requested_at: datetime
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    approval_method: str = "manual"  # manual, auto, scheduled

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "requested_at": self.requested_at.isoformat(),
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "approved_by": self.approved_by,
            "approval_method": self.approval_method
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ApprovalMetadata":
        """Create from dictionary."""
        return cls(
            requested_at=datetime.fromisoformat(data["requested_at"]),
            approved_at=datetime.fromisoformat(data["approved_at"]) if data.get("approved_at") else None,
            approved_by=data.get("approved_by"),
            approval_method=data.get("approval_method", "manual")
        )


@dataclass
class SocialMediaPost:
    """Social media post entity for multi-platform content publishing.

    Storage: AI_Employee_Vault/Social_Media/posts/{post_id}.md
    """

    post_id: str
    platforms: List[Platform]
    content: str
    status: PostStatus
    approval_metadata: ApprovalMetadata
    media_urls: List[str] = field(default_factory=list)
    posted_at: Optional[datetime] = None
    performance_metrics: Dict[str, PerformanceMetrics] = field(default_factory=dict)
    cross_post_group_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate entity after initialization."""
        # At least one platform must be specified
        if not self.platforms:
            raise ValueError("At least one platform must be specified")

        # Content length validation (Twitter has 280 char limit)
        if Platform.TWITTER in self.platforms and len(self.content) > 280:
            raise ValueError("Content exceeds Twitter's 280 character limit")

        # General content length (2200 chars for other platforms)
        if len(self.content) > 2200:
            raise ValueError("Content exceeds maximum length of 2200 characters")

        # If status is posted, posted_at must be set
        if self.status == PostStatus.POSTED and not self.posted_at:
            raise ValueError("Posted status requires posted_at timestamp")

    @classmethod
    def create(cls, platforms: List[Platform], content: str,
               media_urls: Optional[List[str]] = None,
               cross_post_group_id: Optional[str] = None) -> "SocialMediaPost":
        """Create a new SocialMediaPost entity."""
        return cls(
            post_id=str(uuid.uuid4()),
            platforms=platforms,
            content=content,
            media_urls=media_urls or [],
            status=PostStatus.DRAFT,
            approval_metadata=ApprovalMetadata(requested_at=datetime.now()),
            cross_post_group_id=cross_post_group_id
        )

    def request_approval(self) -> None:
        """Request approval for post."""
        self.status = PostStatus.PENDING_APPROVAL
        self.approval_metadata.requested_at = datetime.now()
        self.updated_at = datetime.now()

    def approve(self, approved_by: str, approval_method: str = "manual") -> None:
        """Approve post for publishing."""
        self.status = PostStatus.APPROVED
        self.approval_metadata.approved_at = datetime.now()
        self.approval_metadata.approved_by = approved_by
        self.approval_metadata.approval_method = approval_method
        self.updated_at = datetime.now()

    def mark_posted(self) -> None:
        """Mark post as successfully published."""
        self.status = PostStatus.POSTED
        self.posted_at = datetime.now()
        self.updated_at = datetime.now()

    def mark_failed(self) -> None:
        """Mark post as failed to publish."""
        self.status = PostStatus.FAILED
        self.updated_at = datetime.now()

    def update_metrics(self, platform: Platform, metrics: PerformanceMetrics) -> None:
        """Update performance metrics for a platform."""
        self.performance_metrics[platform.value] = metrics
        self.updated_at = datetime.now()

    def get_total_reach(self) -> int:
        """Calculate total reach across all platforms."""
        return sum(m.reach for m in self.performance_metrics.values())

    def get_total_engagement(self) -> int:
        """Calculate total engagement across all platforms."""
        return sum(m.engagement for m in self.performance_metrics.values())

    def get_total_clicks(self) -> int:
        """Calculate total clicks across all platforms."""
        return sum(m.clicks for m in self.performance_metrics.values())

    def get_engagement_rate(self) -> float:
        """Calculate engagement rate (engagement / reach)."""
        total_reach = self.get_total_reach()
        if total_reach == 0:
            return 0.0
        return (self.get_total_engagement() / total_reach) * 100

    def to_markdown(self) -> str:
        """Convert entity to Markdown format."""
        metadata = {
            "post_id": self.post_id,
            "platforms": [p.value for p in self.platforms],
            "status": self.status.value,
            "posted_at": self.posted_at.isoformat() if self.posted_at else None,
            "cross_post_group_id": self.cross_post_group_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "approval_metadata": self.approval_metadata.to_dict(),
            "performance_metrics": {
                platform: metrics.to_dict()
                for platform, metrics in self.performance_metrics.items()
            }
        }

        # Build platform list
        platform_names = ", ".join(p.value.title() for p in self.platforms)

        # Build media section
        media_section = ""
        if self.media_urls:
            media_section = "\n## Media\n" + "\n".join(f"- {url}" for url in self.media_urls)

        # Build performance section
        performance_section = ""
        if self.performance_metrics:
            total_reach = self.get_total_reach()
            total_engagement = self.get_total_engagement()
            total_clicks = self.get_total_clicks()
            engagement_rate = self.get_engagement_rate()

            performance_section = f"""
## Performance Summary
- **Total Reach**: {total_reach:,}
- **Total Engagement**: {total_engagement:,}
- **Total Clicks**: {total_clicks:,}
- **Engagement Rate**: {engagement_rate:.1f}%

## Platform-Specific Performance
"""
            for platform, metrics in self.performance_metrics.items():
                platform_reach = metrics.reach
                platform_engagement = metrics.engagement
                platform_rate = (metrics.engagement / metrics.reach * 100) if metrics.reach > 0 else 0

                performance_section += f"- **{platform.title()}**: {platform_reach:,} reach, {platform_engagement:,} engagement ({platform_rate:.1f}% rate)\n"

        body = f"""# Social Media Post: {self.content[:50]}{'...' if len(self.content) > 50 else ''}

**Platforms**: {platform_names}
**Status**: {self.status.value.replace('_', ' ').title()}
{f"**Posted**: {self.posted_at.strftime('%Y-%m-%d %H:%M:%S')}" if self.posted_at else ""}

## Content

{self.content}
{media_section}
{performance_section}
"""

        post = frontmatter.Post(body, **metadata)
        return frontmatter.dumps(post)

    @classmethod
    def from_markdown(cls, content: str) -> "SocialMediaPost":
        """Parse SocialMediaPost from Markdown file."""
        post = frontmatter.loads(content)

        return cls(
            post_id=post["post_id"],
            platforms=[Platform(p) for p in post["platforms"]],
            content=post.content.split("## Content\n\n")[1].split("\n##")[0].strip(),
            status=PostStatus(post["status"]),
            posted_at=datetime.fromisoformat(post["posted_at"]) if post.get("posted_at") else None,
            performance_metrics={
                platform: PerformanceMetrics.from_dict(metrics)
                for platform, metrics in post.get("performance_metrics", {}).items()
            },
            approval_metadata=ApprovalMetadata.from_dict(post["approval_metadata"]),
            cross_post_group_id=post.get("cross_post_group_id"),
            created_at=datetime.fromisoformat(post["created_at"]),
            updated_at=datetime.fromisoformat(post["updated_at"])
        )

    def save(self, vault_path: Path) -> Path:
        """Save entity to vault."""
        post_dir = vault_path / "Social_Media" / "posts"
        post_dir.mkdir(parents=True, exist_ok=True)

        file_path = post_dir / f"{self.post_id}.md"
        file_path.write_text(self.to_markdown(), encoding="utf-8")

        return file_path

    @classmethod
    def load(cls, vault_path: Path, post_id: str) -> "SocialMediaPost":
        """Load entity from vault."""
        file_path = vault_path / "Social_Media" / "posts" / f"{post_id}.md"

        if not file_path.exists():
            raise FileNotFoundError(f"SocialMediaPost {post_id} not found")

        content = file_path.read_text(encoding="utf-8")
        return cls.from_markdown(content)

    @classmethod
    def find_by_status(cls, vault_path: Path, status: PostStatus) -> List["SocialMediaPost"]:
        """Find all posts with a specific status.

        Args:
            vault_path: Path to vault
            status: Post status to filter by

        Returns:
            List of posts with matching status
        """
        post_dir = vault_path / "Social_Media" / "posts"
        if not post_dir.exists():
            return []

        posts = []
        for post_file in post_dir.glob("*.md"):
            try:
                post = cls.load(vault_path, post_file.stem)
                if post.status == status:
                    posts.append(post)
            except Exception:
                continue

        return posts
