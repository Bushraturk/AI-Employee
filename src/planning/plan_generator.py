"""
Plan Generator Module

Generates structured Plan.md files for complex multi-step tasks.
Analyzes problems, evaluates approaches, and creates execution plans.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import frontmatter

logger = logging.getLogger(__name__)


class PlanGenerator:
    """Generate structured plans for complex tasks"""

    def __init__(self, vault_path: str, config: Dict[str, Any] = None):
        """
        Initialize plan generator

        Args:
            vault_path: Path to vault directory
            config: Configuration with:
                - plans_folder: Folder for storing plans (default: 'Plans')
                - min_steps_for_plan: Minimum steps to trigger plan generation (default: 3)
        """
        self.vault_path = Path(vault_path)
        self.config = config or {}

        # Configuration
        self.plans_folder = self.vault_path / self.config.get('plans_folder', 'Plans')
        self.plans_folder.mkdir(parents=True, exist_ok=True)
        self.min_steps_for_plan = self.config.get('min_steps_for_plan', 3)

    def should_create_plan(self, task_data: Dict[str, Any]) -> bool:
        """
        Determine if a task requires a plan

        Args:
            task_data: Task data dictionary

        Returns:
            True if plan should be created
        """
        # Check task complexity indicators
        # Try both 'description' and 'content' fields
        description = task_data.get('description', '') or task_data.get('content', '')

        # Count potential steps (look for numbered lists, bullet points)
        # More flexible pattern matching
        import re

        # Count numbered items (1., 2., 3., etc.)
        numbered_items = len(re.findall(r'\d+\.', description))

        # Count bullet points
        bullet_points = description.count('- ') + description.count('* ')

        # Count sequential words
        sequential_words = sum(1 for word in ['first', 'then', 'next', 'finally', 'step']
                              if word in description.lower())

        step_count = numbered_items + bullet_points + sequential_words

        # Check for complexity keywords
        complexity_keywords = [
            'complex', 'multiple', 'several', 'various',
            'integrate', 'implement', 'design', 'architect',
            'refactor', 'migrate', 'transform'
        ]

        has_complexity = any(keyword in description.lower() for keyword in complexity_keywords)

        # Require plan if:
        # 1. Multiple steps detected
        # 2. Complexity keywords present
        # 3. Task explicitly requests planning
        return (
            step_count >= self.min_steps_for_plan or
            has_complexity or
            'plan' in description.lower() or
            'strategy' in description.lower()
        )

    def generate_plan(
        self,
        task_data: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> Optional[str]:
        """
        Generate a structured plan for a task

        Args:
            task_data: Task data dictionary
            context: Optional additional context

        Returns:
            Plan ID or None if generation fails
        """
        try:
            # Extract task information
            task_id = task_data.get('task_id', 'unknown')
            title = task_data.get('title', 'Untitled Task')
            description = task_data.get('description', '')
            priority = task_data.get('priority', 'P2')

            # Generate plan ID
            plan_id = f"plan-{task_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

            # Analyze the problem
            problem_analysis = self._analyze_problem(description, context)

            # Generate approach options
            approaches = self._generate_approaches(description, problem_analysis, context)

            # Select recommended approach
            recommended = self._select_recommended_approach(approaches)

            # Generate execution plan
            execution_plan = self._generate_execution_plan(recommended, description)

            # Identify success criteria
            success_criteria = self._identify_success_criteria(description, execution_plan)

            # Identify risks and mitigation
            risks = self._identify_risks(description, execution_plan)

            # Create plan content
            plan_content = self._format_plan(
                title=title,
                description=description,
                problem_analysis=problem_analysis,
                approaches=approaches,
                recommended=recommended,
                execution_plan=execution_plan,
                success_criteria=success_criteria,
                risks=risks
            )

            # Create plan metadata
            metadata = {
                'plan_id': plan_id,
                'task_id': task_id,
                'title': f"Plan: {title}",
                'priority': priority,
                'status': 'draft',
                'created_at': datetime.now().isoformat(),
                'task_reference': task_id
            }

            # Save plan file
            plan_file = self.plans_folder / f"{plan_id}.md"
            post = frontmatter.Post(plan_content, **metadata)

            with open(plan_file, 'w', encoding='utf-8') as f:
                f.write(frontmatter.dumps(post))

            logger.info(f"Generated plan: {plan_id} for task: {task_id}")

            return plan_id

        except Exception as e:
            logger.error(f"Error generating plan: {e}")
            return None

    def _analyze_problem(
        self,
        description: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Analyze the problem to understand requirements and constraints

        Args:
            description: Task description
            context: Optional context

        Returns:
            Problem analysis dictionary
        """
        analysis = {
            'core_problem': '',
            'requirements': [],
            'constraints': [],
            'dependencies': [],
            'assumptions': []
        }

        # Extract core problem (first sentence or paragraph)
        lines = description.split('\n')
        analysis['core_problem'] = lines[0] if lines else description[:200]

        # Identify requirements (look for "must", "should", "need to")
        requirement_keywords = ['must', 'should', 'need to', 'required', 'necessary']
        for line in lines:
            if any(keyword in line.lower() for keyword in requirement_keywords):
                analysis['requirements'].append(line.strip())

        # Identify constraints (look for "cannot", "limited", "within")
        constraint_keywords = ['cannot', 'limited', 'within', 'constraint', 'restriction']
        for line in lines:
            if any(keyword in line.lower() for keyword in constraint_keywords):
                analysis['constraints'].append(line.strip())

        # Identify dependencies (look for "depends on", "requires", "needs")
        dependency_keywords = ['depends on', 'requires', 'needs', 'prerequisite']
        for line in lines:
            if any(keyword in line.lower() for keyword in dependency_keywords):
                analysis['dependencies'].append(line.strip())

        return analysis

    def _generate_approaches(
        self,
        description: str,
        problem_analysis: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple approach options

        Args:
            description: Task description
            problem_analysis: Problem analysis
            context: Optional context

        Returns:
            List of approach dictionaries
        """
        approaches = []

        # Approach 1: Incremental (default for most tasks)
        approaches.append({
            'name': 'Incremental Approach',
            'description': 'Break down into small, testable steps. Implement and validate each step before moving to the next.',
            'pros': [
                'Lower risk - issues caught early',
                'Easier to test and validate',
                'Can deliver value incrementally',
                'Easier to rollback if needed'
            ],
            'cons': [
                'May take longer overall',
                'Requires more coordination',
                'May need refactoring between steps'
            ],
            'effort': 'Medium',
            'risk': 'Low'
        })

        # Approach 2: Big Bang (for simple or tightly coupled tasks)
        approaches.append({
            'name': 'Complete Implementation',
            'description': 'Implement the entire solution in one go, then test comprehensively.',
            'pros': [
                'Faster if everything works',
                'No intermediate states to manage',
                'Simpler coordination'
            ],
            'cons': [
                'Higher risk - issues found late',
                'Harder to debug',
                'All-or-nothing delivery',
                'Difficult to rollback'
            ],
            'effort': 'Low',
            'risk': 'High'
        })

        # Approach 3: Prototype First (for uncertain or complex tasks)
        if any(keyword in description.lower() for keyword in ['complex', 'uncertain', 'new', 'experimental']):
            approaches.append({
                'name': 'Prototype First',
                'description': 'Build a quick prototype to validate approach, then implement properly.',
                'pros': [
                    'Validates approach early',
                    'Identifies issues before full implementation',
                    'Allows experimentation',
                    'Reduces uncertainty'
                ],
                'cons': [
                    'Requires building twice',
                    'May waste time on prototype',
                    'Prototype code may leak into production'
                ],
                'effort': 'High',
                'risk': 'Medium'
            })

        return approaches

    def _select_recommended_approach(
        self,
        approaches: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Select the recommended approach

        Args:
            approaches: List of approach options

        Returns:
            Recommended approach
        """
        # Default to incremental approach (lowest risk)
        for approach in approaches:
            if approach['risk'] == 'Low':
                return approach

        # Fallback to first approach
        return approaches[0] if approaches else {}

    def _generate_execution_plan(
        self,
        approach: Dict[str, Any],
        description: str
    ) -> List[Dict[str, str]]:
        """
        Generate step-by-step execution plan

        Args:
            approach: Selected approach
            description: Task description

        Returns:
            List of execution steps
        """
        steps = []

        # Step 1: Always start with analysis/planning
        steps.append({
            'step': '1',
            'title': 'Analyze and Plan',
            'description': 'Review requirements, identify dependencies, and create detailed plan',
            'deliverable': 'Detailed implementation plan with dependencies identified'
        })

        # Step 2: Setup/preparation
        steps.append({
            'step': '2',
            'title': 'Setup and Preparation',
            'description': 'Set up development environment, install dependencies, create necessary files',
            'deliverable': 'Development environment ready, all dependencies installed'
        })

        # Step 3: Core implementation
        steps.append({
            'step': '3',
            'title': 'Core Implementation',
            'description': 'Implement the main functionality according to requirements',
            'deliverable': 'Core functionality implemented and working'
        })

        # Step 4: Testing
        steps.append({
            'step': '4',
            'title': 'Testing and Validation',
            'description': 'Write and run tests, validate against requirements',
            'deliverable': 'All tests passing, requirements validated'
        })

        # Step 5: Documentation and cleanup
        steps.append({
            'step': '5',
            'title': 'Documentation and Cleanup',
            'description': 'Document code, clean up temporary files, update README',
            'deliverable': 'Code documented, repository clean'
        })

        return steps

    def _identify_success_criteria(
        self,
        description: str,
        execution_plan: List[Dict[str, str]]
    ) -> List[str]:
        """
        Identify success criteria

        Args:
            description: Task description
            execution_plan: Execution plan

        Returns:
            List of success criteria
        """
        criteria = []

        # Default criteria based on execution plan
        criteria.append('All execution steps completed successfully')
        criteria.append('All tests passing')
        criteria.append('Code reviewed and approved')
        criteria.append('Documentation updated')

        # Extract specific criteria from description
        if 'test' in description.lower():
            criteria.append('Comprehensive test coverage achieved')

        if 'performance' in description.lower():
            criteria.append('Performance requirements met')

        if 'security' in description.lower():
            criteria.append('Security requirements validated')

        return criteria

    def _identify_risks(
        self,
        description: str,
        execution_plan: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """
        Identify risks and mitigation strategies

        Args:
            description: Task description
            execution_plan: Execution plan

        Returns:
            List of risk dictionaries
        """
        risks = []

        # Common risks
        risks.append({
            'risk': 'Requirements misunderstanding',
            'impact': 'Medium',
            'mitigation': 'Clarify requirements early, validate understanding with stakeholders'
        })

        risks.append({
            'risk': 'Technical complexity underestimated',
            'impact': 'High',
            'mitigation': 'Break down into smaller steps, prototype uncertain areas first'
        })

        risks.append({
            'risk': 'Dependencies unavailable or incompatible',
            'impact': 'Medium',
            'mitigation': 'Verify dependencies early, have fallback options'
        })

        # Task-specific risks
        if 'integrat' in description.lower():  # Matches both "integrate" and "integration"
            risks.append({
                'risk': 'Integration issues with external systems',
                'impact': 'High',
                'mitigation': 'Test integrations early, have mock/stub implementations ready'
            })

        if 'migrat' in description.lower():  # Matches both "migrate" and "migration"
            risks.append({
                'risk': 'Data loss during migration',
                'impact': 'Critical',
                'mitigation': 'Backup all data, test migration on copy first, have rollback plan'
            })

        return risks

    def _format_plan(
        self,
        title: str,
        description: str,
        problem_analysis: Dict[str, Any],
        approaches: List[Dict[str, Any]],
        recommended: Dict[str, Any],
        execution_plan: List[Dict[str, str]],
        success_criteria: List[str],
        risks: List[Dict[str, str]]
    ) -> str:
        """Format plan as markdown"""
        content = f"# Plan: {title}\n\n"
        content += f"**Created**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        content += "---\n\n"

        # Problem Analysis
        content += "## Problem Analysis\n\n"
        content += f"**Core Problem**: {problem_analysis['core_problem']}\n\n"

        if problem_analysis['requirements']:
            content += "**Requirements**:\n"
            for req in problem_analysis['requirements']:
                content += f"- {req}\n"
            content += "\n"

        if problem_analysis['constraints']:
            content += "**Constraints**:\n"
            for constraint in problem_analysis['constraints']:
                content += f"- {constraint}\n"
            content += "\n"

        if problem_analysis['dependencies']:
            content += "**Dependencies**:\n"
            for dep in problem_analysis['dependencies']:
                content += f"- {dep}\n"
            content += "\n"

        # Approach Options
        content += "## Approach Options\n\n"
        for i, approach in enumerate(approaches, 1):
            content += f"### Option {i}: {approach['name']}\n\n"
            content += f"{approach['description']}\n\n"
            content += f"**Effort**: {approach['effort']} | **Risk**: {approach['risk']}\n\n"

            content += "**Pros**:\n"
            for pro in approach['pros']:
                content += f"- {pro}\n"
            content += "\n"

            content += "**Cons**:\n"
            for con in approach['cons']:
                content += f"- {con}\n"
            content += "\n"

        # Recommended Approach
        content += "## Recommended Approach\n\n"
        content += f"**{recommended['name']}**\n\n"
        content += f"{recommended['description']}\n\n"
        content += f"This approach is recommended because it offers the best balance of risk ({recommended['risk']}) and effort ({recommended['effort']}).\n\n"

        # Execution Plan
        content += "## Execution Plan\n\n"
        for step in execution_plan:
            content += f"### Step {step['step']}: {step['title']}\n\n"
            content += f"{step['description']}\n\n"
            content += f"**Deliverable**: {step['deliverable']}\n\n"

        # Success Criteria
        content += "## Success Criteria\n\n"
        for criterion in success_criteria:
            content += f"- [ ] {criterion}\n"
        content += "\n"

        # Risks and Mitigation
        content += "## Risks and Mitigation\n\n"
        for risk in risks:
            content += f"**Risk**: {risk['risk']} (Impact: {risk['impact']})\n"
            content += f"**Mitigation**: {risk['mitigation']}\n\n"

        return content

    def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """
        Get plan by ID

        Args:
            plan_id: Plan ID

        Returns:
            Plan data or None
        """
        plan_file = self.plans_folder / f"{plan_id}.md"

        if not plan_file.exists():
            return None

        try:
            with open(plan_file, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)

            return {
                **post.metadata,
                'content': post.content
            }

        except Exception as e:
            logger.error(f"Error loading plan: {e}")
            return None

    def list_plans(self, task_id: str = None) -> List[Dict[str, Any]]:
        """
        List all plans

        Args:
            task_id: Optional filter by task ID

        Returns:
            List of plan summaries
        """
        plans = []

        for plan_file in self.plans_folder.glob('*.md'):
            try:
                with open(plan_file, 'r', encoding='utf-8') as f:
                    post = frontmatter.load(f)

                # Filter by task_id if specified
                if task_id and post.metadata.get('task_id') != task_id:
                    continue

                plans.append({
                    'plan_id': post.metadata.get('plan_id'),
                    'task_id': post.metadata.get('task_id'),
                    'title': post.metadata.get('title'),
                    'status': post.metadata.get('status'),
                    'created_at': post.metadata.get('created_at')
                })

            except Exception as e:
                logger.error(f"Error loading plan {plan_file}: {e}")

        # Sort by created_at (newest first)
        plans.sort(key=lambda p: p.get('created_at', ''), reverse=True)

        return plans
