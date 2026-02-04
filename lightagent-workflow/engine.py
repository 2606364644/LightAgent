"""
Workflow execution engine

Orchestrates planning, prompts, and tools to execute complex workflows
"""
from typing import Any, Dict, List, Optional, Callable
from pydantic import BaseModel, Field
import asyncio
from datetime import datetime

from .base import WorkflowState, TaskStatus
from .prompts import PromptManager, PromptTemplate
from .planning import TaskGraph, Task, BasePlanner, BaseExecutor, create_planner, create_executor
from lightagent.tools import create_file_tools, FileToolConfig


class WorkflowEngine(BaseModel):
    """
    Complete workflow execution engine

    Combines:
    - Enhanced Prompts for dynamic prompt generation
    - Planning Tools for task decomposition
    - File System Tools for file operations
    - Execution orchestration

    This is similar to DeepAgents' workflow capabilities
    """

    # Core components
    agent: Any = None  # Agent instance for LLM calls
    prompt_manager: PromptManager = Field(default_factory=PromptManager)
    planner: Optional[BasePlanner] = None
    executor: Optional[BaseExecutor] = None

    # Tools
    enable_file_tools: bool = True
    file_tool_config: Optional[FileToolConfig] = None

    # Configuration
    verbose: bool = True
    enable_planning: bool = True
    auto_retry: bool = True
    max_retries: int = 2

    # State
    current_state: Optional[WorkflowState] = None
    execution_history: List[Dict[str, Any]] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data):
        super().__init__(**data)

        # Initialize planner if not provided
        if self.planner is None and self.agent:
            from .planning import LLMPlanner
            self.planner = LLMPlanner(agent=self.agent)

        # Initialize executor if not provided
        if self.executor is None:
            from .planning import TaskExecutor
            self.executor = TaskExecutor(agent=self.agent)

    async def initialize(self):
        """Initialize the workflow engine"""
        # Load default prompts
        from .prompts import load_default_prompts
        load_default_prompts(self.prompt_manager)

        if self.verbose:
            print(f"Workflow engine initialized")
            print(f"  - Planning: {self.enable_planning}")
            print(f"  - File tools: {self.enable_file_tools}")

    async def execute(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None,
        execution_mode: str = 'sequential'
    ) -> Dict[str, Any]:
        """
        Execute a workflow

        Args:
            goal: Goal to achieve
            context: Optional execution context
            execution_mode: How to execute tasks ('sequential', 'parallel', 'adaptive')

        Returns:
            Workflow result
        """
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"Executing workflow: {goal}")
            print(f"{'='*60}\n")

        # Create workflow state
        self.current_state = WorkflowState(
            workflow_id=str(datetime.now().timestamp()),
            context=context or {}
        )

        result = None

        try:
            if self.enable_planning and self.planner:
                # Planning mode: decompose goal into tasks
                result = await self._execute_with_planning(goal, context, execution_mode)
            else:
                # Direct mode: execute goal directly
                result = await self._execute_direct(goal, context)

            # Record history
            self.execution_history.append({
                'goal': goal,
                'result': result,
                'timestamp': datetime.now().isoformat()
            })

            return result

        except Exception as e:
            error_result = {
                'success': False,
                'error': str(e),
                'goal': goal
            }

            if self.verbose:
                print(f"Workflow failed: {e}")

            return error_result

    async def _execute_with_planning(
        self,
        goal: str,
        context: Optional[Dict[str, Any]],
        execution_mode: str
    ) -> Dict[str, Any]:
        """
        Execute workflow with planning phase

        Args:
            goal: Goal to achieve
            context: Optional context
            execution_mode: Execution mode

        Returns:
            Result dictionary
        """
        # Step 1: Plan
        if self.verbose:
            print("Step 1: Planning...")

        plan = await self.planner.plan(goal, context)

        if self.verbose:
            print(f"  Created plan with {len(plan)} tasks")
            for i, task in enumerate(plan):
                print(f"    {i+1}. {task.get('name', 'Unnamed')}")

        # Step 2: Create task graph
        task_graph = TaskGraph()
        task_map = {}  # Maps step numbers to task IDs

        for i, task_def in enumerate(plan):
            task = Task(
                name=task_def.get('name', f'Task {i+1}'),
                description=task_def.get('description', ''),
                priority=task_def.get('priority', 'medium')
            )

            task_graph.add_task(task)
            task_map[i] = task.task_id

        # Resolve dependencies
        for i, task_def in enumerate(plan):
            deps = task_def.get('dependencies', [])
            task_id = task_map[i]

            for dep_step in deps:
                if dep_step in task_map:
                    dep_id = task_map[dep_step]
                    task_graph.add_dependency(task_id, dep_id)

        # Step 3: Execute
        if self.verbose:
            print("\nStep 2: Executing tasks...")

        summary = await self.executor.execute_plan(task_graph, execution_mode)

        # Step 4: Prepare result
        result = {
            'success': summary['failed'] == 0,
            'goal': goal,
            'total_tasks': summary['total'],
            'completed_tasks': summary['completed'],
            'failed_tasks': summary['failed'],
            'errors': summary['errors'],
            'progress': task_graph.get_progress(),
            'stats': task_graph.get_stats()
        }

        if self.verbose:
            print(f"\nExecution complete:")
            print(f"  - Completed: {summary['completed']}/{summary['total']}")
            print(f"  - Failed: {summary['failed']}")
            print(f"  - Progress: {task_graph.get_progress():.1f}%")

        return result

    async def _execute_direct(
        self,
        goal: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute goal directly without planning

        Args:
            goal: Goal to execute
            context: Optional context

        Returns:
            Result dictionary
        """
        if self.verbose:
            print("Executing goal directly...")

        if self.agent:
            # Use agent to execute
            result = await self.agent.run(goal, context=context)

            return {
                'success': result.get('success', True),
                'response': result.get('response', ''),
                'goal': goal
            }
        else:
            return {
                'success': False,
                'error': 'No agent available for execution',
                'goal': goal
            }

    async def execute_with_tools(
        self,
        goal: str,
        tools: Optional[List[Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute workflow with specific tools

        Args:
            goal: Goal to achieve
            tools: List of tools to use
            context: Optional context

        Returns:
            Result dictionary
        """
        # Add file tools if enabled
        if self.enable_file_tools:
            file_tools = create_file_tools(self.file_tool_config)
            if tools is None:
                tools = file_tools
            else:
                tools.extend(file_tools)

        # If agent has tools capability
        if self.agent and hasattr(self.agent, 'tools'):
            # Save original tools
            original_tools = self.agent.tools.copy()

            # Add new tools
            for tool in tools:
                self.agent.add_tool(tool)

            try:
                result = await self.execute(goal, context)
            finally:
                # Restore original tools
                self.agent.tools = original_tools

            return result
        else:
            return await self.execute(goal, context)

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
            print(f"\nRefining workflow based on feedback...")

        # Add feedback to context
        new_context = {
            **(context or {}),
            'feedback': feedback,
            'previous_errors': previous_result.get('errors', []),
            'previous_result': previous_result
        }

        # Retry execution
        return await self.execute(goal, new_context)

    def use_prompt_template(
        self,
        template_name: str,
        **kwargs
    ) -> str:
        """
        Use a prompt template

        Args:
            template_name: Name of the template
            **kwargs: Variables for the template

        Returns:
            Formatted prompt
        """
        template = self.prompt_manager.get_template(template_name)
        if template:
            return template.format(**kwargs)
        else:
            raise ValueError(f"Template '{template_name}' not found")

    def add_prompt_template(
        self,
        name: str,
        template: PromptTemplate,
        category: Optional[str] = None
    ):
        """
        Add a prompt template

        Args:
            name: Template name
            template: PromptTemplate instance
            category: Optional category
        """
        self.prompt_manager.register_template(name, template, category)

    def get_available_prompts(self, category: Optional[str] = None) -> List[str]:
        """
        Get list of available prompt templates

        Args:
            category: Filter by category

        Returns:
            List of template names
        """
        return self.prompt_manager.list_templates(category=category)

    def get_execution_stats(self) -> Dict[str, Any]:
        """
        Get execution statistics

        Returns:
            Statistics dictionary
        """
        return {
            'total_workflows': len(self.execution_history),
            'successful': sum(1 for h in self.execution_history if h.get('result', {}).get('success')),
            'failed': sum(1 for h in self.execution_history if not h.get('result', {}).get('success')),
            'history': self.execution_history
        }


async def create_workflow_engine(
    agent: Any = None,
    enable_file_tools: bool = True,
    file_tool_config: Optional[FileToolConfig] = None,
    verbose: bool = True,
    **kwargs
) -> WorkflowEngine:
    """
    Create and initialize a workflow engine

    Args:
        agent: Agent instance for LLM calls
        enable_file_tools: Whether to enable file system tools
        file_tool_config: Optional file tool configuration
        verbose: Whether to print verbose output
        **kwargs: Additional engine configuration

    Returns:
        Initialized WorkflowEngine
    """
    engine = WorkflowEngine(
        agent=agent,
        enable_file_tools=enable_file_tools,
        file_tool_config=file_tool_config,
        verbose=verbose,
        **kwargs
    )

    await engine.initialize()

    return engine
