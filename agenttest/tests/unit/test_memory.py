"""Unit tests for short-term memory."""

import pytest

from agenttest.capabilities.memory.short_term import ShortTermMemory
from agenttest.core.types import Message, Role


class TestShortTermMemory:
    """Tests for ShortTermMemory class."""

    def test_initial_state(self) -> None:
        """Test initial memory state."""
        memory = ShortTermMemory(max_messages=10)
        assert memory.is_empty is True
        assert memory.size == 0
        assert memory.is_full is False

    def test_add_message(self) -> None:
        """Test adding a message."""
        memory = ShortTermMemory()
        msg = Message.user("Hello")
        memory.add(msg)
        assert memory.size == 1
        assert memory.is_empty is False

    def test_add_many_messages(self) -> None:
        """Test adding multiple messages."""
        memory = ShortTermMemory()
        messages = [
            Message.user("Hello"),
            Message.assistant("Hi"),
            Message.user("How are you?"),
        ]
        memory.add_many(messages)
        assert memory.size == 3

    def test_max_capacity(self) -> None:
        """Test that memory respects max capacity."""
        memory = ShortTermMemory(max_messages=3)
        for i in range(5):
            memory.add(Message.user(f"Message {i}"))
        assert memory.size == 3
        # Oldest messages should be removed
        assert memory.messages[0].content == "Message 2"

    def test_get_recent(self) -> None:
        """Test getting recent messages."""
        memory = ShortTermMemory()
        for i in range(5):
            memory.add(Message.user(f"Message {i}"))

        recent = memory.get_recent(2)
        assert len(recent) == 2
        assert recent[0].content == "Message 3"
        assert recent[1].content == "Message 4"

    def test_get_recent_more_than_available(self) -> None:
        """Test getting more messages than available."""
        memory = ShortTermMemory()
        memory.add(Message.user("Only one"))

        recent = memory.get_recent(10)
        assert len(recent) == 1

    def test_get_by_role(self) -> None:
        """Test filtering messages by role."""
        memory = ShortTermMemory()
        memory.add(Message.user("Hello"))
        memory.add(Message.assistant("Hi"))
        memory.add(Message.user("How are you?"))

        user_msgs = memory.get_by_role("user")
        assert len(user_msgs) == 2

        assistant_msgs = memory.get_by_role("assistant")
        assert len(assistant_msgs) == 1

    def test_get_last_user_message(self) -> None:
        """Test getting last user message."""
        memory = ShortTermMemory()
        memory.add(Message.user("First"))
        memory.add(Message.assistant("Response"))
        memory.add(Message.user("Second"))

        last_user = memory.get_last_user_message()
        assert last_user is not None
        assert last_user.content == "Second"

    def test_get_last_assistant_message(self) -> None:
        """Test getting last assistant message."""
        memory = ShortTermMemory()
        memory.add(Message.user("First"))
        memory.add(Message.assistant("Response"))
        memory.add(Message.user("Second"))

        last_assistant = memory.get_last_assistant_message()
        assert last_assistant is not None
        assert last_assistant.content == "Response"

    def test_clear(self) -> None:
        """Test clearing memory."""
        memory = ShortTermMemory()
        memory.add(Message.user("Hello"))
        memory.clear()
        assert memory.is_empty is True
        assert memory.size == 0

    def test_to_dict(self) -> None:
        """Test serializing memory to dictionary."""
        memory = ShortTermMemory(max_messages=10)
        memory.add(Message.user("Hello"))
        d = memory.to_dict()
        assert d["max_messages"] == 10
        assert d["current_size"] == 1
        assert len(d["messages"]) == 1

    def test_from_dict(self) -> None:
        """Test deserializing memory from dictionary."""
        data = {
            "max_messages": 5,
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi"},
            ],
        }
        memory = ShortTermMemory.from_dict(data)
        assert memory.size == 2
        assert memory.messages[0].content == "Hello"
        assert memory.messages[1].content == "Hi"
