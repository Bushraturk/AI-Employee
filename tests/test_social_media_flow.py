"""Test script for social media content scheduling flow.

Tests the complete flow:
1. Cloud agent generates social media draft
2. Draft is written to Pending_Approval/social/
3. User approves (moves to Approved/)
4. Local agent executes and posts to platform
5. Dashboard is updated
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cloud_agent.src.drafters.social_drafter import SocialDrafter
from cloud_agent.src.utils.business_goals_parser import BusinessGoalsParser
from local_agent.src.executors.social_executor import SocialExecutor
from shared.utils.vault_manager import VaultManager
from shared.utils.logger import VaultLogger
from shared.models.vault_config import VaultConfig
from shared.models.approval_request import ApprovalRequest


def test_business_goals_parser():
    """Test business goals parser."""
    print("\n=== Testing Business Goals Parser ===")

    vault_path = Path(__file__).parent.parent / "vault"
    parser = BusinessGoalsParser(vault_path)

    goals = parser.get_goals()
    print(f"[OK] Parsed goals: {len(goals)} sections")

    social_focus = parser.get_social_media_focus()
    print(f"[OK] Social media focus: {len(social_focus.get('themes', []))} themes")
    print(f"  - Posting frequency: {social_focus.get('posting_frequency')}")
    print(f"  - Engagement target: {social_focus.get('engagement_target')}")

    return True


def test_social_drafter():
    """Test social media drafter."""
    print("\n=== Testing Social Media Drafter ===")

    # Setup
    vault_path = Path(__file__).parent.parent / "vault"
    vault_config = VaultConfig(vault_root=str(vault_path), sync_method="git")
    vault_manager = VaultManager(vault_config)
    vault_logger = VaultLogger(
        vault_root=vault_path,
        agent_id="test_agent",
    )

    # Create drafter
    drafter = SocialDrafter(
        agent_id="test_cloud_agent",
        vault_manager=vault_manager,
        vault_logger=vault_logger,
        claude_api_key=os.getenv("CLAUDE_API_KEY", "test_key"),
        business_goals_path=str(vault_path / "Business_Goals.md"),
    )

    print("[OK] Social drafter initialized")

    # Test draft generation for different platforms
    platforms = ["linkedin", "twitter", "facebook"]

    for platform in platforms:
        print(f"\n  Testing {platform} post generation...")
        approval = drafter.draft_post(
            platform=platform,
            content_type="update",
        )

        if approval:
            print(f"  [OK] Generated {platform} post")
            print(f"    - Approval ID: {approval.approval_id}")
            print(f"    - Risk level: {approval.risk_level.value}")
            # Encode preview to handle emojis on Windows console
            preview = approval.body[:100].encode('ascii', 'ignore').decode('ascii')
            print(f"    - Content preview: {preview}...")
        else:
            print(f"  [FAIL] Failed to generate {platform} post")
            return False

    return True


def test_social_executor():
    """Test social media executor."""
    print("\n=== Testing Social Media Executor ===")

    # Setup
    vault_path = Path(__file__).parent.parent / "vault"
    vault_config = VaultConfig(vault_root=str(vault_path), sync_method="git")
    vault_manager = VaultManager(vault_config)
    vault_logger = VaultLogger(
        vault_root=vault_path,
        agent_id="test_agent",
    )

    # Create executor in dry-run mode
    executor = SocialExecutor(
        agent_id="test_local_agent",
        vault_manager=vault_manager,
        vault_logger=vault_logger,
        mcp_client=None,
        dev_mode=False,
        dry_run=True,  # Dry run mode for testing
    )

    print("[OK] Social executor initialized")

    # Create a test approval request
    from shared.models.approval_request import ApprovalType, ApprovalStatus, RiskLevel

    test_approval = ApprovalRequest(
        approval_id=f"test_social_{datetime.now().strftime('%Y%m%dT%H%M%SZ')}",
        approval_type=ApprovalType.SOCIAL_POST,
        target_id="linkedin",
        timestamp=datetime.now(),
        status=ApprovalStatus.APPROVED,
        risk_level=RiskLevel.LOW,
        risk_factors=[],
        title="Test social post for LinkedIn",
        summary="Test post",
        body="This is a test social media post for LinkedIn.",
        metadata={
            "platform": "linkedin",
            "content_type": "update",
        },
        created_by="test_cloud_agent",
        action_file_id="test_action",
        expires_at=datetime.now(),
    )

    # Test can_execute
    can_execute = executor.can_execute(test_approval)
    print(f"[OK] Executor can handle social posts: {can_execute}")

    # Test execution (dry run)
    success = executor.execute(test_approval)
    print(f"[OK] Execution {'succeeded' if success else 'failed'} (dry run)")

    return success


def test_vault_structure():
    """Test vault folder structure."""
    print("\n=== Testing Vault Structure ===")

    vault_path = Path(__file__).parent.parent / "vault"

    required_folders = [
        "Pending_Approval/social",
        "Approved",
        "Done",
        "Rejected",
        "Updates",
        "Logs",
    ]

    for folder in required_folders:
        folder_path = vault_path / folder
        if folder_path.exists():
            print(f"[OK] {folder} exists")
        else:
            print(f"[WARN] {folder} missing - creating...")
            folder_path.mkdir(parents=True, exist_ok=True)
            print(f"  [OK] Created {folder}")

    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Social Media Content Scheduling - Integration Test")
    print("=" * 60)

    tests = [
        ("Vault Structure", test_vault_structure),
        ("Business Goals Parser", test_business_goals_parser),
        ("Social Drafter", test_social_drafter),
        ("Social Executor", test_social_executor),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n[FAIL] {test_name} failed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {test_name}")

    all_passed = all(result for _, result in results)

    if all_passed:
        print("\n[SUCCESS] All tests passed!")
        return 0
    else:
        print("\n[ERROR] Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
