"""
Task Scheduling Skill
Wraps task scheduling functionality as an agent skill
"""
import logging
from typing import Dict, Any
from pathlib import Path

from skills.framework import Skill
from scheduling.task_scheduler import TaskScheduler

logger = logging.getLogger(__name__)


class SchedulingSkill(Skill):
    """Skill for scheduling recurring tasks"""

    def __init__(self, vault_path: str, task_scheduler: TaskScheduler):
        """
        Initialize scheduling skill

        Args:
            vault_path: Path to vault directory
            task_scheduler: TaskScheduler instance
        """
        super().__init__(
            skill_id='scheduling',
            name='Task Scheduling',
            description='Schedules recurring tasks with cron or interval-based triggers',
            category='automation'
        )

        self.vault_path = Path(vault_path)
        self.task_scheduler = task_scheduler

    def validate_context(self, context: Dict[str, Any]) -> bool:
        """
        Validate execution context

        Args:
            context: Must contain 'action' and relevant data

        Returns:
            True if valid, False otherwise
        """
        if 'action' not in context:
            logger.error("Scheduling skill requires 'action' in context")
            return False

        action = context['action']
        valid_actions = ['add', 'remove', 'list', 'pause', 'resume']

        if action not in valid_actions:
            logger.error(f"Invalid action: {action}")
            return False

        return True

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute scheduling skill

        Args:
            context: Execution context with action and data

        Returns:
            Result with success status and details
        """
        action = context['action']

        if action == 'add':
            # Add scheduled task
            schedule_data = context.get('schedule_data', {})

            # Create schedule using TaskScheduler's create_schedule method
            schedule_id = self.task_scheduler.create_schedule(
                name=schedule_data.get('description', 'Scheduled Task'),
                schedule_type=schedule_data.get('schedule_type', 'interval'),
                task_template={'task_id': schedule_data.get('task_id')},
                schedule_config={
                    'interval_seconds': schedule_data.get('interval_seconds', 3600)
                },
                enabled=schedule_data.get('enabled', True)
            )

            return {
                'action': 'add',
                'success': True,
                'schedule_id': schedule_id
            }

        elif action == 'remove':
            # Remove scheduled task
            schedule_id = context.get('schedule_id')
            self.task_scheduler.delete_schedule(schedule_id)

            return {
                'action': 'remove',
                'success': True,
                'schedule_id': schedule_id
            }

        elif action == 'list':
            # List all schedules
            schedules = self.task_scheduler.list_schedules()

            return {
                'action': 'list',
                'success': True,
                'schedules': schedules
            }

        elif action == 'pause':
            # Pause schedule
            schedule_id = context.get('schedule_id')
            schedule = self.task_scheduler.get_schedule(schedule_id)
            if schedule:
                schedule['enabled'] = False
                self.task_scheduler.update_schedule(schedule_id, schedule)

            return {
                'action': 'pause',
                'success': True,
                'schedule_id': schedule_id
            }

        elif action == 'resume':
            # Resume schedule
            schedule_id = context.get('schedule_id')
            schedule = self.task_scheduler.get_schedule(schedule_id)
            if schedule:
                schedule['enabled'] = True
                self.task_scheduler.update_schedule(schedule_id, schedule)

            return {
                'action': 'resume',
                'success': True,
                'schedule_id': schedule_id
            }
