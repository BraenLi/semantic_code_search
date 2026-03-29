"""Short-term memory for conversation history management."""

from collections import deque
from dataclasses import dataclass
from typing import Any

from agenttest.core.types import Message


@dataclass
class MemoryEntry:
    """A single memory entry."""

    message: Message
    timestamp: float
    metadata: dict[str, Any] | None = None


class ShortTermMemory:
    """
    Short-term memory for managing conversation history.

    Uses a deque for efficient O(1) append and pop operations.
    Automatically truncates when max_size is exceeded.
    """

    def __init__(self, max_messages: int = 100) -> None:
        self.max_messages = max_messages
        self._messages: deque[Message] = deque(maxlen=max_messages)

    @property
    def messages(self) -> list[Message]:
        """Get all messages as a list."""
        return list(self._messages)

    @property
    def size(self) -> int:
        """Get current number of stored messages."""
        return len(self._messages)

    @property
    def is_empty(self) -> bool:
        """Check if memory is empty."""
        return len(self._messages) == 0

    @property
    def is_full(self) -> bool:
        """Check if memory has reached max capacity."""
        return len(self._messages) >= self.max_messages

    def add(self, message: Message) -> None:
        """
        Add a message to memory.

        Args:
            message: The message to add
        """
        self._messages.append(message)

    def add_many(self, messages: list[Message]) -> None:
        """
        Add multiple messages to memory.

        Args:
            messages: List of messages to add
        """
        for msg in messages:
            self._messages.append(msg)

    def clear(self) -> None:
        """Clear all messages from memory."""
        self._messages.clear()

    def get_recent(self, n: int) -> list[Message]:
        """
        Get the n most recent messages.

        Args:
            n: Number of messages to retrieve

        Returns:
            List of the n most recent messages
        """
        if n <= 0:
            return []

        messages = list(self._messages)
        return messages[-n:] if n < len(messages) else messages

    def get_by_role(self, role: str) -> list[Message]:
        """
        Get all messages with a specific role.

        Args:
            role: The role to filter by

        Returns:
            List of messages with the specified role
        """
        return [msg for msg in self._messages if msg.role.value == role]

    def get_last_user_message(self) -> Message | None:
        """Get the last user message."""
        for msg in reversed(self._messages):
            if msg.role.value == "user":
                return msg
        return None

    def get_last_assistant_message(self) -> Message | None:
        """Get the last assistant message."""
        for msg in reversed(self._messages):
            if msg.role.value == "assistant":
                return msg
        return None

    def truncate_to_tokens(self, max_tokens: int) -> None:
        """
        Truncate messages to fit within token limit.

        This is a simplified estimation - actual tokenization should be
        done by the LLM provider.

        Args:
            max_tokens: Maximum number of tokens allowed
        """
        # Rough estimation: 1 token ≈ 4 characters
        while self._messages:
            total_chars = sum(len(msg.content) for msg in self._messages)
            if total_chars / 4 <= max_tokens:
                break
            self._messages.popleft()

    def to_dict(self) -> dict[str, Any]:
        """Serialize memory to dictionary."""
        return {
            "max_messages": self.max_messages,
            "current_size": self.size,
            "messages": [msg.to_dict() for msg in self._messages],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ShortTermMemory":
        """Deserialize memory from dictionary."""
        from agenttest.core.types import Message, Role, ToolCall

        memory = cls(max_messages=data.get("max_messages", 100))

        for msg_data in data.get("messages", []):
            tool_calls = []
            for tc_data in msg_data.get("tool_calls", []):
                func = tc_data.get("function", {})
                tool_calls.append(
                    ToolCall(
                        id=tc_data["id"],
                        name=func.get("name", ""),
                        arguments=func.get("arguments", {}),
                    )
                )

            message = Message(
                role=Role(msg_data["role"]),
                content=msg_data["content"],
                tool_calls=tool_calls,
                tool_call_id=msg_data.get("tool_call_id"),
                name=msg_data.get("name"),
            )
            memory.add(message)

        return memory
