"""
Risk Classifier Module

Classifies actions by risk level (low, medium, high) to determine
approval requirements and handling procedures.
"""

from typing import Dict, Any, List


class RiskClassifier:
    """Classify actions by risk level"""

    # Keywords that indicate high-risk content
    HIGH_RISK_KEYWORDS = [
        'urgent', 'immediate', 'critical', 'emergency',
        'payment', 'invoice', 'transfer', 'wire',
        'confidential', 'sensitive', 'private',
        'delete', 'remove', 'cancel', 'terminate'
    ]

    # Keywords that indicate medium-risk content
    MEDIUM_RISK_KEYWORDS = [
        'important', 'deadline', 'asap',
        'contract', 'agreement', 'legal',
        'customer', 'client', 'partner'
    ]

    @staticmethod
    def classify_action(
        action_type: str,
        parameters: Dict[str, Any]
    ) -> str:
        """
        Classify action risk level

        Args:
            action_type: Type of action (send_email, post_linkedin, send_whatsapp)
            parameters: Action parameters

        Returns:
            Risk level: 'low', 'medium', or 'high'
        """
        # Base risk level by action type
        base_risk = RiskClassifier._get_base_risk(action_type)

        # Check for bulk operations (high risk)
        if RiskClassifier._is_bulk_operation(action_type, parameters):
            return 'high'

        # Check for sensitive content
        if RiskClassifier._contains_sensitive_content(parameters):
            return 'high'

        # Check for high-risk keywords
        if RiskClassifier._contains_high_risk_keywords(parameters):
            return 'high'

        # Check for medium-risk keywords
        if RiskClassifier._contains_medium_risk_keywords(parameters):
            return max(base_risk, 'medium', key=lambda x: ['low', 'medium', 'high'].index(x))

        return base_risk

    @staticmethod
    def _get_base_risk(action_type: str) -> str:
        """Get base risk level for action type"""
        risk_map = {
            'send_email': 'medium',
            'post_linkedin': 'medium',
            'send_whatsapp': 'medium',
            'read_email': 'low',
            'get_linkedin_analytics': 'low',
            'create_task': 'low',
            'update_dashboard': 'low'
        }
        return risk_map.get(action_type, 'medium')

    @staticmethod
    def _is_bulk_operation(action_type: str, parameters: Dict[str, Any]) -> bool:
        """Check if action is a bulk operation"""
        if action_type == 'send_email':
            recipients = parameters.get('to', [])
            if isinstance(recipients, list) and len(recipients) > 5:
                return True

        if action_type == 'send_whatsapp':
            # Check if sending to multiple recipients
            recipients = parameters.get('recipients', [])
            if isinstance(recipients, list) and len(recipients) > 5:
                return True

        return False

    @staticmethod
    def _contains_sensitive_content(parameters: Dict[str, Any]) -> bool:
        """Check if parameters contain sensitive content"""
        # Check for potential PII patterns
        content_fields = ['body', 'message', 'content', 'subject']

        for field in content_fields:
            if field in parameters:
                content = str(parameters[field]).lower()

                # Check for credit card patterns
                if RiskClassifier._contains_credit_card_pattern(content):
                    return True

                # Check for SSN patterns
                if RiskClassifier._contains_ssn_pattern(content):
                    return True

                # Check for password/credential mentions
                if any(word in content for word in ['password', 'credential', 'api key', 'secret']):
                    return True

        return False

    @staticmethod
    def _contains_credit_card_pattern(text: str) -> bool:
        """Check for credit card number patterns"""
        import re
        # Simple pattern for credit card numbers (16 digits)
        pattern = r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
        return bool(re.search(pattern, text))

    @staticmethod
    def _contains_ssn_pattern(text: str) -> bool:
        """Check for SSN patterns"""
        import re
        # Pattern for SSN (XXX-XX-XXXX)
        pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        return bool(re.search(pattern, text))

    @staticmethod
    def _contains_high_risk_keywords(parameters: Dict[str, Any]) -> bool:
        """Check if parameters contain high-risk keywords"""
        content_fields = ['body', 'message', 'content', 'subject']

        for field in content_fields:
            if field in parameters:
                content = str(parameters[field]).lower()
                if any(keyword in content for keyword in RiskClassifier.HIGH_RISK_KEYWORDS):
                    return True

        return False

    @staticmethod
    def _contains_medium_risk_keywords(parameters: Dict[str, Any]) -> bool:
        """Check if parameters contain medium-risk keywords"""
        content_fields = ['body', 'message', 'content', 'subject']

        for field in content_fields:
            if field in parameters:
                content = str(parameters[field]).lower()
                if any(keyword in content for keyword in RiskClassifier.MEDIUM_RISK_KEYWORDS):
                    return True

        return False

    @staticmethod
    def get_risk_description(risk_level: str) -> str:
        """Get human-readable risk description"""
        descriptions = {
            'low': 'Low risk - Read-only operations, internal notifications',
            'medium': 'Medium risk - Single external communications, standard operations',
            'high': 'High risk - Bulk operations, sensitive content, or critical actions'
        }
        return descriptions.get(risk_level, 'Unknown risk level')
