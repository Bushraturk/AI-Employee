"""Instagram Graph API Client for Gold Tier.

Provides interface to Instagram Graph API for posting and metrics collection.
"""

import logging
import os
import time
from typing import Dict, Optional, Any
from datetime import datetime
import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()


class InstagramAPIError(Exception):
    """Raised when Instagram API call fails."""
    pass


class InstagramGraphAPI:
    """Client for Instagram Graph API.

    Features:
    - Two-step publishing (create container, then publish)
    - Post photos with captions
    - Retrieve post insights (reach, engagement, impressions)
    - Daily limit: 25 posts per day
    - Requires Instagram Business or Creator account
    """

    BASE_URL = "https://graph.facebook.com/v18.0"

    def __init__(self, access_token: Optional[str] = None, instagram_account_id: Optional[str] = None):
        """Initialize Instagram Graph API client.

        Args:
            access_token: Instagram access token (default: from INSTAGRAM_ACCESS_TOKEN env var)
            instagram_account_id: Instagram Business account ID (default: from INSTAGRAM_ACCOUNT_ID env var)
        """
        self.access_token = access_token or os.getenv('INSTAGRAM_ACCESS_TOKEN')
        self.instagram_account_id = instagram_account_id or os.getenv('INSTAGRAM_ACCOUNT_ID')

        if not self.access_token:
            raise ValueError("Instagram access token not configured. Set INSTAGRAM_ACCESS_TOKEN")

        if not self.instagram_account_id:
            raise ValueError("Instagram account ID not configured. Set INSTAGRAM_ACCOUNT_ID")

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AI-Employee-Bot/1.0'
        })

    def create_media_container(self, image_url: str, caption: str) -> str:
        """Create media container (step 1 of publishing).

        Args:
            image_url: URL of image to post (must be publicly accessible)
            caption: Post caption

        Returns:
            Container ID

        Raises:
            InstagramAPIError: If container creation fails
        """
        try:
            endpoint = f"{self.BASE_URL}/{self.instagram_account_id}/media"

            data = {
                "access_token": self.access_token,
                "image_url": image_url,
                "caption": caption
            }

            response = self.session.post(endpoint, data=data)
            response.raise_for_status()

            result = response.json()

            if "error" in result:
                raise InstagramAPIError(f"Instagram API error: {result['error']}")

            container_id = result.get("id")

            if not container_id:
                raise InstagramAPIError("No container ID returned")

            logger.info(f"Created Instagram media container: {container_id}")

            return container_id

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create Instagram media container: {e}")
            raise InstagramAPIError(f"Request failed: {e}")

    def check_status(self, container_id: str) -> str:
        """Check status of media container.

        Args:
            container_id: Container ID from create_media_container

        Returns:
            Status code (FINISHED, IN_PROGRESS, ERROR)

        Raises:
            InstagramAPIError: If status check fails
        """
        try:
            endpoint = f"{self.BASE_URL}/{container_id}"

            params = {
                "access_token": self.access_token,
                "fields": "status_code"
            }

            response = self.session.get(endpoint, params=params)
            response.raise_for_status()

            result = response.json()

            if "error" in result:
                raise InstagramAPIError(f"Instagram API error: {result['error']}")

            status = result.get("status_code", "UNKNOWN")

            logger.info(f"Instagram container {container_id} status: {status}")

            return status

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to check Instagram container status: {e}")
            raise InstagramAPIError(f"Request failed: {e}")

    def publish_media(self, container_id: str) -> Dict[str, Any]:
        """Publish media container (step 2 of publishing).

        Args:
            container_id: Container ID from create_media_container

        Returns:
            Dictionary with media_id

        Raises:
            InstagramAPIError: If publishing fails
        """
        try:
            endpoint = f"{self.BASE_URL}/{self.instagram_account_id}/media_publish"

            data = {
                "access_token": self.access_token,
                "creation_id": container_id
            }

            response = self.session.post(endpoint, data=data)
            response.raise_for_status()

            result = response.json()

            if "error" in result:
                raise InstagramAPIError(f"Instagram API error: {result['error']}")

            media_id = result.get("id")

            if not media_id:
                raise InstagramAPIError("No media ID returned")

            logger.info(f"Published Instagram media: {media_id}")

            return {
                "success": True,
                "media_id": media_id,
                "message": "Posted to Instagram successfully"
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to publish Instagram media: {e}")
            raise InstagramAPIError(f"Request failed: {e}")

    def post_photo(self, image_url: str, caption: str, max_wait: int = 30) -> Dict[str, Any]:
        """Post photo to Instagram (complete two-step process).

        Args:
            image_url: URL of image to post
            caption: Post caption
            max_wait: Maximum seconds to wait for container to be ready

        Returns:
            Dictionary with media_id

        Raises:
            InstagramAPIError: If posting fails
        """
        try:
            # Step 1: Create media container
            container_id = self.create_media_container(image_url, caption)

            # Step 2: Wait for container to be ready
            wait_time = 0
            status = "IN_PROGRESS"

            while status == "IN_PROGRESS" and wait_time < max_wait:
                time.sleep(2)
                wait_time += 2
                status = self.check_status(container_id)

            if status == "ERROR":
                raise InstagramAPIError("Media container processing failed")

            if status != "FINISHED":
                raise InstagramAPIError(f"Media container not ready after {max_wait}s")

            # Step 3: Publish media
            result = self.publish_media(container_id)

            return result

        except Exception as e:
            logger.error(f"Failed to post photo to Instagram: {e}")
            raise InstagramAPIError(f"Post failed: {e}")

    def get_insights(self, media_id: str) -> Dict[str, Any]:
        """Get insights (metrics) for a post.

        Args:
            media_id: Instagram media ID

        Returns:
            Dictionary with metrics (reach, impressions, engagement)

        Raises:
            InstagramAPIError: If request fails
        """
        try:
            endpoint = f"{self.BASE_URL}/{media_id}/insights"

            params = {
                "access_token": self.access_token,
                "metric": "reach,impressions,engagement"
            }

            response = self.session.get(endpoint, params=params)
            response.raise_for_status()

            result = response.json()

            if "error" in result:
                raise InstagramAPIError(f"Instagram API error: {result['error']}")

            # Parse insights data
            insights = result.get("data", [])
            metrics = {
                "reach": 0,
                "impressions": 0,
                "engagement": 0,
                "clicks": 0,  # Instagram doesn't provide clicks directly
                "last_updated": datetime.now().isoformat()
            }

            for insight in insights:
                metric_name = insight.get("name")
                values = insight.get("values", [])

                if not values:
                    continue

                value = values[0].get("value", 0)

                if metric_name == "reach":
                    metrics["reach"] = value
                elif metric_name == "impressions":
                    metrics["impressions"] = value
                elif metric_name == "engagement":
                    metrics["engagement"] = value

            logger.info(f"Retrieved insights for Instagram media {media_id}")

            return metrics

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get Instagram insights: {e}")
            raise InstagramAPIError(f"Request failed: {e}")

    def get_user_info(self) -> Dict[str, Any]:
        """Get information about the Instagram account.

        Returns:
            Dictionary with account information

        Raises:
            InstagramAPIError: If request fails
        """
        try:
            endpoint = f"{self.BASE_URL}/{self.instagram_account_id}"

            params = {
                "access_token": self.access_token,
                "fields": "username,followers_count,follows_count,media_count"
            }

            response = self.session.get(endpoint, params=params)
            response.raise_for_status()

            result = response.json()

            if "error" in result:
                raise InstagramAPIError(f"Instagram API error: {result['error']}")

            logger.info(f"Retrieved Instagram account info: {result.get('username')}")

            return {
                "username": result.get("username"),
                "followers_count": result.get("followers_count", 0),
                "follows_count": result.get("follows_count", 0),
                "media_count": result.get("media_count", 0)
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get Instagram account info: {e}")
            raise InstagramAPIError(f"Request failed: {e}")

    def check_daily_limit(self) -> Dict[str, Any]:
        """Check daily posting limit status.

        Returns:
            Dictionary with limit information
        """
        # Instagram has a 25 posts per day limit
        # This would need to track posts in vault to calculate remaining
        return {
            "daily_limit": 25,
            "remaining": "unknown",  # Would need to count today's posts
            "reset_time": "midnight UTC"
        }
