"""Core type definitions for the Agent system."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Awaitable


class Role(str, Enum):
    """Message role enumeration."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class ToolCall:
    """Represents a tool call request from the LLM."""

    id: str
    name: str
    arguments: dict[str, Any]

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("ToolCall id cannot be empty")
        if not self.name:
            raise ValueError("ToolCall name cannot be empty")


@dataclass
class ToolResult:
    """Represents the result of a tool execution."""

    tool_call_id: str
    success: bool
    result: Any | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        if not self.tool_call_id:
            raise ValueError("ToolResult tool_call_id cannot be empty")
        if self.success and self.result is None:
            self.result = "Tool executed successfully (no output)"
        if not self.success and not self.error:
            self.error = "Unknown error occurred"


@dataclass
class Message:
    """Represents a message in the conversation."""

    role: Role
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_call_id: str | None = None
    name: str | None = None

    def __post_init__(self) -> None:
        if self.role == Role.TOOL and not self.tool_call_id:
            raise ValueError("Tool message must have tool_call_id")

    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary format."""
        result: dict[str, Any] = {
            "role": self.role.value,
            "content": self.content,
        }
        if self.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": tc.arguments,
                    }
                }
                for tc in self.tool_calls
            ]
        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id
        if self.name:
            result["name"] = self.name
        return result

    @classmethod
    def system(cls, content: str) -> "Message":
        """Create a system message."""
        return cls(role=Role.SYSTEM, content=content)

    @classmethod
    def user(cls, content: str) -> "Message":
        """Create a user message."""
        return cls(role=Role.USER, content=content)

    @classmethod
    def assistant(
        cls,
        content: str = "",
        tool_calls: list[ToolCall] | None = None
    ) -> "Message":
        """Create an assistant message."""
        return cls(
            role=Role.ASSISTANT,
            content=content,
            tool_calls=tool_calls or []
        )

    @classmethod
    def tool(
        cls,
        content: str,
        tool_call_id: str,
        name: str | None = None
    ) -> "Message":
        """Create a tool result message."""
        return cls(
            role=Role.TOOL,
            content=content,
            tool_call_id=tool_call_id,
            name=name
        )


@dataclass
class Tool:
    """Represents a tool definition for the LLM."""

    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[[dict[str, Any]], Awaitable[Any]] | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Tool name cannot be empty")
        if not self.description:
            raise ValueError("Tool description cannot be empty")

    def to_dict(self) -> dict[str, Any]:
        """Convert tool to dictionary format for LLM API."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            }
        }


@dataclass
class Response:
    """Represents a response from the LLM."""

    message: Message
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    stop_reason: str | None = None

    @property
    def has_tool_calls(self) -> bool:
        """Check if response contains tool calls."""
        return len(self.message.tool_calls) > 0

    @property
    def tool_calls(self) -> list[ToolCall]:
        """Get tool calls from the response."""
        return self.message.tool_calls

    @property
    def content(self) -> str:
        """Get text content from the response."""
        return self.message.content
