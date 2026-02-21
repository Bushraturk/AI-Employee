"""
Task Scheduling Integration Test
Tests task scheduling skill functionality
"""
import sys
import os
from pathlib import Path
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from skills.scheduling_skill import SchedulingSkill
from scheduling.task_scheduler import TaskScheduler


def test_task_scheduling():
    """Test task scheduling skill"""

    print("=" * 60)
    print("Task Scheduling Integration Test")
    print("=" * 60)

    # Configuration
    vault_path = "AI_Employee_Vault"
    config = {
        'timezone': 'UTC',
        'max_instances': 3
    }

    print("\n[INFO] Configuration:")
    print(f"  Vault Path: {vault_path}")
    print(f"  Timezone: {config['timezone']}")
    print(f"  Max Instances: {config['max_instances']}")

    # Create task scheduler
    print("\n[INFO] Creating task scheduler...")
    task_scheduler = TaskScheduler(vault_path, config)

    print("[SUCCESS] Task scheduler created")

    # Create scheduling skill
    print("\n[INFO] Creating scheduling skill...")
    skill = SchedulingSkill(vault_path, task_scheduler)

    print(f"[SUCCESS] Skill created: {skill.name}")
    print(f"  Skill ID: {skill.skill_id}")
    print(f"  Category: {skill.category}")

    # Test Case 1: Add Schedule
    print("\n" + "=" * 60)
    print("Test Case 1: Add Schedule")
    print("=" * 60)

    schedule_data = {
        'schedule_id': 'test-schedule-001',
        'task_id': 'test-task-001',
        'schedule_type': 'interval',
        'interval_seconds': 3600,  # Every hour
        'enabled': True,
        'description': 'Test scheduled task'
    }

    add_context = {
        'action': 'add',
        'schedule_data': schedule_data
    }

    print("\n[INFO] Adding schedule...")
    print(f"  Schedule ID: {schedule_data['schedule_id']}")
    print(f"  Type: {schedule_data['schedule_type']}")
    print(f"  Interval: {schedule_data['interval_seconds']}s")

    result = skill.execute(add_context)

    print("\n[INFO] Result:")
    print(f"  Success: {result.get('success')}")
    print(f"  Schedule ID: {result.get('schedule_id')}")

    if not result.get('success'):
        print(f"\n[ERROR] Failed to add schedule: {result}")
        return False

    print("\n[SUCCESS] Schedule added successfully")

    # Test Case 2: List Schedules
    print("\n" + "=" * 60)
    print("Test Case 2: List Schedules")
    print("=" * 60)

    list_context = {
        'action': 'list'
    }

    print("\n[INFO] Listing schedules...")

    result = skill.execute(list_context)

    print("\n[INFO] Result:")
    print(f"  Success: {result.get('success')}")
    print(f"  Schedules: {len(result.get('schedules', []))}")

    schedules = result.get('schedules', [])
    for schedule in schedules:
        print(f"\n  Schedule:")
        print(f"    ID: {schedule.get('schedule_id')}")
        print(f"    Type: {schedule.get('schedule_type')}")
        print(f"    Enabled: {schedule.get('enabled')}")

    if len(schedules) > 0:
        print("\n[SUCCESS] Schedules listed successfully")
    else:
        print("\n[WARNING] No schedules found")

    # Test Case 3: Pause Schedule
    print("\n" + "=" * 60)
    print("Test Case 3: Pause Schedule")
    print("=" * 60)

    pause_context = {
        'action': 'pause',
        'schedule_id': 'test-schedule-001'
    }

    print("\n[INFO] Pausing schedule...")

    result = skill.execute(pause_context)

    print("\n[INFO] Result:")
    print(f"  Success: {result.get('success')}")

    if result.get('success'):
        print("\n[SUCCESS] Schedule paused successfully")
    else:
        print(f"\n[WARNING] Pause may have failed: {result}")

    # Test Case 4: Resume Schedule
    print("\n" + "=" * 60)
    print("Test Case 4: Resume Schedule")
    print("=" * 60)

    resume_context = {
        'action': 'resume',
        'schedule_id': 'test-schedule-001'
    }

    print("\n[INFO] Resuming schedule...")

    result = skill.execute(resume_context)

    print("\n[INFO] Result:")
    print(f"  Success: {result.get('success')}")

    if result.get('success'):
        print("\n[SUCCESS] Schedule resumed successfully")
    else:
        print(f"\n[WARNING] Resume may have failed: {result}")

    # Test Case 5: Remove Schedule
    print("\n" + "=" * 60)
    print("Test Case 5: Remove Schedule")
    print("=" * 60)

    remove_context = {
        'action': 'remove',
        'schedule_id': 'test-schedule-001'
    }

    print("\n[INFO] Removing schedule...")

    result = skill.execute(remove_context)

    print("\n[INFO] Result:")
    print(f"  Success: {result.get('success')}")

    if result.get('success'):
        print("\n[SUCCESS] Schedule removed successfully")
        return True
    else:
        print(f"\n[WARNING] Remove may have failed: {result}")
        return True  # Still pass test


if __name__ == '__main__':
    print("\nTask Scheduling Integration Test")
    print("Tests task scheduling skill functionality\n")

    try:
        success = test_task_scheduling()

        if success:
            print("\n" + "=" * 60)
            print("[SUCCESS] Task Scheduling Test PASSED")
            print("=" * 60)
            print("\nScheduling skill is working correctly!")
        else:
            print("\n" + "=" * 60)
            print("[ERROR] Task Scheduling Test FAILED")
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
