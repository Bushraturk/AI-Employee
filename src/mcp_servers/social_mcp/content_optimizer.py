"""Content Optimizer for Social Media.

Adapts content for platform-specific requirements and best practices.
"""

import logging
import re
from typing import Dict, List, Optional
from src.models.social_media_post import Platform

logger = logging.getLogger(__name__)


class ContentOptimizer:
    """Optimizes content for different social media platforms.

    Features:
    - Character limit enforcement
    - Hashtag optimization per platform
    - Media format validation
    - Platform-specific best practices
    """

    # Platform-specific character limits
    CHAR_LIMITS = {
        Platform.TWITTER: 280,
        Platform.FACEBOOK: 2200,
        Platform.INSTAGRAM: 2200,
        Platform.LINKEDIN: 3000
    }

    # Platform-specific hashtag recommendations
    HASHTAG_LIMITS = {
        Platform.TWITTER: 2,  # 1-2 hashtags recommended
        Platform.FACEBOOK: 3,  # 2-3 hashtags recommended
        Platform.INSTAGRAM: 30,  # Up to 30 hashtags allowed
        Platform.LINKEDIN: 5  # 3-5 hashtags recommended
    }

    def optimize_for_platform(self, content: str, platform: Platform,
                             media_urls: Optional[List[str]] = None) -> Dict[str, any]:
        """Optimize content for a specific platform.

        Args:
            content: Original content
            platform: Target platform
            media_urls: Optional media URLs

        Returns:
            Dictionary with optimized content and metadata
        """
        result = {
            "platform": platform.value,
            "original_content": content,
            "optimized_content": content,
            "truncated": False,
            "warnings": [],
            "recommendations": []
        }

        # Check character limit
        char_limit = self.CHAR_LIMITS.get(platform, 2200)
        if len(content) > char_limit:
            result["optimized_content"] = self._truncate_content(content, char_limit)
            result["truncated"] = True
            result["warnings"].append(
                f"Content truncated from {len(content)} to {char_limit} characters"
            )

        # Optimize hashtags
        hashtag_result = self._optimize_hashtags(content, platform)
        if hashtag_result["modified"]:
            result["optimized_content"] = hashtag_result["content"]
            result["recommendations"].extend(hashtag_result["recommendations"])

        # Platform-specific optimizations
        if platform == Platform.TWITTER:
            result = self._optimize_for_twitter(result, media_urls)
        elif platform == Platform.INSTAGRAM:
            result = self._optimize_for_instagram(result, media_urls)
        elif platform == Platform.FACEBOOK:
            result = self._optimize_for_facebook(result, media_urls)
        elif platform == Platform.LINKEDIN:
            result = self._optimize_for_linkedin(result, media_urls)

        return result

    def _truncate_content(self, content: str, limit: int) -> str:
        """Truncate content to character limit.

        Args:
            content: Content to truncate
            limit: Character limit

        Returns:
            Truncated content
        """
        if len(content) <= limit:
            return content

        # Try to truncate at word boundary
        truncated = content[:limit - 3]
        last_space = truncated.rfind(' ')

        if last_space > limit * 0.8:  # If we can save 80% of content
            truncated = truncated[:last_space]

        return truncated + "..."

    def _optimize_hashtags(self, content: str, platform: Platform) -> Dict[str, any]:
        """Optimize hashtags for platform.

        Args:
            content: Content with hashtags
            platform: Target platform

        Returns:
            Dictionary with optimized content and metadata
        """
        # Extract hashtags
        hashtags = re.findall(r'#\w+', content)
        hashtag_count = len(hashtags)

        recommended_limit = self.HASHTAG_LIMITS.get(platform, 5)

        result = {
            "content": content,
            "modified": False,
            "recommendations": []
        }

        if hashtag_count > recommended_limit:
            result["recommendations"].append(
                f"Consider reducing hashtags from {hashtag_count} to {recommended_limit} "
                f"for better {platform.value} engagement"
            )

        if hashtag_count == 0 and platform == Platform.INSTAGRAM:
            result["recommendations"].append(
                "Instagram posts perform better with hashtags (recommended: 5-10)"
            )

        return result

    def _optimize_for_twitter(self, result: Dict[str, any],
                             media_urls: Optional[List[str]]) -> Dict[str, any]:
        """Apply Twitter-specific optimizations.

        Args:
            result: Optimization result dictionary
            media_urls: Media URLs

        Returns:
            Updated result dictionary
        """
        content = result["optimized_content"]

        # Twitter best practices
        if len(content) < 100:
            result["recommendations"].append(
                "Twitter posts with 100-280 characters tend to get more engagement"
            )

        # Check for URLs (Twitter auto-shortens to 23 chars)
        urls = re.findall(r'https?://\S+', content)
        if urls:
            result["recommendations"].append(
                f"URLs will be shortened to 23 characters by Twitter (found {len(urls)} URLs)"
            )

        # Media recommendations
        if not media_urls:
            result["recommendations"].append(
                "Tweets with images get 150% more retweets"
            )

        return result

    def _optimize_for_instagram(self, result: Dict[str, any],
                               media_urls: Optional[List[str]]) -> Dict[str, any]:
        """Apply Instagram-specific optimizations.

        Args:
            result: Optimization result dictionary
            media_urls: Media URLs

        Returns:
            Updated result dictionary
        """
        content = result["optimized_content"]

        # Instagram requires media
        if not media_urls:
            result["warnings"].append(
                "Instagram posts require at least one image"
            )

        # Hashtag recommendations
        hashtags = re.findall(r'#\w+', content)
        if len(hashtags) < 5:
            result["recommendations"].append(
                "Instagram posts with 5-10 hashtags tend to perform better"
            )

        # First line is most important (preview)
        lines = content.split('\n')
        if lines and len(lines[0]) > 125:
            result["recommendations"].append(
                "Keep first line under 125 characters for better preview visibility"
            )

        return result

    def _optimize_for_facebook(self, result: Dict[str, any],
                              media_urls: Optional[List[str]]) -> Dict[str, any]:
        """Apply Facebook-specific optimizations.

        Args:
            result: Optimization result dictionary
            media_urls: Media URLs

        Returns:
            Updated result dictionary
        """
        content = result["optimized_content"]

        # Facebook best practices
        if len(content) < 40:
            result["recommendations"].append(
                "Facebook posts with 40-80 characters get higher engagement"
            )

        # Hashtag recommendations
        hashtags = re.findall(r'#\w+', content)
        if len(hashtags) > 3:
            result["recommendations"].append(
                "Facebook posts with 1-3 hashtags perform better than posts with many hashtags"
            )

        # Media recommendations
        if media_urls:
            result["recommendations"].append(
                "Facebook posts with images get 2.3x more engagement"
            )

        return result

    def _optimize_for_linkedin(self, result: Dict[str, any],
                              media_urls: Optional[List[str]]) -> Dict[str, any]:
        """Apply LinkedIn-specific optimizations.

        Args:
            result: Optimization result dictionary
            media_urls: Media URLs

        Returns:
            Updated result dictionary
        """
        content = result["optimized_content"]

        # LinkedIn best practices
        if len(content) < 150:
            result["recommendations"].append(
                "LinkedIn posts with 150-300 characters tend to get more engagement"
            )

        # Professional tone check (simplified)
        informal_words = ['lol', 'omg', 'btw', 'tbh']
        if any(word in content.lower() for word in informal_words):
            result["warnings"].append(
                "Consider using professional language for LinkedIn"
            )

        # Hashtag recommendations
        hashtags = re.findall(r'#\w+', content)
        if len(hashtags) < 3:
            result["recommendations"].append(
                "LinkedIn posts with 3-5 relevant hashtags increase discoverability"
            )

        return result

    def optimize_for_cross_post(self, content: str, platforms: List[Platform],
                               media_urls: Optional[List[str]] = None) -> Dict[Platform, Dict[str, any]]:
        """Optimize content for multiple platforms simultaneously.

        Args:
            content: Original content
            platforms: List of target platforms
            media_urls: Optional media URLs

        Returns:
            Dictionary mapping platform to optimization results
        """
        results = {}

        for platform in platforms:
            results[platform] = self.optimize_for_platform(content, platform, media_urls)

        # Check for cross-platform conflicts
        conflicts = self._check_cross_platform_conflicts(results)

        if conflicts:
            logger.warning(f"Cross-platform conflicts detected: {conflicts}")

        return results

    def _check_cross_platform_conflicts(self, results: Dict[Platform, Dict[str, any]]) -> List[str]:
        """Check for conflicts when posting to multiple platforms.

        Args:
            results: Optimization results per platform

        Returns:
            List of conflict descriptions
        """
        conflicts = []

        # Check if content was truncated for any platform
        truncated_platforms = [
            platform.value for platform, result in results.items()
            if result.get("truncated")
        ]

        if truncated_platforms:
            conflicts.append(
                f"Content truncated for: {', '.join(truncated_platforms)}"
            )

        # Check if Instagram is included without media
        if Platform.INSTAGRAM in results:
            instagram_result = results[Platform.INSTAGRAM]
            if "Instagram posts require at least one image" in instagram_result.get("warnings", []):
                conflicts.append("Instagram requires media but none provided")

        return conflicts

    def validate_media_format(self, media_url: str, platform: Platform) -> Dict[str, any]:
        """Validate media format for platform.

        Args:
            media_url: Media URL
            platform: Target platform

        Returns:
            Validation result dictionary
        """
        result = {
            "valid": True,
            "warnings": [],
            "recommendations": []
        }

        # Check file extension
        supported_formats = {
            Platform.TWITTER: ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
            Platform.FACEBOOK: ['.jpg', '.jpeg', '.png', '.gif', '.bmp'],
            Platform.INSTAGRAM: ['.jpg', '.jpeg', '.png'],
            Platform.LINKEDIN: ['.jpg', '.jpeg', '.png', '.gif']
        }

        platform_formats = supported_formats.get(platform, [])
        file_ext = media_url.lower().split('.')[-1]

        if f'.{file_ext}' not in platform_formats:
            result["valid"] = False
            result["warnings"].append(
                f"File format .{file_ext} may not be supported by {platform.value}"
            )

        # Platform-specific recommendations
        if platform == Platform.INSTAGRAM:
            result["recommendations"].append(
                "Instagram recommends square (1:1) or vertical (4:5) images"
            )

        return result
