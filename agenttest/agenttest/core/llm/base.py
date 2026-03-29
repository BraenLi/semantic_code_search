"""Base LLM provider abstraction."""

from abc import ABC, abstractmethod
from typing import Any

from agenttest.core.types import Message, Response, Tool


class BaseLLM(ABC):
    """Abstract base class for LLM providers."""

    def __init__(
        self,
        model: str,
        api_key: str | None = None,
        base_url: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        timeout: int = 60,
    ) -> None:
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        system_prompt: str | None = None,
    ) -> Response:
        """
        Send a chat request to the LLM.

        Args:
            messages: List of conversation messages
            tools: Optional list of available tools
            system_prompt: Optional system prompt to prepend

        Returns:
            Response from the LLM
        """
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        system_prompt: str | None = None,
    ) -> Any:
        """
        Send a streaming chat request to the LLM.

        Args:
            messages: List of conversation messages
            tools: Optional list of available tools
            system_prompt: Optional system prompt to prepend

        Yields:
            Chunks of the response
        """
        pass

    def _prepend_system_prompt(
        self,
        messages: list[Message],
        system_prompt: str | None,
    ) -> list[Message]:
        """Prepend system prompt to messages if provided."""
        if not system_prompt:
            return messages

        # Check if there's already a system message
        if messages and messages[0].role.value == "system":
            # Prepend to existing system message
            existing = messages[0]
            new_system = Message.system(
                f"{system_prompt}\n\n{existing.content}"
            )
            return [new_system] + messages[1:]

        return [Message.system(system_prompt)] + messages

    def _validate_messages(self, messages: list[Message]) -> None:
        """Validate that messages are properly formatted."""
        if not messages:
            raise ValueError("Messages list cannot be empty")

        for i, msg in enumerate(messages):
            if not isinstance(msg, Message):
                raise ValueError(f"Message {i} is not a Message instance")

            if msg.role.value == "tool" and not msg.tool_call_id:
                raise ValueError(
                    f"Tool message at index {i} must have tool_call_id"
                )
