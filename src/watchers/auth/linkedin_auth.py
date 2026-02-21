"""
LinkedIn Authentication Module

Handles OAuth2 authentication for LinkedIn API access.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
import requests
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient

from watchers.auth.token_storage import TokenStorage


class LinkedInAuth:
    """LinkedIn OAuth2 authentication handler"""

    # LinkedIn API OAuth2 endpoints
    AUTHORIZATION_URL = 'https://www.linkedin.com/oauth/v2/authorization'
    TOKEN_URL = 'https://www.linkedin.com/oauth/v2/accessToken'
    API_BASE_URL = 'https://api.linkedin.com/v2'

    # Required scopes for LinkedIn API
    # Using OpenID Connect + Share on LinkedIn scopes
    SCOPES = [
        'openid',             # OpenID Connect
        'profile',            # Read basic profile (replaces r_liteprofile)
        'w_member_social',    # Post on LinkedIn
    ]

    def __init__(self, credentials_path: str = "credentials/linkedin_credentials.json"):
        """
        Initialize LinkedIn authentication

        Args:
            credentials_path: Path to OAuth2 credentials JSON file
        """
        self.credentials_path = Path(credentials_path)
        self.token_storage = TokenStorage()
        self.client_id = None
        self.client_secret = None
        self.redirect_uri = None
        self.access_token = None
        self.refresh_token = None

        # Load credentials
        self._load_credentials()

    def _load_credentials(self) -> bool:
        """Load OAuth2 credentials from file"""
        if not self.credentials_path.exists():
            print(f"Error: Credentials file not found at {self.credentials_path}")
            print("Please create credentials file with client_id, client_secret, and redirect_uri")
            return False

        try:
            with open(self.credentials_path, 'r') as f:
                creds = json.load(f)
                self.client_id = creds.get('client_id')
                self.client_secret = creds.get('client_secret')
                self.redirect_uri = creds.get('redirect_uri', 'http://localhost:8080/callback')

            if not self.client_id or not self.client_secret:
                print("Error: Missing client_id or client_secret in credentials file")
                return False

            return True
        except Exception as e:
            print(f"Error loading credentials: {e}")
            return False

    def authenticate(self) -> bool:
        """
        Authenticate with LinkedIn API using OAuth2

        Returns:
            True if authentication successful
        """
        # Try to load existing token
        token_data = self.token_storage.get_token('linkedin')

        if token_data:
            self.access_token = token_data.get('access_token')
            self.refresh_token = token_data.get('refresh_token')

            # Verify token is still valid
            if self._verify_token():
                return True

        # If no valid token, start OAuth2 flow
        return self._oauth_flow()

    def _oauth_flow(self) -> bool:
        """
        Run OAuth2 authorization flow

        Returns:
            True if successful
        """
        try:
            # Allow insecure transport for localhost development
            import os
            os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

            # Create OAuth2 session
            oauth = OAuth2Session(
                self.client_id,
                redirect_uri=self.redirect_uri,
                scope=self.SCOPES
            )

            # Get authorization URL
            authorization_url, state = oauth.authorization_url(self.AUTHORIZATION_URL)

            print("\n" + "="*60)
            print("LinkedIn Authentication Required")
            print("="*60)
            print(f"\n1. Open this URL in your browser:\n\n{authorization_url}\n")
            print("2. Authorize the application")
            print("3. Copy the full redirect URL from your browser")
            print("   (It will look like: http://localhost:8080/callback?code=...)")
            print("\n" + "="*60 + "\n")

            # Get redirect URL from user
            redirect_response = input("Paste the full redirect URL here: ").strip()

            # Fetch token with explicit client credentials
            token = oauth.fetch_token(
                self.TOKEN_URL,
                authorization_response=redirect_response,
                client_secret=self.client_secret,
                include_client_id=True,
                client_id=self.client_id
            )

            self.access_token = token.get('access_token')
            self.refresh_token = token.get('refresh_token')

            # Save token
            self._save_token(token)

            print("\n✅ LinkedIn authentication successful!")
            return True

        except Exception as e:
            print(f"Error during OAuth2 flow: {e}")
            return False

    def _verify_token(self) -> bool:
        """
        Verify access token is valid

        Returns:
            True if token is valid
        """
        if not self.access_token:
            return False

        try:
            # Test token by fetching user profile
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }

            response = requests.get(
                f'{self.API_BASE_URL}/me',
                headers=headers,
                timeout=10
            )

            return response.status_code == 200

        except Exception as e:
            print(f"Error verifying token: {e}")
            return False

    def _save_token(self, token: Dict[str, Any]) -> bool:
        """Save token to secure storage"""
        token_data = {
            'access_token': token.get('access_token'),
            'refresh_token': token.get('refresh_token'),
            'token_type': token.get('token_type'),
            'expires_in': token.get('expires_in'),
            'scope': token.get('scope')
        }

        return self.token_storage.store_token('linkedin', token_data)

    def get_access_token(self) -> Optional[str]:
        """
        Get valid access token

        Returns:
            Access token string or None if not authenticated
        """
        if not self.access_token:
            if not self.authenticate():
                return None

        return self.access_token

    def get_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers with authentication

        Returns:
            Dictionary of headers for API requests
        """
        token = self.get_access_token()
        if not token:
            return {}

        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0'
        }

    def verify_authentication(self) -> bool:
        """
        Verify authentication is working

        Returns:
            True if can access LinkedIn API
        """
        try:
            headers = self.get_headers()
            if not headers:
                print("❌ LinkedIn authentication failed: No valid token")
                return False

            # Get user profile
            response = requests.get(
                f'{self.API_BASE_URL}/me',
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                profile = response.json()
                name = f"{profile.get('localizedFirstName', '')} {profile.get('localizedLastName', '')}"
                print(f"✅ LinkedIn authentication successful: {name}")
                return True
            else:
                print(f"❌ LinkedIn authentication failed: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ LinkedIn authentication failed: {e}")
            return False

    def revoke_authentication(self) -> bool:
        """
        Revoke authentication and delete stored token

        Returns:
            True if revoked successfully
        """
        self.access_token = None
        self.refresh_token = None
        return self.token_storage.delete_token('linkedin')


# CLI interface for authentication
if __name__ == "__main__":
    import sys

    auth = LinkedInAuth()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "--authenticate":
            print("Starting LinkedIn authentication...")
            if auth.authenticate():
                print("✅ Authentication successful!")
                auth.verify_authentication()
            else:
                print("❌ Authentication failed")
                sys.exit(1)

        elif command == "--verify":
            print("Verifying LinkedIn authentication...")
            if auth.verify_authentication():
                sys.exit(0)
            else:
                sys.exit(1)

        elif command == "--revoke":
            print("Revoking LinkedIn authentication...")
            if auth.revoke_authentication():
                print("✅ Authentication revoked")
            else:
                print("❌ Failed to revoke authentication")
                sys.exit(1)

        else:
            print(f"Unknown command: {command}")
            print("Usage: python linkedin_auth.py [--authenticate|--verify|--revoke]")
            sys.exit(1)
    else:
        print("Usage: python linkedin_auth.py [--authenticate|--verify|--revoke]")
        sys.exit(1)
