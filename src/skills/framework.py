"""
Agent Skills Framework
Provides skill registration, discovery, and invocation system
"""
import logging
from typing import Dict, Any, Callable, List, Optional
from pathlib import Path
import importlib
import inspect

logger = logging.getLogger(__name__)


class Skill:
    """Base class for agent skills"""

    def __init__(self, skill_id: str, name: str, description: str, category: str):
        """
        Initialize skill

        Args:
            skill_id: Unique skill identifier
            name: Human-readable skill name
            description: Skill description
            category: Skill category (planning, communication, analysis, etc.)
        """
        self.skill_id = skill_id
        self.name = name
        self.description = description
        self.category = category
        self.enabled = True

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the skill

        Args:
            context: Execution context with input parameters

        Returns:
            Result dictionary with output data
        """
        raise NotImplementedError("Subclasses must implement execute()")

    def validate_context(self, context: Dict[str, Any]) -> bool:
        """
        Validate execution context

        Args:
            context: Execution context to validate

        Returns:
            True if valid, False otherwise
        """
        return True

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get skill metadata

        Returns:
            Metadata dictionary
        """
        return {
            'skill_id': self.skill_id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'enabled': self.enabled
        }


class SkillRegistry:
    """Registry for managing agent skills"""

    def __init__(self):
        """Initialize skill registry"""
        self.skills: Dict[str, Skill] = {}
        self.categories: Dict[str, List[str]] = {}

    def register(self, skill: Skill) -> None:
        """
        Register a skill

        Args:
            skill: Skill instance to register
        """
        if skill.skill_id in self.skills:
            logger.warning(f"Skill {skill.skill_id} already registered, overwriting")

        self.skills[skill.skill_id] = skill

        # Add to category index
        if skill.category not in self.categories:
            self.categories[skill.category] = []
        if skill.skill_id not in self.categories[skill.category]:
            self.categories[skill.category].append(skill.skill_id)

        logger.info(f"Registered skill: {skill.skill_id} ({skill.name})")

    def unregister(self, skill_id: str) -> None:
        """
        Unregister a skill

        Args:
            skill_id: Skill ID to unregister
        """
        if skill_id not in self.skills:
            logger.warning(f"Skill {skill_id} not found in registry")
            return

        skill = self.skills[skill_id]

        # Remove from category index
        if skill.category in self.categories:
            if skill_id in self.categories[skill.category]:
                self.categories[skill.category].remove(skill_id)

        del self.skills[skill_id]
        logger.info(f"Unregistered skill: {skill_id}")

    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """
        Get skill by ID

        Args:
            skill_id: Skill ID

        Returns:
            Skill instance or None if not found
        """
        return self.skills.get(skill_id)

    def get_skills_by_category(self, category: str) -> List[Skill]:
        """
        Get all skills in a category

        Args:
            category: Category name

        Returns:
            List of skill instances
        """
        skill_ids = self.categories.get(category, [])
        return [self.skills[sid] for sid in skill_ids if sid in self.skills]

    def get_all_skills(self) -> List[Skill]:
        """
        Get all registered skills

        Returns:
            List of all skill instances
        """
        return list(self.skills.values())

    def get_enabled_skills(self) -> List[Skill]:
        """
        Get all enabled skills

        Returns:
            List of enabled skill instances
        """
        return [skill for skill in self.skills.values() if skill.enabled]

    def list_skills(self) -> List[Dict[str, Any]]:
        """
        List all skills with metadata

        Returns:
            List of skill metadata dictionaries
        """
        return [skill.get_metadata() for skill in self.skills.values()]

    def list_categories(self) -> List[str]:
        """
        List all skill categories

        Returns:
            List of category names
        """
        return list(self.categories.keys())


class SkillExecutor:
    """Executor for running agent skills"""

    def __init__(self, registry: SkillRegistry):
        """
        Initialize skill executor

        Args:
            registry: Skill registry instance
        """
        self.registry = registry

    def execute(self, skill_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a skill

        Args:
            skill_id: Skill ID to execute
            context: Execution context

        Returns:
            Execution result dictionary
        """
        # Get skill
        skill = self.registry.get_skill(skill_id)
        if not skill:
            return {
                'success': False,
                'error': f"Skill not found: {skill_id}"
            }

        # Check if enabled
        if not skill.enabled:
            return {
                'success': False,
                'error': f"Skill disabled: {skill_id}"
            }

        # Validate context
        if not skill.validate_context(context):
            return {
                'success': False,
                'error': f"Invalid context for skill: {skill_id}"
            }

        # Execute skill
        try:
            logger.info(f"Executing skill: {skill_id}")
            result = skill.execute(context)

            return {
                'success': True,
                'skill_id': skill_id,
                'result': result
            }

        except Exception as e:
            logger.error(f"Error executing skill {skill_id}: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'skill_id': skill_id
            }


# Global skill registry
_global_registry = SkillRegistry()


def get_global_registry() -> SkillRegistry:
    """
    Get global skill registry

    Returns:
        Global SkillRegistry instance
    """
    return _global_registry


def register_skill(skill: Skill) -> None:
    """
    Register skill in global registry

    Args:
        skill: Skill instance to register
    """
    _global_registry.register(skill)


def get_skill(skill_id: str) -> Optional[Skill]:
    """
    Get skill from global registry

    Args:
        skill_id: Skill ID

    Returns:
        Skill instance or None
    """
    return _global_registry.get_skill(skill_id)
