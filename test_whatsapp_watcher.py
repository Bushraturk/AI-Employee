"""
WhatsApp Watcher Integration Test
Tests WhatsApp watcher in isolation
"""
import sys
import os
import logging
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from watchers.whatsapp_watcher import WhatsAppWatcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


def test_whatsapp_watcher():
    """Test WhatsApp watcher functionality"""

    print("=" * 60)
    print("WhatsApp Watcher Integration Test")
    print("=" * 60)

    # Configuration
    vault_path = "AI_Employee_Vault"
    config = {
        'poll_interval_seconds': 30,
        'session_path': 'whatsapp_session/',
        'monitor_groups': True,
        'group_whitelist': []
    }

    print("\n[INFO] Configuration:")
    print(f"  Vault Path: {vault_path}")
    print(f"  Session Path: {config['session_path']}")
    print(f"  Poll Interval: {config['poll_interval_seconds']}s")
    print(f"  Monitor Groups: {config['monitor_groups']}")

    # Create watcher
    print("\n[INFO] Creating WhatsApp watcher...")
    watcher = WhatsAppWatcher(vault_path, config)

    try:
        # Start watcher
        print("\n[INFO] Starting WhatsApp watcher...")
        print("[INFO] Browser will open - please scan QR code if needed")
        print("[INFO] You have 5 minutes to authenticate")
        print()

        watcher.start()

        print("\n" + "=" * 60)
        print("[SUCCESS] WhatsApp watcher started!")
        print("=" * 60)
        print("\n[INFO] Watcher is now monitoring for messages...")
        print("[INFO] Send a test message to your WhatsApp")
        print("[INFO] Monitoring for 2 minutes...")
        print()

        # Monitor for 2 minutes
        start_time = time.time()
        check_count = 0
        tasks_found = 0

        while (time.time() - start_time) < 120:  # 2 minutes
            check_count += 1
            print(f"\n[CHECK {check_count}] Looking for new messages...")

            # Get new tasks
            tasks = watcher.get_new_tasks()

            if tasks:
                tasks_found += len(tasks)
                print(f"[SUCCESS] Found {len(tasks)} new message(s)!")

                for task in tasks:
                    print(f"\n  Task ID: {task['task_id']}")
                    print(f"  File: {task['file_path']}")
                    print(f"  Channel: {task['channel']}")
                    print(f"  Message ID: {task['message_id']}")

                    # Read and display task file
                    task_file = Path(task['file_path'])
                    if task_file.exists():
                        print(f"\n  Task File Content:")
                        print("  " + "-" * 56)
                        with open(task_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # Show first 300 chars
                            preview = content[:300] + "..." if len(content) > 300 else content
                            for line in preview.split('\n'):
                                print(f"  {line}")
                        print("  " + "-" * 56)
            else:
                print("[INFO] No new messages")

            # Wait before next check
            print(f"[INFO] Waiting {config['poll_interval_seconds']} seconds...")
            time.sleep(config['poll_interval_seconds'])

        print("\n" + "=" * 60)
        print("Test Complete!")
        print("=" * 60)
        print(f"\nTotal checks: {check_count}")
        print(f"Tasks found: {tasks_found}")

        if tasks_found > 0:
            print("\n[SUCCESS] WhatsApp watcher is working!")
            print(f"[SUCCESS] Created {tasks_found} task file(s) in {vault_path}/Inbox/")
        else:
            print("\n[INFO] No messages detected during test")
            print("[INFO] This is normal if no one sent you messages")
            print("[INFO] Try sending yourself a message and run the test again")

    except KeyboardInterrupt:
        print("\n\n[INFO] Test interrupted by user")

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Stop watcher
        print("\n[INFO] Stopping WhatsApp watcher...")
        try:
            watcher.stop()
            print("[SUCCESS] Watcher stopped")
        except Exception as e:
            print(f"[WARNING] Error stopping watcher: {e}")

    return True


if __name__ == '__main__':
    print("\nWhatsApp Watcher Integration Test")
    print("This will test the WhatsApp watcher in isolation\n")

    print("Prerequisites:")
    print("1. Playwright installed: pip install playwright")
    print("2. Chromium installed: playwright install chromium")
    print("3. WhatsApp account ready to scan QR code")
    print()
    print("Starting test in 3 seconds...")
    time.sleep(3)

    try:
        success = test_whatsapp_watcher()

        if success:
            print("\n[SUCCESS] Test completed successfully!")
        else:
            print("\n[ERROR] Test failed!")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Test cancelled by user")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\nDone!")
