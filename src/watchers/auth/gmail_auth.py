"""
Gmail Authentication Module

Handles OAuth2 authentication for Gmail API access.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from watchers.auth.token_storage import TokenStorage


class GmailAuth:
    """Gmail OAuth2 authentication handler"""

    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.modify'
    ]

    def __init__(self, credentials_path: str = "credentials/gmail_credentials.json"):
        """
        Initialize Gmail authentication

        Args:
            credentials_path: Path to OAuth2 credentials JSON file
        """
        self.credentials_path = Path(credentials_path)
        self.token_storage = TokenStorage()
        self.creds: Optional[Credentials] = None

    def authenticate(self) -> bool:
        """
        Authenticate with Gmail API using OAuth2

        Returns:
            True if authentication successful
        """
        # Try to load existing token
        token_data = self.token_storage.get_token('gmail')

        if token_data:
            self.creds = Credentials.from_authorized_user_info(token_data, self.SCOPES)

        # If no valid credentials, authenticate
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                # Refresh expired token
                try:
                    self.creds.refresh(Request())
                    self._save_credentials()
                    return True
                except Exception as e:
                    print(f"Error refreshing token: {e}")
                    # Fall through to re-authenticate

            # Run OAuth2 flow
            if not self.credentials_path.exists():
                print(f"Error: Credentials file not found at {self.credentials_path}")
                print("Please download OAuth2 credentials from Google Cloud Console")
                return False

            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path),
                    self.SCOPES
                )
                self.creds = flow.run_local_server(port=0)
                self._save_credentials()
                return True
            except Exception as e:
                print(f"Error during OAuth2 flow: {e}")
                return False

        return True

    def _save_credentials(self) -> bool:
        """Save credentials to secure storage"""
        if not self.creds:
            return False

        token_data = {
            'token': self.creds.token,
            'refresh_token': self.creds.refresh_token,
            'token_uri': self.creds.token_uri,
            'client_id': self.creds.client_id,
            'client_secret': self.creds.client_secret,
            'scopes': self.creds.scopes
        }

        return self.token_storage.store_token('gmail', token_data)

    def get_service(self):
        """
        Get authenticated Gmail API service

        Returns:
            Gmail API service object or None if not authenticated
        """
        if not self.creds or not self.creds.valid:
            if not self.authenticate():
                return None

        try:
            service = build('gmail', 'v1', credentials=self.creds)
            return service
        except Exception as e:
            print(f"Error building Gmail service: {e}")
            return None

    def verify_authentication(self) -> bool:
        """
        Verify authentication is working

        Returns:
            True if can access Gmail API
        """
        service = self.get_service()
        if not service:
            return False

        try:
            # Try to get user profile
            profile = service.users().getProfile(userId='me').execute()
            print(f"[OK] Gmail authentication successful: {profile.get('emailAddress')}")
            return True
        except Exception as e:
            print(f"[FAIL] Gmail authentication failed: {e}")
            return False

    def revoke_authentication(self) -> bool:
        """
        Revoke authentication and delete stored token

        Returns:
            True if revoked successfully
        """
        self.creds = None
        return self.token_storage.delete_token('gmail')


# CLI interface for authentication
if __name__ == "__main__":
    import sys

    auth = GmailAuth()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "--authenticate":
            print("Starting Gmail authentication...")
            if auth.authenticate():
                print("[OK] Authentication successful!")
                auth.verify_authentication()
            else:
                print("[FAIL] Authentication failed")
                sys.exit(1)

        elif command == "--verify":
            print("Verifying Gmail authentication...")
            if auth.verify_authentication():
                print("[OK] Verification complete")
                sys.exit(0)
            else:
                print("[FAIL] Verification failed")
                sys.exit(1)

        elif command == "--refresh":
            print("Refreshing Gmail token...")
            if auth.authenticate():
                print("[OK] Token refreshed successfully!")
            else:
                print("[FAIL] Token refresh failed")
                sys.exit(1)

        elif command == "--revoke":
            print("Revoking Gmail authentication...")
            if auth.revoke_authentication():
                print("[OK] Authentication revoked")
            else:
                print("[FAIL] Failed to revoke authentication")
                sys.exit(1)

        else:
            print(f"Unknown command: {command}")
            print("Usage: python gmail_auth.py [--authenticate|--verify|--refresh|--revoke]")
            sys.exit(1)
    else:
        print("Usage: python gmail_auth.py [--authenticate|--verify|--refresh|--revoke]")
        sys.exit(1)
