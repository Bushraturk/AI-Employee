"""
LinkedIn Posting Skill
Wraps LinkedIn posting functionality as an agent skill
"""
import logging
from typing import Dict, Any
from pathlib import Path

from skills.framework import Skill
from linkedin.poster import LinkedInPoster
from linkedin.post_generator import PostGenerator

logger = logging.getLogger(__name__)


class LinkedInPostingSkill(Skill):
    """Skill for posting to LinkedIn"""

    def __init__(self, vault_path: str, config: Dict[str, Any]):
        """
        Initialize LinkedIn posting skill

        Args:
            vault_path: Path to vault directory
            config: Configuration dictionary
        """
        super().__init__(
            skill_id='linkedin_posting',
            name='LinkedIn Auto-Posting',
            description='Generates and posts business updates to LinkedIn',
            category='communication'
        )

        self.vault_path = Path(vault_path)
        self.poster = LinkedInPoster(str(vault_path), config)
        self.post_generator = PostGenerator(str(vault_path), config)

    def validate_context(self, context: Dict[str, Any]) -> bool:
        """
        Validate execution context

        Args:
            context: Must contain 'action' (generate or post) and relevant data

        Returns:
            True if valid, False otherwise
        """
        if 'action' not in context:
            logger.error("LinkedIn skill requires 'action' in context")
            return False

        action = context['action']
        if action not in ['generate', 'post']:
            logger.error(f"Invalid action: {action}")
            return False

        if action == 'post' and 'approval_id' not in context:
            logger.error("Post action requires 'approval_id'")
            return False

        return True

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute LinkedIn posting skill

        Args:
            context: Execution context with action and data

        Returns:
            Result with success status and details
        """
        action = context['action']

        if action == 'generate':
            # Generate post content
            business_context = context.get('business_context', {})
            post_content = self.post_generator.generate_post(business_context)

            return {
                'action': 'generate',
                'success': True,
                'post_content': post_content
            }

        elif action == 'post':
            # Post to LinkedIn
            approval_id = context['approval_id']
            result = self.poster.post_approved(approval_id)

            return {
                'action': 'post',
                'success': result.get('success', False),
                'post_id': result.get('post_id'),
                'error': result.get('error')
            }
