"""Social Media MCP Server for Gold Tier.

Provides multi-platform social media posting and metrics collection via JSON-RPC interface.
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.mcp_servers.social_mcp.facebook_client import FacebookGraphAPI
from src.mcp_servers.social_mcp.instagram_client import InstagramGraphAPI
from src.mcp_servers.social_mcp.twitter_client import TwitterAPIClient
from src.models.social_media_post import SocialMediaPost, Platform, PostStatus
from src.services.error_recovery import ErrorRecoveryService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SocialMCPServer:
    """MCP Server for multi-platform social media management.

    Provides tools:
    - post_facebook: Post to Facebook page
    - post_instagram: Post to Instagram (two-step publishing)
    - post_twitter: Post to Twitter
    - post_linkedin: Post to LinkedIn (placeholder)
    - collect_social_metrics: Collect performance metrics from all platforms
    """

    def __init__(self, vault_path: Path):
        """Initialize social media MCP server.

        Args:
            vault_path: Path to AI Employee vault
        """
        self.vault_path = vault_path
        self.error_recovery = ErrorRecoveryService(vault_path)

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

        # Tool registry
        self.tools = {
            "post_facebook": self.post_facebook,
            "post_instagram": self.post_instagram,
            "post_twitter": self.post_twitter,
            "post_linkedin": self.post_linkedin,
            "collect_social_metrics": self.collect_social_metrics,
        }

        logger.info("Social Media MCP Server initialized")

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming JSON-RPC request.

        Args:
            request: JSON-RPC request dictionary

        Returns:
            JSON-RPC response dictionary
        """
        try:
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")

            if method not in self.tools:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }

            # Execute tool
            result = self.tools[method](**params)

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }

        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }

    def post_facebook(self, post_id: str) -> Dict[str, Any]:
        """Post to Facebook page.

        Args:
            post_id: SocialMediaPost ID to publish

        Returns:
            Publishing result dictionary
        """
        try:
            if not self.facebook_client:
                return {
                    "success": False,
                    "error": "Facebook client not initialized"
                }

            # Load post from vault
            post = SocialMediaPost.load(self.vault_path, post_id)

            # Check if post is approved
            if post.status != PostStatus.APPROVED:
                return {
                    "success": False,
                    "error": f"Post must be approved before publishing (current status: {post.status.value})"
                }

            # Check if Facebook is in platforms
            if Platform.FACEBOOK not in post.platforms:
                return {
                    "success": False,
                    "error": "Post is not targeted for Facebook"
                }

            # Post to Facebook
            if post.media_urls:
                # Post with photo
                result = self.facebook_client.post_photo(
                    image_url=post.media_urls[0],
                    caption=post.content
                )
            else:
                # Post text only
                result = self.facebook_client.post_to_page(
                    message=post.content
                )

            # Update post status
            if result.get("success"):
                post.mark_posted()
                post.save(self.vault_path)

            return result

        except Exception as e:
            logger.error(f"Failed to post to Facebook: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def post_instagram(self, post_id: str) -> Dict[str, Any]:
        """Post to Instagram (two-step publishing).

        Args:
            post_id: SocialMediaPost ID to publish

        Returns:
            Publishing result dictionary
        """
        try:
            if not self.instagram_client:
                return {
                    "success": False,
                    "error": "Instagram client not initialized"
                }

            # Load post from vault
            post = SocialMediaPost.load(self.vault_path, post_id)

            # Check if post is approved
            if post.status != PostStatus.APPROVED:
                return {
                    "success": False,
                    "error": f"Post must be approved before publishing (current status: {post.status.value})"
                }

            # Check if Instagram is in platforms
            if Platform.INSTAGRAM not in post.platforms:
                return {
                    "success": False,
                    "error": "Post is not targeted for Instagram"
                }

            # Instagram requires media
            if not post.media_urls:
                return {
                    "success": False,
                    "error": "Instagram posts require media (image URL)"
                }

            # Post to Instagram (two-step process)
            result = self.instagram_client.post_photo(
                image_url=post.media_urls[0],
                caption=post.content
            )

            # Update post status
            if result.get("success"):
                post.mark_posted()
                post.save(self.vault_path)

            return result

        except Exception as e:
            logger.error(f"Failed to post to Instagram: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def post_twitter(self, post_id: str) -> Dict[str, Any]:
        """Post to Twitter.

        Args:
            post_id: SocialMediaPost ID to publish

        Returns:
            Publishing result dictionary
        """
        try:
            if not self.twitter_client:
                return {
                    "success": False,
                    "error": "Twitter client not initialized"
                }

            # Load post from vault
            post = SocialMediaPost.load(self.vault_path, post_id)

            # Check if post is approved
            if post.status != PostStatus.APPROVED:
                return {
                    "success": False,
                    "error": f"Post must be approved before publishing (current status: {post.status.value})"
                }

            # Check if Twitter is in platforms
            if Platform.TWITTER not in post.platforms:
                return {
                    "success": False,
                    "error": "Post is not targeted for Twitter"
                }

            # Check character limit
            if len(post.content) > 280:
                return {
                    "success": False,
                    "error": "Content exceeds Twitter's 280 character limit"
                }

            # Post to Twitter
            if post.media_urls:
                # Post with media
                result = self.twitter_client.create_tweet_with_media(
                    text=post.content,
                    media_path=post.media_urls[0]
                )
            else:
                # Post text only
                result = self.twitter_client.create_tweet(
                    text=post.content
                )

            # Update post status
            if result.get("success"):
                post.mark_posted()
                post.save(self.vault_path)

            return result

        except Exception as e:
            logger.error(f"Failed to post to Twitter: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def post_linkedin(self, post_id: str) -> Dict[str, Any]:
        """Post to LinkedIn (placeholder).

        Args:
            post_id: SocialMediaPost ID to publish

        Returns:
            Publishing result dictionary
        """
        # LinkedIn integration is from Silver Tier
        # This is a placeholder for Gold Tier integration
        return {
            "success": False,
            "error": "LinkedIn posting not yet implemented in Gold Tier"
        }

    def collect_social_metrics(self, post_id: str) -> Dict[str, Any]:
        """Collect performance metrics from all platforms for a post.

        Args:
            post_id: SocialMediaPost ID

        Returns:
            Metrics collection result dictionary
        """
        try:
            # Load post from vault
            post = SocialMediaPost.load(self.vault_path, post_id)

            # Check if post is published
            if post.status != PostStatus.POSTED:
                return {
                    "success": False,
                    "error": f"Post must be published to collect metrics (current status: {post.status.value})"
                }

            metrics_collected = {}

            # Collect Facebook metrics
            if Platform.FACEBOOK in post.platforms and self.facebook_client:
                try:
                    # Note: Would need to store platform-specific post IDs
                    # This is simplified - full implementation would track post IDs per platform
                    logger.info("Facebook metrics collection not yet implemented")
                    metrics_collected["facebook"] = "not_implemented"
                except Exception as e:
                    logger.error(f"Failed to collect Facebook metrics: {e}")
                    metrics_collected["facebook"] = "error"

            # Collect Instagram metrics
            if Platform.INSTAGRAM in post.platforms and self.instagram_client:
                try:
                    logger.info("Instagram metrics collection not yet implemented")
                    metrics_collected["instagram"] = "not_implemented"
                except Exception as e:
                    logger.error(f"Failed to collect Instagram metrics: {e}")
                    metrics_collected["instagram"] = "error"

            # Collect Twitter metrics
            if Platform.TWITTER in post.platforms and self.twitter_client:
                try:
                    logger.info("Twitter metrics collection not yet implemented")
                    metrics_collected["twitter"] = "not_implemented"
                except Exception as e:
                    logger.error(f"Failed to collect Twitter metrics: {e}")
                    metrics_collected["twitter"] = "error"

            return {
                "success": True,
                "metrics_collected": metrics_collected,
                "message": "Metrics collection initiated"
            }

        except Exception as e:
            logger.error(f"Failed to collect social metrics: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def run(self) -> None:
        """Run MCP server (read from stdin, write to stdout)."""
        logger.info("Social Media MCP Server started")

        try:
            while True:
                # Read JSON-RPC request from stdin
                line = sys.stdin.readline()

                if not line:
                    break

                try:
                    request = json.loads(line)
                    response = self.handle_request(request)

                    # Write JSON-RPC response to stdout
                    sys.stdout.write(json.dumps(response) + "\n")
                    sys.stdout.flush()

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        }
                    }
                    sys.stdout.write(json.dumps(error_response) + "\n")
                    sys.stdout.flush()

        except KeyboardInterrupt:
            logger.info("Social Media MCP Server stopped")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Social Media MCP Server")
    parser.add_argument("--vault", type=str, required=True, help="Path to AI Employee vault")
    args = parser.parse_args()

    vault_path = Path(args.vault)

    if not vault_path.exists():
        logger.error(f"Vault path does not exist: {vault_path}")
        sys.exit(1)

    server = SocialMCPServer(vault_path)
    server.run()


if __name__ == "__main__":
    main()
