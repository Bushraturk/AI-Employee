"""Approval Manager for Gold Tier.

Manages approval workflow for social media posts and other risk actions.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.models.social_media_post import SocialMediaPost, PostStatus, Platform

logger = logging.getLogger(__name__)


class ApprovalManager:
    """Manages approval workflow for risk actions.

    Features:
    - Request approval for social media posts
    - Multi-platform post review with platform-specific previews
    - Batch approval for cross-post groups
    - Approval history tracking
    - Automatic approval for low-risk actions (optional)
    """

    def __init__(self, vault_path: Path):
        """Initialize approval manager.

        Args:
            vault_path: Path to AI Employee vault
        """
        self.vault_path = vault_path
        self.approval_queue_dir = vault_path / "Approval_Queue"
        self.approval_queue_dir.mkdir(parents=True, exist_ok=True)

    def request_approval(self, post_id: str, requester: str = "system") -> Dict[str, Any]:
        """Request approval for a social media post.

        Args:
            post_id: SocialMediaPost ID
            requester: Who requested approval

        Returns:
            Request result dictionary
        """
        try:
            # Load post from vault
            post = SocialMediaPost.load(self.vault_path, post_id)

            # Check if already approved
            if post.status == PostStatus.APPROVED:
                return {
                    "success": False,
                    "error": "Post is already approved"
                }

            # Update post status
            post.request_approval()
            post.save(self.vault_path)

            # Create approval request file
            self._create_approval_request(post, requester)

            logger.info(f"Approval requested for post {post_id}")

            return {
                "success": True,
                "post_id": post_id,
                "message": "Approval requested"
            }

        except Exception as e:
            logger.error(f"Failed to request approval for post {post_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _create_approval_request(self, post: SocialMediaPost, requester: str) -> None:
        """Create approval request file in queue.

        Args:
            post: SocialMediaPost entity
            requester: Who requested approval
        """
        try:
            request_file = self.approval_queue_dir / f"{post.post_id}.md"

            # Build platform previews
            platform_previews = []
            for platform in post.platforms:
                preview = f"### {platform.value.title()}\n"
                preview += f"**Content**: {post.content}\n"

                if platform == Platform.TWITTER and len(post.content) > 280:
                    preview += f"⚠️ **Warning**: Content exceeds Twitter's 280 character limit\n"

                if platform == Platform.INSTAGRAM and not post.media_urls:
                    preview += f"⚠️ **Warning**: Instagram requires media\n"

                platform_previews.append(preview)

            content = f"""# Approval Request: Social Media Post

**Post ID**: {post.post_id}
**Requested By**: {requester}
**Requested At**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Status**: Pending Approval

## Platforms
{', '.join(p.value.title() for p in post.platforms)}

## Content Preview

{post.content}

## Media
{chr(10).join(f"- {url}" for url in post.media_urls) if post.media_urls else "No media"}

## Platform-Specific Previews

{chr(10).join(platform_previews)}

## Actions

To approve this post, run:
```
approve_post {post.post_id}
```

