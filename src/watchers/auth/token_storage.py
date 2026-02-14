"""
Token Storage Module

Securely stores OAuth2 tokens using OS keyring with encrypted file fallback.
Supports Gmail, LinkedIn, and other OAuth2 services.
"""

import json
import keyring
from pathlib import Path
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
import base64
import hashlib


class TokenStorage:
    """Secure token storage using OS keyring with encrypted file fallback"""

    SERVICE_NAME = "ai-employee-system"
    FALLBACK_DIR = Path.home() / ".ai-employee" / "tokens"

    def __init__(self):
        """Initialize token storage"""
        self.FALLBACK_DIR.mkdir(parents=True, exist_ok=True)
        self._encryption_key = self._get_or_create_encryption_key()

    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for fallback storage"""
        key_file = self.FALLBACK_DIR / ".key"

        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            # Make key file read-only
            key_file.chmod(0o600)
            return key

    def store_token(self, account: str, token: Dict[str, Any]) -> bool:
        """
        Store OAuth2 token securely

        Args:
            account: Account identifier (e.g., 'gmail', 'linkedin')
            token: Token dictionary with access_token, refresh_token, etc.

        Returns:
            True if stored successfully
        """
        token_json = json.dumps(token)

        try:
            # Try OS keyring first
            keyring.set_password(self.SERVICE_NAME, account, token_json)
            return True
        except keyring.errors.KeyringError:
            # Fallback to encrypted file
            return self._store_encrypted_file(account, token_json)

    def get_token(self, account: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve OAuth2 token

        Args:
            account: Account identifier

        Returns:
            Token dictionary or None if not found
        """
        try:
            # Try OS keyring first
            token_json = keyring.get_password(self.SERVICE_NAME, account)
            if token_json:
                return json.loads(token_json)
        except keyring.errors.KeyringError:
            pass

        # Fallback to encrypted file
        return self._get_encrypted_file(account)

    def delete_token(self, account: str) -> bool:
        """
        Delete stored token

        Args:
            account: Account identifier

        Returns:
            True if deleted successfully
        """
        try:
            # Try OS keyring first
            keyring.delete_password(self.SERVICE_NAME, account)
        except keyring.errors.KeyringError:
            pass

        # Delete encrypted file if exists
        token_file = self.FALLBACK_DIR / f"{account}.token"
        if token_file.exists():
            token_file.unlink()

        return True

    def _store_encrypted_file(self, account: str, token_json: str) -> bool:
        """Store token in encrypted file"""
        try:
            fernet = Fernet(self._encryption_key)
            encrypted_data = fernet.encrypt(token_json.encode())

            token_file = self.FALLBACK_DIR / f"{account}.token"
            with open(token_file, 'wb') as f:
                f.write(encrypted_data)

            # Make token file read-only
            token_file.chmod(0o600)
            return True
        except Exception as e:
            print(f"Error storing encrypted token: {e}")
            return False

    def _get_encrypted_file(self, account: str) -> Optional[Dict[str, Any]]:
        """Retrieve token from encrypted file"""
        token_file = self.FALLBACK_DIR / f"{account}.token"

        if not token_file.exists():
            return None

        try:
            fernet = Fernet(self._encryption_key)
            with open(token_file, 'rb') as f:
                encrypted_data = f.read()

            decrypted_data = fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            print(f"Error retrieving encrypted token: {e}")
            return None

    def list_accounts(self) -> list[str]:
        """List all stored accounts"""
        accounts = []

        # Check encrypted files
        if self.FALLBACK_DIR.exists():
            for token_file in self.FALLBACK_DIR.glob("*.token"):
                accounts.append(token_file.stem)

        return accounts
