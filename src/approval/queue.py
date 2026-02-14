"""
Approval Queue Module

Manages human-in-the-loop approval workflow for sensitive actions.
"""

import uuid
import frontmatter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List


class ApprovalQueue:
    """Approval queue for human-in-the-loop workflow"""

    def __init__(self, vault_path: str = "vault"):
        """Initialize approval queue"""
        self.vault_path = Path(vault_path)
        self.approval_path = self.vault_path / "Needs_Approval"
        self.approval_path.mkdir(parents=True, exist_ok=True)

    def create_approval(
        self,
        action_type: str,
        action_details: Dict[str, Any],
        risk_level: str,
        task_reference: Optional[str] = None
    ) -> str:
        """
        Create new approval request

        Args:
            action_type: Type of action (send_email, post_linkedin, send_whatsapp)
            action_details: Action-specific parameters
            risk_level: Risk classification (low, medium, high)
            task_reference: Optional task ID that triggered this action

        Returns:
            Approval ID
        """
        approval_id = str(uuid.uuid4())
        created_at = datetime.now()
        timeout_at = created_at + timedelta(hours=24)

        # Create approval metadata
        metadata = {
            'approval_id': approval_id,
            'action_type': action_type,
            'risk_level': risk_level,
            'task_reference': task_reference,
            'created_at': created_at.isoformat(),
            'timeout_at': timeout_at.isoformat(),
            'status': 'pending'
        }

        # Create approval content
        content = self._format_approval_content(action_type, action_details, risk_level)

        # Write approval file
        approval_file = self.approval_path / f"{approval_id}.md"
        post = frontmatter.Post(content, **metadata)

        with open(approval_file, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))

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
                'risk_level': post.metadata.get('risk_level'),
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

            return True
        except Exception as e:
            print(f"Error updating approval {approval_id}: {e}")
            return False

    def check_timeouts(self) -> int:
        """
        Check for expired approvals and auto-reject them

        Returns:
            Number of approvals auto-rejected
        """
        now = datetime.now()
        rejected_count = 0

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
                    post.metadata['status'] = 'expired'
                    post.metadata['reviewer'] = 'system'
                    post.metadata['reviewed_at'] = now.isoformat()
                    post.metadata['decision_notes'] = 'Auto-rejected after 24-hour timeout'

                    with open(approval_file, 'w', encoding='utf-8') as f:
                        f.write(frontmatter.dumps(post))

                    rejected_count += 1
            except Exception as e:
                print(f"Error checking timeout for {approval_file}: {e}")
                continue

        return rejected_count

    def _format_approval_content(
        self,
        action_type: str,
        action_details: Dict[str, Any],
        risk_level: str
    ) -> str:
        """Format approval content for display"""
        content = f"# Approval Required: {action_type.replace('_', ' ').title()}\n\n"

        if action_type == 'send_email':
            content += f"**Action**: Send email to {', '.join(action_details.get('to', []))}\n\n"
            content += f"**Subject**: {action_details.get('subject', 'N/A')}\n\n"
            content += f"**Body**:\n```\n{action_details.get('body', 'N/A')}\n```\n\n"

        elif action_type == 'post_linkedin':
            content += f"**Action**: Create LinkedIn post\n\n"
            content += f"**Content**:\n```\n{action_details.get('content', 'N/A')}\n```\n\n"
            if action_details.get('hashtags'):
                content += f"**Hashtags**: {', '.join(action_details.get('hashtags', []))}\n\n"

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
