"""
LinkedIn Poster

Handles posting content to LinkedIn via API with approval workflow integration.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import requests

from watchers.auth.linkedin_auth import LinkedInAuth
from linkedin.post_generator import LinkedInPostGenerator
from approval.queue import ApprovalQueue
from approval.risk_classifier import RiskClassifier

logger = logging.getLogger(__name__)


class LinkedInPoster:
    """Post content to LinkedIn with approval workflow"""

    def __init__(self, vault_path: str, config: Dict[str, Any] = None):
        """
        Initialize LinkedIn poster

        Args:
            vault_path: Path to vault directory
            config: Configuration with:
                - require_approval: Require approval before posting (default: True)
                - auto_approve_low_risk: Auto-approve low risk posts (default: False)
                - track_performance: Track post performance (default: True)
        """
        self.vault_path = Path(vault_path)
        self.config = config or {}

        # Configuration
        self.require_approval = self.config.get('require_approval', True)
        self.auto_approve_low_risk = self.config.get('auto_approve_low_risk', False)
        self.track_performance = self.config.get('track_performance', True)

        # Components
        self.auth = LinkedInAuth()
        self.post_generator = LinkedInPostGenerator(str(vault_path), config)
        self.approval_queue = ApprovalQueue(str(vault_path))

        # API endpoints
        self.api_base_url = 'https://api.linkedin.com/v2'

        # Performance tracking
        self.posts_path = self.vault_path / 'LinkedIn_Posts'
        self.posts_path.mkdir(parents=True, exist_ok=True)

    def create_post(self, post_type: str = 'product', topic: str = None) -> Dict[str, Any]:
        """
        Create LinkedIn post and submit for approval

        Args:
            post_type: Type of post (product, service, value, insight, announcement)
            topic: Optional specific topic

        Returns:
            Dictionary with post ID and approval ID
        """
        # Generate post
        post_data = self.post_generator.generate_post(post_type, topic)

        # Save post
        post_id = self.post_generator.save_post(post_data)

        if not post_id:
            logger.error("Failed to save post")
            return None

        # Check if approval required
        if self.require_approval:
            # Classify risk
            risk = RiskClassifier.classify_action(
                action_type='post_linkedin',
                action_details={'content': post_data['content']}
            )

            # Auto-approve low risk if configured
            if self.auto_approve_low_risk and risk['risk_level'] == 'low':
                post_data['status'] = 'approved'
                post_data['approved_at'] = datetime.now().isoformat()
                post_data['approved_by'] = 'auto'
                self.post_generator.save_post(post_data)

                logger.info(f"Auto-approved low risk post: {post_id}")

                return {
                    'post_id': post_id,
                    'status': 'approved',
                    'approval_id': None
                }

            # Create approval request
            approval_id = self.approval_queue.create_approval(
                action_type='post_linkedin',
                description=f"Post to LinkedIn: {post_data['post_type']}",
                action_details={
                    'post_id': post_id,
                    'content': post_data['content'],
                    'hashtags': post_data['hashtags'],
                    'scheduled_time': post_data['scheduled_time']
                },
                risk_level=risk['risk_level'],
                risk_factors=risk['risk_factors']
            )

            logger.info(f"Created approval request for post: {post_id} (approval: {approval_id})")

            return {
                'post_id': post_id,
                'status': 'pending_approval',
                'approval_id': approval_id
            }

        else:
            # No approval required, mark as approved
            post_data['status'] = 'approved'
            post_data['approved_at'] = datetime.now().isoformat()
            self.post_generator.save_post(post_data)

            return {
                'post_id': post_id,
                'status': 'approved',
                'approval_id': None
            }

    def post_to_linkedin(self, post_id: str) -> bool:
        """
        Post content to LinkedIn

        Args:
            post_id: Post ID

        Returns:
            True if successful
        """
        # Get post data
        post_data = self.post_generator.get_post(post_id)

        if not post_data:
            logger.error(f"Post not found: {post_id}")
            return False

        # Check if approved
        if post_data.get('status') != 'approved':
            logger.error(f"Post not approved: {post_id}")
            return False

        # Authenticate
        if not self.auth.authenticate():
            logger.error("LinkedIn authentication failed")
            return False

        try:
            # Get user profile ID
            profile_id = self._get_profile_id()

            if not profile_id:
                logger.error("Failed to get LinkedIn profile ID")
                return False

            # Create post payload
            payload = self._create_post_payload(profile_id, post_data)

            # Post to LinkedIn
            headers = self.auth.get_headers()
            response = requests.post(
                f'{self.api_base_url}/ugcPosts',
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 201:
                # Success
                post_data['status'] = 'posted'
                post_data['posted_at'] = datetime.now().isoformat()
                post_data['linkedin_post_id'] = response.json().get('id')

                # Track performance if enabled
                if self.track_performance:
                    post_data['performance'] = {
                        'views': 0,
                        'likes': 0,
                        'comments': 0,
                        'shares': 0,
                        'last_updated': datetime.now().isoformat()
                    }

                self.post_generator.save_post(post_data)

                logger.info(f"Successfully posted to LinkedIn: {post_id}")
                return True

            else:
                logger.error(f"LinkedIn API error: {response.status_code} - {response.text}")
                post_data['status'] = 'failed'
                post_data['error'] = f"API error: {response.status_code}"
                self.post_generator.save_post(post_data)
                return False

        except Exception as e:
            logger.error(f"Error posting to LinkedIn: {e}")
            post_data['status'] = 'failed'
            post_data['error'] = str(e)
            self.post_generator.save_post(post_data)
            return False

    def update_post_performance(self, post_id: str) -> Optional[Dict[str, Any]]:
        """
        Update post performance metrics

        Args:
            post_id: Post ID

        Returns:
            Performance metrics dictionary or None
        """
        if not self.track_performance:
            return None

        post_data = self.post_generator.get_post(post_id)

        if not post_data or post_data.get('status') != 'posted':
            return None

        linkedin_post_id = post_data.get('linkedin_post_id')

        if not linkedin_post_id:
            return None

        try:
            # Get post analytics
            headers = self.auth.get_headers()
            response = requests.get(
                f'{self.api_base_url}/socialActions/{linkedin_post_id}',
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                analytics = response.json()

                # Update performance metrics
                performance = {
                    'views': analytics.get('impressionCount', 0),
                    'likes': analytics.get('likeCount', 0),
                    'comments': analytics.get('commentCount', 0),
                    'shares': analytics.get('shareCount', 0),
                    'last_updated': datetime.now().isoformat()
                }

                post_data['performance'] = performance
                self.post_generator.save_post(post_data)

                logger.info(f"Updated performance for post: {post_id}")
                return performance

            else:
                logger.warning(f"Failed to get post analytics: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error updating post performance: {e}")
            return None

    def get_post_history(self, limit: int = 10) -> list:
        """
        Get post history

        Args:
            limit: Maximum number of posts to return

        Returns:
            List of post data dictionaries
        """
        posts = self.post_generator.list_posts()
        return posts[:limit]

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get performance summary across all posts

        Returns:
            Summary dictionary with aggregate metrics
        """
        posts = self.post_generator.list_posts(status='posted')

        summary = {
            'total_posts': len(posts),
            'total_views': 0,
            'total_likes': 0,
            'total_comments': 0,
            'total_shares': 0,
            'avg_views': 0,
            'avg_likes': 0,
            'avg_comments': 0,
            'avg_shares': 0
        }

        if not posts:
            return summary

        for post in posts:
            performance = post.get('performance', {})
            summary['total_views'] += performance.get('views', 0)
            summary['total_likes'] += performance.get('likes', 0)
            summary['total_comments'] += performance.get('comments', 0)
            summary['total_shares'] += performance.get('shares', 0)

        # Calculate averages
        summary['avg_views'] = summary['total_views'] / len(posts)
        summary['avg_likes'] = summary['total_likes'] / len(posts)
        summary['avg_comments'] = summary['total_comments'] / len(posts)
        summary['avg_shares'] = summary['total_shares'] / len(posts)

        return summary

    def _get_profile_id(self) -> Optional[str]:
        """Get LinkedIn profile ID"""
        try:
            headers = self.auth.get_headers()
            response = requests.get(
                f'{self.api_base_url}/me',
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                profile = response.json()
                return profile.get('id')

            return None

        except Exception as e:
            logger.error(f"Error getting profile ID: {e}")
            return None

    def _create_post_payload(self, profile_id: str, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create LinkedIn post payload"""
        return {
            'author': f'urn:li:person:{profile_id}',
            'lifecycleState': 'PUBLISHED',
            'specificContent': {
                'com.linkedin.ugc.ShareContent': {
                    'shareCommentary': {
                        'text': post_data['content']
                    },
                    'shareMediaCategory': 'NONE'
                }
            },
            'visibility': {
                'com.linkedin.ugc.MemberNetworkVisibility': 'PUBLIC'
            }
        }

    def handle_approval_decision(self, approval_id: str, decision: str) -> bool:
        """
        Handle approval decision for LinkedIn post

        Args:
            approval_id: Approval ID
            decision: Decision (approved/rejected)

        Returns:
            True if handled successfully
        """
        # Get approval
        approval = self.approval_queue.get_approval(approval_id)

        if not approval:
            logger.error(f"Approval not found: {approval_id}")
            return False

        # Get post ID from approval
        post_id = approval.get('action_details', {}).get('post_id')

        if not post_id:
            logger.error(f"Post ID not found in approval: {approval_id}")
            return False

        # Update post status
        if decision == 'approved':
            success = self.post_generator.update_post_status(
                post_id,
                'approved',
                f"Approved via {approval_id}"
            )

            if success:
                logger.info(f"Post approved: {post_id}")
                # Optionally auto-post
                # self.post_to_linkedin(post_id)

            return success

        elif decision == 'rejected':
            success = self.post_generator.update_post_status(
                post_id,
                'rejected',
                f"Rejected via {approval_id}"
            )

            if success:
                logger.info(f"Post rejected: {post_id}")

            return success

        return False
