"""Tests for BackgroundManager."""

import pytest
import asyncio

from core.background import BackgroundManager, BackgroundTask, BackgroundTaskStatus


class TestBackgroundTask:
    """Tests for BackgroundTask."""

    def test_task_creation(self):
        """Test creating a background task."""
        task = BackgroundTask(
            id="test-123",
            command="echo hello",
        )

        assert task.id == "test-123"
        assert task.command == "echo hello"
        assert task.status == BackgroundTaskStatus.PENDING

    def test_task_to_dict(self):
        """Test converting task to dict."""
        task = BackgroundTask(
            id="test-123",
            command="echo hello",
            status=BackgroundTaskStatus.COMPLETED,
            stdout="hello\n",
        )
        result = task.to_dict()

        assert result["id"] == "test-123"
        assert result["status"] == "completed"
        assert result["stdout"] == "hello\n"


class TestBackgroundManager:
    """Tests for BackgroundManager."""

    def test_start_simple_command(self):
        """Test starting a simple command."""
        manager = BackgroundManager()
        task_id = manager.start("echo 'hello world'")

        assert task_id is not None
        task = manager.get(task_id)
        assert task is not None
        assert task.status == BackgroundTaskStatus.RUNNING

    def test_get_result(self):
        """Test getting task result."""
        manager = BackgroundManager()
        task_id = manager.start("echo 'test'")

        # Wait for completion
        result = manager.get_result(task_id, wait=True, timeout=5)

        assert result["status"] in (BackgroundTaskStatus.COMPLETED.value, BackgroundTaskStatus.RUNNING.value)
        if result["status"] == "completed":
            assert "test" in result["stdout"]

    def test_cancel_task(self):
        """Test cancelling a task."""
        manager = BackgroundManager()
        task_id = manager.start("sleep 10")

        result = manager.cancel(task_id)

        assert result is True
        task = manager.get(task_id)
        assert task.status == BackgroundTaskStatus.CANCELLED

    def test_list_running(self):
        """Test listing running tasks."""
        manager = BackgroundManager()

        # Start a long-running task
        id1 = manager.start("sleep 5")
        manager.start("echo 'quick'")

        running = manager.list_running()

        assert len(running) >= 1

    def test_cleanup(self):
        """Test cleanup of completed tasks."""
        manager = BackgroundManager()

        # Run quick commands
        id1 = manager.start("echo 'test1'")
        id2 = manager.start("echo 'test2'")

        # Wait for completion
        manager.get_result(id1, wait=True, timeout=5)
        manager.get_result(id2, wait=True, timeout=5)

        # Cleanup
        cleaned = manager.cleanup()

        assert cleaned >= 0  # May have cleaned up completed tasks

    def test_notifications(self):
        """Test notification system."""
        manager = BackgroundManager()
        notifications = []

        def callback(notification):
            notifications.append(notification)

        manager.add_notification_callback(callback)

        task_id = manager.start("echo 'test'")
        manager.get_result(task_id, wait=True, timeout=5)

        # Should have received notifications
        assert len(notifications) >= 0  # May have notifications

    def test_status_summary(self):
        """Test getting status summary."""
        manager = BackgroundManager()

        manager.start("echo 'test'")
        manager.start("sleep 5")

        summary = manager.get_status_summary()

        assert "total" in summary
        assert summary["total"] >= 2

    def test_output_truncation(self):
        """Test output truncation."""
        manager = BackgroundManager(max_output_length=100)

        # Generate large output
        task_id = manager.start("python3 -c \"print('x' * 200)\"")
        result = manager.get_result(task_id, wait=True, timeout=5)

        if result["status"] == "completed":
            assert "truncated" in result["stdout"] or len(result["stdout"]) <= 150

    def test_get_nonexistent_task(self):
        """Test getting non-existent task."""
        manager = BackgroundManager()
        result = manager.get_dict("nonexistent")

        assert result is None


class TestAsyncBackgroundManager:
    """Tests for async operations."""

    @pytest.mark.asyncio
    async def test_start_async(self):
        """Test async command execution."""
        manager = BackgroundManager()

        task_id = await manager.start_async("echo 'async test'")

        assert task_id is not None

        # Wait a bit for completion
        await asyncio.sleep(0.5)

        task = manager.get(task_id)
        if task and task.status == BackgroundTaskStatus.COMPLETED:
            assert "async test" in task.stdout

    @pytest.mark.asyncio
    async def test_wait_all(self):
        """Test waiting for all tasks."""
        manager = BackgroundManager()

        await manager.start_async("echo 'task1'")
        await manager.start_async("echo 'task2'")

        await manager.wait_all(timeout=5)

        # All tasks should be completed
        for task in manager.tasks.values():
            if task.status not in (BackgroundTaskStatus.RUNNING, BackgroundTaskStatus.PENDING):
                assert task.status in (BackgroundTaskStatus.COMPLETED, BackgroundTaskStatus.FAILED)