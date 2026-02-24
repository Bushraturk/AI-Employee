"""Ralph Wiggum Orchestrator for Gold Tier.

Autonomous multi-step workflow execution with error recovery and safety boundaries.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.models.workflow_execution import WorkflowExecution, ExecutionStep, ExecutionStatus, StepStatus
from src.orchestrator.mcp_server_orchestrator import MCPServerOrchestrator
from src.services.error_recovery import ErrorRecoveryService, ServiceType, ErrorType

logger = logging.getLogger(__name__)


class RalphWiggumOrchestrator:
    """Orchestrates autonomous multi-step workflow execution.

    Features:
    - Detect complex multi-step tasks
    - Generate execution plans with dependencies
    - Execute steps automatically in order
    - Track execution state and context
    - Automatic error recovery with retry
    - Human escalation when needed
    - Safety boundary enforcement (FR-050)
    - Process improvement analysis
    """

    # Risk actions that require approval (FR-050)
    RISK_ACTIONS = {
        "send_email",
        "send_whatsapp",
        "post_facebook",
        "post_instagram",
        "post_twitter",
        "post_linkedin",
        "create_odoo_invoice",
        "create_odoo_expense",
        "delete_file",
        "execute_command"
    }

    def __init__(self, vault_path: Path, mcp_orchestrator: MCPServerOrchestrator):
        """Initialize Ralph Wiggum orchestrator.

        Args:
            vault_path: Path to AI Employee vault
            mcp_orchestrator: MCP server orchestrator instance
        """
        self.vault_path = vault_path
        self.mcp_orchestrator = mcp_orchestrator
        self.error_recovery = ErrorRecoveryService(vault_path)

    def execute_workflow(self, task_reference: str) -> Dict[str, Any]:
        """Execute a multi-step workflow autonomously.

        Args:
            task_reference: Path to task file

        Returns:
            Execution result dictionary
        """
        try:
            logger.info(f"Starting workflow execution for task: {task_reference}")

            # Analyze task to determine if it's complex
            if not self._is_complex_task(task_reference):
                return {
                    "success": False,
                    "error": "Task is not complex enough for autonomous execution"
                }

            # Generate execution plan
            plan = self._generate_plan(task_reference)

            if not plan.get("success"):
                return {
                    "success": False,
                    "error": f"Failed to generate plan: {plan.get('error')}"
                }

            # Create workflow execution
            steps = [
                ExecutionStep(
                    step_id=step["step_id"],
                    description=step["description"],
                    action_type=step["action_type"],
                    parameters=step["parameters"],
                    status=StepStatus.PENDING,
                    dependencies=step.get("dependencies", [])
                )
                for step in plan["steps"]
            ]

            execution = WorkflowExecution.create(
                task_reference=task_reference,
                plan_reference=plan["plan_path"],
                steps=steps
            )

            # Save initial execution state
            execution.save(self.vault_path)

            # Execute steps in order
            result = self._execute_steps(execution)

            # Save final execution state
            execution.save(self.vault_path)

            logger.info(f"Workflow execution completed: {execution.execution_id}")

            return {
                "success": result.get("success", False),
                "execution_id": execution.execution_id,
                "status": execution.status.value,
                "steps_completed": sum(1 for s in execution.steps if s.status == StepStatus.COMPLETED),
                "total_steps": len(execution.steps),
                "message": result.get("message", "Workflow execution completed")
            }

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _is_complex_task(self, task_reference: str) -> bool:
        """Detect if task is complex enough for autonomous execution.

        Args:
            task_reference: Path to task file

        Returns:
            True if task is complex
        """
        try:
            # Read task file
            task_path = self.vault_path / task_reference
            if not task_path.exists():
                return False

            content = task_path.read_text(encoding="utf-8")

            # Check for multiple action types
            action_keywords = [
                "sync", "create", "post", "send", "generate", "analyze"
            ]

            action_count = sum(1 for keyword in action_keywords if keyword in content.lower())

            # Check for cross-domain operations
            domains = ["odoo", "facebook", "instagram", "twitter", "email", "whatsapp"]
            domain_count = sum(1 for domain in domains if domain in content.lower())

            # Complex if multiple actions or cross-domain
            is_complex = action_count >= 2 or domain_count >= 2

            logger.info(
                f"Task complexity analysis: {action_count} actions, "
                f"{domain_count} domains, complex={is_complex}"
            )

            return is_complex

        except Exception as e:
            logger.error(f"Failed to analyze task complexity: {e}")
            return False

    def _generate_plan(self, task_reference: str) -> Dict[str, Any]:
        """Generate execution plan for task.

        Args:
            task_reference: Path to task file

        Returns:
            Plan generation result dictionary
        """
        try:
            # Read task file
            task_path = self.vault_path / task_reference
            content = task_path.read_text(encoding="utf-8")

            # Parse task to identify required steps
            # This is a simplified implementation
            # Full implementation would use NLP or structured task format

            steps = []

            # Example: Detect invoice processing workflow
            if "invoice" in content.lower() and "odoo" in content.lower():
                steps.append({
                    "step_id": "step_1",
                    "description": "Sync invoice to Odoo",
                    "action_type": "sync_odoo_transaction",
                    "parameters": {},
                    "dependencies": []
                })

            if "post" in content.lower() or "announce" in content.lower():
                steps.append({
                    "step_id": "step_2",
                    "description": "Post announcement on social media",
                    "action_type": "post_facebook",
                    "parameters": {},
                    "dependencies": ["step_1"] if steps else []
                })

            if not steps:
                return {
                    "success": False,
                    "error": "Could not identify workflow steps"
                }

            # Create plan file
            plan_dir = self.vault_path / "Workflows" / "plans"
            plan_dir.mkdir(parents=True, exist_ok=True)

            plan_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            plan_path = plan_dir / f"plan_{plan_id}.md"

            plan_content = f"""# Workflow Execution Plan

