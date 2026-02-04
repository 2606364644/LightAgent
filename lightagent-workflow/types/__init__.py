"""
Workflow types implementations

This module registers all available workflow types with the WorkflowManager.
"""
from .planning import PlanningWorkflow
from .sequential import SequentialWorkflow
from .interactive import InteractiveWorkflow
from .code_execute import CodeExecuteRefineWorkflow
from .human_loop import HumanInTheLoopWorkflow

__all__ = [
    'PlanningWorkflow',
    'SequentialWorkflow',
    'InteractiveWorkflow',
    'CodeExecuteRefineWorkflow',
    'HumanInTheLoopWorkflow',
    'register_default_workflow_types',
]


def register_default_workflow_types(manager):
    """
    Register all default workflow types with a WorkflowManager

    Args:
        manager: WorkflowManager instance
    """
    manager.register_workflow_type('planning', PlanningWorkflow)
    manager.register_workflow_type('sequential', SequentialWorkflow)
    manager.register_workflow_type('interactive', InteractiveWorkflow)
    manager.register_workflow_type('code_execute_refine', CodeExecuteRefineWorkflow)
    manager.register_workflow_type('human_loop', HumanInTheLoopWorkflow)
