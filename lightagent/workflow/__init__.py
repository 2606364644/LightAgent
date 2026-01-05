"""
LightAgent Workflow Module

A comprehensive workflow system similar to DeepAgents, providing:
- Enhanced Prompts: Advanced prompt template management
- Planning Tools: Task decomposition and execution
- File System Access: Safe file operations
- Workflow Engine: Complete orchestration

This module integrates with LightAgent's core Agent system to provide
advanced workflow capabilities for complex, multi-step tasks.
"""

from .base import (
    BasePromptTemplate,
    BasePlanner,
    BaseExecutor,
    TaskStatus,
    WorkflowState
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

# Re-export file tools from core tools module for backward compatibility
from lightagent.tools import (
    create_file_tools,
    FileToolConfig,
    SafePathConfig
)

from .engine import (
    WorkflowEngine,
    create_workflow_engine
)

__all__ = [
    # Base
    'BasePromptTemplate',
    'BasePlanner',
    'BaseExecutor',
    'TaskStatus',
    'WorkflowState',

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

    # Tools
    'create_file_tools',
    'FileToolConfig',
    'SafePathConfig',

    # Engine
    'WorkflowEngine',
    'create_workflow_engine',
]


__version__ = '0.1.0'
