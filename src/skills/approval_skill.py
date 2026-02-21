"""
Approval Skill
Wraps approval workflow functionality as an agent skill
"""
import logging
from typing import Dict, Any
from pathlib import Path

from skills.framework import Skill
from approval.queue import ApprovalQueue
from approval.risk_classifier import RiskClassifier

logger = logging.getLogger(__name__)


class ApprovalSkill(Skill):
    """Skill for managing approval workflow"""

    def __init__(self, vault_path: str, approval_queue: ApprovalQueue):
        """
        Initialize approval skill

        Args:
            vault_path: Path to vault directory
            approval_queue: ApprovalQueue instance
        """
        super().__init__(
            skill_id='approval',
            name='Human-in-the-Loop Approval',
            description='Manages approval workflow for high-risk actions',
            category='workflow'
        )

        self.vault_path = Path(vault_path)
        self.approval_queue = approval_queue
        self.risk_classifier = RiskClassifier()

    def validate_context(self, context: Dict[str, Any]) -> bool:
        """
        Validate execution context

        Args:
            context: Must contain 'action' and relevant data

        Returns:
            True if valid, False otherwise
        """
        if 'action' not in context:
            logger.error("Approval skill requires 'action' in context")
            return False

        action = context['action']
        valid_actions = ['classify', 'request', 'check', 'approve', 'reject']

        if action not in valid_actions:
            logger.error(f"Invalid action: {action}")
            return False

        return True

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute approval skill

        Args:
            context: Execution context with action and data

        Returns:
            Result with success status and details
        """
        action = context['action']

        if action == 'classify':
            # Classify risk level
            action_data = context.get('action_data', {})
            risk_level = self.risk_classifier.classify(action_data)

            return {
                'action': 'classify',
                'success': True,
                'risk_level': risk_level
            }

        elif action == 'request':
            # Request approval
            action_data = context.get('action_data', {})
            approval_id = self.approval_queue.request_approval(action_data)

            return {
                'action': 'request',
                'success': True,
                'approval_id': approval_id
            }

        elif action == 'check':
            # Check approval status
            approval_id = context.get('approval_id')
            status = self.approval_queue.get_status(approval_id)

            return {
                'action': 'check',
                'success': True,
                'approval_id': approval_id,
                'status': status
            }

        elif action == 'approve':
            # Approve action
            approval_id = context.get('approval_id')
            reviewer = context.get('reviewer', 'system')
            self.approval_queue.approve(approval_id, reviewer)

            return {
                'action': 'approve',
                'success': True,
                'approval_id': approval_id
            }

        elif action == 'reject':
            # Reject action
            approval_id = context.get('approval_id')
            reviewer = context.get('reviewer', 'system')
            reason = context.get('reason', 'No reason provided')
            self.approval_queue.reject(approval_id, reviewer, reason)

            return {
                'action': 'reject',
                'success': True,
                'approval_id': approval_id
            }
