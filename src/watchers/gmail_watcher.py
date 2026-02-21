"""
Gmail Watcher Module

Monitors Gmail inbox for new emails and converts them to tasks.
"""

import base64
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import frontmatter
import uuid

from watchers.base_watcher import BaseWatcher, WatcherStatus
from watchers.auth.gmail_auth import GmailAuth

logger = logging.getLogger(__name__)


class GmailWatcher(BaseWatcher):
    """Gmail watcher - monitors inbox for new emails"""

    def __init__(self, vault_path: str, config: Dict[str, Any]):
        """
        Initialize Gmail watcher

        Args:
            vault_path: Path to vault directory
            config: Configuration with:
                - poll_interval_seconds: How often to check for new emails (default: 30)
                - labels_to_monitor: List of Gmail labels to monitor (default: ['INBOX'])
                - exclude_labels: List of labels to exclude (default: ['SPAM', 'TRASH'])
                - max_results_per_poll: Max emails to fetch per poll (default: 10)
        """
        super().__init__(
            watcher_id='gmail',
            watcher_type='gmail',
            config=config
        )

        self.vault_path = Path(vault_path)
        self.inbox_path = self.vault_path / 'Inbox'
        self.inbox_path.mkdir(parents=True, exist_ok=True)

        # Configuration
        self.poll_interval = config.get('poll_interval_seconds', 30)
        self.labels_to_monitor = config.get('labels_to_monitor', ['INBOX'])
        self.exclude_labels = config.get('exclude_labels', ['SPAM', 'TRASH'])
        self.max_results = config.get('max_results_per_poll', 10)

        # Authentication
        self.auth = GmailAuth()
        self.service = None

        # State for incremental sync
        self.history_id = None
        self.processed_message_ids = set()

        # Tracking
        self.new_tasks = []

    def start(self) -> None:
        """Start monitoring Gmail inbox"""
        logger.info("Starting Gmail watcher...")

        # Authenticate
        if not self.auth.authenticate():
            raise RuntimeError("Gmail authentication failed")

        self.service = self.auth.get_service()
        if not self.service:
            raise RuntimeError("Failed to get Gmail service")

        # Get initial history ID for incremental sync
        try:
            profile = self.service.users().getProfile(userId='me').execute()
            self.history_id = profile.get('historyId')
            logger.info(f"Gmail watcher initialized with historyId: {self.history_id}")
        except Exception as e:
            logger.error(f"Error getting Gmail profile: {e}")
            raise

        self.status = WatcherStatus.RUNNING
        logger.info("Gmail watcher started successfully")

    def stop(self) -> None:
        """Stop monitoring Gmail inbox"""
        logger.info("Stopping Gmail watcher...")
        self.status = WatcherStatus.STOPPED
        self.service = None
        logger.info("Gmail watcher stopped")

    def get_new_tasks(self) -> List[Dict[str, Any]]:
        """
        Get new emails and convert to tasks

        Returns:
            List of task information dictionaries
        """
        if self.status != WatcherStatus.RUNNING:
            return []

        try:
            # Fetch new emails
            new_emails = self._fetch_new_emails()

            # Convert emails to tasks
            tasks = []
            for email_data in new_emails:
                task_info = self._email_to_task(email_data)
                if task_info:
                    tasks.append(task_info)

            self._update_last_check()
            self._reset_error_count()

            return tasks

        except Exception as e:
            logger.error(f"Error getting new tasks from Gmail: {e}")
            self._increment_error_count()
            if self.error_count >= 5:
                self.status = WatcherStatus.ERROR
            return []

    def mark_processed(self, task_id: str) -> None:
        """
        Mark email as processed

        Args:
            task_id: Task ID (corresponds to Gmail message ID)
        """
        self.processed_message_ids.add(task_id)

    def _fetch_new_emails(self) -> List[Dict[str, Any]]:
        """
        Fetch new emails from Gmail

        Returns:
            List of email data dictionaries
        """
        try:
            # Build query
            query_parts = []

            # Add label filters
            for label in self.labels_to_monitor:
                query_parts.append(f"label:{label}")

            # Exclude labels
            for label in self.exclude_labels:
                query_parts.append(f"-label:{label}")

            # Only unread emails
            query_parts.append("is:unread")

            query = " ".join(query_parts)

            # List messages
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=self.max_results
            ).execute()

            messages = results.get('messages', [])

            # Fetch full message details
            emails = []
            for message in messages:
                msg_id = message['id']

                # Skip if already processed
                if msg_id in self.processed_message_ids:
                    continue

                # Get full message
                msg = self.service.users().messages().get(
                    userId='me',
                    id=msg_id,
                    format='full'
                ).execute()

                emails.append(msg)

            return emails

        except Exception as e:
            logger.error(f"Error fetching emails from Gmail: {e}")
            raise

    def _email_to_task(self, email_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert Gmail email to task format

        Args:
            email_data: Gmail API message object

        Returns:
            Task information dictionary or None if conversion fails
        """
        try:
            # Extract message ID
            message_id = email_data['id']
            thread_id = email_data['threadId']

            # Extract headers
            headers = {h['name']: h['value'] for h in email_data['payload']['headers']}
            sender = headers.get('From', 'Unknown')
            subject = headers.get('Subject', 'No Subject')
            date = headers.get('Date', '')

            # Extract body
            body = self._extract_email_body(email_data['payload'])

            # Create task file
            task_id = str(uuid.uuid4())
            task_file = self.inbox_path / f"{task_id}.md"

            # Create task metadata
            metadata = {
                'task_id': task_id,
                'title': f"Email: {subject}",
                'priority': 'P2',  # Default, will be classified by agent skill
                'status': 'inbox',
                'channel': 'gmail',
                'channel_metadata': {
                    'sender': sender,
                    'subject': subject,
                    'message_id': message_id,
                    'thread_id': thread_id,
                    'date': date
                },
                'created_at': datetime.now().isoformat(),
                'category': 'email'
            }

            # Create task content
            content = f"# Email from {sender}\n\n"
            content += f"**Subject**: {subject}\n\n"
            content += f"**Date**: {date}\n\n"
            content += f"**Body**:\n\n{body}\n\n"
            content += f"---\n\n"
            content += f"**Action Required**: Classify and process this email\n"

            # Write task file
            post = frontmatter.Post(content, **metadata)
            with open(task_file, 'w', encoding='utf-8') as f:
                f.write(frontmatter.dumps(post))

            logger.info(f"Created task from Gmail email: {subject}")

            return {
                'file_path': str(task_file),
                'task_id': task_id,
                'detected_at': datetime.now().isoformat(),
                'channel': 'gmail',
                'message_id': message_id
            }

        except Exception as e:
            logger.error(f"Error converting email to task: {e}")
            return None

    def _extract_email_body(self, payload: Dict[str, Any]) -> str:
        """
        Extract email body from Gmail payload

        Args:
            payload: Gmail message payload

        Returns:
            Email body text
        """
        body = ""

        # Check for body in payload
        if 'body' in payload and 'data' in payload['body']:
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        elif 'parts' in payload:
            # Multi-part message
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
                elif part['mimeType'] == 'text/html' and not body:
                    # Fallback to HTML if no plain text
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')

        # Truncate if too long
        if len(body) > 5000:
            body = body[:5000] + "\n\n[... truncated ...]"

        return body

    def _handle_rate_limit(self, retry_after: int = 5):
        """
        Handle Gmail API rate limit

        Args:
            retry_after: Seconds to wait before retry
        """
        logger.warning(f"Gmail API rate limit hit, waiting {retry_after} seconds...")
        time.sleep(retry_after)
