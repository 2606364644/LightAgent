"""
Task executor implementation
"""
from typing import Any, Dict, List, Optional, Callable
from pydantic import BaseModel, Field
from ..base import BaseExecutor, TaskStatus
from .task import Task, TaskGraph
import asyncio
from datetime import datetime


class TaskExecutor(BaseExecutor, BaseModel):
    """
    Task executor with support for different execution strategies

    Features:
    - Sequential execution
    - Parallel execution of independent tasks
    - Error handling and retry
    - Progress tracking
    """

    agent: Any = None  # Agent for executing tasks
    max_parallel_tasks: int = 3
    retry_failed_tasks: bool = True
    max_retries: int = 2
    execution_context: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

    async def execute(
        self,
        task: Task,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a single task

        Args:
            task: Task to execute
            context: Optional execution context

        Returns:
            Execution result
        """
        execution_context = {**self.execution_context, **(context or {})}

        task.mark_started()

        try:
            # If task has an agent assigned, use that agent
            if task.agent and hasattr(task.agent, 'run'):
                result = await task.agent.run(task.description, context=execution_context)
                task.mark_completed(result=result, output=result.get('response', ''))
                return result

            # If executor has an agent, use it
            elif self.agent:
                result = await self.agent.run(task.description, context=execution_context)
                task.mark_completed(result=result, output=result.get('response', ''))
                return result

            # Otherwise, use custom executor function if provided in context
            elif 'executor_func' in execution_context:
                executor_func: Callable = execution_context['executor_func']
                result = await executor_func(task, execution_context)
                task.mark_completed(result=result, output=str(result))
                return result

            # Default: simple execution
            else:
                result = {
                    'success': True,
                    'message': f'Task "{task.name}" executed',
                    'task': task.name
                }
                task.mark_completed(result=result)
                return result

        except Exception as e:
            error_msg = f"Execution failed: {str(e)}"
            task.mark_failed(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'task': task.name
            }

    async def check_status(self, task_id: str) -> str:
        """
        Check the status of a task

        Args:
            task_id: Task identifier

        Returns:
            Current task status
        """
        # This would need to be implemented with a task registry
        # For now, return unknown
        return TaskStatus.PENDING

    async def execute_plan(
        self,
        task_graph: TaskGraph,
        mode: str = 'sequential'
    ) -> Dict[str, Any]:
        """
        Execute a complete task graph

        Args:
            task_graph: TaskGraph to execute
            mode: Execution mode ('sequential', 'parallel', 'adaptive')

        Returns:
            Execution summary
        """
        if mode == 'sequential':
            return await self._execute_sequential(task_graph)
        elif mode == 'parallel':
            return await self._execute_parallel(task_graph)
        elif mode == 'adaptive':
            return await self._execute_adaptive(task_graph)
        else:
            raise ValueError(f"Unknown execution mode: {mode}")

    async def _execute_sequential(self, task_graph: TaskGraph) -> Dict[str, Any]:
        """
        Execute tasks sequentially, respecting dependencies

        Args:
            task_graph: TaskGraph to execute

        Returns:
            Execution summary
        """
        summary = {
            'total': len(task_graph.tasks),
            'completed': 0,
            'failed': 0,
            'errors': []
        }

        while True:
            # Get ready tasks
            ready_tasks = task_graph.get_ready_tasks()

            if not ready_tasks:
                # No more ready tasks
                break

            # Execute each ready task
            for task in ready_tasks:
                try:
                    await self.execute(task)

                    if task.status == TaskStatus.COMPLETED:
                        summary['completed'] += 1
                    elif task.status == TaskStatus.FAILED:
                        summary['failed'] += 1
                        summary['errors'].append({
                            'task': task.name,
                            'error': task.error
                        })

                except Exception as e:
                    summary['failed'] += 1
                    summary['errors'].append({
                        'task': task.name,
                        'error': str(e)
                    })

        return summary

    async def _execute_parallel(self, task_graph: TaskGraph) -> Dict[str, Any]:
        """
        Execute independent tasks in parallel

        Args:
            task_graph: TaskGraph to execute

        Returns:
            Execution summary
        """
        summary = {
            'total': len(task_graph.tasks),
            'completed': 0,
            'failed': 0,
            'errors': []
        }

        while True:
            # Get ready tasks
            ready_tasks = task_graph.get_ready_tasks()

            if not ready_tasks:
                break

            # Limit parallelism
            batch_size = min(len(ready_tasks), self.max_parallel_tasks)
            batch = ready_tasks[:batch_size]

            # Execute batch in parallel
            results = await asyncio.gather(
                *[self.execute(task) for task in batch],
                return_exceptions=True
            )

            # Process results
            for task, result in zip(batch, results):
                if isinstance(result, Exception):
                    summary['failed'] += 1
                    summary['errors'].append({
                        'task': task.name,
                        'error': str(result)
                    })
                elif task.status == TaskStatus.COMPLETED:
                    summary['completed'] += 1
                elif task.status == TaskStatus.FAILED:
                    summary['failed'] += 1

        return summary

    async def _execute_adaptive(self, task_graph: TaskGraph) -> Dict[str, Any]:
        """
        Execute tasks adaptively based on priority and dependencies

        Args:
            task_graph: TaskGraph to execute

        Returns:
            Execution summary
        """
        # For adaptive, use parallel execution with priority-based scheduling
        return await self._execute_parallel(task_graph)


class WorkflowExecutor(BaseModel):
    """
    Complete workflow executor with planning and execution

    Combines planning and execution into a single workflow
    """

    planner: Any = None
    task_executor: TaskExecutor = None
    auto_refine: bool = False
    verbose: bool = True

    class Config:
        arbitrary_types_allowed = True

    async def run_workflow(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None,
        execution_mode: str = 'sequential'
    ) -> Dict[str, Any]:
        """
        Run a complete workflow from goal to execution

        Args:
            goal: Goal to achieve
            context: Optional context
            execution_mode: How to execute tasks

        Returns:
            Workflow result
        """
        if self.verbose:
            print(f"Planning workflow for: {goal}")

        # Create plan
        plan = await self.planner.plan(goal, context)

        if self.verbose:
            print(f"Created plan with {len(plan)} tasks")

        # Convert plan to task graph
        task_graph = TaskGraph()

        for i, task_def in enumerate(plan):
            task = Task(
                name=task_def.get('name', f'Task {i+1}'),
                description=task_def.get('description', ''),
                priority=task_def.get('priority', 'medium')
            )

            # Add dependencies (convert step numbers to task IDs later)
            deps = task_def.get('dependencies', [])
            if deps:
                # Dependencies are step numbers (0-indexed), convert to task IDs
                # Will be resolved after all tasks are created
                task.metadata['dependency_steps'] = deps

            task_graph.add_task(task)

        # Resolve dependencies
        for task in task_graph.tasks.values():
            dep_steps = task.metadata.get('dependency_steps', [])
            for step in dep_steps:
                # Find task by step number
                for t in task_graph.tasks.values():
                    if t.name.startswith(f"Task {step + 1}") or \
                       any(plan[j].get('name', '') == t.name for j in range(len(plan)) if j == step):
                        task.add_dependency(t.task_id)

        # Execute plan
        if self.verbose:
            print(f"Executing plan in {execution_mode} mode...")

        summary = await self.task_executor.execute_plan(task_graph, execution_mode)

        # Prepare result
        result = {
            'goal': goal,
            'total_tasks': summary['total'],
            'completed': summary['completed'],
            'failed': summary['failed'],
            'success': summary['failed'] == 0,
            'errors': summary['errors'],
            'progress': task_graph.get_progress(),
            'stats': task_graph.get_stats()
        }

        if self.verbose:
            print(f"Workflow completed: {summary['completed']}/{summary['total']} tasks successful")
            if summary['errors']:
                print(f"Errors: {summary['errors']}")

        return result

    async def refine_and_retry(
        self,
        goal: str,
        previous_result: Dict[str, Any],
        feedback: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Refine a failed workflow and retry

        Args:
            goal: Original goal
            previous_result: Result from previous execution
            feedback: Feedback for refinement
            context: Optional context

        Returns:
            New workflow result
        """
        if self.verbose:
            print(f"Refining workflow based on feedback...")

        # Get original plan (would need to store this)
        # For now, just re-run with feedback as context
        new_context = {
            **(context or {}),
            'feedback': feedback,
            'previous_errors': previous_result.get('errors', [])
        }

        return await self.run_workflow(goal, new_context)


def create_executor(
    executor_type: str = 'basic',
    agent: Any = None,
    **kwargs
) -> TaskExecutor:
    """
    Factory function to create a task executor

    Args:
        executor_type: Type of executor ('basic', 'parallel')
        agent: Agent for task execution
        **kwargs: Additional executor arguments

    Returns:
        TaskExecutor instance
    """
    return TaskExecutor(agent=agent, **kwargs)
