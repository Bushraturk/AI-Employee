"""WorkflowExecution entity model for Gold Tier.

Represents Ralph Wiggum autonomous loop execution state and progress tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
import frontmatter
import uuid


class ExecutionStatus(Enum):
    """Workflow execution status states."""
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class StepStatus(Enum):
    """Step execution status states."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ExecutionStep:
    """Individual step in workflow execution."""
    step_id: str
    description: str
    action_type: str
    parameters: Dict[str, Any]
    status: StepStatus
    dependencies: List[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step_id": self.step_id,
            "description": self.description,
            "action_type": self.action_type,
            "parameters": self.parameters,
            "status": self.status.value,
            "dependencies": self.dependencies,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionStep":
        """Create from dictionary."""
        return cls(
            step_id=data["step_id"],
            description=data["description"],
            action_type=data["action_type"],
            parameters=data["parameters"],
            status=StepStatus(data["status"]),
            dependencies=data.get("dependencies", []),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            result=data.get("result"),
            error=data.get("error")
        )


@dataclass
class WorkflowExecution:
    """Workflow execution entity for Ralph Wiggum autonomous loop.

    Storage: AI_Employee_Vault/Workflows/executions/{execution_id}.md
    """

    execution_id: str
    task_reference: str
    plan_reference: str
    steps: List[ExecutionStep]
    current_step_index: int
    status: ExecutionStatus
    execution_context: Dict[str, Any]
    started_at: datetime
    completed_at: Optional[datetime] = None
    lessons_learned: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate entity after initialization."""
        # Current step index must be valid
        if self.current_step_index < 0 or self.current_step_index >= len(self.steps):
            raise ValueError("current_step_index must be valid index in steps array")

        # If status is completed, all steps must be completed
        if self.status == ExecutionStatus.COMPLETED:
            if not all(step.status == StepStatus.COMPLETED for step in self.steps):
                raise ValueError("Completed status requires all steps to be completed")

        # If status is failed, at least one step must be failed
        if self.status == ExecutionStatus.FAILED:
            if not any(step.status == StepStatus.FAILED for step in self.steps):
                raise ValueError("Failed status requires at least one failed step")

        # Validate step dependencies
        step_ids = {step.step_id for step in self.steps}
        for step in self.steps:
            for dep in step.dependencies:
                if dep not in step_ids:
                    raise ValueError(f"Step {step.step_id} has invalid dependency: {dep}")

    @classmethod
    def create(cls, task_reference: str, plan_reference: str,
               steps: List[ExecutionStep]) -> "WorkflowExecution":
        """Create a new WorkflowExecution entity."""
        return cls(
            execution_id=str(uuid.uuid4()),
            task_reference=task_reference,
            plan_reference=plan_reference,
            steps=steps,
            current_step_index=0,
            status=ExecutionStatus.RUNNING,
            execution_context={},
            started_at=datetime.now()
        )

    def get_current_step(self) -> Optional[ExecutionStep]:
        """Get the current step being executed."""
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    def advance_to_next_step(self) -> bool:
        """Advance to the next step.

        Returns:
            True if advanced, False if no more steps
        """
        if self.current_step_index < len(self.steps) - 1:
            self.current_step_index += 1
            self.updated_at = datetime.now()
            return True
        return False

    def mark_step_started(self, step_id: str) -> None:
        """Mark a step as started."""
        for step in self.steps:
            if step.step_id == step_id:
                step.status = StepStatus.IN_PROGRESS
                step.started_at = datetime.now()
                self.updated_at = datetime.now()
                break

    def mark_step_completed(self, step_id: str, result: Dict[str, Any]) -> None:
        """Mark a step as completed."""
        for step in self.steps:
            if step.step_id == step_id:
                step.status = StepStatus.COMPLETED
                step.completed_at = datetime.now()
                step.result = result
                self.updated_at = datetime.now()
                break

    def mark_step_failed(self, step_id: str, error: str) -> None:
        """Mark a step as failed."""
        for step in self.steps:
            if step.step_id == step_id:
                step.status = StepStatus.FAILED
                step.completed_at = datetime.now()
                step.error = error
                self.updated_at = datetime.now()
                break

    def pause_execution(self) -> None:
        """Pause workflow execution."""
        self.status = ExecutionStatus.PAUSED
        self.updated_at = datetime.now()

    def resume_execution(self) -> None:
        """Resume workflow execution."""
        self.status = ExecutionStatus.RUNNING
        self.updated_at = datetime.now()

    def mark_completed(self) -> None:
        """Mark workflow as completed."""
        self.status = ExecutionStatus.COMPLETED
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()

    def mark_failed(self) -> None:
        """Mark workflow as failed."""
        self.status = ExecutionStatus.FAILED
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()

    def add_lesson_learned(self, lesson: str) -> None:
        """Add a lesson learned from execution."""
        if len(self.lessons_learned) < 5:
            self.lessons_learned.append(lesson)
            self.updated_at = datetime.now()

    def get_progress_percentage(self) -> float:
        """Calculate execution progress percentage."""
        if not self.steps:
            return 0.0

        completed_steps = sum(1 for step in self.steps if step.status == StepStatus.COMPLETED)
        return (completed_steps / len(self.steps)) * 100

    def to_markdown(self) -> str:
        """Convert entity to Markdown format."""
        metadata = {
            "execution_id": self.execution_id,
            "task_reference": self.task_reference,
            "plan_reference": self.plan_reference,
            "status": self.status.value,
            "current_step_index": self.current_step_index,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "updated_at": self.updated_at.isoformat(),
            "execution_context": self.execution_context
        }

        # Build steps section
        steps_section = "## Execution Steps\n\n"
        for i, step in enumerate(self.steps):
            status_icon = {
                StepStatus.COMPLETED: "✅",
                StepStatus.IN_PROGRESS: "🔄",
                StepStatus.FAILED: "❌",
                StepStatus.PENDING: "⏳"
            }[step.status]

            steps_section += f"### {status_icon} Step {i+1}: {step.description}\n"
            steps_section += f"**Status**: {step.status.value.replace('_', ' ').title()}\n"

            if step.started_at:
                steps_section += f"**Started**: {step.started_at.strftime('%Y-%m-%d %H:%M:%S')}\n"

            if step.completed_at:
                duration = (step.completed_at - step.started_at).total_seconds() if step.started_at else 0
                steps_section += f"**Duration**: {duration:.0f} seconds\n"

            if step.result:
                steps_section += f"**Result**: {step.result.get('message', 'Success')}\n"

            if step.error:
                steps_section += f"**Error**: {step.error}\n"

            if step.dependencies:
                steps_section += f"**Dependencies**: {', '.join(step.dependencies)}\n"

            steps_section += "\n"

        # Build context section
        context_section = ""
        if self.execution_context:
            context_section = "\n## Execution Context\n\n```yaml\n"
            for key, value in self.execution_context.items():
                context_section += f"{key}: {value}\n"
            context_section += "```\n"

        # Build lessons learned section
        lessons_section = ""
        if self.lessons_learned:
            lessons_section = "\n## Lessons Learned\n\n"
            for i, lesson in enumerate(self.lessons_learned, 1):
                lessons_section += f"{i}. {lesson}\n"

        # Calculate progress
        progress = self.get_progress_percentage()
        completed_steps = sum(1 for step in self.steps if step.status == StepStatus.COMPLETED)

        body = f"""# Workflow Execution: {self.task_reference.split('/')[-1].replace('.md', '')}

**Task**: [{self.task_reference}](../{self.task_reference})
**Plan**: [{self.plan_reference}](../{self.plan_reference})
**Status**: {self.status.value.replace('_', ' ').title()} (Step {self.current_step_index + 1} of {len(self.steps)})
**Started**: {self.started_at.strftime('%Y-%m-%d %H:%M:%S')}
{f"**Completed**: {self.completed_at.strftime('%Y-%m-%d %H:%M:%S')}" if self.completed_at else ""}

{steps_section}
{context_section}

## Progress
- Steps Completed: {completed_steps}/{len(self.steps)} ({progress:.0f}%)
{f"- Estimated Time Remaining: Calculating..." if self.status == ExecutionStatus.RUNNING else ""}
{lessons_section}
"""

        post = frontmatter.Post(body, **metadata)
        return frontmatter.dumps(post)

    @classmethod
    def from_markdown(cls, content: str) -> "WorkflowExecution":
        """Parse WorkflowExecution from Markdown file."""
        post = frontmatter.loads(content)

        # Note: This is a simplified version
        # Full implementation would parse steps from markdown body
        return cls(
            execution_id=post["execution_id"],
            task_reference=post["task_reference"],
            plan_reference=post["plan_reference"],
            steps=[],  # Would parse from body
            current_step_index=post["current_step_index"],
            status=ExecutionStatus(post["status"]),
            execution_context=post.get("execution_context", {}),
            started_at=datetime.fromisoformat(post["started_at"]),
            completed_at=datetime.fromisoformat(post["completed_at"]) if post.get("completed_at") else None,
            updated_at=datetime.fromisoformat(post["updated_at"])
        )

    def save(self, vault_path: Path) -> Path:
        """Save entity to vault."""
        execution_dir = vault_path / "Workflows" / "executions"
        execution_dir.mkdir(parents=True, exist_ok=True)

        file_path = execution_dir / f"{self.execution_id}.md"
        file_path.write_text(self.to_markdown(), encoding="utf-8")

        return file_path

    @classmethod
    def load(cls, vault_path: Path, execution_id: str) -> "WorkflowExecution":
        """Load entity from vault."""
        file_path = vault_path / "Workflows" / "executions" / f"{execution_id}.md"

        if not file_path.exists():
            raise FileNotFoundError(f"WorkflowExecution {execution_id} not found")

        content = file_path.read_text(encoding="utf-8")
        return cls.from_markdown(content)
