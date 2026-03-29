"""Tests for TodoManager."""

import pytest

from core.todo import TodoManager, TodoList, TodoItem, TodoStatus


class TestTodoItem:
    """Tests for TodoItem."""

    def test_todo_item_creation(self):
        """Test creating a todo item."""
        item = TodoItem(id="1", content="Test task")

        assert item.id == "1"
        assert item.content == "Test task"
        assert item.status == TodoStatus.PENDING

    def test_todo_item_to_dict(self):
        """Test converting todo item to dict."""
        item = TodoItem(id="1", content="Test task", status=TodoStatus.IN_PROGRESS)
        result = item.to_dict()

        assert result["id"] == "1"
        assert result["content"] == "Test task"
        assert result["status"] == "in_progress"


class TestTodoList:
    """Tests for TodoList."""

    def test_add_item(self):
        """Test adding an item."""
        todo_list = TodoList()
        item = todo_list.add("Test task")

        assert item is not None
        assert item.content == "Test task"
        assert len(todo_list.items) == 1

    def test_add_item_max_limit(self):
        """Test max item limit."""
        todo_list = TodoList(max_items=3)

        todo_list.add("Task 1")
        todo_list.add("Task 2")
        todo_list.add("Task 3")
        item = todo_list.add("Task 4")

        assert item is None
        assert len(todo_list.items) == 3

    def test_start_item(self):
        """Test starting an item."""
        todo_list = TodoList()
        todo_list.add("Task 1")
        todo_list.add("Task 2")

        result = todo_list.start("1", active_form="Working on Task 1")

        assert result is True
        assert todo_list.get("1").status == TodoStatus.IN_PROGRESS
        assert todo_list.get("1").active_form == "Working on Task 1"

    def test_start_only_one_in_progress(self):
        """Test only one item can be in_progress."""
        todo_list = TodoList()
        todo_list.add("Task 1")
        todo_list.add("Task 2")

        todo_list.start("1")
        todo_list.start("2")

        # Only task 2 should be in_progress
        assert todo_list.get("1").status == TodoStatus.PENDING
        assert todo_list.get("2").status == TodoStatus.IN_PROGRESS

    def test_complete_item(self):
        """Test completing an item."""
        todo_list = TodoList()
        todo_list.add("Task 1")
        todo_list.start("1")
        todo_list.complete("1")

        assert todo_list.get("1").status == TodoStatus.COMPLETED
        assert todo_list.get("1").active_form is None

    def test_remove_item(self):
        """Test removing an item."""
        todo_list = TodoList()
        todo_list.add("Task 1")
        todo_list.add("Task 2")

        result = todo_list.remove("1")

        assert result is True
        assert len(todo_list.items) == 1
        assert todo_list.get("1") is None


class TestTodoManager:
    """Tests for TodoManager."""

    def test_add(self):
        """Test adding a todo."""
        manager = TodoManager()
        todo_id = manager.add("Test task")

        assert todo_id is not None
        assert len(manager.list_all()) == 1

    def test_start(self):
        """Test starting a todo."""
        manager = TodoManager()
        todo_id = manager.add("Test task")

        result = manager.start(todo_id, active_form="Working on it")

        assert result is True
        active = manager.get_active()
        assert active is not None
        assert active["id"] == todo_id

    def test_complete(self):
        """Test completing a todo."""
        manager = TodoManager()
        todo_id = manager.add("Test task")
        manager.start(todo_id)
        manager.complete(todo_id)

        assert manager.get_active() is None
        assert manager.get(todo_id)["status"] == "completed"

    def test_status_summary(self):
        """Test getting status summary."""
        manager = TodoManager()
        manager.add("Task 1")
        todo_id = manager.add("Task 2")
        manager.start(todo_id)

        summary = manager.get_status_summary()

        assert summary["pending"] == 1
        assert summary["in_progress"] == 1
        assert summary["completed"] == 0
        assert summary["total"] == 2

    def test_execute_tool_add(self):
        """Test executing tool action: add."""
        manager = TodoManager()
        result = manager.execute_tool("add", content="New task")

        assert result["success"] is True
        assert "todo_id" in result

    def test_execute_tool_list(self):
        """Test executing tool action: list."""
        manager = TodoManager()
        manager.add("Task 1")
        manager.add("Task 2")

        result = manager.execute_tool("list")

        assert result["success"] is True
        assert len(result["todos"]) == 2
        assert "summary" in result

    def test_execute_tool_unknown(self):
        """Test executing unknown tool action."""
        manager = TodoManager()
        result = manager.execute_tool("unknown")

        assert result["success"] is False
        assert "Unknown action" in result["error"]