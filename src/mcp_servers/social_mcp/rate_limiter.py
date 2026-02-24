"""Rate Limiter for Social Media APIs.

Enforces platform-specific rate limits to prevent API throttling.
"""

import logging
import time
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime, timedelta
from collections import deque

from src.models.social_media_post import Platform

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for social media API calls.

    Features:
    - Platform-specific rate limits
    - Sliding window rate limiting
    - Automatic wait when limit reached
    - Persistent rate limit tracking
    - Daily limit enforcement (Instagram)
    """

    # Platform-specific rate limits
    RATE_LIMITS = {
        Platform.FACEBOOK: {
            "calls_per_hour": 200,
            "calls_per_day": None,  # No daily limit
            "window_seconds": 3600
        },
        Platform.INSTAGRAM: {
            "calls_per_hour": None,  # No hourly limit
            "calls_per_day": 25,  # 25 posts per day
            "window_seconds": 86400
        },
        Platform.TWITTER: {
            "calls_per_hour": 100,  # 300 per 3 hours = ~100/hour
            "calls_per_day": None,
            "window_seconds": 3600
        },
        Platform.LINKEDIN: {
            "calls_per_hour": 100,
            "calls_per_day": None,
            "window_seconds": 3600
        }
    }

    def __init__(self, vault_path: Path):
        """Initialize rate limiter.

        Args:
            vault_path: Path to AI Employee vault
        """
        self.vault_path = vault_path
        self.rate_limit_dir = vault_path / "System" / "rate_limits"
        self.rate_limit_dir.mkdir(parents=True, exist_ok=True)

        # In-memory tracking (sliding window)
        self.call_history: Dict[Platform, deque] = {
            platform: deque() for platform in Platform
        }

        # Load existing rate limit data
        self._load_rate_limits()

    def _load_rate_limits(self) -> None:
        """Load rate limit history from vault."""
        for platform in Platform:
            rate_file = self.rate_limit_dir / f"{platform.value}_calls.txt"
            if rate_file.exists():
                try:
                    lines = rate_file.read_text().strip().split('\n')
                    for line in lines:
                        if line:
                            timestamp = float(line)
                            self.call_history[platform].append(timestamp)
                except Exception as e:
                    logger.error(f"Failed to load rate limits for {platform.value}: {e}")

    def _save_rate_limits(self, platform: Platform) -> None:
        """Save rate limit history to vault.

        Args:
            platform: Platform to save
        """
        try:
            rate_file = self.rate_limit_dir / f"{platform.value}_calls.txt"
            timestamps = '\n'.join(str(ts) for ts in self.call_history[platform])
            rate_file.write_text(timestamps)
        except Exception as e:
            logger.error(f"Failed to save rate limits for {platform.value}: {e}")

    def check_rate_limit(self, platform: Platform) -> Dict[str, any]:
        """Check if rate limit allows a new call.

        Args:
            platform: Platform to check

        Returns:
            Dictionary with rate limit status
        """
        limits = self.RATE_LIMITS.get(platform, {})
        current_time = time.time()

        # Clean old entries
        self._clean_old_entries(platform, current_time)

        # Check hourly limit
        if limits.get("calls_per_hour"):
            hourly_calls = self._count_calls_in_window(
                platform,
                current_time,
                3600
            )

            if hourly_calls >= limits["calls_per_hour"]:
                wait_time = self._calculate_wait_time(platform, 3600)
                return {
                    "allowed": False,
                    "reason": "hourly_limit_reached",
                    "limit": limits["calls_per_hour"],
                    "current": hourly_calls,
                    "wait_seconds": wait_time,
                    "reset_at": datetime.fromtimestamp(current_time + wait_time).isoformat()
                }

        # Check daily limit
        if limits.get("calls_per_day"):
            daily_calls = self._count_calls_in_window(
                platform,
                current_time,
                86400
            )

            if daily_calls >= limits["calls_per_day"]:
                wait_time = self._calculate_wait_time(platform, 86400)
                return {
                    "allowed": False,
                    "reason": "daily_limit_reached",
                    "limit": limits["calls_per_day"],
                    "current": daily_calls,
                    "wait_seconds": wait_time,
                    "reset_at": datetime.fromtimestamp(current_time + wait_time).isoformat()
                }

        # Rate limit allows call
        return {
            "allowed": True,
            "hourly_remaining": (
                limits.get("calls_per_hour", 0) -
                self._count_calls_in_window(platform, current_time, 3600)
            ) if limits.get("calls_per_hour") else None,
            "daily_remaining": (
                limits.get("calls_per_day", 0) -
                self._count_calls_in_window(platform, current_time, 86400)
            ) if limits.get("calls_per_day") else None
        }

    def record_call(self, platform: Platform) -> None:
        """Record an API call for rate limiting.

        Args:
            platform: Platform that was called
        """
        current_time = time.time()
        self.call_history[platform].append(current_time)

        # Save to vault
        self._save_rate_limits(platform)

        logger.debug(f"Recorded API call for {platform.value}")

    def wait_if_needed(self, platform: Platform, max_wait: int = 300) -> bool:
        """Wait if rate limit is reached.

        Args:
            platform: Platform to check
            max_wait: Maximum seconds to wait (default: 5 minutes)

        Returns:
            True if call can proceed, False if max wait exceeded
        """
        status = self.check_rate_limit(platform)

        if status["allowed"]:
            return True

        wait_time = status.get("wait_seconds", 0)

        if wait_time > max_wait:
            logger.warning(
                f"Rate limit wait time ({wait_time}s) exceeds max wait ({max_wait}s) "
                f"for {platform.value}"
            )
            return False

        logger.info(
            f"Rate limit reached for {platform.value}. "
            f"Waiting {wait_time} seconds..."
        )

        time.sleep(wait_time)
        return True

    def _clean_old_entries(self, platform: Platform, current_time: float) -> None:
        """Remove entries older than the longest window.

        Args:
            platform: Platform to clean
            current_time: Current timestamp
        """
        limits = self.RATE_LIMITS.get(platform, {})
        max_window = max(
            limits.get("window_seconds", 3600),
            86400 if limits.get("calls_per_day") else 0
        )

        cutoff_time = current_time - max_window

        while self.call_history[platform] and self.call_history[platform][0] < cutoff_time:
            self.call_history[platform].popleft()

    def _count_calls_in_window(self, platform: Platform, current_time: float,
                               window_seconds: int) -> int:
        """Count API calls within a time window.

        Args:
            platform: Platform to count
            current_time: Current timestamp
            window_seconds: Window size in seconds

        Returns:
            Number of calls in window
        """
        cutoff_time = current_time - window_seconds
        return sum(1 for ts in self.call_history[platform] if ts >= cutoff_time)

    def _calculate_wait_time(self, platform: Platform, window_seconds: int) -> int:
        """Calculate time to wait until rate limit resets.

        Args:
            platform: Platform to check
            window_seconds: Window size in seconds

        Returns:
            Seconds to wait
        """
        if not self.call_history[platform]:
            return 0

        oldest_call = self.call_history[platform][0]
        current_time = time.time()
        time_since_oldest = current_time - oldest_call

        wait_time = window_seconds - time_since_oldest

        return max(0, int(wait_time) + 1)

    def get_rate_limit_status(self, platform: Platform) -> Dict[str, any]:
        """Get current rate limit status for a platform.

        Args:
            platform: Platform to check

        Returns:
            Status dictionary
        """
        limits = self.RATE_LIMITS.get(platform, {})
        current_time = time.time()

        self._clean_old_entries(platform, current_time)

        hourly_calls = self._count_calls_in_window(platform, current_time, 3600)
        daily_calls = self._count_calls_in_window(platform, current_time, 86400)

        return {
            "platform": platform.value,
            "hourly_limit": limits.get("calls_per_hour"),
            "hourly_used": hourly_calls,
            "hourly_remaining": (
                limits.get("calls_per_hour", 0) - hourly_calls
            ) if limits.get("calls_per_hour") else None,
            "daily_limit": limits.get("calls_per_day"),
            "daily_used": daily_calls,
            "daily_remaining": (
                limits.get("calls_per_day", 0) - daily_calls
            ) if limits.get("calls_per_day") else None,
            "total_calls_tracked": len(self.call_history[platform])
        }

    def get_all_rate_limit_status(self) -> Dict[str, Dict[str, any]]:
        """Get rate limit status for all platforms.

        Returns:
            Dictionary mapping platform to status
        """
        return {
            platform.value: self.get_rate_limit_status(platform)
            for platform in Platform
        }

    def reset_rate_limits(self, platform: Optional[Platform] = None) -> None:
        """Reset rate limit tracking (for testing/debugging).

        Args:
            platform: Platform to reset, or None for all platforms
        """
        if platform:
            self.call_history[platform].clear()
            self._save_rate_limits(platform)
            logger.info(f"Reset rate limits for {platform.value}")
        else:
            for p in Platform:
                self.call_history[p].clear()
                self._save_rate_limits(p)
            logger.info("Reset rate limits for all platforms")
