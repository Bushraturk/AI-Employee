"""Metrics Aggregator for Social Media.

Collects and aggregates performance metrics from all social media platforms.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.models.social_media_post import SocialMediaPost, Platform, PostStatus, PerformanceMetrics
from src.mcp_servers.social_mcp.facebook_client import FacebookGraphAPI
from src.mcp_servers.social_mcp.instagram_client import InstagramGraphAPI
from src.mcp_servers.social_mcp.twitter_client import TwitterAPIClient

logger = logging.getLogger(__name__)


class MetricsAggregator:
    """Aggregates performance metrics from all social media platforms.

    Features:
    - Collect metrics from Facebook, Instagram, Twitter, LinkedIn
    - Update SocialMediaPost entities with latest metrics
    - Calculate aggregate metrics across platforms
    - Track metric history over time
    """

    def __init__(self, vault_path: Path):
        """Initialize metrics aggregator.

        Args:
            vault_path: Path to AI Employee vault
        """
        self.vault_path = vault_path

        # Initialize API clients
        try:
            self.facebook_client = FacebookGraphAPI()
        except Exception as e:
            logger.warning(f"Facebook client not initialized: {e}")
            self.facebook_client = None

        try:
            self.instagram_client = InstagramGraphAPI()
        except Exception as e:
            logger.warning(f"Instagram client not initialized: {e}")
            self.instagram_client = None

        try:
            self.twitter_client = TwitterAPIClient()
        except Exception as e:
            logger.warning(f"Twitter client not initialized: {e}")
            self.twitter_client = None

    def collect_metrics_for_post(self, post_id: str) -> Dict[str, Any]:
        """Collect metrics for a specific post from all platforms.

        Args:
            post_id: SocialMediaPost ID

        Returns:
            Collection result dictionary
        """
        try:
            # Load post from vault
            post = SocialMediaPost.load(self.vault_path, post_id)

            # Check if post is published
            if post.status != PostStatus.POSTED:
                return {
                    "success": False,
                    "error": f"Post must be published to collect metrics (status: {post.status.value})"
                }

            metrics_collected = {}
            errors = []

            # Collect metrics for each platform
            for platform in post.platforms:
                try:
                    if platform == Platform.FACEBOOK and self.facebook_client:
                        metrics = self._collect_facebook_metrics(post)
                        if metrics:
                            post.update_metrics(platform, metrics)
                            metrics_collected[platform.value] = metrics.to_dict()
                    elif platform == Platform.INSTAGRAM and self.instagram_client:
                        metrics = self._collect_instagram_metrics(post)
                        if metrics:
                            post.update_metrics(platform, metrics)
                            metrics_collected[platform.value] = metrics.to_dict()
                    elif platform == Platform.TWITTER and self.twitter_client:
                        metrics = self._collect_twitter_metrics(post)
                        if metrics:
                            post.update_metrics(platform, metrics)
                            metrics_collected[platform.value] = metrics.to_dict()
                    elif platform == Platform.LINKEDIN:
                        # LinkedIn metrics from Silver Tier
                        logger.info("LinkedIn metrics collection not yet implemented")
                        metrics_collected[platform.value] = "not_implemented"
                except Exception as e:
                    logger.error(f"Failed to collect {platform.value} metrics: {e}")
                    errors.append(f"{platform.value}: {str(e)}")

            # Save updated post
            if metrics_collected:
                post.save(self.vault_path)

            return {
                "success": len(metrics_collected) > 0,
                "post_id": post_id,
                "metrics_collected": metrics_collected,
                "errors": errors,
                "message": f"Collected metrics for {len(metrics_collected)} platforms"
            }

        except Exception as e:
            logger.error(f"Failed to collect metrics for post {post_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _collect_facebook_metrics(self, post: SocialMediaPost) -> Optional[PerformanceMetrics]:
        """Collect metrics from Facebook.

        Args:
            post: SocialMediaPost entity

        Returns:
            PerformanceMetrics or None
        """
        try:
            # Note: This requires storing platform-specific post IDs
            # For now, this is a placeholder implementation
            # Full implementation would track Facebook post ID in post metadata

            logger.info("Facebook metrics collection requires platform-specific post ID")
            return None

        except Exception as e:
            logger.error(f"Failed to collect Facebook metrics: {e}")
            return None

    def _collect_instagram_metrics(self, post: SocialMediaPost) -> Optional[PerformanceMetrics]:
        """Collect metrics from Instagram.

        Args:
            post: SocialMediaPost entity

        Returns:
            PerformanceMetrics or None
        """
        try:
            # Note: This requires storing platform-specific media IDs
            # For now, this is a placeholder implementation
            # Full implementation would track Instagram media ID in post metadata

            logger.info("Instagram metrics collection requires platform-specific media ID")
            return None

        except Exception as e:
            logger.error(f"Failed to collect Instagram metrics: {e}")
            return None

    def _collect_twitter_metrics(self, post: SocialMediaPost) -> Optional[PerformanceMetrics]:
        """Collect metrics from Twitter.

        Args:
            post: SocialMediaPost entity

        Returns:
            PerformanceMetrics or None
        """
        try:
            # Note: This requires storing platform-specific tweet IDs
            # For now, this is a placeholder implementation
            # Full implementation would track Twitter tweet ID in post metadata

            logger.info("Twitter metrics collection requires platform-specific tweet ID")
            return None

        except Exception as e:
            logger.error(f"Failed to collect Twitter metrics: {e}")
            return None

    def collect_metrics_for_all_posts(self, max_age_days: int = 7) -> Dict[str, Any]:
        """Collect metrics for all recent published posts.

        Args:
            max_age_days: Only collect metrics for posts published within this many days

        Returns:
            Collection result dictionary
        """
        try:
            post_dir = self.vault_path / "Social_Media" / "posts"
            if not post_dir.exists():
                return {
                    "success": False,
                    "error": "No posts found"
                }

            cutoff_date = datetime.now().timestamp() - (max_age_days * 24 * 3600)

            posts_processed = 0
            posts_updated = 0
            errors = []

            for post_file in post_dir.glob("*.md"):
                try:
                    post = SocialMediaPost.load(self.vault_path, post_file.stem)

                    # Skip if not posted
                    if post.status != PostStatus.POSTED:
                        continue

                    # Skip if too old
                    if post.posted_at and post.posted_at.timestamp() < cutoff_date:
                        continue

                    posts_processed += 1

                    # Collect metrics
                    result = self.collect_metrics_for_post(post.post_id)

                    if result.get("success"):
                        posts_updated += 1

                    if result.get("errors"):
                        errors.extend(result["errors"])

                except Exception as e:
                    logger.error(f"Failed to process post {post_file.stem}: {e}")
                    errors.append(f"{post_file.stem}: {str(e)}")

            logger.info(
                f"Metrics collection complete: {posts_updated}/{posts_processed} posts updated"
            )

            return {
                "success": True,
                "posts_processed": posts_processed,
                "posts_updated": posts_updated,
                "errors": errors,
                "message": f"Updated metrics for {posts_updated} of {posts_processed} posts"
            }

        except Exception as e:
            logger.error(f"Failed to collect metrics for all posts: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_aggregate_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get aggregate metrics across all platforms for a time period.

        Args:
            days: Number of days to aggregate

        Returns:
            Aggregate metrics dictionary
        """
        try:
            post_dir = self.vault_path / "Social_Media" / "posts"
            if not post_dir.exists():
                return {
                    "success": False,
                    "error": "No posts found"
                }

            cutoff_date = datetime.now().timestamp() - (days * 24 * 3600)

            aggregate = {
                "total_posts": 0,
                "total_reach": 0,
                "total_impressions": 0,
                "total_engagement": 0,
                "total_clicks": 0,
                "by_platform": {}
            }

            for post_file in post_dir.glob("*.md"):
                try:
                    post = SocialMediaPost.load(self.vault_path, post_file.stem)

                    # Skip if not posted or too old
                    if post.status != PostStatus.POSTED:
                        continue

                    if post.posted_at and post.posted_at.timestamp() < cutoff_date:
                        continue

                    aggregate["total_posts"] += 1

                    # Aggregate metrics
                    for platform, metrics in post.performance_metrics.items():
                        aggregate["total_reach"] += metrics.reach
                        aggregate["total_impressions"] += metrics.impressions
                        aggregate["total_engagement"] += metrics.engagement
                        aggregate["total_clicks"] += metrics.clicks

                        # By platform
                        if platform not in aggregate["by_platform"]:
                            aggregate["by_platform"][platform] = {
                                "posts": 0,
                                "reach": 0,
                                "impressions": 0,
                                "engagement": 0,
                                "clicks": 0
                            }

                        aggregate["by_platform"][platform]["posts"] += 1
                        aggregate["by_platform"][platform]["reach"] += metrics.reach
                        aggregate["by_platform"][platform]["impressions"] += metrics.impressions
                        aggregate["by_platform"][platform]["engagement"] += metrics.engagement
                        aggregate["by_platform"][platform]["clicks"] += metrics.clicks

                except Exception as e:
                    logger.error(f"Failed to aggregate post {post_file.stem}: {e}")

            # Calculate engagement rate
            if aggregate["total_reach"] > 0:
                aggregate["engagement_rate"] = (
                    aggregate["total_engagement"] / aggregate["total_reach"] * 100
                )
            else:
                aggregate["engagement_rate"] = 0.0

            return {
                "success": True,
                "period_days": days,
                "metrics": aggregate
            }

        except Exception as e:
            logger.error(f"Failed to get aggregate metrics: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class MetricsScheduler:
    """Schedules periodic metrics collection.

    Features:
    - Collect metrics every 6 hours for recent posts
    - Track last collection time
    - Handle collection failures gracefully
    """

    def __init__(self, vault_path: Path):
        """Initialize metrics scheduler.

        Args:
            vault_path: Path to AI Employee vault
        """
        self.vault_path = vault_path
        self.aggregator = MetricsAggregator(vault_path)
        self.last_collection_file = vault_path / "System" / "last_metrics_collection.txt"

    def run_scheduled_collection(self) -> Dict[str, Any]:
        """Run scheduled metrics collection (called every 6 hours).

        Returns:
            Collection result dictionary
        """
        try:
            logger.info("Starting scheduled metrics collection")

            # Collect metrics for posts from last 7 days
            result = self.aggregator.collect_metrics_for_all_posts(max_age_days=7)

            # Update last collection time
            self._update_last_collection_time()

            logger.info("Scheduled metrics collection complete")

            return result

        except Exception as e:
            logger.error(f"Scheduled metrics collection failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _update_last_collection_time(self) -> None:
        """Update last collection timestamp."""
        try:
            self.last_collection_file.parent.mkdir(parents=True, exist_ok=True)
            self.last_collection_file.write_text(datetime.now().isoformat())
        except Exception as e:
            logger.error(f"Failed to update last collection time: {e}")

    def get_last_collection_time(self) -> Optional[datetime]:
        """Get timestamp of last collection.

        Returns:
            Last collection timestamp or None
        """
        if self.last_collection_file.exists():
            try:
                timestamp_str = self.last_collection_file.read_text().strip()
                return datetime.fromisoformat(timestamp_str)
            except Exception as e:
                logger.error(f"Failed to read last collection time: {e}")

        return None
