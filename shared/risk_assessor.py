"""Risk assessment for approval requests."""

from typing import List, Dict, Any
import re
import logging

from shared.models.approval_request import RiskLevel


logger = logging.getLogger(__name__)


class RiskAssessor:
    """Assesses risk level for approval requests.

    Analyzes content, recipients, amounts, and other factors to determine
    risk level and identify risk factors.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize risk assessor.

        Args:
            config: Risk assessment configuration
        """
        self.config = config or {}

        # Known contacts (low risk)
        self.known_contacts = set(self.config.get("known_contacts", []))

        # High-risk keywords
        self.high_risk_keywords = set(self.config.get("high_risk_keywords", [
            "urgent", "immediate", "wire transfer", "password", "credentials",
            "bank account", "social security", "credit card", "confidential",
        ]))

        # Financial thresholds
        self.low_amount_threshold = self.config.get("low_amount_threshold", 100)
        self.medium_amount_threshold = self.config.get("medium_amount_threshold", 1000)
        self.high_amount_threshold = self.config.get("high_amount_threshold", 10000)

        logger.info(f"Initialized risk assessor with {len(self.known_contacts)} known contacts")

    def assess_email_send(
        self,
        recipient: str,
        subject: str,
        body: str,
        attachments: List[str] = None,
    ) -> tuple[RiskLevel, List[str]]:
        """Assess risk for sending an email.

        Args:
            recipient: Email recipient
            subject: Email subject
            body: Email body
            attachments: List of attachment filenames

        Returns:
            Tuple of (risk_level, risk_factors)
        """
        risk_factors = []
        risk_score = 0

        # Check if recipient is known
        if recipient not in self.known_contacts:
            risk_factors.append(f"Unknown recipient: {recipient}")
            risk_score += 2

        # Check for high-risk keywords
        content = f"{subject} {body}".lower()
        found_keywords = [kw for kw in self.high_risk_keywords if kw in content]
        if found_keywords:
            risk_factors.append(f"High-risk keywords: {', '.join(found_keywords)}")
            risk_score += len(found_keywords)

        # Check for external domains
        if not self._is_internal_email(recipient):
            risk_factors.append("External recipient")
            risk_score += 1

        # Check for attachments
        if attachments:
            risk_factors.append(f"{len(attachments)} attachment(s)")
            risk_score += 1

            # Check for sensitive file types
            sensitive_extensions = [".exe", ".zip", ".rar", ".pdf"]
            for attachment in attachments:
                if any(attachment.lower().endswith(ext) for ext in sensitive_extensions):
                    risk_factors.append(f"Sensitive attachment: {attachment}")
                    risk_score += 1

        # Determine risk level
        risk_level = self._score_to_level(risk_score)

        logger.debug(f"Email risk assessment: {risk_level.value} (score={risk_score})")
        return risk_level, risk_factors

    def assess_social_post(
        self,
        platform: str,
        content: str,
        visibility: str = "public",
    ) -> tuple[RiskLevel, List[str]]:
        """Assess risk for posting to social media.

        Args:
            platform: Social media platform
            content: Post content
            visibility: Post visibility (public, private, etc.)

        Returns:
            Tuple of (risk_level, risk_factors)
        """
        risk_factors = []
        risk_score = 0

        # Public posts are higher risk
        if visibility == "public":
            risk_factors.append("Public post")
            risk_score += 2

        # Check for high-risk keywords
        found_keywords = [kw for kw in self.high_risk_keywords if kw in content.lower()]
        if found_keywords:
            risk_factors.append(f"High-risk keywords: {', '.join(found_keywords)}")
            risk_score += len(found_keywords) * 2  # Higher weight for social media

        # Check for personal information patterns
        if self._contains_personal_info(content):
            risk_factors.append("Contains potential personal information")
            risk_score += 3

        # Check content length (very short or very long posts)
        if len(content) < 10:
            risk_factors.append("Very short post")
            risk_score += 1
        elif len(content) > 1000:
            risk_factors.append("Very long post")
            risk_score += 1

        # Determine risk level
        risk_level = self._score_to_level(risk_score)

        logger.debug(f"Social post risk assessment: {risk_level.value} (score={risk_score})")
        return risk_level, risk_factors

    def assess_accounting_entry(
        self,
        entry_type: str,
        amount: float,
        account: str,
        description: str,
    ) -> tuple[RiskLevel, List[str]]:
        """Assess risk for creating an accounting entry.

        Args:
            entry_type: Type of entry (invoice, payment, etc.)
            amount: Transaction amount
            account: Account name/number
            description: Entry description

        Returns:
            Tuple of (risk_level, risk_factors)
        """
        risk_factors = []
        risk_score = 0

        # Assess amount
        if amount >= self.high_amount_threshold:
            risk_factors.append(f"High amount: ${amount:,.2f}")
            risk_score += 4
        elif amount >= self.medium_amount_threshold:
            risk_factors.append(f"Medium amount: ${amount:,.2f}")
            risk_score += 2
        elif amount >= self.low_amount_threshold:
            risk_factors.append(f"Low amount: ${amount:,.2f}")
            risk_score += 1

        # Check entry type
        high_risk_types = ["payment", "transfer", "withdrawal"]
        if entry_type.lower() in high_risk_types:
            risk_factors.append(f"High-risk entry type: {entry_type}")
            risk_score += 2

        # Check for unusual patterns in description
        if self._contains_suspicious_patterns(description):
            risk_factors.append("Suspicious description pattern")
            risk_score += 2

        # Determine risk level
        risk_level = self._score_to_level(risk_score)

        logger.debug(f"Accounting entry risk assessment: {risk_level.value} (score={risk_score})")
        return risk_level, risk_factors

    def assess_whatsapp_send(
        self,
        recipient: str,
        message: str,
        attachments: List[str] = None,
    ) -> tuple[RiskLevel, List[str]]:
        """Assess risk for sending a WhatsApp message.

        Args:
            recipient: WhatsApp recipient
            message: Message content
            attachments: List of attachment filenames

        Returns:
            Tuple of (risk_level, risk_factors)
        """
        risk_factors = []
        risk_score = 0

        # Check if recipient is known
        if recipient not in self.known_contacts:
            risk_factors.append(f"Unknown recipient: {recipient}")
            risk_score += 2

        # Check for high-risk keywords
        found_keywords = [kw for kw in self.high_risk_keywords if kw in message.lower()]
        if found_keywords:
            risk_factors.append(f"High-risk keywords: {', '.join(found_keywords)}")
            risk_score += len(found_keywords)

        # Check for attachments
        if attachments:
            risk_factors.append(f"{len(attachments)} attachment(s)")
            risk_score += 1

        # Check for personal information
        if self._contains_personal_info(message):
            risk_factors.append("Contains potential personal information")
            risk_score += 2

        # Determine risk level
        risk_level = self._score_to_level(risk_score)

        logger.debug(f"WhatsApp risk assessment: {risk_level.value} (score={risk_score})")
        return risk_level, risk_factors

    def _score_to_level(self, score: int) -> RiskLevel:
        """Convert risk score to risk level.

        Args:
            score: Risk score

        Returns:
            Risk level
        """
        if score >= 8:
            return RiskLevel.CRITICAL
        elif score >= 5:
            return RiskLevel.HIGH
        elif score >= 2:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _is_internal_email(self, email: str) -> bool:
        """Check if email is internal.

        Args:
            email: Email address

        Returns:
            True if internal, False otherwise
        """
        internal_domains = self.config.get("internal_domains", [])
        if not internal_domains:
            return False

        domain = email.split("@")[-1] if "@" in email else ""
        return domain in internal_domains

    def _contains_personal_info(self, text: str) -> bool:
        """Check if text contains potential personal information.

        Args:
            text: Text to check

        Returns:
            True if contains personal info, False otherwise
        """
        # Check for phone numbers
        phone_pattern = r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"
        if re.search(phone_pattern, text):
            return True

        # Check for email addresses
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        if re.search(email_pattern, text):
            return True

        # Check for credit card patterns
        cc_pattern = r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"
        if re.search(cc_pattern, text):
            return True

        return False

    def _contains_suspicious_patterns(self, text: str) -> bool:
        """Check if text contains suspicious patterns.

        Args:
            text: Text to check

        Returns:
            True if suspicious, False otherwise
        """
        suspicious_patterns = [
            r"test",
            r"dummy",
            r"xxx",
            r"temp",
        ]

        text_lower = text.lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, text_lower):
                return True

        return False
