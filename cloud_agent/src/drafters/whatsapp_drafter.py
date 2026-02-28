"""WhatsApp drafter for cloud agent.

Generates draft WhatsApp responses using Claude API.
Writes drafts to Pending_Approval/whatsapp/ for human review.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path

from shared.models.action_file import ActionFile, ActionType
from shared.models.approval_request import ApprovalRequest, ApprovalType, ApprovalStatus, RiskLevel
from shared.utils.vault_manager import VaultManager
from shared.utils.logger import VaultLogger, LogCategory
from shared.risk_assessor import RiskAssessor


logger = logging.getLogger(__name__)


class WhatsAppDrafter:
    """Drafts WhatsApp responses using Claude API.

    Analyzes incoming WhatsApp messages and generates appropriate responses
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
        """Initialize WhatsApp drafter.

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

        logger.info("WhatsApp drafter initialized")

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
        """Draft WhatsApp response for an action.

        Args:
            action: Action file representing incoming WhatsApp message

        Returns:
            ApprovalRequest instance or None if drafting failed
        """
        try:
            self.vault_logger.info(
                LogCategory.AGENT,
                f"Drafting WhatsApp response for action: {action.action_id}",
                details={"action_id": action.action_id}
            )

            # Extract message metadata
            sender = action.metadata.get("sender_name", "Unknown")
            message_text = action.metadata.get("message_text", "")
            chat_type = action.metadata.get("chat_type", "direct")

            # Generate draft using Claude API
            draft_body = self._generate_draft(action)

            if not draft_body:
                logger.error(f"Failed to generate draft for action: {action.action_id}")
                return None

            # Assess risk
            risk_level, risk_factors = self._assess_risk(sender, draft_body, chat_type)

            # Create approval request
            approval_id = f"whatsapp_approval_{action.action_id}_{datetime.now().strftime('%Y%m%dT%H%M%SZ')}"

            approval = ApprovalRequest(
                approval_id=approval_id,
                approval_type=ApprovalType.WHATSAPP_SEND,
                target_id=sender,
                timestamp=datetime.now(),
                status=ApprovalStatus.PENDING,
                risk_level=risk_level,
                risk_factors=risk_factors,
                title=f"WhatsApp to {sender}",
                summary=f"Draft response to WhatsApp message from {sender}",
                body=draft_body,
                metadata={
                    "recipient": sender,
                    "original_message": message_text,
                    "message_id": action.metadata.get("message_id"),
                    "chat_type": chat_type,
                },
                created_by=self.agent_id,
                action_file_id=action.action_id,
                expires_at=datetime.now() + timedelta(hours=24),
            )

            # Write approval request to vault
            approval_folder = "Pending_Approval/whatsapp"
            approval_path = self.vault_manager.get_folder_path(approval_folder) / approval.get_filename()
            approval.to_file(str(approval_path))

            self.vault_logger.info(
                LogCategory.AGENT,
                f"Created WhatsApp approval request: {approval_id}",
                details={
                    "approval_id": approval_id,
                    "recipient": sender,
                    "risk_level": risk_level.value,
                }
            )

            # Write update for dashboard
            self._write_dashboard_update(action, approval)

            return approval

        except Exception as e:
            self.vault_logger.error(
                LogCategory.AGENT,
                f"Failed to draft WhatsApp response: {e}",
                error_type=type(e).__name__,
                stack_trace=str(e),
            )
            return None

    def _generate_draft(self, action: ActionFile) -> Optional[str]:
        """Generate draft WhatsApp message using Claude API.

        Args:
            action: Action file with message content

        Returns:
            Draft message body or None if generation failed
        """
        try:
            # For now, return a simple template
            # TODO: Integrate with Claude API via MCP

            sender = action.metadata.get("sender_name", "Unknown")
            message_text = action.metadata.get("message_text", "")

            # Analyze message context
            context = self._analyze_message_context(message_text)

            # Simple template for MVP
            if "invoice" in message_text.lower():
                draft = f"""Hi {sender.split()[0]},

Thanks for your message about the invoice. I've received your request and will review it shortly.

I'll get back to you with the details within the next few hours.

Best regards"""
            elif "payment" in message_text.lower():
                draft = f"""Hi {sender.split()[0]},

I've received your message regarding payment. Let me check the status and I'll update you shortly.

Thanks for your patience.

Best regards"""
            elif "urgent" in message_text.lower() or "asap" in message_text.lower():
                draft = f"""Hi {sender.split()[0]},

I understand this is urgent. I'm looking into it right now and will get back to you as soon as possible.

Thanks for flagging this.

Best regards"""
            elif "help" in message_text.lower():
                draft = f"""Hi {sender.split()[0]},

I'm here to help! Let me review your request and I'll provide assistance shortly.

Feel free to share any additional details that might be helpful.

Best regards"""
            else:
                draft = f"""Hi {sender.split()[0]},

Thanks for your message. I've received it and will review the details.

I'll get back to you shortly with a response.

Best regards"""

            return draft

        except Exception as e:
            logger.error(f"Failed to generate draft: {e}")
            return None

    def _analyze_message_context(self, message_text: str) -> str:
        """Analyze message context to determine appropriate response.

        Args:
            message_text: Message text

        Returns:
            Context category
        """
        message_lower = message_text.lower()

        if "invoice" in message_lower:
            return "invoice_inquiry"
        elif "payment" in message_lower:
            return "payment_inquiry"
        elif "urgent" in message_lower or "asap" in message_lower:
            return "urgent_request"
        elif "help" in message_lower:
            return "help_request"
        else:
            return "general_inquiry"

    def _assess_risk(self, recipient: str, message: str, chat_type: str) -> tuple[RiskLevel, list[str]]:
        """Assess risk of sending WhatsApp message.

        Args:
            recipient: Recipient name
            message: Message content
            chat_type: Chat type (direct or group)

        Returns:
            Tuple of (risk_level, risk_factors)
        """
        risk_factors = []

        # Group messages are higher risk
        if chat_type == "group":
            risk_factors.append("Group message (multiple recipients)")

        # Check for sensitive keywords
        sensitive_keywords = ["payment", "invoice", "money", "account", "confidential"]
        if any(keyword in message.lower() for keyword in sensitive_keywords):
            risk_factors.append("Contains sensitive information")

        # Determine risk level
        if len(risk_factors) >= 2:
            risk_level = RiskLevel.HIGH
        elif len(risk_factors) == 1:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        return risk_level, risk_factors

    def _write_dashboard_update(self, action: ActionFile, approval: ApprovalRequest) -> None:
        """Write update for dashboard merger.

        Args:
            action: Original action file
            approval: Created approval request
        """
        try:
            update_folder = "Updates"
            update_filename = f"whatsapp_draft_{datetime.now().strftime('%Y%m%dT%H%M%SZ')}.md"
            update_path = self.vault_manager.get_folder_path(update_folder) / update_filename

            update_content = f"""---
type: whatsapp_draft
timestamp: {datetime.now().isoformat()}
action_id: {action.action_id}
approval_id: {approval.approval_id}
---

# WhatsApp Draft Created

**From**: {action.metadata.get('sender_name', 'Unknown')}
**Chat Type**: {action.metadata.get('chat_type', 'direct')}
**Risk Level**: {approval.risk_level.value}

Draft WhatsApp response created and awaiting approval in `Pending_Approval/whatsapp/`.
"""

            with open(update_path, "w", encoding="utf-8") as f:
                f.write(update_content)

        except Exception as e:
            logger.error(f"Failed to write dashboard update: {e}")
