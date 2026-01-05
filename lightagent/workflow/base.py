"""
Base classes and interfaces for the workflow module
"""
from typing import Any, Dict, List, Optional, Protocol
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from enum import Enum
import uuid
from datetime import datetime


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BasePromptTemplate(ABC):
    """
    Base class for prompt templates

    Provides interface for creating and managing prompt templates
    with support for variables, formatting, and validation
    """

    @abstractmethod
    def format(self, **kwargs) -> str:
        """
        Format the template with provided variables

        Args:
            **kwargs: Variables to substitute in template

        Returns:
            Formatted prompt string
        """
        pass

    @abstractmethod
    def validate(self, **kwargs) -> bool:
        """
        Validate that all required variables are provided

        Args:
            **kwargs: Variables to validate

        Returns:
            True if valid, False otherwise
        """
        pass

    @abstractmethod
    def get_required_variables(self) -> List[str]:
        """
        Get list of required variable names

        Returns:
            List of variable names
        """
        pass


class BasePlanner(ABC):
    """
    Base class for task planners

    Provides interface for task decomposition, planning,
    and execution strategy
    """

    @abstractmethod
    async def plan(self, goal: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Create a plan for achieving the given goal

        Args:
            goal: The goal to achieve
            context: Optional context information

        Returns:
            List of task steps in the plan
        """
        pass

    @abstractmethod
    async def refine_plan(self, plan: List[Dict[str, Any]], feedback: str) -> List[Dict[str, Any]]:
        """
        Refine an existing plan based on feedback

        Args:
            plan: Current plan
            feedback: Feedback for refinement

        Returns:
            Refined plan
        """
        pass


class BaseExecutor(ABC):
    """
    Base class for task executors

    Provides interface for executing individual tasks
    and tracking their status
    """

    @abstractmethod
    async def execute(self, task: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a single task

        Args:
            task: Task definition
            context: Execution context

        Returns:
            Execution result
        """
        pass

    @abstractmethod
    async def check_status(self, task_id: str) -> TaskStatus:
        """
        Check the status of a task

        Args:
            task_id: Task identifier

        Returns:
            Current task status
        """
        pass


class WorkflowState(BaseModel):
    """
    Workflow execution state
    """
    workflow_id: str
    current_step: int = 0
    total_steps: int = 0
    tasks: List[Dict[str, Any]] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    status: str = TaskStatus.PENDING
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
