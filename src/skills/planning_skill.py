"""
Planning Skill
Wraps plan generation functionality as an agent skill
"""
import logging
from typing import Dict, Any
from pathlib import Path

from skills.framework import Skill
from planning.plan_generator import PlanGenerator

logger = logging.getLogger(__name__)


class PlanningSkill(Skill):
    """Skill for generating Plan.md files for complex tasks"""

    def __init__(self, vault_path: str, config: Dict[str, Any]):
        """
        Initialize planning skill

        Args:
            vault_path: Path to vault directory
            config: Configuration dictionary
        """
        super().__init__(
            skill_id='planning',
            name='Intelligent Planning',
            description='Generates Plan.md files for complex multi-step tasks',
            category='planning'
        )

        self.vault_path = Path(vault_path)
        self.plan_generator = PlanGenerator(str(vault_path), config)

    def validate_context(self, context: Dict[str, Any]) -> bool:
        """
        Validate execution context

        Args:
            context: Must contain 'task_data' with task information

        Returns:
            True if valid, False otherwise
        """
        if 'task_data' not in context:
            logger.error("Planning skill requires 'task_data' in context")
            return False

        task_data = context['task_data']
        if 'task_id' not in task_data or 'content' not in task_data:
            logger.error("task_data must contain 'task_id' and 'content'")
            return False

        return True

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute planning skill

        Args:
            context: Execution context with task_data

        Returns:
            Result with plan_generated flag and plan_path
        """
        task_data = context['task_data']

        # Check if task needs planning
        needs_plan = self.plan_generator.should_create_plan(task_data)

        if not needs_plan:
            return {
                'plan_generated': False,
                'reason': 'Task does not require planning (too simple)'
            }

        # Generate plan
        plan_id = self.plan_generator.generate_plan(task_data)

        # Get plan path
        if plan_id:
            plan_path = self.vault_path / 'Plans' / f"{plan_id}.md"
        else:
            plan_path = None

        if plan_path:
            return {
                'plan_generated': True,
                'plan_path': str(plan_path),
                'task_id': task_data['task_id']
            }
        else:
            return {
                'plan_generated': False,
                'reason': 'Plan generation failed'
            }
