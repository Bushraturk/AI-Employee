"""
Notification System for Approval Queue

Provides notifications for pending approvals via console, file, and optional email.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class NotificationSystem:
    """Notification system for approval queue"""

    def __init__(self, vault_path: str, config: Dict[str, Any] = None):
        """
        Initialize notification system

        Args:
            vault_path: Path to vault directory
            config: Configuration with:
                - enable_console: Enable console notifications (default: True)
                - enable_file: Enable file notifications (default: True)
                - enable_email: Enable email notifications (default: False)
                - notification_file: Path to notification file (default: 'notifications.log')
        """
        self.vault_path = Path(vault_path)
        self.config = config or {}

        # Configuration
        self.enable_console = self.config.get('enable_console', True)
        self.enable_file = self.config.get('enable_file', True)
        self.enable_email = self.config.get('enable_email', False)

        # Notification file
        self.notification_file = self.vault_path / self.config.get('notification_file', 'notifications.log')
        self.notification_file.parent.mkdir(parents=True, exist_ok=True)

    def notify_pending_approval(self, approval: Dict[str, Any]) -> None:
        """
        Notify about pending approval

        Args:
            approval: Approval data dictionary
        """
        message = self._format_approval_notification(approval)

        # Console notification
        if self.enable_console:
            self._notify_console(message, approval['risk_level'])

        # File notification
        if self.enable_file:
            self._notify_file(message, approval)

        # Email notification (if enabled)
        if self.enable_email:
            self._notify_email(message, approval)

    def notify_approval_timeout(self, approval_id: str, action_type: str) -> None:
        """
        Notify about approval timeout

        Args:
            approval_id: Approval ID
            action_type: Action type
        """
        message = f"⏰ Approval timed out: {approval_id} ({action_type})"

        if self.enable_console:
            logger.warning(message)

        if self.enable_file:
            self._write_notification_file({
                'type': 'timeout',
                'approval_id': approval_id,
                'action_type': action_type,
                'timestamp': datetime.now().isoformat(),
                'message': message
            })

    def notify_approval_decision(self, approval_id: str, decision: str, reviewer: str) -> None:
        """
        Notify about approval decision

        Args:
            approval_id: Approval ID
            decision: Decision (approved/rejected)
            reviewer: Reviewer name
        """
        emoji = "✅" if decision == "approved" else "❌"
        message = f"{emoji} Approval {decision}: {approval_id} by {reviewer}"

        if self.enable_console:
            logger.info(message)

        if self.enable_file:
            self._write_notification_file({
                'type': 'decision',
                'approval_id': approval_id,
                'decision': decision,
                'reviewer': reviewer,
                'timestamp': datetime.now().isoformat(),
                'message': message
            })

    def get_pending_count(self, approval_queue) -> int:
        """
        Get count of pending approvals

        Args:
            approval_queue: ApprovalQueue instance

        Returns:
            Count of pending approvals
        """
        pending = approval_queue.list_approvals(status='pending')
        return len(pending)

    def notify_pending_summary(self, approval_queue) -> None:
        """
        Notify summary of pending approvals

        Args:
            approval_queue: ApprovalQueue instance
        """
        pending = approval_queue.list_approvals(status='pending')

        if not pending:
            return

        # Group by risk level
        by_risk = {'low': 0, 'medium': 0, 'high': 0}
        for approval in pending:
            risk = approval.get('risk_level', 'medium')
            by_risk[risk] = by_risk.get(risk, 0) + 1

        message = f"📋 Pending Approvals: {len(pending)} total"
        if by_risk['high'] > 0:
            message += f" | 🔴 {by_risk['high']} high risk"
        if by_risk['medium'] > 0:
            message += f" | 🟡 {by_risk['medium']} medium risk"
        if by_risk['low'] > 0:
            message += f" | 🟢 {by_risk['low']} low risk"

        if self.enable_console:
            logger.info(message)

        if self.enable_file:
            self._write_notification_file({
                'type': 'summary',
                'total': len(pending),
                'by_risk': by_risk,
                'timestamp': datetime.now().isoformat(),
                'message': message
            })

    def _format_approval_notification(self, approval: Dict[str, Any]) -> str:
        """Format approval notification message"""
        risk_emoji = {
            'low': '🟢',
            'medium': '🟡',
            'high': '🔴'
        }

        emoji = risk_emoji.get(approval['risk_level'], '⚪')
        message = f"{emoji} New approval required: {approval['action_type']}"
        message += f"\nID: {approval['approval_id']}"
        message += f"\nRisk: {approval['risk_level'].upper()}"
        message += f"\nDescription: {approval['description']}"

        if approval.get('timeout_at'):
            message += f"\nTimeout: {approval['timeout_at']}"

        return message

    def _notify_console(self, message: str, risk_level: str) -> None:
        """Send console notification"""
        if risk_level == 'high':
            logger.warning(message)
        else:
            logger.info(message)

    def _notify_file(self, message: str, approval: Dict[str, Any]) -> None:
        """Write notification to file"""
        self._write_notification_file({
            'type': 'pending_approval',
            'approval_id': approval['approval_id'],
            'action_type': approval['action_type'],
            'risk_level': approval['risk_level'],
            'timestamp': datetime.now().isoformat(),
            'message': message
        })

    def _write_notification_file(self, notification: Dict[str, Any]) -> None:
        """Write notification to file"""
        try:
            with open(self.notification_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(notification) + '\n')
        except Exception as e:
            logger.error(f"Error writing notification file: {e}")

    def _notify_email(self, message: str, approval: Dict[str, Any]) -> None:
        """
        Send email notification (placeholder for future implementation)

        Args:
            message: Notification message
            approval: Approval data
        """
        # TODO: Implement email notification via MCP server
        # This will be implemented in Phase 8: MCP Tools
        logger.debug(f"Email notification (not implemented): {message}")

    def clear_old_notifications(self, days: int = 30) -> None:
        """
        Clear old notifications from file

        Args:
            days: Number of days to keep notifications
        """
        if not self.notification_file.exists():
            return

        try:
            # Read all notifications
            with open(self.notification_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Filter recent notifications
            cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
            recent = []

            for line in lines:
                try:
                    notification = json.loads(line)
                    timestamp = datetime.fromisoformat(notification['timestamp']).timestamp()
                    if timestamp >= cutoff:
                        recent.append(line)
                except:
                    continue

            # Write back recent notifications
            with open(self.notification_file, 'w', encoding='utf-8') as f:
                f.writelines(recent)

            logger.info(f"Cleared {len(lines) - len(recent)} old notifications")

        except Exception as e:
            logger.error(f"Error clearing old notifications: {e}")

    def get_recent_notifications(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent notifications

        Args:
            limit: Maximum number of notifications to return

        Returns:
            List of notification dictionaries
        """
        if not self.notification_file.exists():
            return []

        try:
            with open(self.notification_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Parse and return most recent
            notifications = []
            for line in reversed(lines[-limit:]):
                try:
                    notification = json.loads(line)
                    notifications.append(notification)
                except:
                    continue

            return notifications

        except Exception as e:
            logger.error(f"Error reading notifications: {e}")
            return []
