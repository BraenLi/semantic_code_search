"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def sample_messages():
    """Sample messages for testing."""
    from agenttest.core.types import Message

    return [
        Message.user("Hello"),
        Message.assistant("Hi there!"),
        Message.user("How are you?"),
    ]


@pytest.fixture
def sample_tool_call():
    """Sample tool call for testing."""
    from agenttest.core.types import ToolCall

    return ToolCall(
        id="test-123",
        name="test_tool",
        arguments={"key": "value"},
    )
