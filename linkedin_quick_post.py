"""
LinkedIn Company Page Quick Poster
Simple version - no interactive input needed
"""
import pyperclip
import webbrowser
from pathlib import Path
import frontmatter

def quick_post_helper(approval_id):
    """Quick helper - copy and open only"""

    print("=" * 60)
    print("LinkedIn Company Page Quick Poster")
    print("=" * 60)

    # Load approval
    approval_file = Path(f"AI_Employee_Vault/Needs_Approval/{approval_id}.md")

    if not approval_file.exists():
        print(f"[ERROR] File not found: {approval_file}")
        return False

    with open(approval_file, 'r', encoding='utf-8') as f:
        post = frontmatter.load(f)

    # Get content
    content = post.metadata.get('action_details', {}).get('content', '')

    if not content:
        print("[ERROR] No content found")
        return False

    # Show content
    print("\n[INFO] Post Content:")
    print("-" * 60)
    print(content)
    print("-" * 60)

    # Copy to clipboard
    print("\n[INFO] Copying to clipboard...")
    pyperclip.copy(content)
    print("[SUCCESS] Copied!")

    # Open company page
    company_url = "https://www.linkedin.com/company/smart-ai-system/admin/"
    print(f"\n[INFO] Opening: {company_url}")
    webbrowser.open(company_url)

    print("\n" + "=" * 60)
    print("MANUAL STEPS:")
    print("=" * 60)
    print("1. Browser opened with company page admin")
    print("2. Click 'Start a post' button")
    print("3. Press Ctrl+V to paste")
    print("4. Review and click 'Post'")
    print("=" * 60)
    print("\n[SUCCESS] Ready to post!")

    return True

if __name__ == '__main__':
    approval_id = "07723a50-6f86-40d0-a4d1-e5fc3c8eb54a"
    quick_post_helper(approval_id)
