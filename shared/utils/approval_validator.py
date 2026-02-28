"""Approval file validation utilities.

Validates approval request files against schema and business rules.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from shared.models.approval_request import ApprovalRequest, ApprovalStatus, RiskLevel


logger = logging.getLogger(__name__)


class ApprovalValidator:
    """Validates approval request files and content."""

    # Required fields in approval request
    REQUIRED_FIELDS = [
        "approval_id",
        "approval_type",
        "target_id",
        "timestamp",
        "status",
        "risk_level",
        "title",
        "summary",
        "body",
        "created_by",
    ]

    # Valid approval types
    VALID_APPROVAL_TYPES = [
        "email_send",
        "social_post",
        "accounting_entry",
        "whatsapp_send",
        "payment",
        "file_operation",
    ]

    # Risk level thresholds
    RISK_THRESHOLDS = {
        RiskLevel.LOW: [],
        RiskLevel.MEDIUM: ["new_recipient", "large_amount"],
        RiskLevel.HIGH: ["payment", "delete_operation", "external_api"],
        RiskLevel.CRITICAL: ["payment_over_threshold", "destructive_operation"],
    }

    def __init__(self, max_expiration_hours: int = 48):
        """Initialize approval validator.

        Args:
            max_expiration_hours: Maximum allowed expiration time in hours
        """
        self.max_expiration_hours = max_expiration_hours

    def validate_approval_file(self, file_path: Path) -> Tuple[bool, List[str]]:
        """Validate an approval request file.

        Args:
            file_path: Path to approval file

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        # Check file exists
        if not file_path.exists():
            errors.append(f"File does not exist: {file_path}")
            return False, errors

        # Check file extension
        if file_path.suffix != ".md":
            errors.append(f"Invalid file extension: {file_path.suffix} (expected .md)")

        # Try to parse approval request
        try:
            approval = ApprovalRequest.from_file(str(file_path))
        except Exception as e:
            errors.append(f"Failed to parse approval file: {e}")
            return False, errors

        # Validate approval content
        content_errors = self.validate_approval_content(approval)
        errors.extend(content_errors)

        return len(errors) == 0, errors

    def validate_approval_content(self, approval: ApprovalRequest) -> List[str]:
        """Validate approval request content.

        Args:
            approval: Approval request to validate

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if not hasattr(approval, field) or getattr(approval, field) is None:
                errors.append(f"Missing required field: {field}")

        # Validate approval type
        if approval.approval_type.value not in self.VALID_APPROVAL_TYPES:
            errors.append(f"Invalid approval type: {approval.approval_type.value}")

        # Validate approval ID format
        if not approval.approval_id.startswith("approval_"):
            errors.append(f"Invalid approval ID format: {approval.approval_id}")

        # Validate timestamp
        if approval.timestamp > datetime.now():
            errors.append("Timestamp is in the future")

        # Validate expiration
        if approval.expires_at:
            if approval.expires_at < approval.timestamp:
                errors.append("Expiration time is before creation time")

            expiration_hours = (approval.expires_at - approval.timestamp).total_seconds() / 3600
            if expiration_hours > self.max_expiration_hours:
                errors.append(
                    f"Expiration time exceeds maximum ({expiration_hours:.1f}h > {self.max_expiration_hours}h)"
                )

        # Validate risk level
        if approval.risk_level not in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]:
            errors.append(f"Invalid risk level: {approval.risk_level}")

        # Validate risk factors match risk level
        risk_errors = self._validate_risk_factors(approval)
        errors.extend(risk_errors)

        # Validate title and summary
        if len(approval.title) < 5:
            errors.append("Title too short (minimum 5 characters)")

        if len(approval.title) > 200:
            errors.append("Title too long (maximum 200 characters)")

        if len(approval.summary) < 10:
            errors.append("Summary too short (minimum 10 characters)")

        if len(approval.summary) > 500:
            errors.append("Summary too long (maximum 500 characters)")

        # Validate body
        if len(approval.body) < 20:
            errors.append("Body too short (minimum 20 characters)")

        # Validate status transitions
        if approval.status == ApprovalStatus.APPROVED and not approval.approved_by:
            errors.append("Approved status requires approved_by field")

        if approval.status == ApprovalStatus.REJECTED and not approval.rejection_reason:
            errors.append("Rejected status requires rejection_reason field")

        return errors

    def _validate_risk_factors(self, approval: ApprovalRequest) -> List[str]:
        """Validate risk factors match risk level.

        Args:
            approval: Approval request

        Returns:
            List of error messages
        """
        errors = []

        if not approval.risk_factors:
            if approval.risk_level != RiskLevel.LOW:
                errors.append(f"Risk level {approval.risk_level.value} requires risk factors")
            return errors

        # Check for critical risk factors
        critical_factors = ["payment_over_threshold", "destructive_operation"]
        has_critical = any(f in approval.risk_factors for f in critical_factors)

        if has_critical and approval.risk_level != RiskLevel.CRITICAL:
            errors.append("Critical risk factors require CRITICAL risk level")

        # Check for high risk factors
        high_factors = ["payment", "delete_operation", "external_api"]
        has_high = any(f in approval.risk_factors for f in high_factors)

        if has_high and approval.risk_level not in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            errors.append("High risk factors require HIGH or CRITICAL risk level")

        return errors

    def validate_approval_schema(self, data: Dict) -> Tuple[bool, List[str]]:
        """Validate approval data against schema.

        Args:
            data: Approval data dictionary

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        # Validate field types
        if "approval_id" in data and not isinstance(data["approval_id"], str):
            errors.append("approval_id must be a string")

        if "approval_type" in data and not isinstance(data["approval_type"], str):
            errors.append("approval_type must be a string")

        if "target_id" in data and not isinstance(data["target_id"], str):
            errors.append("target_id must be a string")

        if "timestamp" in data and not isinstance(data["timestamp"], (str, datetime)):
            errors.append("timestamp must be a string or datetime")

        if "status" in data and not isinstance(data["status"], str):
            errors.append("status must be a string")

        if "risk_level" in data and not isinstance(data["risk_level"], str):
            errors.append("risk_level must be a string")

        if "risk_factors" in data and not isinstance(data["risk_factors"], list):
            errors.append("risk_factors must be a list")

        if "title" in data and not isinstance(data["title"], str):
            errors.append("title must be a string")

        if "summary" in data and not isinstance(data["summary"], str):
            errors.append("summary must be a string")

        if "body" in data and not isinstance(data["body"], str):
            errors.append("body must be a string")

        if "created_by" in data and not isinstance(data["created_by"], str):
            errors.append("created_by must be a string")

        return len(errors) == 0, errors

    def is_expired(self, approval: ApprovalRequest) -> bool:
        """Check if approval has expired.

        Args:
            approval: Approval request

        Returns:
            True if expired, False otherwise
        """
        if not approval.expires_at:
            return False

        return datetime.now() > approval.expires_at

    def can_approve(self, approval: ApprovalRequest) -> Tuple[bool, Optional[str]]:
        """Check if approval can be approved.

        Args:
            approval: Approval request

        Returns:
            Tuple of (can_approve, reason if not)
        """
        # Check status
        if approval.status != ApprovalStatus.PENDING:
            return False, f"Approval is not pending (status={approval.status.value})"

        # Check expiration
        if self.is_expired(approval):
            return False, "Approval has expired"

        return True, None

    def can_reject(self, approval: ApprovalRequest) -> Tuple[bool, Optional[str]]:
        """Check if approval can be rejected.

        Args:
            approval: Approval request

        Returns:
            Tuple of (can_reject, reason if not)
        """
        # Check status
        if approval.status != ApprovalStatus.PENDING:
            return False, f"Approval is not pending (status={approval.status.value})"

        return True, None

    def validate_batch(self, file_paths: List[Path]) -> Dict[str, Tuple[bool, List[str]]]:
        """Validate multiple approval files.

        Args:
            file_paths: List of file paths to validate

        Returns:
            Dictionary mapping file paths to (is_valid, errors) tuples
        """
        results = {}

        for file_path in file_paths:
            is_valid, errors = self.validate_approval_file(file_path)
            results[str(file_path)] = (is_valid, errors)

        return results
