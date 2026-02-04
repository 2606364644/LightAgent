"""
LightAgent Workflow Module

A comprehensive workflow system for LightAgent, providing:
- Multiple Workflow Types: Planning, Sequential, Interactive, etc.
- Workflow Manager: Manage multiple concurrent workflows
- Enhanced Prompts: Advanced prompt template management
- Planning Tools: Task decomposition and execution

This module extends LightAgent with advanced workflow capabilities
for complex, multi-step tasks.

Setup:
    # Add to Python path or install as editable package
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / "lightagent-workflow"))

Usage:
    from lightagent import Agent
    from lightagent_workflow import WorkflowManager, create_workflow_manager

    # Create agent
    agent = Agent(...)

    # Create workflow manager
    manager = await create_workflow_manager(agent=agent)

    # Create and execute different workflow types
    wf_id = await manager.create_workflow("planning", "Research topic X")
    result = await manager.start_workflow(wf_id, "Research topic X")
"""

from .base import (
    BasePromptTemplate,
    BasePlanner,
    BaseExecutor,
    TaskStatus,
    WorkflowState,
    WorkflowStatus,
    BaseWorkflow,
    WorkflowStep
)

from .manager import (
    WorkflowManager,
    create_workflow_manager
)

from .prompts import (
    PromptTemplate,
    PromptManager,
    get_default_prompts,
    MultiPartPrompt
)

from .planning import (
    Task,
    TaskGraph,
    TaskPriority,
    LLMPlanner,
    SimplePlanner,
    TaskExecutor,
    WorkflowExecutor,
    create_planner,
    create_executor
)

from .engine import (
    WorkflowEngine,
    create_workflow_engine
)

from .types import (
    PlanningWorkflow,
    SequentialWorkflow,
    InteractiveWorkflow,
    CodeExecuteRefineWorkflow,
    HumanInTheLoopWorkflow,
    register_default_workflow_types
)

__all__ = [
    # Base
    'BasePromptTemplate',
    'BasePlanner',
    'BaseExecutor',
    'TaskStatus',
    'WorkflowState',
    'WorkflowStatus',
    'BaseWorkflow',
    'WorkflowStep',

    # Manager
    'WorkflowManager',
    'create_workflow_manager',

    # Prompts
    'PromptTemplate',
    'PromptManager',
    'get_default_prompts',
    'MultiPartPrompt',

    # Planning
    'TaskGraph',
    'Task',
    'TaskPriority',
    'LLMPlanner',
    'SimplePlanner',
    'TaskExecutor',
    'WorkflowExecutor',
    'create_planner',
    'create_executor',

    # Engine (Legacy, kept for backward compatibility)
    'WorkflowEngine',
    'create_workflow_engine',

    # Workflow Types
    'PlanningWorkflow',
    'SequentialWorkflow',
    'InteractiveWorkflow',
    'CodeExecuteRefineWorkflow',
    'HumanInTheLoopWorkflow',
    'register_default_workflow_types',
]

__version__ = '0.2.0'
