"""Unit tests for task planner."""

import pytest

from agenttest.capabilities.planning.task_planner import (
    TaskPlanner,
    Task,
    TaskStatus,
)


class TestTask:
    """Tests for Task class."""

    def test_create_task(self) -> None:
        """Test creating a task."""
        task = Task(id="1", description="Do something")
        assert task.description == "Do something"
        assert task.status == TaskStatus.PENDING
        assert task.parent_id is None

    def test_task_to_dict(self) -> None:
        """Test serializing task to dictionary."""
        task = Task(id="1", description="Test")
        d = task.to_dict()
        assert d["id"] == "1"
        assert d["description"] == "Test"
        assert d["status"] == "pending"

    def test_task_from_dict(self) -> None:
        """Test deserializing task from dictionary."""
        data = {
            "id": "1",
            "description": "Test task",
            "status": "in_progress",
            "parent_id": None,
        }
        task = Task.from_dict(data)
        assert task.id == "1"
        assert task.description == "Test task"
        assert task.status == TaskStatus.IN_PROGRESS


class TestTaskPlanner:
    """Tests for TaskPlanner class."""

    def test_create_task(self) -> None:
        """Test creating a task."""
        planner = TaskPlanner()
        task_id = planner.create_task("Test task")
        assert task_id is not None

        task = planner.get_task(task_id)
        assert task is not None
        assert task.description == "Test task"

    def test_create_subtask(self) -> None:
        """Test creating a subtask."""
        planner = TaskPlanner()
        parent_id = planner.create_task("Parent")
        child_id = planner.create_task("Child", parent_id=parent_id)

        parent = planner.get_task(parent_id)
        assert parent is not None
        assert child_id in parent.subtasks

        child = planner.get_task(child_id)
        assert child is not None
        assert child.parent_id == parent_id

    def test_create_subtask_with_invalid_parent(self) -> None:
        """Test that creating subtask with invalid parent raises error."""
        planner = TaskPlanner()
        with pytest.raises(Exception, match="Parent task not found"):
            planner.create_task("Child", parent_id="nonexistent")

    def test_create_plan(self) -> None:
        """Test creating a plan from goal and steps."""
        planner = TaskPlanner()
        root_id = planner.create_plan(
            goal="Build a house",
            steps=["Lay foundation", "Build walls", "Add roof"],
        )

        root = planner.get_task(root_id)
        assert root is not None
        assert root.description == "Build a house"
        assert len(root.subtasks) == 3

    def test_update_status(self) -> None:
        """Test updating task status."""
        planner = TaskPlanner()
        task_id = planner.create_task("Test")

        planner.update_status(task_id, TaskStatus.IN_PROGRESS)
        task = planner.get_task(task_id)
        assert task is not None
        assert task.status == TaskStatus.IN_PROGRESS

        planner.update_status(
            task_id, TaskStatus.COMPLETED, result="Done!"
        )
        task = planner.get_task(task_id)
        assert task is not None
        assert task.status == TaskStatus.COMPLETED
        assert task.result == "Done!"

    def test_update_nonexistent_task(self) -> None:
        """Test that updating nonexistent task returns False."""
        planner = TaskPlanner()
        result = planner.update_status("nonexistent", TaskStatus.COMPLETED)
        assert result is False

    def test_get_next_pending_task(self) -> None:
        """Test getting next pending task."""
        planner = TaskPlanner()
        root_id = planner.create_plan(
            goal="Goal",
            steps=["Step 1", "Step 2"],
        )

        next_task = planner.get_next_pending_task()
        assert next_task is not None
        assert next_task.description == "Step 1"

    def test_get_next_pending_task_all_completed(self) -> None:
        """Test getting next task when all are completed."""
        planner = TaskPlanner()
        task_id = planner.create_task("Test")
        planner.update_status(task_id, TaskStatus.COMPLETED)

        next_task = planner.get_next_pending_task()
        assert next_task is None

    def test_get_progress(self) -> None:
        """Test getting progress."""
        planner = TaskPlanner()
        planner.create_plan(
            goal="Goal",
            steps=["Step 1", "Step 2", "Step 3"],
        )

        # Initially all pending
        progress = planner.get_progress()
        assert progress["total"] == 4  # root + 3 steps
        assert progress["pending"] == 4
        assert progress["percentage"] == 0

        # Complete one task
        next_task = planner.get_next_pending_task()
        if next_task:
            planner.update_status(next_task.id, TaskStatus.COMPLETED)

        progress = planner.get_progress()
        assert progress["completed"] == 1

    def test_clear(self) -> None:
        """Test clearing all tasks."""
        planner = TaskPlanner()
        planner.create_plan(goal="Goal", steps=["Step 1", "Step 2"])
        planner.clear()

        assert len(planner.get_all_tasks()) == 0
        assert len(planner.get_root_tasks()) == 0

    def test_to_dict(self) -> None:
        """Test serializing planner to dictionary."""
        planner = TaskPlanner()
        planner.create_task("Test")
        d = planner.to_dict()
        assert "tasks" in d
        assert "root_tasks" in d

    def test_from_dict(self) -> None:
        """Test deserializing planner from dictionary."""
        data = {
            "tasks": {
                "1": {
                    "id": "1",
                    "description": "Test",
                    "status": "pending",
                    "subtasks": [],
                }
            },
            "root_tasks": ["1"],
        }
        planner = TaskPlanner.from_dict(data)
        assert len(planner.get_all_tasks()) == 1
