"""
LinkedIn OAuth2 Authentication - Simple Version
Run this to authenticate with LinkedIn
"""
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import keyring
import requests
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import set_key, load_dotenv
import os

# Load environment variables
load_dotenv()

# LinkedIn OAuth2 Configuration
CLIENT_ID = os.getenv('LINKEDIN_CLIENT_ID', '777wvydg3gcbhy')
CLIENT_SECRET = os.getenv('LINKEDIN_CLIENT_SECRET')
REDIRECT_URI = os.getenv('LINKEDIN_REDIRECT_URI', 'http://localhost:8001/callback')
SCOPE = "openid profile email w_member_social w_organization_social"

if not CLIENT_SECRET:
    print("[ERROR] LINKEDIN_CLIENT_SECRET not found in .env file")
    print("Please add it to your .env file")
    exit(1)

# Global variable to store the authorization code
auth_code = None


class CallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth2 callback"""

    def do_GET(self):
        global auth_code

        # Parse the callback URL
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if 'code' in params:
            auth_code = params['code'][0]

            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            html = """
            <html>
            <head><title>LinkedIn Authentication</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1 style="color: #0077B5;">✅ Authentication Successful!</h1>
                <p>You can close this window and return to the terminal.</p>
                <p>Authorization code received. Exchanging for access token...</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        else:
            # Error response
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            error = params.get('error', ['Unknown error'])[0]
            html = f"""
            <html>
            <head><title>LinkedIn Authentication Error</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1 style="color: red;">❌ Authentication Failed</h1>
                <p>Error: {error}</p>
                <p>Please close this window and try again.</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())

    def log_message(self, format, *args):
        # Suppress log messages
        pass


def _save_tokens_to_env(tokens):
    """Save tokens to .env file as fallback"""
    env_file = Path('.env')

    set_key(env_file, 'LINKEDIN_ACCESS_TOKEN', tokens['access_token'])
    set_key(env_file, 'LINKEDIN_TOKEN_TYPE', tokens.get('token_type', 'Bearer'))
    set_key(env_file, 'LINKEDIN_EXPIRES_IN', str(tokens.get('expires_in', 5184000)))
    set_key(env_file, 'LINKEDIN_OBTAINED_AT', tokens['obtained_at'])
    set_key(env_file, 'LINKEDIN_EXPIRES_AT', tokens['expires_at'])

    if 'refresh_token' in tokens:
        set_key(env_file, 'LINKEDIN_REFRESH_TOKEN', tokens['refresh_token'])


def authenticate():
    """Authenticate with LinkedIn OAuth2"""

    print("=" * 60)
    print("LinkedIn OAuth2 Authentication")
    print("=" * 60)

    # Step 1: Generate authorization URL
    auth_url = (
        f"https://www.linkedin.com/oauth/v2/authorization?"
        f"response_type=code&"
        f"client_id={CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"scope={SCOPE}"
    )

    print("\n[INFO] Opening LinkedIn authorization page in your browser...")
    print("[INFO] Please log in and authorize the application")
    print("\nIf the browser doesn't open automatically, visit this URL:")
    print(auth_url)
    print()

    # Open browser
    webbrowser.open(auth_url)

    # Step 2: Start local server to receive callback
    print("[INFO] Starting local server to receive callback...")
    print("[INFO] Listening on http://localhost:8001")
    print("[INFO] Waiting for authorization...")
    print()

    server = HTTPServer(('localhost', 8001), CallbackHandler)

    # Wait for callback (timeout after 5 minutes)
    timeout = 300  # 5 minutes
    server.timeout = timeout

    try:
        server.handle_request()
    except KeyboardInterrupt:
        print("\n[CANCELLED] Authentication cancelled by user")
        return False

    if not auth_code:
        print("\n[ERROR] No authorization code received")
        print("[ERROR] Authentication failed or timed out")
        return False

    print("[SUCCESS] Authorization code received!")
    print()

    # Step 3: Exchange authorization code for access token
    print("[INFO] Exchanging authorization code for access token...")

    token_url = "https://www.linkedin.com/oauth/v2/accessToken"

    data = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }

    try:
        response = requests.post(token_url, data=data)
        response.raise_for_status()

        tokens = response.json()

        # Add timestamp
        tokens['obtained_at'] = datetime.now().isoformat()
        tokens['expires_at'] = (datetime.now() + timedelta(seconds=tokens.get('expires_in', 5184000))).isoformat()

        # Store tokens securely
        print("[INFO] Storing tokens securely...")
        try:
            keyring.set_password('ai_employee', 'linkedin_tokens', json.dumps(tokens))
            print("[SUCCESS] Tokens stored in system keyring")
        except Exception as e:
            print(f"[WARNING] Keyring failed: {e}")
            print("[INFO] Falling back to .env file...")
            _save_tokens_to_env(tokens)
            print("[SUCCESS] Tokens saved to .env file")

        print("\n" + "=" * 60)
        print("[SUCCESS] LinkedIn authentication complete!")
        print("=" * 60)
        print(f"Access Token: {tokens['access_token'][:20]}...")
        print(f"Expires In: {tokens.get('expires_in', 'N/A')} seconds")
        print(f"Token Type: {tokens.get('token_type', 'N/A')}")
        print("=" * 60)

        return True

    except requests.exceptions.RequestException as e:
        print("\n" + "=" * 60)
        print("[ERROR] Failed to exchange authorization code")
        print("=" * 60)
        print(f"Error: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        print("=" * 60)
        return False


if __name__ == '__main__':
    print("\nLinkedIn OAuth2 Authentication")
    print("This will open your browser for authorization\n")

    try:
        success = authenticate()

        if success:
            print("\n✅ You can now post to LinkedIn!")
            print("\nNext steps:")
            print("1. Approve the pending LinkedIn post")
            print("2. Run the posting script")
        else:
            print("\n❌ Authentication failed")
            print("\nTroubleshooting:")
            print("1. Make sure you have a LinkedIn account")
            print("2. Check your internet connection")
            print("3. Verify the client ID and secret in .env")
            print("4. Try running the script again")

    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] {e}")

    print("\nDone!")
