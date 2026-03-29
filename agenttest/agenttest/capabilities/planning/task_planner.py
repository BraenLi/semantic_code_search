"""Task planner for breaking down complex tasks."""

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from agenttest.core.exceptions import PlanningException


class TaskStatus(str, Enum):
    """Status of a task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Task:
    """Represents a single task or subtask."""

    id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    parent_id: str | None = None
    subtasks: list[str] = field(default_factory=list)
    result: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert task to dictionary."""
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status.value,
            "parent_id": self.parent_id,
            "subtasks": self.subtasks,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Task":
        """Create task from dictionary."""
        return cls(
            id=data["id"],
            description=data["description"],
            status=TaskStatus(data.get("status", "pending")),
            parent_id=data.get("parent_id"),
            subtasks=data.get("subtasks", []),
            result=data.get("result"),
            error=data.get("error"),
            metadata=data.get("metadata", {}),
        )


class TaskPlanner:
    """
    Task planner for breaking down complex tasks into subtasks.

    Uses a hierarchical task structure where tasks can have subtasks.
    """

    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}
        self._root_tasks: list[str] = []

    def create_task(
        self,
        description: str,
        parent_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Create a new task.

        Args:
            description: Task description
            parent_id: Optional parent task ID
            metadata: Optional metadata

        Returns:
            The created task ID
        """
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            description=description,
            parent_id=parent_id,
            metadata=metadata or {},
        )

        self._tasks[task_id] = task

        if parent_id:
            if parent_id not in self._tasks:
                raise PlanningException(f"Parent task not found: {parent_id}")
            self._tasks[parent_id].subtasks.append(task_id)
        else:
            self._root_tasks.append(task_id)

        return task_id

    def create_plan(
        self,
        goal: str,
        steps: list[str],
    ) -> str:
        """
        Create a plan from a goal and list of steps.

        Args:
            goal: The overall goal
            steps: List of steps to achieve the goal

        Returns:
            The root task ID
        """
        root_id = self.create_task(
            description=goal,
            metadata={"type": "goal"},
        )

        for step in steps:
            self.create_task(
                description=step,
                parent_id=root_id,
                metadata={"type": "step"},
            )

        return root_id

    def get_task(self, task_id: str) -> Task | None:
        """Get a task by ID."""
        return self._tasks.get(task_id)

    def update_status(
        self,
        task_id: str,
        status: TaskStatus,
        result: str | None = None,
        error: str | None = None,
    ) -> bool:
        """
        Update task status.

        Args:
            task_id: The task ID to update
            status: New status
            result: Optional result message
            error: Optional error message

        Returns:
            True if task was updated, False if not found
        """
        task = self._tasks.get(task_id)
        if not task:
            return False

        task.status = status
        if result:
            task.result = result
        if error:
            task.error = error

        return True

    def get_next_pending_task(self) -> Task | None:
        """
        Get the next pending task (depth-first).

        Returns:
            The next pending task, or None if all tasks are completed
        """
        for root_id in self._root_tasks:
            task = self._find_pending_depth_first(root_id)
            if task:
                return task
        return None

    def _find_pending_depth_first(self, task_id: str) -> Task | None:
        """Find pending task using depth-first search."""
        task = self._tasks.get(task_id)
        if not task:
            return None

        # If task is pending and has no subtasks, return it
        if task.status == TaskStatus.PENDING and not task.subtasks:
            return task

        # Recursively check subtasks
        for subtask_id in task.subtasks:
            result = self._find_pending_depth_first(subtask_id)
            if result:
                return result

        return None

    def get_all_tasks(self) -> list[Task]:
        """Get all tasks."""
        return list(self._tasks.values())

    def get_root_tasks(self) -> list[Task]:
        """Get all root tasks."""
        return [
            self._tasks[task_id] for task_id in self._root_tasks if task_id in self._tasks
        ]

    def get_subtasks(self, task_id: str) -> list[Task]:
        """Get all subtasks of a task."""
        task = self._tasks.get(task_id)
        if not task:
            return []
        return [
            self._tasks[subtask_id]
            for subtask_id in task.subtasks
            if subtask_id in self._tasks
        ]

    def get_progress(self) -> dict[str, Any]:
        """Get overall progress of all tasks."""
        total = len(self._tasks)
        if total == 0:
            return {
                "total": 0,
                "completed": 0,
                "in_progress": 0,
                "pending": 0,
                "failed": 0,
                "percentage": 0,
            }

        status_counts = {status: 0 for status in TaskStatus}
        for task in self._tasks.values():
            status_counts[task.status] += 1

        completed = status_counts[TaskStatus.COMPLETED]

        return {
            "total": total,
            "completed": completed,
            "in_progress": status_counts[TaskStatus.IN_PROGRESS],
            "pending": status_counts[TaskStatus.PENDING],
            "failed": status_counts[TaskStatus.FAILED],
            "percentage": (completed / total) * 100,
        }

    def clear(self) -> None:
        """Clear all tasks."""
        self._tasks.clear()
        self._root_tasks.clear()

    def to_dict(self) -> dict[str, Any]:
        """Serialize planner state to dictionary."""
        return {
            "tasks": {
                task_id: task.to_dict()
                for task_id, task in self._tasks.items()
            },
            "root_tasks": self._root_tasks,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskPlanner":
        """Deserialize planner state from dictionary."""
        planner = cls()
        planner._root_tasks = data.get("root_tasks", [])

        for task_id, task_data in data.get("tasks", {}).items():
            planner._tasks[task_id] = Task.from_dict(task_data)

        return planner
