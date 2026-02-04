"""
Task planner implementation
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from ..base import BasePlanner
from .task import Task, TaskGraph, TaskPriority
import json


class LLMPlanner(BasePlanner, BaseModel):
    """
    LLM-based task planner

    Uses an LLM to decompose complex tasks into smaller steps
    """

    agent: Any = None  # Agent instance for LLM calls
    prompt_template: str = None
    max_refinements: int = 3

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data):
        super().__init__(**data)
        if self.prompt_template is None:
            self.prompt_template = """You are an expert task planner. Break down the following goal into clear, actionable steps.

Goal: {{goal}}

{{context if context else ""}}

Provide a step-by-step plan. For each step, include:
1. Step number
2. Step name (short and clear)
3. Detailed description
4. Dependencies (which previous steps must be completed first)
5. Estimated complexity (simple/medium/complex)
6. Priority (low/medium/high/critical)

Format as a numbered list with clear structure."""

    async def plan(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Create a plan for achieving the given goal

        Args:
            goal: The goal to achieve
            context: Optional context information

        Returns:
            List of task steps in the plan
        """
        # Format the prompt
        prompt = self.prompt_template.replace('{{goal}}', goal)
        if context:
            context_str = f"Context:\n{json.dumps(context, indent=2)}"
            prompt = prompt.replace('{{context if context else ""}}', context_str)
        else:
            prompt = prompt.replace('{{context if context else ""}}', '')

        # Call LLM
        if self.agent:
            response = await self.agent.call(prompt)
            plan_text = response.get('response', '')
        else:
            # Fallback: return simple plan
            return [
                {
                    'name': 'Execute goal',
                    'description': goal,
                    'dependencies': [],
                    'complexity': 'medium',
                    'priority': 'medium'
                }
            ]

        # Parse the response into tasks
        tasks = self._parse_plan(plan_text)
        return tasks

    def _parse_plan(self, plan_text: str) -> List[Dict[str, Any]]:
        """
        Parse LLM response into structured tasks

        Args:
            plan_text: Raw LLM response

        Returns:
            List of task dictionaries
        """
        tasks = []
        lines = plan_text.strip().split('\n')

        current_task = None
        step_num = 0

        for line in lines:
            line = line.strip()

            # Detect step number (e.g., "1.", "Step 1:", etc.)
            if line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')) or \
               line.lower().startswith(('step 1:', 'step 2:', 'step 3:', 'step 4:', 'step 5:')):
                # Save previous task if exists
                if current_task:
                    tasks.append(current_task)

                step_num += 1
                current_task = {
                    'step': step_num,
                    'name': line.split('.', 1)[-1].strip() if '.' in line else line,
                    'description': '',
                    'dependencies': [],
                    'complexity': 'medium',
                    'priority': 'medium'
                }

            # Detect description
            elif current_task and line and not line.startswith('-') and not line.startswith('*'):
                if current_task['description']:
                    current_task['description'] += ' ' + line
                else:
                    current_task['description'] = line

            # Detect metadata (priority, complexity, dependencies)
            elif current_task and line.startswith('-'):
                lower_line = line.lower()
                if 'complexity' in lower_line:
                    for level in ['simple', 'medium', 'complex']:
                        if level in lower_line:
                            current_task['complexity'] = level
                            break
                elif 'priority' in lower_line:
                    for level in ['low', 'medium', 'high', 'critical']:
                        if level in lower_line:
                            current_task['priority'] = level
                            break
                elif 'depend' in lower_line:
                    # Parse dependencies
                    deps = []
                    for i in range(1, step_num):
                        if str(i) in line:
                            deps.append(i - 1)  # Convert to 0-indexed
                    current_task['dependencies'] = deps

        # Add last task
        if current_task:
            tasks.append(current_task)

        # Fallback: if no tasks parsed, create single task
        if not tasks:
            tasks = [
                {
                    'step': 1,
                    'name': 'Execute task',
                    'description': plan_text[:500],
                    'dependencies': [],
                    'complexity': 'medium',
                    'priority': 'medium'
                }
            ]

        return tasks

    async def refine_plan(
        self,
        plan: List[Dict[str, Any]],
        feedback: str
    ) -> List[Dict[str, Any]]:
        """
        Refine an existing plan based on feedback

        Args:
            plan: Current plan
            feedback: Feedback for refinement

        Returns:
            Refined plan
        """
        plan_text = self._format_plan_for_refinement(plan)

        prompt = f"""You are refining a task plan based on feedback.

Current Plan:
{plan_text}

Feedback:
{feedback}

Please provide the refined plan following the same format."""

        # Call LLM
        if self.agent:
            response = await self.agent.call(prompt)
            refined_text = response.get('response', '')
            refined_tasks = self._parse_plan(refined_text)
            return refined_tasks
        else:
            # Return original plan if no agent
            return plan

    def _format_plan_for_refinement(self, plan: List[Dict[str, Any]]) -> str:
        """Format plan for display in refinement prompt"""
        lines = []
        for task in plan:
            lines.append(f"{task.get('step', '?')}. {task.get('name', 'Unnamed')}")
            lines.append(f"   Description: {task.get('description', 'No description')}")
            lines.append(f"   Complexity: {task.get('complexity', 'medium')}")
            lines.append(f"   Priority: {task.get('priority', 'medium')}")
            if task.get('dependencies'):
                lines.append(f"   Dependencies: {', '.join(map(str, task['dependencies']))}")
            lines.append('')
        return '\n'.join(lines)


