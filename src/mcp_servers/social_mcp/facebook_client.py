"""Facebook Graph API Client for Gold Tier.

Provides interface to Facebook Graph API for posting and metrics collection.
"""

import logging
import os
from typing import Dict, Optional, Any
from datetime import datetime
import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()


class FacebookAPIError(Exception):
    """Raised when Facebook API call fails."""
    pass


class FacebookGraphAPI:
    """Client for Facebook Graph API v18.0.

    Features:
    - Post to Facebook page
    - Post photos with captions
    - Retrieve post insights (reach, engagement, clicks)
    - Get page information
    - Rate limiting: 200 calls/hour per page
    """

    BASE_URL = "https://graph.facebook.com/v18.0"

    def __init__(self, access_token: Optional[str] = None, page_id: Optional[str] = None):
        """Initialize Facebook Graph API client.

        Args:
            access_token: Facebook page access token (default: from FACEBOOK_ACCESS_TOKEN env var)
            page_id: Facebook page ID (default: from FACEBOOK_PAGE_ID env var)
        """
        self.access_token = access_token or os.getenv('FACEBOOK_ACCESS_TOKEN')
        self.page_id = page_id or os.getenv('FACEBOOK_PAGE_ID')

        if not self.access_token:
            raise ValueError("Facebook access token not configured. Set FACEBOOK_ACCESS_TOKEN")

        if not self.page_id:
            raise ValueError("Facebook page ID not configured. Set FACEBOOK_PAGE_ID")

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AI-Employee-Bot/1.0'
        })

    def post_to_page(self, message: str, link: Optional[str] = None) -> Dict[str, Any]:
        """Post text message to Facebook page.

        Args:
            message: Post message/caption
            link: Optional URL to include in post

        Returns:
            Dictionary with post_id

        Raises:
            FacebookAPIError: If post fails
        """
        try:
            endpoint = f"{self.BASE_URL}/{self.page_id}/feed"

            data = {
                "access_token": self.access_token,
                "message": message
            }

            if link:
                data["link"] = link

            response = self.session.post(endpoint, data=data)
            response.raise_for_status()

            result = response.json()

            if "error" in result:
                raise FacebookAPIError(f"Facebook API error: {result['error']}")

            logger.info(f"Posted to Facebook: {result.get('id')}")

            return {
                "success": True,
                "post_id": result.get("id"),
                "message": "Posted to Facebook successfully"
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to post to Facebook: {e}")
            raise FacebookAPIError(f"Request failed: {e}")

    def post_photo(self, image_url: str, caption: str) -> Dict[str, Any]:
        """Post photo to Facebook page.

        Args:
            image_url: URL of image to post
            caption: Photo caption

        Returns:
            Dictionary with post_id

        Raises:
            FacebookAPIError: If post fails
        """
        try:
            endpoint = f"{self.BASE_URL}/{self.page_id}/photos"

            data = {
                "access_token": self.access_token,
                "url": image_url,
                "caption": caption
            }

            response = self.session.post(endpoint, data=data)
            response.raise_for_status()

            result = response.json()

            if "error" in result:
                raise FacebookAPIError(f"Facebook API error: {result['error']}")

            logger.info(f"Posted photo to Facebook: {result.get('id')}")

            return {
                "success": True,
                "post_id": result.get("id"),
                "message": "Posted photo to Facebook successfully"
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to post photo to Facebook: {e}")
            raise FacebookAPIError(f"Request failed: {e}")

    def get_insights(self, post_id: str) -> Dict[str, Any]:
        """Get insights (metrics) for a post.

        Args:
            post_id: Facebook post ID

        Returns:
            Dictionary with metrics (reach, impressions, engagement, clicks)

        Raises:
            FacebookAPIError: If request fails
        """
        try:
            endpoint = f"{self.BASE_URL}/{post_id}/insights"

            params = {
                "access_token": self.access_token,
                "metric": "post_impressions,post_engaged_users,post_clicks"
            }

            response = self.session.get(endpoint, params=params)
            response.raise_for_status()

            result = response.json()

            if "error" in result:
                raise FacebookAPIError(f"Facebook API error: {result['error']}")

            # Parse insights data
            insights = result.get("data", [])
            metrics = {
                "reach": 0,
                "impressions": 0,
                "engagement": 0,
                "clicks": 0,
                "last_updated": datetime.now().isoformat()
            }

            for insight in insights:
                metric_name = insight.get("name")
                values = insight.get("values", [])

                if not values:
                    continue

                value = values[0].get("value", 0)

                if metric_name == "post_impressions":
                    metrics["impressions"] = value
                    metrics["reach"] = value  # Approximate reach with impressions
                elif metric_name == "post_engaged_users":
                    metrics["engagement"] = value
                elif metric_name == "post_clicks":
                    metrics["clicks"] = value

            logger.info(f"Retrieved insights for Facebook post {post_id}")

            return metrics

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get Facebook insights: {e}")
            raise FacebookAPIError(f"Request failed: {e}")

    def get_page_info(self) -> Dict[str, Any]:
        """Get information about the Facebook page.

        Returns:
            Dictionary with page information

        Raises:
            FacebookAPIError: If request fails
        """
        try:
            endpoint = f"{self.BASE_URL}/{self.page_id}"

            params = {
                "access_token": self.access_token,
                "fields": "name,fan_count,followers_count"
            }

            response = self.session.get(endpoint, params=params)
            response.raise_for_status()

            result = response.json()

            if "error" in result:
                raise FacebookAPIError(f"Facebook API error: {result['error']}")

            logger.info(f"Retrieved Facebook page info: {result.get('name')}")

            return {
                "name": result.get("name"),
                "fan_count": result.get("fan_count", 0),
                "followers_count": result.get("followers_count", 0)
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get Facebook page info: {e}")
            raise FacebookAPIError(f"Request failed: {e}")

    def delete_post(self, post_id: str) -> bool:
        """Delete a post from Facebook page.

        Args:
            post_id: Facebook post ID

        Returns:
            True if deletion successful

        Raises:
            FacebookAPIError: If deletion fails
        """
        try:
            endpoint = f"{self.BASE_URL}/{post_id}"

            params = {
                "access_token": self.access_token
            }

            response = self.session.delete(endpoint, params=params)
            response.raise_for_status()

            result = response.json()

            if "error" in result:
                raise FacebookAPIError(f"Facebook API error: {result['error']}")

            logger.info(f"Deleted Facebook post: {post_id}")

            return result.get("success", False)

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to delete Facebook post: {e}")
            raise FacebookAPIError(f"Request failed: {e}")

    def check_rate_limit(self) -> Dict[str, Any]:
        """Check current rate limit status.

        Returns:
            Dictionary with rate limit information
        """
        # Facebook includes rate limit info in response headers
        # This is a simplified version - full implementation would track headers
        return {
            "limit": 200,  # 200 calls per hour
            "remaining": "unknown",  # Would need to track from headers
            "reset_time": "unknown"
        }
