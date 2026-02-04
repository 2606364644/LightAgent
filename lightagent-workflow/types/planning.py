"""
Planning Workflow - Task decomposition and execution workflow

Decomposes complex tasks into smaller steps and executes them sequentially or in parallel.
"""
from typing import Any, Dict, List, Optional, Callable
from pydantic import BaseModel, Field
from datetime import datetime

from ..base import BaseWorkflow, WorkflowStatus, WorkflowState
from ..planning import TaskGraph, Task, TaskPriority, LLMPlanner, TaskExecutor


class PlanningWorkflow(BaseWorkflow):
    """
    Planning-based workflow

    Flow:
    1. Plan: Decompose goal into tasks
    2. Execute: Execute task list (sequential/parallel/adaptive)
    3. Validate: Check results
    4. Refine (optional): Retry failed tasks

    Use cases:
    - Complex task decomposition
    - Research workflows
    - Multi-step analysis
    """

    workflow_type: str = "planning"

    # Components
    planner: Optional[LLMPlanner] = None
    executor: Optional[TaskExecutor] = None

    # Configuration
    execution_mode: str = "sequential"  # sequential, parallel, adaptive
    auto_refine: bool = True
    max_refinements: int = 3
    max_recursion_depth: int = 3
    stop_when_simple: bool = True

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data):
        super().__init__(**data)

        # Initialize planner if not provided
        if self.planner is None and self.agent:
            self.planner = LLMPlanner(agent=self.agent)

        # Initialize executor if not provided
        if self.executor is None:
            self.executor = TaskExecutor(agent=self.agent)

    async def execute(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute planning workflow

        Args:
            goal: Goal to achieve
            context: Optional context

        Returns:
            Execution result
        """
        self.status = WorkflowStatus.RUNNING
        self.updated_at = datetime.now()

        if self.verbose:
            print(f"\n{'='*60}")
            print(f"Planning Workflow: {goal}")
            print(f"{'='*60}\n")

        try:
            # Step 1: Plan
            if self.verbose:
                print("Step 1: Planning...")

            plan = await self._create_plan(goal, context, current_depth=0)

            if self.verbose:
                print(f"  Created plan with {len(plan)} tasks")
                for i, task in enumerate(plan):
                    print(f"    {i+1}. {task.get('name', 'Unnamed')}")

            # Step 2: Create task graph
            task_graph = await self._create_task_graph(plan)

            # Update state
            self.current_state = WorkflowState(
                workflow_id=self.workflow_id,
                current_step=0,
                total_steps=len(plan),
                tasks=plan,
                context=context or {}
            )

            # Step 3: Execute
            if self.verbose:
                print("\nStep 2: Executing tasks...")

            summary = await self.executor.execute_plan(
                task_graph,
                self.execution_mode
            )

            # Step 4: Validate and refine
            if summary['failed'] > 0 and self.auto_refine:
                if self.verbose:
                    print(f"\nStep 3: Refining failed tasks ({summary['failed']} failed)...")

                refinement_result = await self._refine_and_retry(
                    goal,
                    task_graph,
                    summary,
                    context
                )
                summary = refinement_result

            # Prepare result
            result = {
                'success': summary['failed'] == 0,
                'goal': goal,
                'total_tasks': summary['total'],
                'completed_tasks': summary['completed'],
                'failed_tasks': summary['failed'],
                'errors': summary.get('errors', []),
                'progress': task_graph.get_progress(),
                'stats': task_graph.get_stats()
            }

            # Update status
            if result['success']:
                self.status = WorkflowStatus.COMPLETED
            else:
                self.status = WorkflowStatus.FAILED

            self.updated_at = datetime.now()

            if self.verbose:
                print(f"\nExecution complete:")
                print(f"  - Completed: {summary['completed']}/{summary['total']}")
                print(f"  - Failed: {summary['failed']}")
                print(f"  - Progress: {task_graph.get_progress():.1f}%")

            return result

        except Exception as e:
            self.status = WorkflowStatus.FAILED
            self.updated_at = datetime.now()

            error_result = {
                'success': False,
                'error': str(e),
                'goal': goal
            }

            if self.verbose:
                print(f"Workflow failed: {e}")

            return error_result

    async def _create_plan(
        self,
        goal: str,
        context: Optional[Dict[str, Any]],
        current_depth: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Create a plan with optional recursive decomposition

        Args:
            goal: Goal to plan
            context: Optional context
            current_depth: Current recursion depth

        Returns:
            List of tasks
        """
        # Stop condition
        if self.stop_when_simple and current_depth >= self.max_recursion_depth:
            return [{
                'name': 'Execute goal',
                'description': goal,
                'dependencies': [],
                'complexity': 'simple',
                'priority': 'medium'
            }]

        # Create plan using planner
        if self.planner:
            tasks = await self.planner.plan(goal, context)
        else:
            # Fallback
            tasks = [{
                'name': 'Execute goal',
                'description': goal,
                'dependencies': [],
                'complexity': 'simple',
                'priority': 'medium'
            }]

        # Recursive decomposition for complex tasks
        if current_depth < self.max_recursion_depth:
            refined_tasks = []
            for task in tasks:
                if task.get('complexity') == 'complex':
                    # Recursively decompose
                    sub_tasks = await self._create_plan(
                        task['description'],
                        context,
                        current_depth + 1
                    )
                    refined_tasks.extend(sub_tasks)
                else:
                    refined_tasks.append(task)
            return refined_tasks

        return tasks

    async def _create_task_graph(self, plan: List[Dict[str, Any]]) -> TaskGraph:
        """
        Create task graph from plan

        Args:
            plan: Plan with tasks

        Returns:
            TaskGraph instance
        """
        task_graph = TaskGraph()
        task_map = {}

        # Create tasks
        for i, task_def in enumerate(plan):
            task = Task(
                name=task_def.get('name', f'Task {i+1}'),
                description=task_def.get('description', ''),
                priority=task_def.get('priority', 'medium')
            )

            task_graph.add_task(task)
            task_map[i] = task.task_id

        # Add dependencies
        for i, task_def in enumerate(plan):
            deps = task_def.get('dependencies', [])
            task_id = task_map[i]

            for dep_step in deps:
                if dep_step in task_map:
                    dep_id = task_map[dep_step]
                    task_graph.add_dependency(task_id, dep_id)

        return task_graph

    async def _refine_and_retry(
        self,
        goal: str,
        task_graph: TaskGraph,
        previous_summary: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Refine failed tasks and retry

        Args:
            goal: Original goal
            task_graph: Task graph
            previous_summary: Previous execution summary
            context: Optional context

        Returns:
            New execution summary
        """
        for attempt in range(self.max_refinements):
            if self.verbose:
                print(f"  Refinement attempt {attempt + 1}/{self.max_refinements}")

            # Retry failed tasks
            summary = await self.executor.execute_plan(
                task_graph,
                self.execution_mode
            )

            if summary['failed'] == 0:
                if self.verbose:
                    print(f"  All tasks completed successfully")
                break

        return summary

    async def validate(self, goal: str) -> bool:
        """
        Validate if goal is suitable for planning workflow

        Args:
            goal: Goal to validate

        Returns:
            True if valid
        """
        # Planning workflow is suitable for most goals
        # It can handle simple and complex tasks
        return len(goal.strip()) > 0
