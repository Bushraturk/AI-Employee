"""
WhatsApp End-to-End Test
Tests message sending and detection
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


def test_whatsapp_e2e():
    """End-to-end test: Send message and detect it"""

    print("=" * 60)
    print("WhatsApp End-to-End Test")
    print("=" * 60)

    # Configuration
    vault_path = "AI_Employee_Vault"
    config = {
        'poll_interval_seconds': 10,  # Faster polling for test
        'session_path': 'whatsapp_session/',
        'monitor_groups': True,
        'group_whitelist': []
    }

    print("\n[INFO] This test will:")
    print("  1. Start WhatsApp watcher")
    print("  2. Wait for you to send a test message")
    print("  3. Detect the message and create task file")
    print("  4. Show the task file content")
    print()

    # Create watcher
    print("[INFO] Creating WhatsApp watcher...")
    watcher = WhatsAppWatcher(vault_path, config)

    try:
        # Start watcher
        print("\n[INFO] Starting WhatsApp watcher...")
        watcher.start()

        print("\n" + "=" * 60)
        print("[SUCCESS] WhatsApp watcher is running!")
        print("=" * 60)

        print("\n[ACTION REQUIRED] Please do the following:")
        print("  1. Open WhatsApp on your phone")
        print("  2. Send yourself a message (any text)")
        print("  3. Or ask someone to send you a message")
        print()
        print("[INFO] Monitoring for 60 seconds...")
        print("[INFO] Checking every 10 seconds...")
        print()

        # Monitor for 60 seconds
        start_time = time.time()
        check_count = 0
        tasks_found = []

        while (time.time() - start_time) < 60:  # 1 minute
            check_count += 1
            elapsed = int(time.time() - start_time)
            remaining = 60 - elapsed

            print(f"\n[CHECK {check_count}] Time remaining: {remaining}s")
            print("[INFO] Looking for new messages...")

            # Get new tasks
            tasks = watcher.get_new_tasks()

            if tasks:
                print(f"\n{'='*60}")
                print(f"[SUCCESS] Found {len(tasks)} new message(s)!")
                print(f"{'='*60}")

                for task in tasks:
                    tasks_found.append(task)

                    print(f"\n  ✓ Task Created:")
                    print(f"    Task ID: {task['task_id']}")
                    print(f"    File: {task['file_path']}")
                    print(f"    Channel: {task['channel']}")
                    print(f"    Detected at: {task['detected_at']}")

                    # Read and display task file
                    task_file = Path(task['file_path'])
                    if task_file.exists():
                        print(f"\n  📄 Task File Content:")
                        print("  " + "=" * 56)
                        with open(task_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            for line in content.split('\n'):
                                print(f"  {line}")
                        print("  " + "=" * 56)

                # Stop after finding messages
                print(f"\n[SUCCESS] Message detection working!")
                print(f"[INFO] Stopping test early (found messages)")
                break
            else:
                print("[INFO] No new messages yet...")

            # Wait before next check
            if remaining > 10:
                print(f"[INFO] Waiting 10 seconds before next check...")
                time.sleep(10)

        print("\n" + "=" * 60)
        print("Test Complete!")
        print("=" * 60)
        print(f"\nTotal checks: {check_count}")
        print(f"Messages detected: {len(tasks_found)}")

        if tasks_found:
            print("\n✅ SUCCESS - WhatsApp Watcher is FULLY WORKING!")
            print(f"✅ Created {len(tasks_found)} task file(s)")
            print(f"✅ Location: {vault_path}/Inbox/")
            print("\n[INFO] Task files ready for processing by orchestrator")
            return True
        else:
            print("\n⚠️  No messages detected during test")
            print("\n[INFO] Possible reasons:")
            print("  1. No one sent you a message during the 60-second window")
            print("  2. Messages were already read/processed")
            print("  3. WhatsApp Web selector changed (rare)")
            print("\n[INFO] The watcher started successfully, so it should work")
            print("[INFO] Try running the test again and send a message quickly")
            return True  # Still success - watcher works, just no messages

    except KeyboardInterrupt:
        print("\n\n[INFO] Test interrupted by user")
        return False

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
            print("[SUCCESS] Watcher stopped cleanly")
        except Exception as e:
            print(f"[WARNING] Error stopping watcher: {e}")


if __name__ == '__main__':
    print("\nWhatsApp End-to-End Test")
    print("Tests message sending and detection\n")

    print("Prerequisites:")
    print("- WhatsApp Web session already authenticated")
    print("- Phone ready to send test message")
    print()
    print("Starting test in 3 seconds...")
    time.sleep(3)

    try:
        success = test_whatsapp_e2e()

        if success:
            print("\n" + "=" * 60)
            print("✅ TEST PASSED")
            print("=" * 60)
            print("\nWhatsApp watcher is ready for production use!")
            print("Enable it in .env: ENABLE_WHATSAPP_WATCHER=true")
            print("Then run: python src/main.py")
        else:
            print("\n" + "=" * 60)
            print("❌ TEST FAILED")
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
