"""
LinkedIn Post Publisher - Test Script
Publishes approved LinkedIn posts
"""
import json
import keyring
import requests
from datetime import datetime
from pathlib import Path
import frontmatter
import os
from dotenv import load_dotenv


def _load_tokens_from_env():
    """Load tokens from .env file as fallback"""
    load_dotenv()

    access_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
    if not access_token:
        return None

    return {
        'access_token': access_token,
        'token_type': os.getenv('LINKEDIN_TOKEN_TYPE', 'Bearer'),
        'expires_in': int(os.getenv('LINKEDIN_EXPIRES_IN', 5184000)),
        'obtained_at': os.getenv('LINKEDIN_OBTAINED_AT'),
        'expires_at': os.getenv('LINKEDIN_EXPIRES_AT'),
        'refresh_token': os.getenv('LINKEDIN_REFRESH_TOKEN')
    }


def get_linkedin_tokens():
    """Retrieve LinkedIn tokens from keyring or .env"""
    # Try keyring first
    try:
        tokens_json = keyring.get_password('ai_employee', 'linkedin_tokens')
        if tokens_json:
            return json.loads(tokens_json)
    except Exception:
        pass

    # Fallback to .env
    return _load_tokens_from_env()


def get_user_profile(access_token):
    """Get LinkedIn user profile to get the person URN"""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(
            'https://api.linkedin.com/v2/userinfo',
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[ERROR] Failed to get user profile: {e}")
        return None


def post_to_linkedin(access_token, person_urn, content):
    """Post content to LinkedIn"""

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'X-Restli-Protocol-Version': '2.0.0'
    }

    # Create UGC post
    post_data = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": content
                },
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }

    try:
        response = requests.post(
            'https://api.linkedin.com/v2/ugcPosts',
            headers=headers,
            json=post_data
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[ERROR] Failed to post: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        return None


def publish_approved_post(approval_id):
    """Publish an approved LinkedIn post"""

    print("=" * 60)
    print("LinkedIn Post Publisher")
    print("=" * 60)

    # Step 1: Check authentication
    print("\n[INFO] Checking LinkedIn authentication...")
    tokens = get_linkedin_tokens()

    if not tokens:
        print("\n[ERROR] Not authenticated with LinkedIn")
        print("\nPlease run: python linkedin_authenticate.py")
        return False

    access_token = tokens.get('access_token')
    print("[SUCCESS] Authentication found!")

    # Step 2: Get user profile
    print("\n[INFO] Getting LinkedIn profile...")
    profile = get_user_profile(access_token)

    if not profile:
        print("[ERROR] Failed to get profile")
        return False

    person_urn = f"urn:li:person:{profile.get('sub')}"
    print(f"[SUCCESS] Profile retrieved: {profile.get('name', 'Unknown')}")

    # Step 3: Load approval
    print(f"\n[INFO] Loading approval: {approval_id}")
    approval_file = Path(f"AI_Employee_Vault/Needs_Approval/{approval_id}.md")

    if not approval_file.exists():
        print(f"[ERROR] Approval file not found: {approval_file}")
        return False

    with open(approval_file, 'r', encoding='utf-8') as f:
        post = frontmatter.load(f)

    # Step 4: Check approval status
    status = post.metadata.get('status')
    print(f"[INFO] Approval status: {status}")

    if status != 'approved':
        print(f"\n[ERROR] Post is not approved (status: {status})")
        print("\nTo approve:")
        print(f"1. Open: {approval_file}")
        print("2. Change: status: pending -> status: approved")
        print("3. Add: reviewer: your_name")
        print("4. Save the file")
        print("5. Run this script again")
        return False

    print("[SUCCESS] Post is approved!")

    # Step 5: Get post content
    content = post.metadata.get('action_details', {}).get('content', '')

    if not content:
        print("[ERROR] No content found in approval")
        return False

    print("\n" + "=" * 60)
    print("Post Content:")
    print("=" * 60)
    print(content)
    print("=" * 60)

    # Step 6: Confirm posting
    confirm = input("\nPost this to LinkedIn? (yes/y): ").strip().lower()

    if confirm not in ['yes', 'y']:
        print("\n[CANCELLED] Post not published")
        return False

    # Step 7: Post to LinkedIn
    print("\n[INFO] Publishing to LinkedIn...")
    result = post_to_linkedin(access_token, person_urn, content)

    if not result:
        print("\n[ERROR] Failed to publish post")
        return False

    post_id = result.get('id', 'unknown')

    print("\n" + "=" * 60)
    print("[SUCCESS] Post published to LinkedIn!")
    print("=" * 60)
    print(f"Post ID: {post_id}")
    print(f"Published at: {datetime.now().isoformat()}")
    print(f"Author: {profile.get('name', 'Unknown')}")
    print("=" * 60)

    # Step 8: Update approval file
    print("\n[INFO] Updating approval file...")
    post.metadata['status'] = 'completed'
    post.metadata['completed_at'] = datetime.now().isoformat()
    post.metadata['linkedin_post_id'] = post_id

    with open(approval_file, 'w', encoding='utf-8') as f:
        f.write(frontmatter.dumps(post))

    print("[SUCCESS] Approval file updated")

    return True


if __name__ == '__main__':
    print("\nLinkedIn Post Publisher")
    print("Publishes approved LinkedIn posts\n")

    # Use the approval ID from our test
    approval_id = "07723a50-6f86-40d0-a4d1-e5fc3c8eb54a"

    try:
        success = publish_approved_post(approval_id)

        if success:
            print("\n✅ LinkedIn post published successfully!")
            print("\nCheck your LinkedIn profile to see the post!")
        else:
            print("\n❌ Failed to publish post")
            print("\nTroubleshooting:")
            print("1. Make sure you're authenticated: python linkedin_authenticate.py")
            print("2. Approve the post in Needs_Approval folder")
            print("3. Check your internet connection")
            print("4. Verify LinkedIn API credentials in .env")

    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

    print("\nDone!")
