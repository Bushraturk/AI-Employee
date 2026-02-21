"""
Plan Generation Integration Test
Tests intelligent planning skill
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from skills.planning_skill import PlanningSkill


def test_plan_generation():
    """Test plan generation for complex tasks"""

    print("=" * 60)
    print("Plan Generation Integration Test")
    print("=" * 60)

    # Configuration
    vault_path = "AI_Employee_Vault"
    config = {
        'min_steps_for_plan': 3
    }

    print("\n[INFO] Configuration:")
    print(f"  Vault Path: {vault_path}")
    print(f"  Min Steps for Plan: {config['min_steps_for_plan']}")

    # Create planning skill
    print("\n[INFO] Creating planning skill...")
    skill = PlanningSkill(vault_path, config)

    print(f"[SUCCESS] Skill created: {skill.name}")
    print(f"  Skill ID: {skill.skill_id}")
    print(f"  Category: {skill.category}")
    print(f"  Description: {skill.description}")

    # Test Case 1: Simple task (should NOT generate plan)
    print("\n" + "=" * 60)
    print("Test Case 1: Simple Task (No Plan Needed)")
    print("=" * 60)

    simple_task = {
        'task_id': 'test-simple-001',
        'title': 'Send email to John',
        'content': 'Send a quick email to John about the meeting.',
        'priority': 'P2'
    }

    context = {'task_data': simple_task}

    print("\n[INFO] Task:")
    print(f"  Title: {simple_task['title']}")
    print(f"  Content: {simple_task['content']}")

    result = skill.execute(context)

    print("\n[INFO] Result:")
    print(f"  Plan Generated: {result.get('plan_generated')}")
    print(f"  Reason: {result.get('reason', 'N/A')}")

    if not result['plan_generated']:
        print("\n[SUCCESS] Correctly identified as simple task")
    else:
        print("\n[ERROR] Should not have generated plan for simple task")
        return False

    # Test Case 2: Complex task (SHOULD generate plan)
    print("\n" + "=" * 60)
    print("Test Case 2: Complex Task (Plan Required)")
    print("=" * 60)

    complex_task = {
        'task_id': 'test-complex-001',
        'title': 'Build new authentication system',
        'content': '''
        Build a new authentication system with the following requirements:
        1. User registration with email verification
        2. Login with JWT tokens
        3. Password reset functionality
        4. Two-factor authentication
        5. Session management
        6. OAuth2 integration with Google and GitHub
        7. Role-based access control
        8. Audit logging for security events
        ''',
        'priority': 'P1'
    }

    context = {'task_data': complex_task}

    print("\n[INFO] Task:")
    print(f"  Title: {complex_task['title']}")
    print(f"  Content: {complex_task['content'][:100]}...")

    result = skill.execute(context)

    print("\n[INFO] Result:")
    print(f"  Plan Generated: {result.get('plan_generated')}")

    if result['plan_generated']:
        plan_path = result.get('plan_path')
        print(f"  Plan Path: {plan_path}")

        # Read and display plan
        if plan_path and Path(plan_path).exists():
            print("\n[INFO] Plan File Content:")
            print("-" * 60)
            with open(plan_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Show first 500 chars
                preview = content[:500] + "..." if len(content) > 500 else content
                print(preview)
            print("-" * 60)

            print("\n[SUCCESS] Plan generated successfully!")
            return True
        else:
            print("\n[ERROR] Plan file not found")
            return False
    else:
        print(f"\n[ERROR] Should have generated plan for complex task")
        print(f"  Reason: {result.get('reason')}")
        return False


if __name__ == '__main__':
    print("\nPlan Generation Integration Test")
    print("Tests intelligent planning skill\n")

    try:
        success = test_plan_generation()

        if success:
            print("\n" + "=" * 60)
            print("[SUCCESS] Plan Generation Test PASSED")
            print("=" * 60)
            print("\nPlanning skill is working correctly!")
        else:
            print("\n" + "=" * 60)
            print("[ERROR] Plan Generation Test FAILED")
            print("=" * 60)
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Test cancelled by user")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\nDone!")
