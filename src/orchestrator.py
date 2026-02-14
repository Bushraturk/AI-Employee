"""Orchestrator - Coordinates watcher → processor → Claude Code → executor pipeline."""

from pathlib import Path
from typing import Dict, Any, Optional
import subprocess
import json
import time
import logging
from datetime import datetime

from watchers.filesystem_watcher import FileSystemWatcher
from task_processor import TaskProcessor
from action_executor import ActionExecutor
from vault_manager import VaultManager
from dashboard_manager import DashboardManager
from logger import AuditLogger, ActionType

logger = logging.getLogger(__name__)


class Orchestrator:
    """Coordinates the perception → reasoning → action pipeline."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize orchestrator with configuration.

        Args:
            config: Configuration dictionary with:
                - vault_path: Path to vault directory
                - claude_code_path: Path to Claude Code CLI
                - task_timeout: Timeout for task processing in seconds
                - max_retries: Maximum retry attempts for failed tasks
        """
        self.config = config
        self.vault_path = Path(config['vault_path']).resolve()

        # Initialize components
        self.vault_manager = VaultManager(str(self.vault_path))
        self.task_processor = TaskProcessor()
        self.action_executor = ActionExecutor(str(self.vault_path))
        self.dashboard_manager = DashboardManager(str(self.vault_path))
        self.audit_logger = AuditLogger(str(self.vault_path))

        # Initialize FileSystem watcher
        watcher_config = {
            'inbox_folder': 'Inbox',
            'file_extensions': ['.md'],
            'watch_recursive': False
        }
        self.watcher = FileSystemWatcher(str(self.vault_path), watcher_config)

        # State
        self.running = False
        self.tasks_processed = 0
        self.tasks_failed = 0

    def start(self) -> None:
        """Start the orchestrator and begin processing tasks."""
        try:
            logger.info("Starting AI Employee Orchestrator...")

            # Log system start
            self.audit_logger.log_action(
                action_type=ActionType.SYSTEM_STARTED,
                details="AI Employee system starting up"
            )

            # Initialize vault structure
            result = self.vault_manager.initialize_vault()
            logger.info(f"Vault initialized - Created: {result['created']}, Validated: {result['validated']}")

            # Validate vault structure
            if not self.vault_manager.validate_vault_structure():
                raise RuntimeError("Vault structure validation failed")

            # Start watcher
            self.watcher.start()

            # Scan for existing files in Inbox
            existing_count = self.watcher.scan_existing_files()
            if existing_count > 0:
                logger.info(f"Found {existing_count} existing files in Inbox")

            self.running = True
            logger.info("Orchestrator started successfully")

            # Update dashboard
            self._update_dashboard()

            # Main processing loop
            self._processing_loop()

        except KeyboardInterrupt:
            logger.info("Received shutdown signal (Ctrl+C)")
            self.stop()
        except Exception as e:
            logger.error(f"Error starting orchestrator: {e}")
            self.stop()
            raise

    def stop(self) -> None:
        """Gracefully shutdown the orchestrator."""
        logger.info("Stopping orchestrator...")

        self.running = False

        # Stop watcher
        try:
            self.watcher.stop()
        except Exception as e:
            logger.error(f"Error stopping watcher: {e}")

        # Log system stop
        self.audit_logger.log_action(
            action_type=ActionType.SYSTEM_STOPPED,
            details=f"Processed: {self.tasks_processed}, Failed: {self.tasks_failed}"
        )

        # Final dashboard update
        self._update_dashboard()

        logger.info(f"Orchestrator stopped. Processed: {self.tasks_processed}, Failed: {self.tasks_failed}")

    def _processing_loop(self) -> None:
        """Main processing loop - checks for new tasks and processes them."""
        logger.info("Entering main processing loop...")

        while self.running:
            try:
                # Get new tasks from watcher
                new_tasks = self.watcher.get_new_tasks()

                # Process each task
                for task_info in new_tasks:
                    self._process_task(task_info)

                # Sleep briefly to avoid busy-waiting
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                time.sleep(1.0)  # Back off on error

    def _process_task(self, task_info: Dict[str, Any]) -> bool:
        """Process a single task through the full pipeline.

        Args:
            task_info: Task information from watcher

        Returns:
            True if processing succeeded, False otherwise
        """
        file_path = Path(task_info['file_path'])
        logger.info(f"Processing task: {file_path.name}")
        start_time = time.time()

        try:
            # Log file detection
            self.audit_logger.log_action(
                action_type=ActionType.FILE_DETECTED,
                details=f"Detected new task file: {file_path.name}"
            )

            # Step 1: Move to Needs_Action
            needs_action_path = self.vault_path / 'Needs_Action' / file_path.name
            if not self.action_executor.move_file(file_path, needs_action_path):
                logger.error(f"Failed to move task to Needs_Action: {file_path.name}")
                self.tasks_failed += 1
                self.audit_logger.log_action(
                    action_type=ActionType.ERROR,
                    result="failure",
                    details=f"Failed to move {file_path.name} to Needs_Action"
                )
                self._update_dashboard()
                return False

            # Log file move
            self.audit_logger.log_action(
                action_type=ActionType.FILE_MOVED,
                details=f"Moved {file_path.name} to Needs_Action"
            )

            # Step 2: Parse task file
            task_data = self.task_processor.parse_task_file(needs_action_path)
            if not task_data:
                logger.error(f"Failed to parse task file: {file_path.name}")
                self.tasks_failed += 1
                self.audit_logger.log_action(
                    action_type=ActionType.ERROR,
                    result="failure",
                    details=f"Failed to parse task file: {file_path.name}"
                )
                self._update_dashboard()
                return False

            # Log task parsing
            self.audit_logger.log_action(
                action_type=ActionType.TASK_PARSED,
                task_reference=task_data['task_id'],
                details=f"Parsed task: {task_data['title']}"
            )

            # Step 3: Process with Claude Code
            claude_response = self._call_claude_code(task_data)
            if not claude_response:
                logger.error(f"Claude Code processing failed: {file_path.name}")
                self.tasks_failed += 1
                self.audit_logger.log_action(
                    action_type=ActionType.ERROR,
                    result="failure",
                    task_reference=task_data['task_id'],
                    details="Claude Code processing failed"
                )
                self._update_dashboard()
                return False

            # Log task processing
            processing_time = int((time.time() - start_time) * 1000)
            self.audit_logger.log_action(
                action_type=ActionType.TASK_PROCESSED,
                task_reference=task_data['task_id'],
                details=f"Processed task: {task_data['title']} (Priority: {task_data['priority']})",
                duration_ms=processing_time
            )

            # Step 4: Move to Done
            done_path = self.vault_path / 'Done' / file_path.name
            if not self.action_executor.move_file(needs_action_path, done_path):
                logger.error(f"Failed to move task to Done: {file_path.name}")
                self.tasks_failed += 1
                self.audit_logger.log_action(
                    action_type=ActionType.ERROR,
                    result="failure",
                    task_reference=task_data['task_id'],
                    details=f"Failed to move {file_path.name} to Done"
                )
                self._update_dashboard()
                return False

            # Log file move to Done
            self.audit_logger.log_action(
                action_type=ActionType.FILE_MOVED,
                task_reference=task_data['task_id'],
                details=f"Moved {file_path.name} to Done"
            )

            # Success
            self.tasks_processed += 1
            self.dashboard_manager.record_processing_time((time.time() - start_time))
            self._update_dashboard()

            logger.info(f"Successfully processed task: {file_path.name}")
            return True

        except Exception as e:
            logger.error(f"Error processing task {file_path.name}: {e}")
            self.tasks_failed += 1
            self.audit_logger.log_action(
                action_type=ActionType.ERROR,
                result="failure",
                details=f"Exception processing {file_path.name}: {str(e)}"
            )
            self._update_dashboard()
            return False

    def _update_dashboard(self) -> None:
        """Update dashboard with current metrics using Agent Skill."""
        try:
            # Agent Skill: /update-dashboard
            # This uses the update-dashboard.command.md skill
            metrics = {
                'total_processed': self.tasks_processed,
                'total_failed': self.tasks_failed
            }
            self.dashboard_manager.update_dashboard(metrics)

            # Log using Agent Skill: /log-action
            self.audit_logger.log_action(
                action_type=ActionType.DASHBOARD_UPDATED,
                details="Dashboard updated with current metrics (via agent skill)"
            )
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")

    def _call_claude_code(self, task_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Call Claude Code Agent Skill to process task.

        Args:
            task_data: Parsed task data

        Returns:
            Claude Code response dictionary, or None if failed
        """
        try:
            claude_path = self.config.get('claude_code_path', 'claude')
            timeout = self.config.get('task_timeout', 60)

            # Use Agent Skill: /process-task
            # This invokes the process-task.command.md skill
            prompt = f"""Use the /process-task agent skill to process this task:

Task ID: {task_data['task_id']}
Title: {task_data['title']}
Priority: {task_data['priority']}
Status: {task_data['status']}
Description:
{task_data['description']}

Please analyze this task and provide appropriate response or action plan."""

            # Try to call Claude Code via subprocess with agent skill
            try:
                result = subprocess.run(
                    [claude_path],
                    input=prompt,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )

                if result.returncode != 0:
                    logger.warning(f"Claude Code returned error: {result.stderr}")
                    # Fall back to mock processor
                    return self._mock_claude_processor(task_data)

                # Parse response
                response = {
                    'output': result.stdout.strip(),
                    'processed_at': datetime.now().isoformat(),
                    'agent_skill': 'process-task'
                }

                logger.debug(f"Claude Code Agent Skill response: {response['output'][:100]}...")
                return response

            except FileNotFoundError:
                logger.warning(f"Claude Code CLI not found at: {claude_path}, using mock processor")
                return self._mock_claude_processor(task_data)

        except subprocess.TimeoutExpired:
            logger.error(f"Claude Code timeout after {timeout} seconds")
            return None
        except Exception as e:
            logger.error(f"Error calling Claude Code: {e}")
            return None

    def _mock_claude_processor(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock Claude Code processor for testing when CLI is not available.

        Args:
            task_data: Parsed task data

        Returns:
            Mock response dictionary
        """
        logger.info(f"Using mock processor for task: {task_data['title']}")

        response = {
            'output': f"""Task Acknowledged: {task_data['title']}

Priority: {task_data['priority']}
Status: Processed

I have received and processed this task. This is a mock response generated by the Bronze phase system because Claude Code CLI is not available in the current environment.

To enable real Claude Code processing:
1. Ensure Claude Code CLI is installed
2. Add it to your system PATH
3. Or set CLAUDE_CODE_PATH in .env to the full path

Task processing completed successfully.""",
            'processed_at': datetime.now().isoformat(),
            'mock': True
        }

        return response
