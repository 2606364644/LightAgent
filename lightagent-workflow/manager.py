"""
Workflow Manager - Manages multiple workflow instances

Provides centralized management for workflows of different types,
including creation, execution, monitoring, and lifecycle control.
"""
from typing import Any, Dict, List, Optional, Type, Callable
import asyncio
from datetime import datetime
from pydantic import BaseModel, Field

from .base import BaseWorkflow, WorkflowStatus


class WorkflowManager(BaseModel):
    """
    Manages multiple workflow instances

    Features:
    - Create workflows of different types
    - Execute multiple workflows concurrently
    - Query workflow status and progress
    - Control workflow lifecycle (pause/resume/cancel)
    - Event callbacks for workflow events
    """

    # Core
    agent: Any = None
    workflows: Dict[str, BaseWorkflow] = Field(default_factory=dict)
    workflow_types: Dict[str, Type[BaseWorkflow]] = Field(default_factory=dict)

    # Configuration
    max_concurrent_workflows: int = 10
    default_timeout: int = 300  # seconds

    # Event callbacks
    on_workflow_started_callbacks: List[Callable] = Field(default_factory=list)
    on_task_completed_callbacks: List[Callable] = Field(default_factory=list)
    on_workflow_completed_callbacks: List[Callable] = Field(default_factory=list)
    on_workflow_failed_callbacks: List[Callable] = Field(default_factory=list)

    # State
    active_tasks: Dict[str, asyncio.Task] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data):
        super().__init__(**data)
        self._register_default_types()

    def _register_default_types(self):
        """
        Register default workflow types

        Note: Workflow types are registered here to avoid circular imports.
        Actual types are registered in types/__init__.py
        """
        # Placeholder - will be populated by types module
        pass

    def register_workflow_type(
        self,
        name: str,
        workflow_class: Type[BaseWorkflow]
    ):
        """
        Register a custom workflow type

        Args:
            name: Type name
            workflow_class: Workflow class (must inherit from BaseWorkflow)
        """
        if not issubclass(workflow_class, BaseWorkflow):
            raise TypeError(f"{workflow_class} must inherit from BaseWorkflow")

        self.workflow_types[name] = workflow_class

        if self.verbose:
            print(f"Registered workflow type: {name}")

    async def create_workflow(
        self,
        workflow_type: str,
        goal: str,
        config: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> BaseWorkflow:
        """
        Create a workflow instance

        Args:
            workflow_type: Type of workflow to create
            goal: Goal for the workflow
            config: Optional workflow configuration
            context: Optional initial context

        Returns:
            Created workflow instance
        """
        if workflow_type not in self.workflow_types:
            available = ', '.join(self.workflow_types.keys())
            raise ValueError(
                f"Unknown workflow type: '{workflow_type}'. "
                f"Available types: {available}"
            )

        workflow_class = self.workflow_types[workflow_type]
        workflow = workflow_class(
            agent=self.agent,
            config=config or {},
            verbose=self.config.get('verbose', True)
        )

        # Validate goal
        is_valid = await workflow.validate(goal)
        if not is_valid:
            raise ValueError(f"Goal is not suitable for workflow type '{workflow_type}'")

        # Store workflow
        self.workflows[workflow.workflow_id] = workflow

        if self.verbose:
            print(f"Created workflow {workflow.workflow_id} of type '{workflow_type}'")

        return workflow

    async def start_workflow(
        self,
        workflow_id: str,
        goal: str,
        context: Optional[Dict[str, Any]] = None,
        block: bool = True,
        timeout: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Start a workflow execution

        Args:
            workflow_id: Workflow ID
            goal: Goal to achieve
            context: Optional execution context
            block: If True, wait for completion. If False, run in background.
            timeout: Optional timeout in seconds

        Returns:
            Execution result if block=True, None otherwise
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        timeout = timeout or self.default_timeout

        if block:
            # Synchronous execution
            return await self._execute_workflow(workflow, goal, context)
        else:
            # Asynchronous execution
            task = asyncio.create_task(
                self._execute_workflow(workflow, goal, context)
            )
            self.active_tasks[workflow_id] = task
            return None

    async def start_workflows(
        self,
        workflow_ids: List[str],
        goals: Optional[List[str]] = None,
        contexts: Optional[List[Dict[str, Any]]] = None
    ) -> List[asyncio.Task]:
        """
        Start multiple workflows concurrently

        Args:
            workflow_ids: List of workflow IDs
            goals: Optional list of goals (if different from creation)
            contexts: Optional list of contexts

        Returns:
            List of asyncio tasks
        """
        if goals is None:
            goals = []
        if contexts is None:
            contexts = []

        tasks = []
        for i, wf_id in enumerate(workflow_ids):
            goal = goals[i] if i < len(goals) else None
            context = contexts[i] if i < len(contexts) else None

            workflow = self.workflows.get(wf_id)
            if workflow and goal:
                task = asyncio.create_task(
                    self._execute_workflow(workflow, goal, context)
                )
                self.active_tasks[wf_id] = task
                tasks.append(task)

        return tasks

    async def _execute_workflow(
        self,
        workflow: BaseWorkflow,
        goal: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Internal method to execute a workflow

        Args:
            workflow: Workflow instance
            goal: Goal to achieve
            context: Optional context

        Returns:
            Execution result
        """
        workflow.status = WorkflowStatus.RUNNING
        workflow.updated_at = datetime.now()

        # Trigger started callback
        await self._trigger_callbacks(
            self.on_workflow_started_callbacks,
            workflow.workflow_id
        )

        try:
            if self.verbose:
                print(f"Starting workflow {workflow.workflow_id}")

            result = await workflow.execute(goal, context)

            # Update status
            if result.get('success', True):
                workflow.status = WorkflowStatus.COMPLETED
                await self._trigger_callbacks(
                    self.on_workflow_completed_callbacks,
                    workflow.workflow_id,
                    result
                )
            else:
                workflow.status = WorkflowStatus.FAILED
                await self._trigger_callbacks(
                    self.on_workflow_failed_callbacks,
                    workflow.workflow_id,
                    result.get('error', 'Unknown error')
                )

            workflow.updated_at = datetime.now()

            # Record history
            workflow.execution_history.append({
                'goal': goal,
                'result': result,
                'timestamp': datetime.now().isoformat()
            })

            return result

        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.updated_at = datetime.now()
            error_msg = str(e)

            if self.verbose:
                print(f"Workflow {workflow.workflow_id} failed: {error_msg}")

            await self._trigger_callbacks(
                self.on_workflow_failed_callbacks,
                workflow.workflow_id,
                error_msg
            )

            return {
                'success': False,
                'error': error_msg,
                'workflow_id': workflow.workflow_id
            }

    async def pause_workflow(self, workflow_id: str):
        """
        Pause a running workflow

        Args:
            workflow_id: Workflow ID
        """
        workflow = self.workflows.get(workflow_id)
        if workflow:
            await workflow.pause()
            if self.verbose:
                print(f"Paused workflow {workflow_id}")

    async def resume_workflow(self, workflow_id: str):
        """
        Resume a paused workflow

        Args:
            workflow_id: Workflow ID
        """
        workflow = self.workflows.get(workflow_id)
        if workflow:
            await workflow.resume()
            if self.verbose:
                print(f"Resumed workflow {workflow_id}")

    async def cancel_workflow(self, workflow_id: str):
        """
        Cancel a workflow

        Args:
            workflow_id: Workflow ID
        """
        workflow = self.workflows.get(workflow_id)
        if workflow:
            await workflow.cancel()

            # Cancel active task if exists
            if workflow_id in self.active_tasks:
                task = self.active_tasks[workflow_id]
                if not task.done():
                    task.cancel()
                del self.active_tasks[workflow_id]

            if self.verbose:
                print(f"Cancelled workflow {workflow_id}")

    async def cancel_workflows(self, workflow_ids: List[str]):
        """
        Cancel multiple workflows

        Args:
            workflow_ids: List of workflow IDs
        """
        await asyncio.gather(
            *[self.cancel_workflow(wf_id) for wf_id in workflow_ids]
        )

    async def get_workflow(self, workflow_id: str) -> Optional[BaseWorkflow]:
        """
        Get a workflow by ID

        Args:
            workflow_id: Workflow ID

        Returns:
            Workflow instance or None
        """
        return self.workflows.get(workflow_id)

    async def list_workflows(
        self,
        status: Optional[str] = None,
        workflow_type: Optional[str] = None
    ) -> List[BaseWorkflow]:
        """
        List workflows with optional filtering

        Args:
            status: Optional status filter
            workflow_type: Optional workflow type filter

        Returns:
            List of workflows
        """
        workflows = list(self.workflows.values())

        if status:
            workflows = [w for w in workflows if w.status == status]

        if workflow_type:
            workflows = [w for w in workflows if w.workflow_type == workflow_type]

        return workflows

    async def wait_for_completion(
        self,
        workflow_id: str,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Wait for workflow completion

        Args:
            workflow_id: Workflow ID
            timeout: Optional timeout in seconds

        Returns:
            Execution result
        """
        if workflow_id not in self.active_tasks:
            workflow = self.workflows.get(workflow_id)
            if workflow and workflow.status == WorkflowStatus.COMPLETED:
                return workflow.execution_history[-1]['result']
            raise ValueError(f"No active task for workflow: {workflow_id}")

        task = self.active_tasks[workflow_id]
        timeout = timeout or self.default_timeout

        try:
            result = await asyncio.wait_for(task, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            await self.cancel_workflow(workflow_id)
            raise TimeoutError(f"Workflow {workflow_id} timed out")
        finally:
            if workflow_id in self.active_tasks:
                del self.active_tasks[workflow_id]

    async def wait_for_all(
        self,
        workflow_ids: List[str],
        timeout: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Wait for multiple workflows to complete

        Args:
            workflow_ids: List of workflow IDs
            timeout: Optional timeout in seconds

        Returns:
            List of execution results
        """
        tasks = []
        for wf_id in workflow_ids:
            if wf_id in self.active_tasks:
                tasks.append(self.active_tasks[wf_id])

        if not tasks:
            return []

        timeout = timeout or self.default_timeout

        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks),
                timeout=timeout
            )
            return results
        except asyncio.TimeoutError:
            await self.cancel_workflows(workflow_ids)
            raise TimeoutError(f"One or more workflows timed out")

    async def cleanup_completed(
        self,
        older_than: int = 3600
    ):
        """
        Remove completed workflows older than specified time

        Args:
            older_than: Age in seconds (default: 1 hour)
        """
        now = datetime.now()
        to_remove = []

        for wf_id, workflow in self.workflows.items():
            if workflow.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]:
                age = (now - workflow.updated_at).total_seconds()
                if age > older_than:
                    to_remove.append(wf_id)

        for wf_id in to_remove:
            del self.workflows[wf_id]
            if self.verbose:
                print(f"Cleaned up workflow {wf_id}")

    # Event callbacks
    def on_workflow_started(self, callback: Callable):
        """Register callback for workflow started event"""
        self.on_workflow_started_callbacks.append(callback)

    def on_task_completed(self, callback: Callable):
        """Register callback for task completed event"""
        self.on_task_completed_callbacks.append(callback)

    def on_workflow_completed(self, callback: Callable):
        """Register callback for workflow completed event"""
        self.on_workflow_completed_callbacks.append(callback)

    def on_workflow_failed(self, callback: Callable):
        """Register callback for workflow failed event"""
        self.on_workflow_failed_callbacks.append(callback)

    async def _trigger_callbacks(self, callbacks: List[Callable], *args):
        """Trigger all callbacks in a list"""
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(*args)
                else:
                    callback(*args)
            except Exception as e:
                if self.verbose:
                    print(f"Callback error: {e}")


async def create_workflow_manager(
    agent: Any,
    max_concurrent_workflows: int = 10,
    verbose: bool = True
) -> WorkflowManager:
    """
    Create and initialize a workflow manager

    Args:
        agent: Agent instance
        max_concurrent_workflows: Maximum concurrent workflows
        verbose: Enable verbose output

    Returns:
        Initialized WorkflowManager
    """
    manager = WorkflowManager(
        agent=agent,
        max_concurrent_workflows=max_concurrent_workflows,
        config={'verbose': verbose}
    )

    return manager
