"""
Task Scheduler Module

Manages scheduled and recurring tasks using APScheduler.
Supports cron-like syntax and event-triggered tasks.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
import frontmatter
import uuid

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Schedule and manage recurring tasks"""

    def __init__(self, vault_path: str, config: Dict[str, Any] = None):
        """
        Initialize task scheduler

        Args:
            vault_path: Path to vault directory
            config: Configuration with:
                - timezone: Timezone for scheduling (default: UTC)
                - max_instances: Max concurrent instances (default: 3)
        """
        self.vault_path = Path(vault_path)
        self.config = config or {}

        # Create schedules folder
        self.schedules_folder = self.vault_path / 'Schedules'
        self.schedules_folder.mkdir(parents=True, exist_ok=True)

        # Create execution history folder
        self.history_folder = self.vault_path / 'Schedule_History'
        self.history_folder.mkdir(parents=True, exist_ok=True)

        # Initialize APScheduler
        timezone = self.config.get('timezone', 'UTC')
        max_instances = self.config.get('max_instances', 3)

        self.scheduler = BackgroundScheduler(
            timezone=timezone,
            job_defaults={
                'coalesce': False,
                'max_instances': max_instances
            }
        )

        # Track active schedules
        self.active_schedules = {}

    def start(self) -> None:
        """Start the scheduler"""
        try:
            # Load existing schedules from disk
            self._load_schedules()

            # Start APScheduler
            self.scheduler.start()
            logger.info("Task scheduler started successfully")

        except Exception as e:
            logger.error(f"Error starting task scheduler: {e}")
            raise

    def stop(self) -> None:
        """Stop the scheduler"""
        try:
            self.scheduler.shutdown(wait=True)
            logger.info("Task scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping task scheduler: {e}")

    def create_schedule(
        self,
        name: str,
        schedule_type: str,
        task_template: Dict[str, Any],
        schedule_config: Dict[str, Any],
        enabled: bool = True
    ) -> str:
        """
        Create a new schedule

        Args:
            name: Schedule name
            schedule_type: Type (cron, interval, one_time, event_triggered)
            task_template: Template for tasks to create
            schedule_config: Schedule-specific configuration
            enabled: Whether schedule is enabled

        Returns:
            Schedule ID
        """
        try:
            schedule_id = str(uuid.uuid4())
            created_at = datetime.now()

            # Create schedule metadata
            metadata = {
                'schedule_id': schedule_id,
                'name': name,
                'schedule_type': schedule_type,
                'enabled': enabled,
                'created_at': created_at.isoformat(),
                'last_run': None,
                'next_run': None,
                'run_count': 0,
                'failure_count': 0
            }

            # Create schedule content
            content = self._format_schedule_content(
                name=name,
                schedule_type=schedule_type,
                task_template=task_template,
                schedule_config=schedule_config
            )

            # Save schedule file
            schedule_file = self.schedules_folder / f"{schedule_id}.md"
            post = frontmatter.Post(content, **metadata)

            with open(schedule_file, 'w', encoding='utf-8') as f:
                f.write(frontmatter.dumps(post))

            # Add to scheduler if enabled
            if enabled:
                self._add_to_scheduler(
                    schedule_id=schedule_id,
                    schedule_type=schedule_type,
                    schedule_config=schedule_config,
                    task_template=task_template
                )

            logger.info(f"Created schedule: {schedule_id} ({name})")
            return schedule_id

        except Exception as e:
            logger.error(f"Error creating schedule: {e}")
            return None

    def _add_to_scheduler(
        self,
        schedule_id: str,
        schedule_type: str,
        schedule_config: Dict[str, Any],
        task_template: Dict[str, Any]
    ) -> None:
        """
        Add schedule to APScheduler

        Args:
            schedule_id: Schedule ID
            schedule_type: Schedule type
            schedule_config: Schedule configuration
            task_template: Task template
        """
        try:
            # Create trigger based on schedule type
            trigger = self._create_trigger(schedule_type, schedule_config)

            if not trigger:
                logger.error(f"Failed to create trigger for schedule: {schedule_id}")
                return

            # Add job to scheduler
            job = self.scheduler.add_job(
                func=self._execute_scheduled_task,
                trigger=trigger,
                args=[schedule_id, task_template],
                id=schedule_id,
                name=schedule_config.get('name', schedule_id),
                replace_existing=True
            )

            # Track active schedule
            self.active_schedules[schedule_id] = {
                'job': job,
                'task_template': task_template,
                'schedule_config': schedule_config
            }

            logger.info(f"Added schedule to scheduler: {schedule_id}")

        except Exception as e:
            logger.error(f"Error adding schedule to scheduler: {e}")

    def _create_trigger(
        self,
        schedule_type: str,
        schedule_config: Dict[str, Any]
    ):
        """
        Create APScheduler trigger

        Args:
            schedule_type: Schedule type
            schedule_config: Schedule configuration

        Returns:
            APScheduler trigger or None
        """
        try:
            if schedule_type == 'cron':
                # Cron-based schedule
                cron_expression = schedule_config.get('cron_expression')
                if not cron_expression:
                    logger.error("Cron expression required for cron schedule")
                    return None

                # Parse cron expression (minute hour day month day_of_week)
                parts = cron_expression.split()
                if len(parts) != 5:
                    logger.error(f"Invalid cron expression: {cron_expression}")
                    return None

                return CronTrigger(
                    minute=parts[0],
                    hour=parts[1],
                    day=parts[2],
                    month=parts[3],
                    day_of_week=parts[4]
                )

            elif schedule_type == 'interval':
                # Interval-based schedule
                interval_type = schedule_config.get('interval_type', 'minutes')
                interval_value = schedule_config.get('interval_value', 60)

                kwargs = {interval_type: interval_value}
                return IntervalTrigger(**kwargs)

            elif schedule_type == 'one_time':
                # One-time execution
                run_date = schedule_config.get('run_date')
                if not run_date:
                    logger.error("Run date required for one-time schedule")
                    return None

                # Parse run_date
                if isinstance(run_date, str):
                    run_date = datetime.fromisoformat(run_date)

                return DateTrigger(run_date=run_date)

            else:
                logger.error(f"Unsupported schedule type: {schedule_type}")
                return None

        except Exception as e:
            logger.error(f"Error creating trigger: {e}")
            return None

    def _execute_scheduled_task(
        self,
        schedule_id: str,
        task_template: Dict[str, Any]
    ) -> None:
        """
        Execute a scheduled task

        Args:
            schedule_id: Schedule ID
            task_template: Task template
        """
        try:
            logger.info(f"Executing scheduled task: {schedule_id}")

            # Create task from template
            task_id = f"scheduled-{schedule_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

            # Ensure Inbox folder exists
            inbox_folder = self.vault_path / 'Inbox'
            inbox_folder.mkdir(parents=True, exist_ok=True)

            # Create task file in Inbox
            task_file = inbox_folder / f"{task_id}.md"

            # Prepare task content
            task_content = task_template.get('description', '')

            # Prepare task metadata
            task_metadata = {
                'task_id': task_id,
                'title': task_template.get('title', 'Scheduled Task'),
                'priority': task_template.get('priority', 'P2'),
                'status': 'pending',
                'category': task_template.get('category', 'scheduled'),
                'created_at': datetime.now().isoformat(),
                'schedule_id': schedule_id,
                'scheduled': True
            }

            # Write task file
            post = frontmatter.Post(task_content, **task_metadata)
            with open(task_file, 'w', encoding='utf-8') as f:
                f.write(frontmatter.dumps(post))

            # Update schedule metadata
            self._update_schedule_execution(schedule_id, success=True)

            # Log execution
            self._log_execution(schedule_id, task_id, success=True)

            logger.info(f"Created scheduled task: {task_id}")

        except Exception as e:
            logger.error(f"Error executing scheduled task: {e}")
            self._update_schedule_execution(schedule_id, success=False)
            self._log_execution(schedule_id, None, success=False, error=str(e))

    def _update_schedule_execution(
        self,
        schedule_id: str,
        success: bool
    ) -> None:
        """
        Update schedule execution metadata

        Args:
            schedule_id: Schedule ID
            success: Whether execution succeeded
        """
        try:
            schedule_file = self.schedules_folder / f"{schedule_id}.md"

            if not schedule_file.exists():
                return

            with open(schedule_file, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)

            # Update metadata
            post.metadata['last_run'] = datetime.now().isoformat()
            post.metadata['run_count'] = post.metadata.get('run_count', 0) + 1

            if not success:
                post.metadata['failure_count'] = post.metadata.get('failure_count', 0) + 1

            # Get next run time from scheduler
            if schedule_id in self.active_schedules:
                job = self.active_schedules[schedule_id]['job']
                if job.next_run_time:
                    post.metadata['next_run'] = job.next_run_time.isoformat()

            # Write updated file
            with open(schedule_file, 'w', encoding='utf-8') as f:
                f.write(frontmatter.dumps(post))

        except Exception as e:
            logger.error(f"Error updating schedule execution: {e}")

    def _log_execution(
        self,
        schedule_id: str,
        task_id: Optional[str],
        success: bool,
        error: str = None
    ) -> None:
        """
        Log schedule execution to history

        Args:
            schedule_id: Schedule ID
            task_id: Created task ID (if successful)
            success: Whether execution succeeded
            error: Error message (if failed)
        """
        try:
            # Create daily history file
            date_str = datetime.now().strftime('%Y-%m-%d')
            history_file = self.history_folder / f"schedule-history-{date_str}.md"

            # Create or append to history file
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                content = f"# Schedule Execution History - {date_str}\n\n"

            # Format execution entry
            timestamp = datetime.now().strftime('%H:%M:%S')
            status = "✅ SUCCESS" if success else "❌ FAILED"

            entry = f"## {timestamp} - {status}\n\n"
            entry += f"**Schedule ID**: {schedule_id}\n"

            if task_id:
                entry += f"**Task Created**: {task_id}\n"

            if error:
                entry += f"**Error**: {error}\n"

            entry += "\n---\n\n"

            content += entry

            # Write updated history
            with open(history_file, 'w', encoding='utf-8') as f:
                f.write(content)

        except Exception as e:
            logger.error(f"Error logging execution: {e}")

    def _format_schedule_content(
        self,
        name: str,
        schedule_type: str,
        task_template: Dict[str, Any],
        schedule_config: Dict[str, Any]
    ) -> str:
        """Format schedule as markdown"""
        content = f"# Schedule: {name}\n\n"
        content += f"**Type**: {schedule_type}\n\n"

        # Schedule configuration
        content += "## Schedule Configuration\n\n"

        if schedule_type == 'cron':
            content += f"**Cron Expression**: `{schedule_config.get('cron_expression')}`\n\n"
        elif schedule_type == 'interval':
            interval_type = schedule_config.get('interval_type', 'minutes')
            interval_value = schedule_config.get('interval_value', 60)
            content += f"**Interval**: Every {interval_value} {interval_type}\n\n"
        elif schedule_type == 'one_time':
            run_date = schedule_config.get('run_date')
            content += f"**Run Date**: {run_date}\n\n"

        # Task template
        content += "## Task Template\n\n"
        content += f"**Title**: {task_template.get('title')}\n"
        content += f"**Priority**: {task_template.get('priority', 'P2')}\n"
        content += f"**Category**: {task_template.get('category', 'scheduled')}\n\n"
        content += "**Description**:\n"
        content += f"{task_template.get('description', '')}\n\n"

        return content

    def _load_schedules(self) -> None:
        """Load existing schedules from disk"""
        try:
            for schedule_file in self.schedules_folder.glob('*.md'):
                try:
                    with open(schedule_file, 'r', encoding='utf-8') as f:
                        post = frontmatter.load(f)

                    # Skip disabled schedules
                    if not post.metadata.get('enabled', True):
                        continue

                    schedule_id = post.metadata.get('schedule_id')
                    schedule_type = post.metadata.get('schedule_type')

                    # Parse task template and schedule config from content
                    # This is simplified - in production you'd parse the markdown
                    task_template = {
                        'title': 'Scheduled Task',
                        'description': post.content,
                        'priority': 'P2'
                    }

                    schedule_config = {
                        'name': post.metadata.get('name')
                    }

                    # Add to scheduler
                    self._add_to_scheduler(
                        schedule_id=schedule_id,
                        schedule_type=schedule_type,
                        schedule_config=schedule_config,
                        task_template=task_template
                    )

                except Exception as e:
                    logger.error(f"Error loading schedule {schedule_file}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error loading schedules: {e}")

    def list_schedules(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """
        List all schedules

        Args:
            enabled_only: Only return enabled schedules

        Returns:
            List of schedule summaries
        """
        schedules = []

        try:
            for schedule_file in self.schedules_folder.glob('*.md'):
                try:
                    with open(schedule_file, 'r', encoding='utf-8') as f:
                        post = frontmatter.load(f)

                    # Filter by enabled status
                    if enabled_only and not post.metadata.get('enabled', True):
                        continue

                    schedules.append({
                        'schedule_id': post.metadata.get('schedule_id'),
                        'name': post.metadata.get('name'),
                        'schedule_type': post.metadata.get('schedule_type'),
                        'enabled': post.metadata.get('enabled', True),
                        'last_run': post.metadata.get('last_run'),
                        'next_run': post.metadata.get('next_run'),
                        'run_count': post.metadata.get('run_count', 0),
                        'failure_count': post.metadata.get('failure_count', 0)
                    })

                except Exception as e:
                    logger.error(f"Error reading schedule {schedule_file}: {e}")
                    continue

            # Sort by name
            schedules.sort(key=lambda s: s.get('name', ''))

        except Exception as e:
            logger.error(f"Error listing schedules: {e}")

        return schedules

    def get_schedule(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """
        Get schedule details

        Args:
            schedule_id: Schedule ID

        Returns:
            Schedule details or None
        """
        try:
            schedule_file = self.schedules_folder / f"{schedule_id}.md"

            if not schedule_file.exists():
                return None

            with open(schedule_file, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)

            return {
                **post.metadata,
                'content': post.content
            }

        except Exception as e:
            logger.error(f"Error getting schedule: {e}")
            return None

    def enable_schedule(self, schedule_id: str) -> bool:
        """Enable a schedule"""
        return self._set_schedule_enabled(schedule_id, True)

    def disable_schedule(self, schedule_id: str) -> bool:
        """Disable a schedule"""
        return self._set_schedule_enabled(schedule_id, False)

    def _set_schedule_enabled(self, schedule_id: str, enabled: bool) -> bool:
        """
        Enable or disable a schedule

        Args:
            schedule_id: Schedule ID
            enabled: Whether to enable or disable

        Returns:
            True if successful
        """
        try:
            schedule_file = self.schedules_folder / f"{schedule_id}.md"

            if not schedule_file.exists():
                return False

            with open(schedule_file, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)

            # Update enabled status
            post.metadata['enabled'] = enabled

            # Write updated file
            with open(schedule_file, 'w', encoding='utf-8') as f:
                f.write(frontmatter.dumps(post))

            # Update scheduler
            if enabled:
                # Add to scheduler
                schedule_type = post.metadata.get('schedule_type')
                # Parse config from content (simplified)
                schedule_config = {'name': post.metadata.get('name')}
                task_template = {'title': 'Scheduled Task', 'description': post.content}

                self._add_to_scheduler(
                    schedule_id=schedule_id,
                    schedule_type=schedule_type,
                    schedule_config=schedule_config,
                    task_template=task_template
                )
            else:
                # Remove from scheduler
                if schedule_id in self.active_schedules:
                    self.scheduler.remove_job(schedule_id)
                    del self.active_schedules[schedule_id]

            logger.info(f"Schedule {schedule_id} {'enabled' if enabled else 'disabled'}")
            return True

        except Exception as e:
            logger.error(f"Error setting schedule enabled status: {e}")
            return False

    def delete_schedule(self, schedule_id: str) -> bool:
        """
        Delete a schedule

        Args:
            schedule_id: Schedule ID

        Returns:
            True if successful
        """
        try:
            # Remove from scheduler
            if schedule_id in self.active_schedules:
                self.scheduler.remove_job(schedule_id)
                del self.active_schedules[schedule_id]

            # Delete file
            schedule_file = self.schedules_folder / f"{schedule_id}.md"
            if schedule_file.exists():
                schedule_file.unlink()

            logger.info(f"Deleted schedule: {schedule_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting schedule: {e}")
            return False