To reject this post, run:
```
reject_post {post.post_id}
```
"""

            request_file.write_text(content, encoding="utf-8")

        except Exception as e:
            logger.error(f"Failed to create approval request: {e}")

    def approve_post(self, post_id: str, approved_by: str,
                    approval_method: str = "manual") -> Dict[str, Any]:
        """Approve a social media post.

        Args:
            post_id: SocialMediaPost ID
            approved_by: User who approved
            approval_method: Approval method (manual, auto, scheduled)

        Returns:
            Approval result dictionary
        """
        try:
            # Load post from vault
            post = SocialMediaPost.load(self.vault_path, post_id)

            # Check if already approved
            if post.status == PostStatus.APPROVED:
                return {
                    "success": False,
                    "error": "Post is already approved"
                }

            # Approve post
            post.approve(approved_by, approval_method)
            post.save(self.vault_path)

            # Remove from approval queue
            request_file = self.approval_queue_dir / f"{post_id}.md"
            if request_file.exists():
                request_file.unlink()

            logger.info(f"Post {post_id} approved by {approved_by}")

            return {
                "success": True,
                "post_id": post_id,
                "message": f"Post approved by {approved_by}"
            }

        except Exception as e:
            logger.error(f"Failed to approve post {post_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def reject_post(self, post_id: str, rejected_by: str, reason: str) -> Dict[str, Any]:
        """Reject a social media post.

        Args:
            post_id: SocialMediaPost ID
            rejected_by: User who rejected
            reason: Rejection reason

        Returns:
            Rejection result dictionary
        """
        try:
            # Load post from vault
            post = SocialMediaPost.load(self.vault_path, post_id)

            # Update post status to draft
            post.status = PostStatus.DRAFT
            post.updated_at = datetime.now()
            post.save(self.vault_path)

            # Remove from approval queue
            request_file = self.approval_queue_dir / f"{post_id}.md"
            if request_file.exists():
                request_file.unlink()

            logger.info(f"Post {post_id} rejected by {rejected_by}: {reason}")

            return {
                "success": True,
                "post_id": post_id,
                "message": f"Post rejected: {reason}"
            }

        except Exception as e:
            logger.error(f"Failed to reject post {post_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get all posts pending approval.

        Returns:
            List of pending approval dictionaries
        """
        try:
            pending = []

            # Find all pending posts
            post_dir = self.vault_path / "Social_Media" / "posts"
            if not post_dir.exists():
                return pending

            for post_file in post_dir.glob("*.md"):
                try:
                    post = SocialMediaPost.load(self.vault_path, post_file.stem)

                    if post.status == PostStatus.PENDING_APPROVAL:
                        pending.append({
                            "post_id": post.post_id,
                            "platforms": [p.value for p in post.platforms],
                            "content_preview": post.content[:100] + "..." if len(post.content) > 100 else post.content,
                            "requested_at": post.approval_metadata.requested_at.isoformat(),
                            "cross_post_group_id": post.cross_post_group_id
                        })

                except Exception as e:
                    logger.error(f"Failed to load post {post_file.stem}: {e}")

            return pending

        except Exception as e:
            logger.error(f"Failed to get pending approvals: {e}")
            return []

    def approve_cross_post_group(self, cross_post_group_id: str,
                                approved_by: str) -> Dict[str, Any]:
        """Approve all posts in a cross-post group.

        Args:
            cross_post_group_id: Cross-post group ID
            approved_by: User who approved

        Returns:
            Approval result dictionary
        """
        try:
            post_dir = self.vault_path / "Social_Media" / "posts"
            if not post_dir.exists():
                return {
                    "success": False,
                    "error": "No posts found"
                }

            approved_count = 0
            for post_file in post_dir.glob("*.md"):
                try:
                    post = SocialMediaPost.load(self.vault_path, post_file.stem)

                    if post.cross_post_group_id == cross_post_group_id:
                        if post.status == PostStatus.PENDING_APPROVAL:
                            result = self.approve_post(post.post_id, approved_by, "batch")
                            if result.get("success"):
                                approved_count += 1

                except Exception as e:
                    logger.error(f"Failed to approve post {post_file.stem}: {e}")

            if approved_count == 0:
                return {
                    "success": False,
                    "error": "No posts were approved"
                }

            logger.info(
                f"Approved {approved_count} posts in group {cross_post_group_id}"
            )

            return {
                "success": True,
                "approved_count": approved_count,
                "message": f"Approved {approved_count} posts"
            }

        except Exception as e:
            logger.error(f"Failed to approve cross-post group: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_approval_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get approval history for recent posts.

        Args:
            days: Number of days to look back

        Returns:
            List of approval history entries
        """
        try:
            history = []
            cutoff_date = datetime.now().timestamp() - (days * 24 * 3600)

            post_dir = self.vault_path / "Social_Media" / "posts"
            if not post_dir.exists():
                return history

            for post_file in post_dir.glob("*.md"):
                try:
                    post = SocialMediaPost.load(self.vault_path, post_file.stem)

                    # Skip if not approved or too old
                    if post.status != PostStatus.APPROVED and post.status != PostStatus.POSTED:
                        continue

                    if post.approval_metadata.approved_at:
                        if post.approval_metadata.approved_at.timestamp() < cutoff_date:
                            continue

                        history.append({
                            "post_id": post.post_id,
                            "platforms": [p.value for p in post.platforms],
                            "approved_at": post.approval_metadata.approved_at.isoformat(),
                            "approved_by": post.approval_metadata.approved_by,
                            "approval_method": post.approval_metadata.approval_method,
                            "status": post.status.value
                        })

                except Exception as e:
                    logger.error(f"Failed to load post {post_file.stem}: {e}")

            # Sort by approval time (most recent first)
            history.sort(key=lambda x: x["approved_at"], reverse=True)

            return history

        except Exception as e:
            logger.error(f"Failed to get approval history: {e}")
            return []
