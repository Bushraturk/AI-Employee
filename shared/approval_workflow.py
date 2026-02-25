"""Approval workflow handler for managing approval lifecycle."""

from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List
import logging

from shared.models.approval_request import ApprovalRequest, ApprovalStatus, RiskLevel
from shared.models.action_file import ActionFile
from shared.utils.vault_manager import VaultManager
from shared.utils.logger import VaultLogger, LogCategory


logger = logging.getLogger(__name__)


class ApprovalWorkflow:
    """Manages the approval workflow lifecycle.

    Handles creation, expiration, and state transitions of approval requests.
    """

    def __init__(
        self,
        vault_manager: VaultManager,
        vault_logger: VaultLogger,
        default_timeout_hours: int = 24,
    ):
        """Initialize approval workflow handler.

        Args:
            vault_manager: Vault manager instance
            vault_logger: Vault logger instance
            default_timeout_hours: Default approval timeout in hours
        """
        self.vault_manager = vault_manager
        self.vault_logger = vault_logger
        self.default_timeout_hours = default_timeout_hours

    def create_approval_request(
        self,
        action: ActionFile,
        approval_type: str,
        target_id: str,
        title: str,
        summary: str,
        body: str,
        risk_level: RiskLevel,
        risk_factors: List[str],
        created_by: str,
        target_folder: str,
        timeout_hours: Optional[int] = None,
    ) -> ApprovalRequest:
        """Create a new approval request.

        Args:
            action: Related action file
            approval_type: Type of approval
            target_id: Target identifier
            title: Approval title
            summary: Brief summary
            body: Full draft content
            risk_level: Risk level
            risk_factors: List of risk factors
            created_by: Agent that created this request
            target_folder: Target folder (e.g., "Pending_Approval/email")
            timeout_hours: Approval timeout in hours (defaults to default_timeout_hours)

        Returns:
            Created approval request
        """
        timeout = timeout_hours or self.default_timeout_hours
        now = datetime.now()

        approval = ApprovalRequest(
            approval_id=f"approval_{action.action_id}_{now.strftime('%Y%m%dT%H%M%SZ')}",
            approval_type=approval_type,
            target_id=target_id,
            timestamp=now,
            status=ApprovalStatus.PENDING,
            risk_level=risk_level,
            risk_factors=risk_factors,
            title=title,
            summary=summary,
            body=body,
            created_by=created_by,
            action_file_id=action.action_id,
            expires_at=now + timedelta(hours=timeout),
        )

        # Write to vault
        self.vault_manager.write_approval_request(approval, target_folder)

        self.vault_logger.info(
            LogCategory.APPROVAL,
            f"Created approval request: {title}",
            approval_id=approval.approval_id,
            action_id=action.action_id,
            details={
                "risk_level": risk_level.value,
                "expires_at": approval.expires_at.isoformat(),
            },
        )

        return approval

    def check_expired_approvals(self) -> int:
        """Check for and handle expired approval requests.

        Returns:
            Number of expired approvals processed
        """
        expired_count = 0

        # Check all pending approval folders
        for subfolder in ["email", "social", "accounting", "whatsapp"]:
            folder = f"Pending_Approval/{subfolder}"
            files = self.vault_manager.list_files(folder, "*.md")

            for file_path in files:
                try:
                    approval = self.vault_manager.read_approval_request(file_path)

                    if approval.status == ApprovalStatus.PENDING and approval.is_expired():
                        # Move to Rejected folder
                        approval.status = ApprovalStatus.EXPIRED
                        approval.rejection_reason = "Approval request expired"

                        # Write updated approval to Rejected folder
                        self.vault_manager.write_approval_request(approval, "Rejected")

                        # Delete from Pending_Approval
                        self.vault_manager.delete_file(file_path)

                        expired_count += 1

                        self.vault_logger.warning(
                            LogCategory.APPROVAL,
                            f"Approval expired: {approval.title}",
                            approval_id=approval.approval_id,
                        )

                except Exception as e:
                    logger.error(f"Error processing approval {file_path}: {e}")

        return expired_count

    def get_pending_approvals(self, subfolder: Optional[str] = None) -> List[ApprovalRequest]:
        """Get all pending approval requests.

        Args:
            subfolder: Optional subfolder filter (e.g., "email")

        Returns:
            List of pending approval requests
        """
        approvals = []

        if subfolder:
            folders = [f"Pending_Approval/{subfolder}"]
        else:
            folders = [
                "Pending_Approval/email",
                "Pending_Approval/social",
                "Pending_Approval/accounting",
                "Pending_Approval/whatsapp",
            ]

        for folder in folders:
            files = self.vault_manager.list_files(folder, "*.md")

            for file_path in files:
                try:
                    approval = self.vault_manager.read_approval_request(file_path)
                    if approval.status == ApprovalStatus.PENDING:
                        approvals.append(approval)
                except Exception as e:
                    logger.error(f"Error reading approval {file_path}: {e}")

        return approvals

    def get_approved_actions(self) -> List[ApprovalRequest]:
        """Get all approved actions ready for execution.

        Returns:
            List of approved requests
        """
        approvals = []
        files = self.vault_manager.list_files("Approved", "*.md")

        for file_path in files:
            try:
                approval = self.vault_manager.read_approval_request(file_path)
                if approval.status == ApprovalStatus.APPROVED:
                    approvals.append(approval)
            except Exception as e:
                logger.error(f"Error reading approved action {file_path}: {e}")

        return approvals

    def mark_as_completed(self, approval: ApprovalRequest) -> None:
        """Mark an approval request as completed.

        Moves the approval from Approved/ to Done/.

        Args:
            approval: Approval request to mark as completed
        """
        # Find the file in Approved folder
        approved_files = self.vault_manager.list_files("Approved", "*.md")

        for file_path in approved_files:
            try:
                existing = self.vault_manager.read_approval_request(file_path)
                if existing.approval_id == approval.approval_id:
                    # Move to Done folder
                    self.vault_manager.move_file(file_path, "Done")

                    self.vault_logger.info(
                        LogCategory.APPROVAL,
                        f"Approval completed: {approval.title}",
                        approval_id=approval.approval_id,
                    )
                    return

            except Exception as e:
                logger.error(f"Error processing approval {file_path}: {e}")

        logger.warning(f"Approval not found in Approved folder: {approval.approval_id}")
