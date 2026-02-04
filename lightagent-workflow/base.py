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
    BLOCKED = "blocked"


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


class WorkflowStatus(str, Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BaseWorkflow(BaseModel):
    """
    Base class for all workflow types

    All workflow types must inherit from this class and implement
    the execute() and validate() methods
    """
    # Core components
    agent: Any = None
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_type: str = "base"
    status: WorkflowStatus = Field(default=WorkflowStatus.PENDING)

    # Configuration
    config: Dict[str, Any] = Field(default_factory=dict)
    verbose: bool = True

    # State
    current_state: Optional[WorkflowState] = None
    execution_history: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        arbitrary_types_allowed = True

    async def execute(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute the workflow

        Args:
            goal: The goal to achieve
            context: Optional execution context

        Returns:
            Workflow execution result
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement execute()")

    async def validate(self, goal: str) -> bool:
        """
        Validate if the goal is suitable for this workflow type

        Args:
            goal: The goal to validate

        Returns:
            True if valid, False otherwise
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement validate()")

    async def pause(self):
        """Pause the workflow execution"""
        if self.status == WorkflowStatus.RUNNING:
            self.status = WorkflowStatus.PAUSED
            self.updated_at = datetime.now()

    async def resume(self):
        """Resume the workflow execution"""
        if self.status == WorkflowStatus.PAUSED:
            self.status = WorkflowStatus.RUNNING
            self.updated_at = datetime.now()

    async def cancel(self):
        """Cancel the workflow execution"""
        if self.status in [WorkflowStatus.PENDING, WorkflowStatus.RUNNING, WorkflowStatus.PAUSED]:
            self.status = WorkflowStatus.CANCELLED
            self.updated_at = datetime.now()

    def get_progress(self) -> float:
        """
        Get workflow progress percentage

        Returns:
            Progress percentage (0-100)
        """
        if self.current_state and self.current_state.total_steps > 0:
            return (self.current_state.current_step / self.current_state.total_steps) * 100
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary"""
        return {
            'workflow_id': self.workflow_id,
            'workflow_type': self.workflow_type,
            'status': self.status.value,
            'progress': self.get_progress(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'config': self.config
        }


class WorkflowStep(BaseModel):
    """
    A single step in a sequential workflow
    """
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    action: Optional[str] = None  # Action to perform
    agent: Optional[Any] = None  # Specific agent for this step
    stop_on_failure: bool = False
    config: Dict[str, Any] = Field(default_factory=dict)

    async def execute(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the step

        Args:
            context: Execution context

        Returns:
            Step execution result
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement execute()")

    class Config:
        arbitrary_types_allowed = True
