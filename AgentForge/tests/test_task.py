"""Tests for TaskManager."""

import pytest
import tempfile
from pathlib import Path

from core.task import TaskManager, Task, TaskStatus


class TestTask:
    """Tests for Task dataclass."""

    def test_task_creation(self):
        """Test creating a task."""
        task = Task(
            id="1",
            subject="Test Task",
            description="A test task description",
        )

        assert task.id == "1"
        assert task.subject == "Test Task"
        assert task.status == TaskStatus.PENDING

    def test_task_to_dict(self):
        """Test converting task to dict."""
        task = Task(
            id="1",
            subject="Test Task",
            description="Description",
            status=TaskStatus.IN_PROGRESS,
        )
        result = task.to_dict()

        assert result["id"] == "1"
        assert result["status"] == "in_progress"

    def test_task_from_dict(self):
        """Test creating task from dict."""
        data = {
            "id": "1",
            "subject": "Test",
            "description": "Desc",
            "status": "completed",
        }
        task = Task.from_dict(data)

        assert task.id == "1"
        assert task.status == TaskStatus.COMPLETED


class TestTaskManager:
    """Tests for TaskManager."""

    def test_create_task(self):
        """Test creating a task."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = TaskManager(storage_path=f"{tmpdir}/tasks.json")
            task_id = manager.create("Test Task", "Description")

            assert task_id is not None
            assert manager.get(task_id) is not None

    def test_start_task(self):
        """Test starting a task."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = TaskManager(storage_path=f"{tmpdir}/tasks.json")
            task_id = manager.create("Test Task", "Description")

            result = manager.start(task_id, owner="agent1")

            assert result is True
            assert manager.get(task_id).status == TaskStatus.IN_PROGRESS

    def test_complete_task(self):
        """Test completing a task."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = TaskManager(storage_path=f"{tmpdir}/tasks.json")
            task_id = manager.create("Test Task", "Description")
            manager.start(task_id)
            manager.complete(task_id)

            assert manager.get(task_id).status == TaskStatus.COMPLETED

    def test_task_dependencies(self):
        """Test task dependencies."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = TaskManager(storage_path=f"{tmpdir}/tasks.json")

            task1_id = manager.create("Task 1", "First task")
            task2_id = manager.create("Task 2", "Second task")

            # Task 2 depends on Task 1
            manager.add_dependency(task2_id, task1_id)

            # Cannot start task 2 until task 1 is complete
            result = manager.start(task2_id)
            assert result is False

            # Complete task 1
            manager.start(task1_id)
            manager.complete(task1_id)

            # Now can start task 2
            result = manager.start(task2_id)
            assert result is True

    def test_claim_task(self):
        """Test claiming a task."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = TaskManager(storage_path=f"{tmpdir}/tasks.json")
            task_id = manager.create("Test Task", "Description")

            result = manager.claim(task_id, "agent1")

            assert result is True
            assert manager.get(task_id).owner == "agent1"

    def test_get_available_tasks(self):
        """Test getting available tasks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = TaskManager(storage_path=f"{tmpdir}/tasks.json")

            task1_id = manager.create("Task 1", "First")
            task2_id = manager.create("Task 2", "Second")
            task3_id = manager.create("Task 3", "Third")

            # Claim task 2
            manager.claim(task2_id, "agent1")

            # Add dependency: task 3 depends on task 1
            manager.add_dependency(task3_id, task1_id)

            available = manager.get_available()

            # Only task 1 should be available (task 2 is claimed, task 3 is blocked)
            assert len(available) == 1
            assert available[0]["id"] == task1_id

    def test_persistence(self):
        """Test task persistence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = f"{tmpdir}/tasks.json"

            # Create and save
            manager1 = TaskManager(storage_path=storage_path)
            task_id = manager1.create("Persisted Task", "Should persist")

            # Load in new manager
            manager2 = TaskManager(storage_path=storage_path)
            task = manager2.get(task_id)

            assert task is not None
            assert task.subject == "Persisted Task"

    def test_list_all(self):
        """Test listing all tasks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = TaskManager(storage_path=f"{tmpdir}/tasks.json")

            manager.create("Task 1", "First")
            manager.create("Task 2", "Second")
            manager.create("Task 3", "Third")

            all_tasks = manager.list_all()

            assert len(all_tasks) == 3

    def test_status_summary(self):
        """Test getting status summary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = TaskManager(storage_path=f"{tmpdir}/tasks.json")

            id1 = manager.create("Task 1", "First")
            id2 = manager.create("Task 2", "Second")
            id3 = manager.create("Task 3", "Third")

            manager.start(id1)
            manager.complete(id2)

            summary = manager.get_status_summary()

            assert summary["pending"] == 1
            assert summary["in_progress"] == 1
            assert summary["completed"] == 1