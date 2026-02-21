"""
Gmail MCP Tool

Implements email sending, draft creation, and email management via Gmail API.
"""

import base64
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class GmailTool:
    """Gmail tool for sending emails and managing drafts"""

    def __init__(self, vault_path: str = "vault"):
        """
        Initialize Gmail tool

        Args:
            vault_path: Path to vault directory
        """
        self.vault_path = Path(vault_path)
        self.gmail_service = None
        self._initialize_gmail_service()

    def _initialize_gmail_service(self):
        """Initialize Gmail API service with OAuth2 credentials"""
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            import os

            SCOPES = ['https://www.googleapis.com/auth/gmail.send',
                      'https://www.googleapis.com/auth/gmail.compose']

            creds = None
            token_path = self.vault_path / '.credentials' / 'gmail_token.json'
            credentials_path = self.vault_path / '.credentials' / 'gmail_credentials.json'

            # Load existing token
            if token_path.exists():
                creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

            # Refresh or get new token
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not credentials_path.exists():
                        logger.error(f"Gmail credentials not found at {credentials_path}")
                        logger.error("Please download OAuth2 credentials from Google Cloud Console")
                        return

                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(credentials_path), SCOPES)
                    creds = flow.run_local_server(port=0)

                # Save token
                token_path.parent.mkdir(parents=True, exist_ok=True)
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())

            self.gmail_service = build('gmail', 'v1', credentials=creds)
            logger.info("Gmail service initialized successfully")

        except ImportError as e:
            logger.error(f"Gmail API dependencies not installed: {e}")
            logger.error("Install with: pip install google-auth-oauthlib google-api-python-client")
        except Exception as e:
            logger.error(f"Error initializing Gmail service: {e}")

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
        html: bool = False
    ) -> Dict[str, Any]:
        """
        Send an email via Gmail API

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body content
            cc: CC recipients (comma-separated)
            bcc: BCC recipients (comma-separated)
            html: Whether body is HTML (default: plain text)

        Returns:
            Result dictionary with message_id and status
        """
        if not self.gmail_service:
            return {
                'success': False,
                'error': 'Gmail service not initialized. Check credentials.'
            }

        try:
            # Create message
            message = MIMEMultipart() if html else MIMEText(body)

            if html:
                message.attach(MIMEText(body, 'html'))

            message['to'] = to
            message['subject'] = subject

            if cc:
                message['cc'] = cc
            if bcc:
                message['bcc'] = bcc

            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

            # Send message
            send_message = self.gmail_service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            logger.info(f"Email sent successfully: {send_message['id']}")

            return {
                'success': True,
                'message_id': send_message['id'],
                'to': to,
                'subject': subject
            }

        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def create_draft(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
        html: bool = False
    ) -> Dict[str, Any]:
        """
        Create an email draft (for rollback capability)

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body content
            cc: CC recipients (comma-separated)
            bcc: BCC recipients (comma-separated)
            html: Whether body is HTML (default: plain text)

        Returns:
            Result dictionary with draft_id and status
        """
        if not self.gmail_service:
            return {
                'success': False,
                'error': 'Gmail service not initialized. Check credentials.'
            }

        try:
            # Create message
            message = MIMEMultipart() if html else MIMEText(body)

            if html:
                message.attach(MIMEText(body, 'html'))

            message['to'] = to
            message['subject'] = subject

            if cc:
                message['cc'] = cc
            if bcc:
                message['bcc'] = bcc

            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

            # Create draft
            draft = self.gmail_service.users().drafts().create(
                userId='me',
                body={'message': {'raw': raw_message}}
            ).execute()

            logger.info(f"Draft created successfully: {draft['id']}")

            return {
                'success': True,
                'draft_id': draft['id'],
                'to': to,
                'subject': subject
            }

        except Exception as e:
            logger.error(f"Error creating draft: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def delete_draft(self, draft_id: str) -> Dict[str, Any]:
        """
        Delete an email draft (rollback capability)

        Args:
            draft_id: Draft ID to delete

        Returns:
            Result dictionary with status
        """
        if not self.gmail_service:
            return {
                'success': False,
                'error': 'Gmail service not initialized. Check credentials.'
            }

        try:
            self.gmail_service.users().drafts().delete(
                userId='me',
                id=draft_id
            ).execute()

            logger.info(f"Draft deleted successfully: {draft_id}")

            return {
                'success': True,
                'draft_id': draft_id
            }

        except Exception as e:
            logger.error(f"Error deleting draft: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def send_draft(self, draft_id: str) -> Dict[str, Any]:
        """
        Send an existing draft

        Args:
            draft_id: Draft ID to send

        Returns:
            Result dictionary with message_id and status
        """
        if not self.gmail_service:
            return {
                'success': False,
                'error': 'Gmail service not initialized. Check credentials.'
            }

        try:
            message = self.gmail_service.users().drafts().send(
                userId='me',
                body={'id': draft_id}
            ).execute()

            logger.info(f"Draft sent successfully: {message['id']}")

            return {
                'success': True,
                'message_id': message['id'],
                'draft_id': draft_id
            }

        except Exception as e:
            logger.error(f"Error sending draft: {e}")
            return {
                'success': False,
                'error': str(e)
            }
