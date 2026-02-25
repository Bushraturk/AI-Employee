"""Email drafter for cloud agent.

Generates draft email responses using Claude API.
Writes drafts to Pending_Approval/email/ for human review.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path

from shared.models.action_file import ActionFile, ActionType
from shared.models.approval_request import ApprovalRequest, ApprovalType, ApprovalStatus, RiskLevel
from shared.utils.vault_manager import VaultManager
from shared.utils.logger import VaultLogger, LogCategory
from shared.risk_assessor import RiskAssessor


logger = logging.getLogger(__name__)


class EmailDrafter:
    """Drafts email responses using Claude API.

    Analyzes incoming emails and generates appropriate responses
    based on company handbook and business context.
    """

    def __init__(
        self,
        agent_id: str,
        vault_manager: VaultManager,
        vault_logger: VaultLogger,
        claude_api_key: str,
        company_handbook_path: str,
    ):
        """Initialize email drafter.

        Args:
            agent_id: Agent ID
            vault_manager: Vault manager instance
            vault_logger: Vault logger instance
            claude_api_key: Claude API key
            company_handbook_path: Path to company handbook
        """
        self.agent_id = agent_id
        self.vault_manager = vault_manager
        self.vault_logger = vault_logger
        self.claude_api_key = claude_api_key
        self.company_handbook_path = company_handbook_path

        # Initialize risk assessor
        self.risk_assessor = RiskAssessor()

        # Load company handbook
        self.company_handbook = self._load_company_handbook()

        logger.info("Email drafter initialized")

    def _load_company_handbook(self) -> str:
        """Load company handbook content.

        Returns:
            Company handbook content
        """
        try:
            handbook_path = Path(self.company_handbook_path)
            if handbook_path.exists():
                with open(handbook_path, "r", encoding="utf-8") as f:
                    return f.read()
            else:
                logger.warning(f"Company handbook not found: {self.company_handbook_path}")
                return ""
        except Exception as e:
            logger.error(f"Failed to load company handbook: {e}")
            return ""

    def draft_response(self, action: ActionFile) -> Optional[ApprovalRequest]:
        """Draft email response for an action.

        Args:
            action: Action file representing incoming email

        Returns:
            ApprovalRequest instance or None if drafting failed
        """
        try:
            self.vault_logger.info(
                LogCategory.AGENT,
                f"Drafting email response for action: {action.action_id}",
                details={"action_id": action.action_id}
            )

            # Extract email metadata
            sender = action.metadata.get("sender", "Unknown")
            subject = action.metadata.get("subject", "(No subject)")

            # Generate draft using Claude API
            draft_body = self._generate_draft(action)

            if not draft_body:
                logger.error(f"Failed to generate draft for action: {action.action_id}")
                return None

            # Assess risk
            risk_assessment = self.risk_assessor.assess_email_send(
                recipient=sender,
                subject=f"Re: {subject}",
                body=draft_body,
            )

            # Create approval request
            approval_id = f"email_approval_{action.action_id}_{datetime.now().strftime('%Y%m%dT%H%M%SZ')}"

            approval = ApprovalRequest(
                approval_id=approval_id,
                approval_type=ApprovalType.EMAIL_SEND,
                target_id=sender,
                timestamp=datetime.now(),
                status=ApprovalStatus.PENDING,
                risk_level=risk_assessment["risk_level"],
                risk_factors=risk_assessment["risk_factors"],
                title=f"Email to {sender}: Re: {subject}",
                summary=f"Draft response to email from {sender}",
                body=draft_body,
                metadata={
                    "recipient": sender,
                    "subject": f"Re: {subject}",
                    "original_message_id": action.metadata.get("message_id"),
                    "thread_id": action.metadata.get("thread_id"),
                },
                created_by=self.agent_id,
                action_file_id=action.action_id,
                expires_at=datetime.now() + timedelta(hours=24),
            )

            # Write approval request to vault
            approval_folder = "Pending_Approval/email"
            approval_path = self.vault_manager.get_folder_path(approval_folder) / approval.get_filename()
            approval.to_file(str(approval_path))

            self.vault_logger.info(
                LogCategory.AGENT,
                f"Created email approval request: {approval_id}",
                details={
                    "approval_id": approval_id,
                    "recipient": sender,
                    "risk_level": risk_assessment["risk_level"].value,
                }
            )

            # Write update for dashboard
            self._write_dashboard_update(action, approval)

            return approval

        except Exception as e:
            self.vault_logger.error(
                LogCategory.AGENT,
                f"Failed to draft email response: {e}",
                error_type=type(e).__name__,
                stack_trace=str(e),
            )
            return None

    def _generate_draft(self, action: ActionFile) -> Optional[str]:
        """Generate draft email using Claude API.

        Args:
            action: Action file with email content

        Returns:
            Draft email body or None if generation failed
        """
        try:
            # For now, return a simple template
            # TODO: Integrate with Claude API via MCP

            sender = action.metadata.get("sender", "Unknown")
            subject = action.metadata.get("subject", "(No subject)")

            # Simple template for MVP
            draft = f"""Dear {sender.split('<')[0].strip()},

Thank you for your email regarding "{subject}".

I have received your message and will review it shortly. I will get back to you with a detailed response within 24 hours.

If this is urgent, please feel free to call me directly.

Best regards,
AI Employee (Draft - Requires Approval)

---
This is a draft response generated by the AI Employee system.
Please review and approve before sending.
"""

            return draft

        except Exception as e:
            logger.error(f"Failed to generate draft: {e}")
            return None

    def _write_dashboard_update(self, action: ActionFile, approval: ApprovalRequest) -> None:
        """Write update for dashboard merger.

        Args:
            action: Original action file
            approval: Created approval request
        """
        try:
            update_folder = "Updates"
            update_filename = f"email_draft_{datetime.now().strftime('%Y%m%dT%H%M%SZ')}.md"
            update_path = self.vault_manager.get_folder_path(update_folder) / update_filename

            update_content = f"""---
type: email_draft
timestamp: {datetime.now().isoformat()}
action_id: {action.action_id}
approval_id: {approval.approval_id}
---

# Email Draft Created

**From**: {action.metadata.get('sender', 'Unknown')}
**Subject**: {action.metadata.get('subject', '(No subject)')}
**Risk Level**: {approval.risk_level.value}

Draft email response created and awaiting approval in `Pending_Approval/email/`.
"""

            with open(update_path, "w", encoding="utf-8") as f:
                f.write(update_content)

        except Exception as e:
            logger.error(f"Failed to write dashboard update: {e}")
