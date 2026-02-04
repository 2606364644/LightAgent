"""
Task models and utilities for planning
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

from ..base import TaskStatus


class TaskPriority:
    """Task priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Task(BaseModel):
    """
    Task model for planning and execution tracking
    """

    # Identification
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str

    # Status and priority
    status: str = TaskStatus.PENDING
    priority: str = TaskPriority.MEDIUM

    # Dependencies
    dependencies: List[str] = Field(default_factory=list)
    dependents: List[str] = Field(default_factory=list)

    # Execution data
    result: Optional[Any] = None
    error: Optional[str] = None
    output: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)

    # Timestamps
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    # Execution context
    context: Dict[str, Any] = Field(default_factory=dict)
    agent: Optional[str] = None  # Agent responsible for this task

    class Config:
        arbitrary_types_allowed = True
        use_enum_values = True

    def can_start(self, completed_tasks: List[str]) -> bool:
        """
        Check if task can start based on dependencies

        Args:
            completed_tasks: List of completed task IDs

        Returns:
            True if all dependencies are satisfied
        """
        return all(dep_id in completed_tasks for dep_id in self.dependencies)

    def is_blocked(self, task_statuses: Dict[str, str]) -> bool:
        """
        Check if task is blocked by failed dependencies

        Args:
            task_statuses: Dictionary of task_id -> status

        Returns:
            True if any dependency has failed
        """
        for dep_id in self.dependencies:
            if task_statuses.get(dep_id) == TaskStatus.FAILED:
                return True
        return False

    def mark_started(self):
        """Mark task as started"""
        self.status = TaskStatus.IN_PROGRESS
        self.started_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    def mark_completed(self, result: Any = None, output: str = None):
        """Mark task as completed"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        if result is not None:
            self.result = result
        if output is not None:
            self.output = output

    def mark_failed(self, error: str):
        """Mark task as failed"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.error = error

    def mark_blocked(self):
        """Mark task as blocked"""
        self.status = TaskStatus.BLOCKED
        self.updated_at = datetime.now().isoformat()

    def add_dependency(self, task_id: str):
        """Add a dependency"""
        if task_id not in self.dependencies:
            self.dependencies.append(task_id)
            self.updated_at = datetime.now().isoformat()

    def add_tag(self, tag: str):
        """Add a tag"""
        if tag not in self.tags:
            self.tags.append(tag)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create from dictionary"""
        return cls(**data)


class TaskGraph(BaseModel):
    """
    Graph of tasks with dependencies

    Provides methods for traversing and validating the task graph
    """

    tasks: Dict[str, Task] = Field(default_factory=dict)

    def add_task(self, task: Task):
        """
        Add a task to the graph

        Args:
            task: Task to add
        """
        self.tasks[task.task_id] = task

    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Get a task by ID

        Args:
            task_id: Task ID

        Returns:
            Task or None
        """
        return self.tasks.get(task_id)

    def remove_task(self, task_id: str):
        """
        Remove a task from the graph

        Args:
            task_id: Task ID to remove
        """
        if task_id in self.tasks:
            # Remove from dependencies of other tasks
            for task in self.tasks.values():
                if task_id in task.dependencies:
                    task.dependencies.remove(task_id)
                if task_id in task.dependents:
                    task.dependents.remove(task_id)

            # Remove the task
            del self.tasks[task_id]

    def add_dependency(self, task_id: str, depends_on: str):
        """
        Add a dependency between tasks

        Args:
            task_id: Task that depends
            depends_on: Task that is depended upon
        """
        if task_id in self.tasks and depends_on in self.tasks:
            task = self.tasks[task_id]
            if depends_on not in task.dependencies:
                task.dependencies.append(depends_on)

            dependent_task = self.tasks[depends_on]
            if task_id not in dependent_task.dependents:
                dependent_task.dependents.append(task_id)

    def get_ready_tasks(self) -> List[Task]:
        """
        Get tasks that are ready to execute

        Returns:
            List of tasks with all dependencies satisfied
        """
        completed_tasks = [
            task_id for task_id, task in self.tasks.items()
            if task.status == TaskStatus.COMPLETED
        ]

        ready_tasks = []
        for task in self.tasks.values():
            if task.status == TaskStatus.PENDING and task.can_start(completed_tasks):
                ready_tasks.append(task)

        # Sort by priority
        priority_order = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 3
        }

        ready_tasks.sort(key=lambda t: priority_order.get(t.priority, 999))

        return ready_tasks

    def get_execution_order(self) -> List[List[Task]]:
        """
        Get tasks organized by execution levels

        Returns:
            List of task lists, where each list contains tasks that can be executed in parallel
        """
        levels = []
        remaining_tasks = set(self.tasks.keys())

        while remaining_tasks:
            # Get tasks that can be executed now
            completed_in_previous = []
            for level in levels:
                for task in level:
                    completed_in_previous.append(task.task_id)

            ready_tasks = []
            for task_id in remaining_tasks:
                task = self.tasks[task_id]
                if task.can_start(completed_in_previous):
                    ready_tasks.append(task)

            if not ready_tasks:
                # Circular dependency or no tasks ready
                break

            levels.append(ready_tasks)
            for task in ready_tasks:
                remaining_tasks.remove(task.task_id)

        return levels

    def validate_dependencies(self) -> List[str]:
        """
        Validate task dependencies

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check for circular dependencies
        visited = set()
        rec_stack = set()

        def has_cycle(task_id: str) -> bool:
            visited.add(task_id)
            rec_stack.add(task_id)

            task = self.tasks.get(task_id)
            if task:
                for dep_id in task.dependencies:
                    if dep_id not in visited:
                        if has_cycle(dep_id):
                            return True
                    elif dep_id in rec_stack:
                        return True

            rec_stack.remove(task_id)
            return False

        for task_id in self.tasks:
            if task_id not in visited:
                if has_cycle(task_id):
                    errors.append(f"Circular dependency detected involving task: {task_id}")

        # Check for non-existent dependencies
        for task_id, task in self.tasks.items():
            for dep_id in task.dependencies:
                if dep_id not in self.tasks:
                    errors.append(f"Task {task_id} depends on non-existent task: {dep_id}")

        return errors

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the task graph

        Returns:
            Statistics dictionary
        """
        status_counts = {}
        for task in self.tasks.values():
            status = task.status
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            'total_tasks': len(self.tasks),
            'status_counts': status_counts,
            'completed': status_counts.get(TaskStatus.COMPLETED, 0),
            'failed': status_counts.get(TaskStatus.FAILED, 0),
            'in_progress': status_counts.get(TaskStatus.IN_PROGRESS, 0),
            'pending': status_counts.get(TaskStatus.PENDING, 0),
            'blocked': status_counts.get(TaskStatus.BLOCKED, 0)
        }

    def get_progress(self) -> float:
        """
        Calculate overall progress

        Returns:
            Progress percentage (0-100)
        """
        if not self.tasks:
            return 0.0

        total = len(self.tasks)
        completed = sum(
            1 for task in self.tasks.values()
            if task.status == TaskStatus.COMPLETED
        )

        return (completed / total) * 100
