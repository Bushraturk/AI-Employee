"""Gmail watcher for cloud agent."""

import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from shared.base_watcher import BaseWatcher
from shared.models.watcher_state import WatcherType
from shared.models.action_file import ActionFile, ActionType, ActionStatus
from shared.utils.vault_manager import VaultManager
from shared.utils.logger import VaultLogger


logger = logging.getLogger(__name__)

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class GmailWatcher(BaseWatcher):
    """Watcher for Gmail inbox monitoring.

    Polls Gmail API for new messages and creates action files.
    """

    def __init__(
        self,
        agent_id: str,
        vault_manager: VaultManager,
        vault_logger: VaultLogger,
        credentials_path: str,
        token_path: str,
        check_interval_seconds: int = 120,
    ):
        """Initialize Gmail watcher.

        Args:
            agent_id: Agent ID
            vault_manager: Vault manager instance
            vault_logger: Vault logger instance
            credentials_path: Path to Gmail credentials JSON
            token_path: Path to Gmail token JSON
            check_interval_seconds: Check interval in seconds
        """
        super().__init__(
            watcher_id=f"{agent_id}_gmail",
            watcher_type=WatcherType.GMAIL,
            watcher_name="Gmail Watcher",
            agent_id=agent_id,
            vault_manager=vault_manager,
            vault_logger=vault_logger,
            check_interval_seconds=check_interval_seconds,
            config={
                "credentials_path": credentials_path,
                "token_path": token_path,
            },
        )

        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None

        # Development mode
        self.dev_mode = os.getenv("DEVELOPMENT_MODE", "false").lower() == "true"
        self.dry_run = os.getenv("DRY_RUN_MODE", "false").lower() == "true"

        # Initialize Gmail API (skip in dev mode or if credentials missing)
        if not self.dev_mode and os.path.exists(credentials_path):
            self._initialize_gmail_api()
        else:
            if self.dev_mode:
                logger.info("[DEV MODE] Skipping Gmail API initialization")
            else:
                logger.warning(f"Gmail credentials not found at {credentials_path}, skipping initialization")

    def _initialize_gmail_api(self) -> None:
        """Initialize Gmail API service."""
        try:
            creds = None

            # Load token if exists
            if os.path.exists(self.token_path):
                creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)

            # If no valid credentials, authenticate
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, SCOPES
                    )
                    creds = flow.run_local_server(port=0)

                # Save credentials
                with open(self.token_path, 'w') as token:
                    token.write(creds.to_json())

            # Build service
            self.service = build('gmail', 'v1', credentials=creds)
            logger.info("Gmail API initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Gmail API: {e}")
            raise

    def check_for_events(self) -> List[ActionFile]:
        """Check Gmail for new messages.

        Returns:
            List of action files for new messages
        """
        if not self.service:
            logger.error("Gmail service not initialized")
            return []

        try:
            # Build query
            query = "is:unread in:inbox"
            if self.state.last_sync_token:
                # Use history API for incremental sync
                return self._check_with_history()
            else:
                # Initial sync - get recent unread messages
                return self._check_with_list(query)

        except HttpError as e:
            logger.error(f"Gmail API error: {e}")
            raise

    def _check_with_list(self, query: str, max_results: int = 10) -> List[ActionFile]:
        """Check for messages using list API.

        Args:
            query: Gmail search query
            max_results: Maximum number of results

        Returns:
            List of action files
        """
        actions = []

        # List messages
        results = self.service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()

        messages = results.get('messages', [])

        for msg in messages:
            # Get full message
            message = self.service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='full'
            ).execute()

            # Create action file
            action = self._create_action_from_message(message)
            if action:
                actions.append(action)

        # Update sync token
        if messages:
            self.state.last_message_id = messages[0]['id']

        return actions

    def _check_with_history(self) -> List[ActionFile]:
        """Check for messages using history API.

        Returns:
            List of action files
        """
        actions = []

        try:
            # Get history
            history = self.service.users().history().list(
                userId='me',
                startHistoryId=self.state.last_sync_token,
                historyTypes=['messageAdded']
            ).execute()

            changes = history.get('history', [])

            for change in changes:
                if 'messagesAdded' in change:
                    for added in change['messagesAdded']:
                        message = added['message']

                        # Get full message
                        full_message = self.service.users().messages().get(
                            userId='me',
                            id=message['id'],
                            format='full'
                        ).execute()

                        # Create action file
                        action = self._create_action_from_message(full_message)
                        if action:
                            actions.append(action)

            # Update sync token
            if 'historyId' in history:
                self.state.last_sync_token = str(history['historyId'])

        except HttpError as e:
            if e.resp.status == 404:
                # History expired, fall back to list
                logger.warning("Gmail history expired, falling back to list")
                self.state.last_sync_token = None
                return self._check_with_list("is:unread in:inbox")
            else:
                raise

        return actions

    def _create_action_from_message(self, message: Dict[str, Any]) -> Optional[ActionFile]:
        """Create action file from Gmail message.

        Args:
            message: Gmail message object

        Returns:
            ActionFile instance or None
        """
        try:
            # Extract headers
            headers = {h['name']: h['value'] for h in message['payload']['headers']}

            sender = headers.get('From', 'Unknown')
            subject = headers.get('Subject', '(No subject)')
            date_str = headers.get('Date', '')

            # Parse message body
            body = self._extract_body(message['payload'])

            # Create action file
            action = ActionFile(
                action_id=f"email_{message['id']}",
                action_type=ActionType.EMAIL,
                source_id=message['id'],
                timestamp=datetime.now(),
                status=ActionStatus.NEEDS_ACTION,
                title=f"Email from {sender}: {subject}",
                body=f"""# Email Message

**From**: {sender}
**Subject**: {subject}
**Date**: {date_str}

## Body

{body}

## Metadata

- Message ID: {message['id']}
- Thread ID: {message.get('threadId', 'N/A')}
- Labels: {', '.join(message.get('labelIds', []))}
""",
                metadata={
                    "sender": sender,
                    "subject": subject,
                    "date": date_str,
                    "message_id": message['id'],
                    "thread_id": message.get('threadId'),
                    "labels": message.get('labelIds', []),
                },
            )

            return action

        except Exception as e:
            logger.error(f"Failed to create action from message {message.get('id')}: {e}")
            return None

    def _extract_body(self, payload: Dict[str, Any]) -> str:
        """Extract message body from payload.

        Args:
            payload: Message payload

        Returns:
            Message body text
        """
        import base64

        body = ""

        if 'parts' in payload:
            # Multipart message
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
        elif 'body' in payload and 'data' in payload['body']:
            # Simple message
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')

        return body or "(No text content)"

    def get_target_folder(self) -> str:
        """Get target vault folder for detected events.

        Returns:
            Folder path
        """
        return "Needs_Action/email"