class SimplePlanner(BasePlanner, BaseModel):
    """
    Simple rule-based planner

    Creates basic task decomposition without LLM
    """

    default_complexity: str = 'medium'
    default_priority: str = 'medium'

    async def plan(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Create a simple plan with a single task

        Args:
            goal: The goal to achieve
            context: Optional context (not used in simple planner)

        Returns:
            List with single task
        """
        return [
            {
                'step': 1,
                'name': 'Complete goal',
                'description': goal,
                'dependencies': [],
                'complexity': self.default_complexity,
                'priority': self.default_priority
            }
        ]

    async def refine_plan(
        self,
        plan: List[Dict[str, Any]],
        feedback: str
    ) -> List[Dict[str, Any]]:
        """
        Return plan unchanged (simple planner doesn't refine)

        Args:
            plan: Current plan
            feedback: Feedback (ignored)

        Returns:
            Original plan
        """
        return plan


class HierarchicalPlanner(BasePlanner, BaseModel):
    """
    Hierarchical planner that creates sub-tasks

    Breaks down complex tasks into hierarchical structure
    """

    max_depth: int = 3
    sub_task_threshold: int = 5  # Number of steps that trigger sub-tasking

    async def plan(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Create a hierarchical plan

        Args:
            goal: The goal to achieve
            context: Optional context

        Returns:
            List of top-level tasks
        """
        # Simple implementation: create phases
        tasks = [
            {
                'step': 1,
                'name': 'Planning and Analysis',
                'description': f'Analyze requirements and plan approach for: {goal}',
                'dependencies': [],
                'complexity': 'medium',
                'priority': 'high'
            },
            {
                'step': 2,
                'name': 'Execution',
                'description': f'Execute the main task: {goal}',
                'dependencies': [0],
                'complexity': 'complex',
                'priority': 'high'
            },
            {
                'step': 3,
                'name': 'Verification',
                'description': 'Verify and validate results',
                'dependencies': [1],
                'complexity': 'simple',
                'priority': 'medium'
            }
        ]

        return tasks

    async def refine_plan(
        self,
        plan: List[Dict[str, Any]],
        feedback: str
    ) -> List[Dict[str, Any]]:
        """
        Refine plan based on feedback

        Args:
            plan: Current plan
            feedback: Feedback

        Returns:
            Refined plan
        """
        # Simple implementation: add a refinement task at the end
        refined_plan = plan.copy()
        refined_plan.append({
            'step': len(plan) + 1,
            'name': 'Apply Refinements',
            'description': f'Address feedback: {feedback}',
            'dependencies': [i for i in range(len(plan))],
            'complexity': 'medium',
            'priority': 'high'
        })

        return refined_plan


def create_planner(
    planner_type: str = 'simple',
    agent: Any = None,
    **kwargs
) -> BasePlanner:
    """
    Factory function to create a planner

    Args:
        planner_type: Type of planner ('simple', 'llm', 'hierarchical')
        agent: Agent instance (for LLM planner)
        **kwargs: Additional planner-specific arguments

    Returns:
        Planner instance
    """
    if planner_type == 'llm':
        return LLMPlanner(agent=agent, **kwargs)
    elif planner_type == 'hierarchical':
        return HierarchicalPlanner(**kwargs)
    else:
        return SimplePlanner(**kwargs)
