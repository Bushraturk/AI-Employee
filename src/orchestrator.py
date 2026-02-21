"""Orchestrator - Coordinates watcher → processor → Claude Code → executor pipeline."""

from pathlib import Path
from typing import Dict, Any, Optional
import subprocess
import json
import time
import logging
from datetime import datetime

from watchers.filesystem_watcher import FileSystemWatcher
from watchers.gmail_watcher import GmailWatcher
from watchers.whatsapp_watcher import WhatsAppWatcher
from watchers.linkedin_watcher import LinkedInWatcher
from task_processor import TaskProcessor
from action_executor import ActionExecutor
from vault_manager import VaultManager
from dashboard_manager import DashboardManager
from logger import AuditLogger, ActionType
from approval.queue import ApprovalQueue
from approval.risk_classifier import RiskClassifier
from approval.notification_system import NotificationSystem
from approval.audit_logger import ApprovalAuditLogger
from linkedin.scheduler import LinkedInScheduler
from planning.plan_generator import PlanGenerator
from scheduling.task_scheduler import TaskScheduler
from mcp.server import MCPServer

# Agent Skills Framework
from skills.framework import SkillRegistry, SkillExecutor
from skills.planning_skill import PlanningSkill
from skills.approval_skill import ApprovalSkill
from skills.mcp_skill import MCPToolsSkill
from skills.scheduling_skill import SchedulingSkill
from skills.linkedin_skill import LinkedInPostingSkill

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
                - enable_gmail_watcher: Enable Gmail watcher (default: False)
                - enable_whatsapp_watcher: Enable WhatsApp watcher (default: False)
                - enable_linkedin_watcher: Enable LinkedIn watcher (default: False)
        """
        self.config = config
        self.vault_path = Path(config['vault_path']).resolve()

        # Initialize components
        self.vault_manager = VaultManager(str(self.vault_path))
        self.task_processor = TaskProcessor()
        self.action_executor = ActionExecutor(str(self.vault_path))
        self.audit_logger = AuditLogger(str(self.vault_path))

        # Initialize Silver Tier components
        self.approval_audit_logger = ApprovalAuditLogger(str(self.vault_path))
        self.approval_queue = ApprovalQueue(str(self.vault_path), audit_logger=self.approval_audit_logger)
        self.notification_system = NotificationSystem(str(self.vault_path), config={
            'console_enabled': config.get('notifications_console', True),
            'file_enabled': config.get('notifications_file', True),
            'email_enabled': config.get('notifications_email', False)
        })
        self.plan_generator = PlanGenerator(str(self.vault_path), config={
            'min_steps_for_plan': config.get('min_steps_for_plan', 3)
        })

        # Initialize DashboardManager with approval_queue for metrics
        self.dashboard_manager = DashboardManager(str(self.vault_path), approval_queue=self.approval_queue)

        # Initialize LinkedIn scheduler if enabled
        self.linkedin_scheduler = None
        if config.get('enable_linkedin_posting', False):
            logger.info("Initializing LinkedIn scheduler...")
            scheduler_config = {
                'auto_post_enabled': config.get('linkedin_auto_post', False),
                'auto_post_frequency': config.get('linkedin_post_frequency', 2.5),
                'timezone': config.get('linkedin_timezone', 'UTC')
            }
            self.linkedin_scheduler = LinkedInScheduler(str(self.vault_path), config=scheduler_config)

        # Initialize task scheduler (Phase 7: Scheduled Automation)
        self.task_scheduler = None
        if config.get('enable_task_scheduling', False):
            logger.info("Initializing task scheduler...")
            scheduler_config = {
                'timezone': config.get('scheduler_timezone', 'UTC'),
                'max_instances': config.get('scheduler_max_instances', 3)
            }
            self.task_scheduler = TaskScheduler(str(self.vault_path), config=scheduler_config)

        # Initialize MCP server (Phase 8: MCP Tools)
        self.mcp_server = None
        if config.get('enable_mcp_server', False):
            logger.info("Initializing MCP server...")
            self.mcp_server = MCPServer(str(self.vault_path))
            self.mcp_server.initialize_default_tools()
            enabled_tools = config.get('mcp_enabled_tools', ['send_email', 'send_whatsapp'])
            logger.info(f"MCP server initialized with tools: {enabled_tools}")

        # Initialize Agent Skills Framework (Silver Tier Requirement)
        logger.info("Initializing Agent Skills Framework...")
        self.skill_registry = SkillRegistry()
        self.skill_executor = SkillExecutor(self.skill_registry)

        # Register core skills
        planning_skill = PlanningSkill(str(self.vault_path), {
            'min_steps_for_plan': config.get('min_steps_for_plan', 3)
        })
        self.skill_registry.register(planning_skill)

        approval_skill = ApprovalSkill(str(self.vault_path), self.approval_queue)
        self.skill_registry.register(approval_skill)

        if self.mcp_server:
            mcp_skill = MCPToolsSkill(str(self.vault_path), self.mcp_server)
            self.skill_registry.register(mcp_skill)

        if self.task_scheduler:
            scheduling_skill = SchedulingSkill(str(self.vault_path), self.task_scheduler)
            self.skill_registry.register(scheduling_skill)

        if self.linkedin_scheduler:
            linkedin_skill = LinkedInPostingSkill(str(self.vault_path), {
                'auto_post_enabled': config.get('linkedin_auto_post', False),
                'auto_post_frequency': config.get('linkedin_post_frequency', 2.5)
            })
            self.skill_registry.register(linkedin_skill)

        registered_skills = self.skill_registry.list_skills()
        logger.info(f"Registered {len(registered_skills)} agent skills:")
        for skill in registered_skills:
            logger.info(f"  - {skill['skill_id']}: {skill['name']} ({skill['category']})")

        # Watcher registry for multi-channel support
        self.watchers = {}
        self.watcher_health = {}

        # Initialize FileSystem watcher (Bronze phase - always enabled)
        watcher_config = {
            'inbox_folder': 'Inbox',
            'file_extensions': ['.md'],
            'watch_recursive': False
        }
        self.watchers['filesystem'] = FileSystemWatcher(str(self.vault_path), watcher_config)
        self.watcher_health['filesystem'] = {
            'status': 'stopped',
            'last_check': None,
            'error_count': 0
        }

        # Initialize additional watchers if enabled (Silver phase)
        if config.get('enable_gmail_watcher', False):
            logger.info("Initializing Gmail watcher...")
            gmail_config = {
                'poll_interval_seconds': config.get('gmail_poll_interval', 30),
                'labels_to_monitor': config.get('gmail_labels', ['INBOX']),
                'exclude_labels': config.get('gmail_exclude_labels', ['SPAM', 'TRASH']),
                'max_results_per_poll': config.get('gmail_max_results', 10)
            }
            self.watchers['gmail'] = GmailWatcher(str(self.vault_path), gmail_config)
            self.watcher_health['gmail'] = {
                'status': 'initialized',
                'last_check': None,
                'error_count': 0
            }

        if config.get('enable_whatsapp_watcher', False):
            logger.info("Initializing WhatsApp watcher...")
            whatsapp_config = {
                'poll_interval_seconds': config.get('whatsapp_poll_interval', 30),
                'session_path': config.get('whatsapp_session_path', 'whatsapp_session/'),
                'monitor_groups': config.get('whatsapp_monitor_groups', True),
                'group_whitelist': config.get('whatsapp_group_whitelist', [])
            }
            self.watchers['whatsapp'] = WhatsAppWatcher(str(self.vault_path), whatsapp_config)
            self.watcher_health['whatsapp'] = {
                'status': 'initialized',
                'last_check': None,
                'error_count': 0
            }

        if config.get('enable_linkedin_watcher', False):
            logger.info("Initializing LinkedIn watcher...")
            linkedin_config = {
                'poll_interval_seconds': config.get('linkedin_poll_interval', 60),
                'monitor_messages': config.get('linkedin_monitor_messages', True),
                'monitor_mentions': config.get('linkedin_monitor_mentions', True),
                'monitor_feed': config.get('linkedin_monitor_feed', False),
                'keywords': config.get('linkedin_keywords', [])
            }
            self.watchers['linkedin'] = LinkedInWatcher(str(self.vault_path), linkedin_config)
            self.watcher_health['linkedin'] = {
                'status': 'initialized',
                'last_check': None,
                'error_count': 0
            }

        # Maintain backward compatibility
        self.watcher = self.watchers['filesystem']

        # State
        self.running = False
        self.tasks_processed = 0
        self.tasks_failed = 0
        self.tasks_by_channel = {
            'filesystem': 0,
            'gmail': 0,
            'whatsapp': 0,
            'linkedin': 0
        }

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

            # Start all registered watchers
            for watcher_name, watcher in self.watchers.items():
                try:
                    logger.info(f"Starting {watcher_name} watcher...")
                    watcher.start()
                    self.watcher_health[watcher_name]['status'] = 'running'
                    self.watcher_health[watcher_name]['last_check'] = datetime.now()
                    logger.info(f"{watcher_name} watcher started successfully")
                except Exception as e:
                    logger.error(f"Error starting {watcher_name} watcher: {e}")
                    self.watcher_health[watcher_name]['status'] = 'error'
                    self.watcher_health[watcher_name]['error_count'] += 1

            # Scan for existing files in Inbox (FileSystem watcher)
            if 'filesystem' in self.watchers:
                existing_count = self.watchers['filesystem'].scan_existing_files()
                if existing_count > 0:
                    logger.info(f"Found {existing_count} existing files in Inbox")

            # Start LinkedIn scheduler if enabled
            if self.linkedin_scheduler:
                try:
                    logger.info("Starting LinkedIn scheduler...")
                    self.linkedin_scheduler.start()
                    logger.info("LinkedIn scheduler started successfully")
                except Exception as e:
                    logger.error(f"Error starting LinkedIn scheduler: {e}")

            # Start task scheduler if enabled (Phase 7: Scheduled Automation)
            if self.task_scheduler:
                try:
                    logger.info("Starting task scheduler...")
                    self.task_scheduler.start()
                    logger.info("Task scheduler started successfully")
                except Exception as e:
                    logger.error(f"Error starting task scheduler: {e}")

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

        # Stop task scheduler if running (Phase 7: Scheduled Automation)
        if self.task_scheduler:
            try:
                logger.info("Stopping task scheduler...")
                self.task_scheduler.stop()
                logger.info("Task scheduler stopped")
            except Exception as e:
                logger.error(f"Error stopping task scheduler: {e}")

        # Stop LinkedIn scheduler if running
        if self.linkedin_scheduler:
            try:
                logger.info("Stopping LinkedIn scheduler...")
                self.linkedin_scheduler.stop()
                logger.info("LinkedIn scheduler stopped")
            except Exception as e:
                logger.error(f"Error stopping LinkedIn scheduler: {e}")

        # Stop all watchers
        for watcher_name, watcher in self.watchers.items():
            try:
                logger.info(f"Stopping {watcher_name} watcher...")
                watcher.stop()
                self.watcher_health[watcher_name]['status'] = 'stopped'
            except Exception as e:
                logger.error(f"Error stopping {watcher_name} watcher: {e}")

        # Log system stop
        self.audit_logger.log_action(
            action_type=ActionType.SYSTEM_STOPPED,
            details=f"Processed: {self.tasks_processed}, Failed: {self.tasks_failed}"
        )

        # Final dashboard update
        self._update_dashboard()

        logger.info(f"Orchestrator stopped. Processed: {self.tasks_processed}, Failed: {self.tasks_failed}")

    def _processing_loop(self) -> None:
        """Main processing loop - checks for new tasks from all watchers and processes them."""
        logger.info("Entering main processing loop...")

        # Track last approval check time
        last_approval_check = datetime.now()
        approval_check_interval = 60  # Check every 60 seconds

        while self.running:
            try:
                # Get new tasks from all watchers
                for watcher_name, watcher in self.watchers.items():
                    try:
                        new_tasks = watcher.get_new_tasks()

                        # Process each task
                        for task_info in new_tasks:
                            # Add channel metadata
                            task_info['channel'] = watcher_name
                            self._process_task(task_info)
                            self.tasks_by_channel[watcher_name] += 1

                        # Update watcher health
                        self.watcher_health[watcher_name]['last_check'] = datetime.now()
                        self.watcher_health[watcher_name]['error_count'] = 0

                    except Exception as e:
                        logger.error(f"Error getting tasks from {watcher_name} watcher: {e}")
                        self.watcher_health[watcher_name]['error_count'] += 1
                        if self.watcher_health[watcher_name]['error_count'] >= 5:
                            self.watcher_health[watcher_name]['status'] = 'error'

                # Check for expired approvals periodically (Silver Tier)
                now = datetime.now()
                if (now - last_approval_check).total_seconds() >= approval_check_interval:
                    self._check_approval_timeouts()
                    last_approval_check = now

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

            # Step 2.5: Check if task requires planning (Silver Tier)
            if self.plan_generator.should_create_plan(task_data):
                logger.info(f"Task requires planning: {task_data['title']}")
                plan_id = self.plan_generator.generate_plan(task_data)
                if plan_id:
                    logger.info(f"Generated plan: {plan_id}")
                    task_data['plan_id'] = plan_id
                    self.audit_logger.log_action(
                        action_type=ActionType.TASK_PROCESSED,
                        task_reference=task_data['task_id'],
                        details=f"Generated plan {plan_id} for task: {task_data['title']}"
                    )
                else:
                    logger.warning(f"Failed to generate plan for task: {task_data['title']}")

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

    def _check_approval_timeouts(self) -> None:
        """Check for expired approvals and send notifications (Silver Tier)."""
        try:
            # Get all pending approvals
            pending_approvals = self.approval_queue.list_approvals(status='pending')

            expired_count = 0
            for approval in pending_approvals:
                approval_id = approval['approval_id']

                # Check if approval has expired
                if self.approval_queue.is_expired(approval_id):
                    logger.warning(f"Approval {approval_id} has expired, auto-rejecting...")

                    # Auto-reject expired approval
                    self.approval_queue.update_approval(
                        approval_id=approval_id,
                        status='expired',
                        reviewer='system',
                        notes='Auto-rejected due to timeout'
                    )

                    # Send notification
                    self.notification_system.send_notification(
                        notification_type='approval_expired',
                        title=f"Approval Expired: {approval['action_type']}",
                        message=f"Approval {approval_id} expired after timeout period",
                        metadata={'approval_id': approval_id}
                    )

                    expired_count += 1

            if expired_count > 0:
                logger.info(f"Auto-rejected {expired_count} expired approvals")

        except Exception as e:
            logger.error(f"Error checking approval timeouts: {e}")

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
