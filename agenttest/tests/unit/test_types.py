"""Unit tests for core types."""

import pytest

from agenttest.core.types import Message, Role, Tool, ToolCall, ToolResult


class TestToolCall:
    """Tests for ToolCall class."""

    def test_create_tool_call(self) -> None:
        """Test creating a valid ToolCall."""
        tc = ToolCall(id="1", name="test_tool", arguments={"key": "value"})
        assert tc.id == "1"
        assert tc.name == "test_tool"
        assert tc.arguments == {"key": "value"}

    def test_empty_id_raises_error(self) -> None:
        """Test that empty id raises ValueError."""
        with pytest.raises(ValueError, match="id cannot be empty"):
            ToolCall(id="", name="test", arguments={})

    def test_empty_name_raises_error(self) -> None:
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            ToolCall(id="1", name="", arguments={})


class TestToolResult:
    """Tests for ToolResult class."""

    def test_successful_result(self) -> None:
        """Test creating a successful result."""
        result = ToolResult(tool_call_id="1", success=True, result="output")
        assert result.success is True
        assert result.result == "output"
        assert result.error is None

    def test_failed_result(self) -> None:
        """Test creating a failed result."""
        result = ToolResult(
            tool_call_id="1", success=False, error="Something went wrong"
        )
        assert result.success is False
        assert result.error == "Something went wrong"

    def test_empty_tool_call_id_raises_error(self) -> None:
        """Test that empty tool_call_id raises ValueError."""
        with pytest.raises(ValueError, match="tool_call_id cannot be empty"):
            ToolResult(tool_call_id="", success=True)


class TestMessage:
    """Tests for Message class."""

    def test_create_user_message(self) -> None:
        """Test creating a user message."""
        msg = Message.user("Hello")
        assert msg.role == Role.USER
        assert msg.content == "Hello"
        assert msg.tool_calls == []

    def test_create_assistant_message(self) -> None:
        """Test creating an assistant message."""
        msg = Message.assistant("Hi there")
        assert msg.role == Role.ASSISTANT
        assert msg.content == "Hi there"

    def test_create_system_message(self) -> None:
        """Test creating a system message."""
        msg = Message.system("You are helpful")
        assert msg.role == Role.SYSTEM

    def test_create_tool_message(self) -> None:
        """Test creating a tool message."""
        msg = Message.tool("Result", tool_call_id="1")
        assert msg.role == Role.TOOL
        assert msg.tool_call_id == "1"

    def test_tool_message_without_id_raises_error(self) -> None:
        """Test that tool message without tool_call_id raises error."""
        with pytest.raises(ValueError, match="must have tool_call_id"):
            Message(role=Role.TOOL, content="test")

    def test_to_dict(self) -> None:
        """Test converting message to dictionary."""
        msg = Message.user("Hello")
        d = msg.to_dict()
        assert d["role"] == "user"
        assert d["content"] == "Hello"

    def test_to_dict_with_tool_calls(self) -> None:
        """Test converting message with tool calls to dictionary."""
        tc = ToolCall(id="1", name="test", arguments={})
        msg = Message.assistant(tool_calls=[tc])
        d = msg.to_dict()
        assert "tool_calls" in d
        assert len(d["tool_calls"]) == 1


class TestTool:
    """Tests for Tool class."""

    def test_create_tool(self) -> None:
        """Test creating a tool."""
        tool = Tool(
            name="test",
            description="A test tool",
            parameters={"type": "object"},
        )
        assert tool.name == "test"
        assert tool.description == "A test tool"

    def test_empty_name_raises_error(self) -> None:
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            Tool(name="", description="test", parameters={})

    def test_to_dict(self) -> None:
        """Test converting tool to dictionary."""
        tool = Tool(
            name="test",
            description="A test tool",
            parameters={"type": "object"},
        )
        d = tool.to_dict()
        assert d["type"] == "function"
        assert d["function"]["name"] == "test"


class TestResponse:
    """Tests for Response class."""

    def test_create_response(self) -> None:
        """Test creating a response."""
        msg = Message.assistant("Hello")
        response = Response(message=msg, model="gpt-4o")
        assert response.message == msg
        assert response.model == "gpt-4o"

    def test_has_tool_calls_false(self) -> None:
        """Test has_tool_calls when no tool calls."""
        msg = Message.assistant("Hello")
        response = Response(message=msg, model="gpt-4o")
        assert response.has_tool_calls is False

    def test_has_tool_calls_true(self) -> None:
        """Test has_tool_calls when tool calls present."""
        tc = ToolCall(id="1", name="test", arguments={})
        msg = Message.assistant(tool_calls=[tc])
        response = Response(message=msg, model="gpt-4o")
        assert response.has_tool_calls is True

    def test_content_property(self) -> None:
        """Test content property."""
        msg = Message.assistant("Hello world")
        response = Response(message=msg, model="gpt-4o")
        assert response.content == "Hello world"
