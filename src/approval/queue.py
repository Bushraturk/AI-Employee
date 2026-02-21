"""
Approval Queue Module

Manages human-in-the-loop approval workflow for sensitive actions.
"""

import uuid
import frontmatter
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class ApprovalQueue:
    """Approval queue for human-in-the-loop workflow"""

    def __init__(self, vault_path: str = "vault", audit_logger=None):
        """
        Initialize approval queue

        Args:
            vault_path: Path to vault directory
            audit_logger: Optional ApprovalAuditLogger instance
        """
        self.vault_path = Path(vault_path)
        self.approval_path = self.vault_path / "Needs_Approval"
        self.approval_path.mkdir(parents=True, exist_ok=True)
        self.audit_logger = audit_logger

    def create_approval(
        self,
        action_type: str,
        description: str,
        action_details: Dict[str, Any],
        risk_level: str,
        risk_factors: List[str] = None,
        task_reference: Optional[str] = None,
        timeout_hours: int = 24
    ) -> str:
        """
        Create new approval request

        Args:
            action_type: Type of action (send_email, post_linkedin, send_whatsapp)
            description: Human-readable description of the action
            action_details: Action-specific parameters
            risk_level: Risk classification (low, medium, high)
            risk_factors: List of identified risk factors
            task_reference: Optional task ID that triggered this action
            timeout_hours: Hours until auto-rejection (default: 24)

        Returns:
            Approval ID
        """
        approval_id = str(uuid.uuid4())
        created_at = datetime.now()
        timeout_at = created_at + timedelta(hours=timeout_hours)

        # Create approval metadata
        metadata = {
            'approval_id': approval_id,
            'action_type': action_type,
            'description': description,
            'risk_level': risk_level,
            'risk_factors': risk_factors or [],
            'action_details': action_details,
            'task_reference': task_reference,
            'created_at': created_at.isoformat(),
            'timeout_at': timeout_at.isoformat(),
            'status': 'pending'
        }

        # Create approval content
        content = self._format_approval_content(action_type, description, action_details, risk_level)

        # Write approval file
        approval_file = self.approval_path / f"{approval_id}.md"
        post = frontmatter.Post(content, **metadata)

        with open(approval_file, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))

        # Log approval creation
        if self.audit_logger:
            self.audit_logger.log_approval_created(
                approval_id=approval_id,
                action_type=action_type,
                description=description,
                risk_level=risk_level,
                risk_factors=risk_factors or [],
                task_reference=task_reference
            )

        logger.info(f"Created approval: {approval_id} ({action_type}, {risk_level} risk)")

        return approval_id

    def list_approvals(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List approval requests

        Args:
            status: Optional filter by status (pending, approved, rejected, expired)

        Returns:
            List of approval summaries
        """
        approvals = []

        for approval_file in self.approval_path.glob("*.md"):
            try:
                with open(approval_file, 'r', encoding='utf-8') as f:
                    post = frontmatter.load(f)

                # Filter by status if specified
                if status and post.metadata.get('status') != status:
                    continue

                approvals.append({
                    'approval_id': post.metadata.get('approval_id'),
                    'action_type': post.metadata.get('action_type'),
                    'risk_level': post.metadata.get('risk_level'),
                    'status': post.metadata.get('status'),
                    'created_at': post.metadata.get('created_at'),
                    'timeout_at': post.metadata.get('timeout_at')
                })
            except Exception as e:
                print(f"Error reading approval file {approval_file}: {e}")
                continue

        # Sort by created_at (newest first)
        approvals.sort(key=lambda x: x['created_at'], reverse=True)

        return approvals

    def get_approval(self, approval_id: str) -> Optional[Dict[str, Any]]:
        """
        Get approval details

        Args:
            approval_id: Approval ID

        Returns:
            Approval details or None if not found
        """
        approval_file = self.approval_path / f"{approval_id}.md"

        if not approval_file.exists():
            return None

        try:
            with open(approval_file, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)

            return {
                'approval_id': post.metadata.get('approval_id'),
                'action_type': post.metadata.get('action_type'),
                'description': post.metadata.get('description'),
                'action_details': post.metadata.get('action_details'),
                'risk_level': post.metadata.get('risk_level'),
                'risk_factors': post.metadata.get('risk_factors', []),
                'task_reference': post.metadata.get('task_reference'),
                'created_at': post.metadata.get('created_at'),
                'timeout_at': post.metadata.get('timeout_at'),
                'status': post.metadata.get('status'),
                'reviewer': post.metadata.get('reviewer'),
                'reviewed_at': post.metadata.get('reviewed_at'),
                'decision_notes': post.metadata.get('decision_notes'),
                'content': post.content
            }
        except Exception as e:
            print(f"Error reading approval {approval_id}: {e}")
            return None

    def update_approval(
        self,
        approval_id: str,
        status: str,
        reviewer: str,
        decision_notes: Optional[str] = None
    ) -> bool:
        """
        Update approval status

        Args:
            approval_id: Approval ID
            status: New status (approved, rejected)
            reviewer: Who made the decision
            decision_notes: Optional notes about the decision

        Returns:
            True if updated successfully
        """
        approval_file = self.approval_path / f"{approval_id}.md"

        if not approval_file.exists():
            return False

        try:
            with open(approval_file, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)

            # Update metadata
            post.metadata['status'] = status
            post.metadata['reviewer'] = reviewer
            post.metadata['reviewed_at'] = datetime.now().isoformat()
            if decision_notes:
                post.metadata['decision_notes'] = decision_notes

            # Write updated file
            with open(approval_file, 'w', encoding='utf-8') as f:
                f.write(frontmatter.dumps(post))

            # Log approval decision
            if self.audit_logger:
                action_type = post.metadata.get('action_type')
                self.audit_logger.log_approval_decision(
                    approval_id=approval_id,
                    decision=status,
                    reviewer=reviewer,
                    notes=decision_notes or "",
                    action_type=action_type
                )

            logger.info(f"Updated approval: {approval_id} - {status} by {reviewer}")

            return True
        except Exception as e:
            print(f"Error updating approval {approval_id}: {e}")
            return False

    def check_timeouts(self) -> List[str]:
        """
        Check for expired approvals and auto-reject them

        Returns:
            List of approval IDs that were auto-rejected
        """
        now = datetime.now()
        rejected_ids = []

        for approval_file in self.approval_path.glob("*.md"):
            try:
                with open(approval_file, 'r', encoding='utf-8') as f:
                    post = frontmatter.load(f)

                # Skip if not pending
                if post.metadata.get('status') != 'pending':
                    continue

                # Check if expired
                timeout_at = datetime.fromisoformat(post.metadata.get('timeout_at'))
                if now > timeout_at:
                    # Auto-reject
                    approval_id = post.metadata.get('approval_id')
                    action_type = post.metadata.get('action_type')

                    post.metadata['status'] = 'rejected'
                    post.metadata['reviewer'] = 'system'
                    post.metadata['reviewed_at'] = now.isoformat()
                    post.metadata['decision_notes'] = 'Auto-rejected after 24-hour timeout'

                    with open(approval_file, 'w', encoding='utf-8') as f:
                        f.write(frontmatter.dumps(post))

                    # Log timeout event
                    if self.audit_logger:
                        self.audit_logger.log_approval_timeout(
                            approval_id=approval_id,
                            action_type=action_type,
                            timeout_hours=24
                        )

                    logger.info(f"Auto-rejected expired approval: {approval_id}")

                    rejected_ids.append(approval_id)
            except Exception as e:
                print(f"Error checking timeout for {approval_file}: {e}")
                continue

        return rejected_ids

    def _format_approval_content(
        self,
        action_type: str,
        description: str,
        action_details: Dict[str, Any],
        risk_level: str
    ) -> str:
        """Format approval content for display"""
        content = f"# Approval Required: {action_type.replace('_', ' ').title()}\n\n"
        content += f"**Description**: {description}\n\n"

        if action_type == 'send_email':
            to_list = action_details.get('to', [])
            if isinstance(to_list, str):
                to_list = [to_list]
            content += f"**Action**: Send email to {', '.join(to_list)}\n\n"
            content += f"**Subject**: {action_details.get('subject', 'N/A')}\n\n"
            content += f"**Body**:\n```\n{action_details.get('body', 'N/A')}\n```\n\n"

        elif action_type == 'post_linkedin':
            content += f"**Action**: Create LinkedIn post\n\n"
            content += f"**Content**:\n```\n{action_details.get('content', 'N/A')}\n```\n\n"
            if action_details.get('hashtags'):
                hashtags = action_details.get('hashtags', [])
                if isinstance(hashtags, list):
                    content += f"**Hashtags**: {', '.join(hashtags)}\n\n"

        elif action_type == 'send_whatsapp':
            content += f"**Action**: Send WhatsApp message to {action_details.get('to', 'N/A')}\n\n"
            content += f"**Message**:\n```\n{action_details.get('message', 'N/A')}\n```\n\n"

        content += f"**Risk Level**: {risk_level.upper()}\n\n"
        content += "---\n"
        content += "**Review Actions**:\n"
        content += "- Approve: Action will be executed immediately\n"
        content += "- Reject: Action will not be executed\n"
        content += "- Edit: Modify action details before approval\n"

        return content