**Task**: {task_reference}
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Steps

{chr(10).join(f"{i+1}. {step['description']} ({step['action_type']})" for i, step in enumerate(steps))}

## Dependencies

{chr(10).join(f"- Step {i+1} depends on: {', '.join(step['dependencies']) if step['dependencies'] else 'None'}" for i, step in enumerate(steps))}

## Success Criteria

- All steps complete successfully
- No errors or conflicts
- Results validated

## Rollback Procedure

If execution fails:
1. Pause execution
2. Log error details
3. Request human intervention
4. Preserve execution state for resume
"""

            plan_path.write_text(plan_content, encoding="utf-8")

            logger.info(f"Generated execution plan with {len(steps)} steps")

            return {
                "success": True,
                "plan_path": str(plan_path.relative_to(self.vault_path)),
                "steps": steps
            }

        except Exception as e:
            logger.error(f"Failed to generate plan: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _execute_steps(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """Execute workflow steps in order.

        Args:
            execution: WorkflowExecution entity

        Returns:
            Execution result dictionary
        """
        try:
            for step in execution.steps:
                # Check if dependencies are met
                if not self._check_dependencies(step, execution):
                    logger.warning(f"Dependencies not met for step {step.step_id}")
                    execution.pause_execution()
                    execution.save(self.vault_path)
                    return {
                        "success": False,
                        "message": "Dependencies not met, execution paused"
                    }

                # Check safety boundaries (FR-050)
                if not self._check_safety_boundaries(step):
                    logger.warning(f"Step {step.step_id} requires approval (risk action)")
                    execution.pause_execution()
                    execution.save(self.vault_path)
                    return {
                        "success": False,
                        "message": "Risk action detected, approval required"
                    }

                # Execute step
                result = self._execute_single_step(step, execution)

                if not result.get("success"):
                    # Attempt error recovery
                    recovery_result = self._attempt_recovery(step, execution, result.get("error"))

                    if not recovery_result.get("success"):
                        # Recovery failed, escalate to human
                        execution.mark_failed()
                        execution.save(self.vault_path)
                        return {
                            "success": False,
                            "message": "Step failed and recovery exhausted, human intervention required"
                        }

                # Advance to next step
                if not execution.advance_to_next_step():
                    # All steps completed
                    execution.mark_completed()
                    break

                execution.save(self.vault_path)

            # Analyze for process improvements
            self._analyze_improvements(execution)

            return {
                "success": True,
                "message": "Workflow completed successfully"
            }

        except Exception as e:
            logger.error(f"Step execution failed: {e}")
            execution.mark_failed()
            execution.save(self.vault_path)
            return {
                "success": False,
                "error": str(e)
            }

    def _check_dependencies(self, step: ExecutionStep, execution: WorkflowExecution) -> bool:
        """Check if step dependencies are met.

        Args:
            step: Step to check
            execution: Workflow execution

        Returns:
            True if dependencies are met
        """
        for dep_id in step.dependencies:
            dep_step = next((s for s in execution.steps if s.step_id == dep_id), None)

            if not dep_step or dep_step.status != StepStatus.COMPLETED:
                return False

        return True

    def _check_safety_boundaries(self, step: ExecutionStep) -> bool:
        """Check if step respects safety boundaries (FR-050).

        Args:
            step: Step to check

        Returns:
            True if step is safe to execute autonomously
        """
        # Check if action is a risk action
        if step.action_type in self.RISK_ACTIONS:
            logger.warning(
                f"Step {step.step_id} is a risk action ({step.action_type}), "
                f"requires approval per FR-050"
            )
            return False

        return True

    def _execute_single_step(self, step: ExecutionStep, execution: WorkflowExecution) -> Dict[str, Any]:
        """Execute a single workflow step.

        Args:
            step: Step to execute
            execution: Workflow execution

        Returns:
            Step execution result
        """
        try:
            # Mark step as started
            execution.mark_step_started(step.step_id)
            execution.save(self.vault_path)

            logger.info(f"Executing step {step.step_id}: {step.description}")

            # Route action to appropriate MCP server
            server_id = self.mcp_orchestrator.route_action(step.action_type)

            if not server_id:
                raise Exception(f"No MCP server available for action: {step.action_type}")

            # Execute action (simplified - would use actual MCP communication)
            result = {
                "success": True,
                "message": f"Step {step.step_id} executed successfully"
            }

            # Update execution context with step results
            execution.execution_context[step.step_id] = result

            # Mark step as completed
            execution.mark_step_completed(step.step_id, result)
            execution.save(self.vault_path)

            return result

        except Exception as e:
            logger.error(f"Step execution failed: {e}")
            execution.mark_step_failed(step.step_id, str(e))
            execution.save(self.vault_path)
            return {
                "success": False,
                "error": str(e)
            }

    def _attempt_recovery(self, step: ExecutionStep, execution: WorkflowExecution,
                         error: str) -> Dict[str, Any]:
        """Attempt automatic error recovery for failed step.

        Args:
            step: Failed step
            execution: Workflow execution
            error: Error message

        Returns:
            Recovery result dictionary
        """
        try:
            logger.info(f"Attempting recovery for step {step.step_id}")

            # Use error recovery service
            # This would integrate with the ErrorRecoveryService
            # For now, simplified implementation

            # Retry step once
            retry_result = self._execute_single_step(step, execution)

            if retry_result.get("success"):
                execution.add_lesson_learned(
                    f"Step {step.step_id} recovered after retry"
                )
                return {
                    "success": True,
                    "message": "Recovery successful"
                }

            return {
                "success": False,
                "message": "Recovery failed"
            }

        except Exception as e:
            logger.error(f"Recovery attempt failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _analyze_improvements(self, execution: WorkflowExecution) -> None:
        """Analyze execution for process improvements.

        Args:
            execution: Completed workflow execution
        """
        try:
            # Calculate total execution time
            if execution.completed_at and execution.started_at:
                duration = (execution.completed_at - execution.started_at).total_seconds()

                if duration > 300:  # More than 5 minutes
                    execution.add_lesson_learned(
                        f"Workflow took {duration:.0f} seconds - consider optimizing step order"
                    )

            # Check for failed steps that recovered
            recovered_steps = [
                s for s in execution.steps
                if s.status == StepStatus.COMPLETED and s.error
            ]

            if recovered_steps:
                execution.add_lesson_learned(
                    f"{len(recovered_steps)} steps required recovery - review error handling"
                )

            execution.save(self.vault_path)

        except Exception as e:
            logger.error(f"Failed to analyze improvements: {e}")

    def pause_workflow(self, execution_id: str) -> Dict[str, Any]:
        """Pause a running workflow.

        Args:
            execution_id: Workflow execution ID

        Returns:
            Pause result dictionary
        """
        try:
            execution = WorkflowExecution.load(self.vault_path, execution_id)

            if execution.status != ExecutionStatus.RUNNING:
                return {
                    "success": False,
                    "error": f"Workflow is not running (status: {execution.status.value})"
                }

            execution.pause_execution()
            execution.save(self.vault_path)

            logger.info(f"Paused workflow execution: {execution_id}")

            return {
                "success": True,
                "message": "Workflow paused"
            }

        except Exception as e:
            logger.error(f"Failed to pause workflow: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def resume_workflow(self, execution_id: str) -> Dict[str, Any]:
        """Resume a paused workflow.

        Args:
            execution_id: Workflow execution ID

        Returns:
            Resume result dictionary
        """
        try:
            execution = WorkflowExecution.load(self.vault_path, execution_id)

            if execution.status != ExecutionStatus.PAUSED:
                return {
                    "success": False,
                    "error": f"Workflow is not paused (status: {execution.status.value})"
                }

            execution.resume_execution()
            execution.save(self.vault_path)

            # Continue execution from current step
            result = self._execute_steps(execution)

            logger.info(f"Resumed workflow execution: {execution_id}")

            return {
                "success": result.get("success", False),
                "message": "Workflow resumed"
            }

        except Exception as e:
            logger.error(f"Failed to resume workflow: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_workflow_status(self, execution_id: str) -> Dict[str, Any]:
        """Get status of a workflow execution.

        Args:
            execution_id: Workflow execution ID

        Returns:
            Status dictionary
        """
        try:
            execution = WorkflowExecution.load(self.vault_path, execution_id)

            return {
                "success": True,
                "execution_id": execution.execution_id,
                "status": execution.status.value,
                "current_step": execution.current_step_index + 1,
                "total_steps": len(execution.steps),
                "progress": execution.get_progress_percentage(),
                "started_at": execution.started_at.isoformat(),
                "completed_at": execution.completed_at.isoformat() if execution.completed_at else None
            }

        except Exception as e:
            logger.error(f"Failed to get workflow status: {e}")
            return {
                "success": False,
                "error": str(e)
            }
