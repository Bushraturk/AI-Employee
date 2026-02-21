"""
Approval Audit Logger Module

Tracks all approval-related events for compliance and debugging.
Provides detailed audit trail for approval decisions.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import frontmatter

logger = logging.getLogger(__name__)


class ApprovalAuditLogger:
    """Log all approval-related events for audit trail"""

    def __init__(self, vault_path: str):
        """
        Initialize approval audit logger

        Args:
            vault_path: Path to vault directory
        """
        self.vault_path = Path(vault_path)
        self.audit_folder = self.vault_path / 'Audit' / 'Approvals'
        self.audit_folder.mkdir(parents=True, exist_ok=True)

    def log_approval_created(
        self,
        approval_id: str,
        action_type: str,
        description: str,
        risk_level: str,
        risk_factors: List[str],
        task_reference: Optional[str] = None
    ) -> None:
        """
        Log approval creation event

        Args:
            approval_id: Approval ID
            action_type: Type of action requiring approval
            description: Action description
            risk_level: Risk level (low, medium, high)
            risk_factors: List of identified risk factors
            task_reference: Optional task ID reference
        """
        try:
            event = {
                'event_type': 'approval_created',
                'approval_id': approval_id,
                'action_type': action_type,
                'description': description,
                'risk_level': risk_level,
                'risk_factors': risk_factors,
                'task_reference': task_reference,
                'timestamp': datetime.now().isoformat(),
                'user': 'system'
            }

            self._write_audit_log(event)
            logger.info(f"Logged approval creation: {approval_id}")

        except Exception as e:
            logger.error(f"Error logging approval creation: {e}")

    def log_approval_decision(
        self,
        approval_id: str,
        decision: str,
        reviewer: str,
        notes: str = "",
        action_type: str = None
    ) -> None:
        """
        Log approval decision event

        Args:
            approval_id: Approval ID
            decision: Decision (approved, rejected, expired)
            reviewer: Reviewer who made the decision
            notes: Optional decision notes
            action_type: Optional action type
        """
        try:
            event = {
                'event_type': 'approval_decision',
                'approval_id': approval_id,
                'decision': decision,
                'reviewer': reviewer,
                'notes': notes,
                'action_type': action_type,
                'timestamp': datetime.now().isoformat()
            }

            self._write_audit_log(event)
            logger.info(f"Logged approval decision: {approval_id} - {decision}")

        except Exception as e:
            logger.error(f"Error logging approval decision: {e}")

    def log_approval_timeout(
        self,
        approval_id: str,
        action_type: str,
        timeout_hours: int
    ) -> None:
        """
        Log approval timeout event

        Args:
            approval_id: Approval ID
            action_type: Type of action
            timeout_hours: Timeout period in hours
        """
        try:
            event = {
                'event_type': 'approval_timeout',
                'approval_id': approval_id,
                'action_type': action_type,
                'timeout_hours': timeout_hours,
                'timestamp': datetime.now().isoformat(),
                'auto_rejected': True
            }

            self._write_audit_log(event)
            logger.info(f"Logged approval timeout: {approval_id}")

        except Exception as e:
            logger.error(f"Error logging approval timeout: {e}")

    def log_approval_edited(
        self,
        approval_id: str,
        editor: str,
        changes: Dict[str, Any]
    ) -> None:
        """
        Log approval edit event

        Args:
            approval_id: Approval ID
            editor: User who edited the approval
            changes: Dictionary of changes made
        """
        try:
            event = {
                'event_type': 'approval_edited',
                'approval_id': approval_id,
                'editor': editor,
                'changes': changes,
                'timestamp': datetime.now().isoformat()
            }

            self._write_audit_log(event)
            logger.info(f"Logged approval edit: {approval_id}")

        except Exception as e:
            logger.error(f"Error logging approval edit: {e}")

    def log_action_executed(
        self,
        approval_id: str,
        action_type: str,
        result: str,
        details: Dict[str, Any] = None
    ) -> None:
        """
        Log action execution after approval

        Args:
            approval_id: Approval ID
            action_type: Type of action executed
            result: Execution result (success, failure)
            details: Optional execution details
        """
        try:
            event = {
                'event_type': 'action_executed',
                'approval_id': approval_id,
                'action_type': action_type,
                'result': result,
                'details': details or {},
                'timestamp': datetime.now().isoformat()
            }

            self._write_audit_log(event)
            logger.info(f"Logged action execution: {approval_id} - {result}")

        except Exception as e:
            logger.error(f"Error logging action execution: {e}")

    def _write_audit_log(self, event: Dict[str, Any]) -> None:
        """
        Write audit log entry to file

        Args:
            event: Event data dictionary
        """
        try:
            # Create daily audit log file
            date_str = datetime.now().strftime('%Y-%m-%d')
            log_file = self.audit_folder / f"approval-audit-{date_str}.md"

            # Create or append to log file
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                content = f"# Approval Audit Log - {date_str}\n\n"

            # Format event as markdown
            event_md = self._format_event(event)
            content += event_md + "\n\n---\n\n"

            # Write updated content
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(content)

        except Exception as e:
            logger.error(f"Error writing audit log: {e}")

    def _format_event(self, event: Dict[str, Any]) -> str:
        """
        Format event as markdown

        Args:
            event: Event data dictionary

        Returns:
            Formatted markdown string
        """
        event_type = event.get('event_type', 'unknown')
        timestamp = event.get('timestamp', '')

        md = f"## {event_type.replace('_', ' ').title()}\n\n"
        md += f"**Timestamp**: {timestamp}\n\n"

        # Add event-specific fields
        for key, value in event.items():
            if key not in ['event_type', 'timestamp']:
                # Format key as title
                key_title = key.replace('_', ' ').title()

                # Format value
                if isinstance(value, list):
                    md += f"**{key_title}**:\n"
                    for item in value:
                        md += f"- {item}\n"
                    md += "\n"
                elif isinstance(value, dict):
                    md += f"**{key_title}**:\n"
                    for k, v in value.items():
                        md += f"- {k}: {v}\n"
                    md += "\n"
                else:
                    md += f"**{key_title}**: {value}\n\n"

        return md

    def get_approval_history(
        self,
        approval_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get complete history for an approval

        Args:
            approval_id: Approval ID

        Returns:
            List of events for this approval
        """
        events = []

        try:
            # Search through all audit log files
            for log_file in sorted(self.audit_folder.glob('approval-audit-*.md')):
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Simple parsing - look for approval_id in content
                if approval_id in content:
                    # Parse events from this file
                    # This is a simplified implementation
                    # In production, you'd want more robust parsing
                    events.append({
                        'file': log_file.name,
                        'content': content
                    })

        except Exception as e:
            logger.error(f"Error getting approval history: {e}")

        return events

    def get_audit_summary(
        self,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict[str, Any]:
        """
        Get audit summary for date range

        Args:
            start_date: Start date (default: 30 days ago)
            end_date: End date (default: now)

        Returns:
            Summary statistics
        """
        try:
            if not start_date:
                start_date = datetime.now().replace(day=1)  # First of month
            if not end_date:
                end_date = datetime.now()

            summary = {
                'total_approvals': 0,
                'approved': 0,
                'rejected': 0,
                'expired': 0,
                'by_action_type': {},
                'by_risk_level': {},
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }

            # Count events in date range
            for log_file in self.audit_folder.glob('approval-audit-*.md'):
                # Parse date from filename
                date_str = log_file.stem.replace('approval-audit-', '')
                try:
                    file_date = datetime.strptime(date_str, '%Y-%m-%d')
                    if start_date <= file_date <= end_date:
                        # Parse file and count events
                        with open(log_file, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # Simple counting (in production, use proper parsing)
                        summary['total_approvals'] += content.count('## Approval Created')
                        summary['approved'] += content.count('**Decision**: approved')
                        summary['rejected'] += content.count('**Decision**: rejected')
                        summary['expired'] += content.count('## Approval Timeout')

                except ValueError:
                    continue

            return summary

        except Exception as e:
            logger.error(f"Error getting audit summary: {e}")
            return {}

    def cleanup_old_logs(self, days_to_keep: int = 90) -> int:
        """
        Clean up old audit logs

        Args:
            days_to_keep: Number of days to keep (default: 90)

        Returns:
            Number of files deleted
        """
        try:
            cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_to_keep)

            deleted_count = 0

            for log_file in self.audit_folder.glob('approval-audit-*.md'):
                # Parse date from filename
                date_str = log_file.stem.replace('approval-audit-', '')
                try:
                    file_date = datetime.strptime(date_str, '%Y-%m-%d')
                    if file_date < cutoff_date:
                        log_file.unlink()
                        deleted_count += 1
                        logger.info(f"Deleted old audit log: {log_file.name}")
                except ValueError:
                    continue

            return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up old logs: {e}")
            return 0
