"""Cross-Posting Coordinator for Social Media.

Manages simultaneous posting to multiple platforms with tracking and error handling.
"""

import logging
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.models.social_media_post import SocialMediaPost, Platform, PostStatus
from src.mcp_servers.social_mcp.content_optimizer import ContentOptimizer

logger = logging.getLogger(__name__)


class CrossPostCoordinator:
    """Coordinates posting to multiple social media platforms simultaneously.

    Features:
    - Create cross-post groups with shared group ID
    - Optimize content per platform
    - Track posting status per platform
    - Handle partial failures gracefully
    - Maintain cross-post relationships
    """

    def __init__(self, vault_path: Path):
        """Initialize cross-post coordinator.

        Args:
            vault_path: Path to AI Employee vault
        """
        self.vault_path = vault_path
        self.content_optimizer = ContentOptimizer()

    def create_cross_post(self, content: str, platforms: List[Platform],
                         media_urls: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a cross-post for multiple platforms.

        Args:
            content: Post content
            platforms: List of target platforms
            media_urls: Optional media URLs

        Returns:
            Dictionary with cross-post information
        """
        try:
            # Generate cross-post group ID
            cross_post_group_id = str(uuid.uuid4())

            # Optimize content for each platform
            optimizations = self.content_optimizer.optimize_for_cross_post(
                content,
                platforms,
                media_urls
            )

            # Check for conflicts
            conflicts = []
            for platform, result in optimizations.items():
                if result.get("warnings"):
                    conflicts.extend([
                        f"{platform.value}: {warning}"
                        for warning in result["warnings"]
                    ])

            if conflicts:
                logger.warning(f"Cross-post conflicts detected: {conflicts}")

            # Create individual posts for each platform
            posts = []
            for platform in platforms:
                optimization = optimizations[platform]

                # Create post with optimized content
                post = SocialMediaPost.create(
                    platforms=[platform],
                    content=optimization["optimized_content"],
                    media_urls=media_urls,
                    cross_post_group_id=cross_post_group_id
                )

                # Request approval
                post.request_approval()
                post.save(self.vault_path)

                posts.append({
                    "post_id": post.post_id,
                    "platform": platform.value,
                    "optimized": optimization.get("truncated", False),
                    "warnings": optimization.get("warnings", []),
                    "recommendations": optimization.get("recommendations", [])
                })

            logger.info(
                f"Created cross-post group {cross_post_group_id} "
                f"with {len(posts)} posts"
            )

            return {
                "success": True,
                "cross_post_group_id": cross_post_group_id,
                "posts": posts,
                "conflicts": conflicts,
                "message": f"Created {len(posts)} posts for approval"
            }

        except Exception as e:
            logger.error(f"Failed to create cross-post: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_cross_post_status(self, cross_post_group_id: str) -> Dict[str, Any]:
        """Get status of all posts in a cross-post group.

        Args:
            cross_post_group_id: Cross-post group ID

        Returns:
            Dictionary with status information
        """
        try:
            # Find all posts in group
            post_dir = self.vault_path / "Social_Media" / "posts"
            if not post_dir.exists():
                return {
                    "success": False,
                    "error": "No posts found"
                }

            group_posts = []
            for post_file in post_dir.glob("*.md"):
                try:
                    post = SocialMediaPost.load(self.vault_path, post_file.stem)
                    if post.cross_post_group_id == cross_post_group_id:
                        group_posts.append({
                            "post_id": post.post_id,
                            "platform": post.platforms[0].value if post.platforms else "unknown",
                            "status": post.status.value,
                            "posted_at": post.posted_at.isoformat() if post.posted_at else None
                        })
                except Exception:
                    continue

            if not group_posts:
                return {
                    "success": False,
                    "error": f"No posts found for group {cross_post_group_id}"
                }

            # Calculate overall status
            statuses = [p["status"] for p in group_posts]
            if all(s == "posted" for s in statuses):
                overall_status = "all_posted"
            elif any(s == "failed" for s in statuses):
                overall_status = "partial_failure"
            elif all(s == "approved" for s in statuses):
                overall_status = "ready_to_post"
            elif all(s == "pending_approval" for s in statuses):
                overall_status = "pending_approval"
            else:
                overall_status = "mixed"

            return {
                "success": True,
                "cross_post_group_id": cross_post_group_id,
                "overall_status": overall_status,
                "posts": group_posts,
                "total_posts": len(group_posts)
            }

        except Exception as e:
            logger.error(f"Failed to get cross-post status: {e}")
            return {
                "success": False,
                "error": str(e)
            }

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
            # Find all posts in group
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
                            post.approve(approved_by, "manual")
                            post.save(self.vault_path)
                            approved_count += 1
                except Exception as e:
                    logger.error(f"Failed to approve post {post_file.stem}: {e}")

            if approved_count == 0:
                return {
                    "success": False,
                    "error": "No posts were approved (already approved or not found)"
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

    def post_cross_post_group(self, cross_post_group_id: str,
                             post_functions: Dict[Platform, callable]) -> Dict[str, Any]:
        """Post all approved posts in a cross-post group.

        Args:
            cross_post_group_id: Cross-post group ID
            post_functions: Dictionary mapping platform to posting function

        Returns:
            Posting result dictionary
        """
        try:
            # Find all approved posts in group
            post_dir = self.vault_path / "Social_Media" / "posts"
            if not post_dir.exists():
                return {
                    "success": False,
                    "error": "No posts found"
                }

            results = {
                "posted": [],
                "failed": [],
                "skipped": []
            }

            for post_file in post_dir.glob("*.md"):
                try:
                    post = SocialMediaPost.load(self.vault_path, post_file.stem)

                    if post.cross_post_group_id != cross_post_group_id:
                        continue

                    if post.status != PostStatus.APPROVED:
                        results["skipped"].append({
                            "post_id": post.post_id,
                            "platform": post.platforms[0].value,
                            "reason": f"Not approved (status: {post.status.value})"
                        })
                        continue

                    # Get posting function for platform
                    platform = post.platforms[0]
                    post_func = post_functions.get(platform)

                    if not post_func:
                        results["failed"].append({
                            "post_id": post.post_id,
                            "platform": platform.value,
                            "error": "No posting function available"
                        })
                        continue

                    # Post to platform
                    result = post_func(post.post_id)

                    if result.get("success"):
                        results["posted"].append({
                            "post_id": post.post_id,
                            "platform": platform.value
                        })
                    else:
                        results["failed"].append({
                            "post_id": post.post_id,
                            "platform": platform.value,
                            "error": result.get("error", "Unknown error")
                        })

                except Exception as e:
                    logger.error(f"Failed to post {post_file.stem}: {e}")
                    results["failed"].append({
                        "post_id": post_file.stem,
                        "error": str(e)
                    })

            success = len(results["posted"]) > 0

            logger.info(
                f"Cross-post group {cross_post_group_id}: "
                f"{len(results['posted'])} posted, "
                f"{len(results['failed'])} failed, "
                f"{len(results['skipped'])} skipped"
            )

            return {
                "success": success,
                "cross_post_group_id": cross_post_group_id,
                "results": results,
                "message": f"Posted {len(results['posted'])} of {len(results['posted']) + len(results['failed'])} posts"
            }

        except Exception as e:
            logger.error(f"Failed to post cross-post group: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_all_cross_post_groups(self) -> List[Dict[str, Any]]:
        """Get all cross-post groups.

        Returns:
            List of cross-post group summaries
        """
        try:
            post_dir = self.vault_path / "Social_Media" / "posts"
            if not post_dir.exists():
                return []

            groups = {}

            for post_file in post_dir.glob("*.md"):
                try:
                    post = SocialMediaPost.load(self.vault_path, post_file.stem)

                    if not post.cross_post_group_id:
                        continue

                    group_id = post.cross_post_group_id

                    if group_id not in groups:
                        groups[group_id] = {
                            "cross_post_group_id": group_id,
                            "posts": [],
                            "created_at": post.created_at
                        }

                    groups[group_id]["posts"].append({
                        "post_id": post.post_id,
                        "platform": post.platforms[0].value if post.platforms else "unknown",
                        "status": post.status.value
                    })

                except Exception:
                    continue

            return list(groups.values())

        except Exception as e:
            logger.error(f"Failed to get cross-post groups: {e}")
            return []
