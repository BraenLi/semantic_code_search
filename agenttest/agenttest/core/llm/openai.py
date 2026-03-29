"""OpenAI LLM provider implementation."""

from typing import Any

from agenttest.core.exceptions import LLMException
from agenttest.core.llm.base import BaseLLM
from agenttest.core.types import Message, Response, Tool, ToolCall


class OpenAILLM(BaseLLM):
    """OpenAI LLM provider implementation."""

    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: str | None = None,
        base_url: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        timeout: int = 60,
    ) -> None:
        super().__init__(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )

        # Lazy import to avoid dependency when not using OpenAI
        try:
            from openai import AsyncOpenAI
        except ImportError as e:
            raise LLMException(
                "OpenAI package not installed. Install with: pip install openai"
            ) from e

        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
        )

    async def chat(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        system_prompt: str | None = None,
    ) -> Response:
        """Send a chat request to OpenAI."""
        self._validate_messages(messages)
        messages_with_system = self._prepend_system_prompt(
            messages, system_prompt
        )

        # Convert messages to OpenAI format
        openai_messages = [msg.to_dict() for msg in messages_with_system]

        # Build request parameters
        params: dict[str, Any] = {
            "model": self.model,
            "messages": openai_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        # Add tools if provided
        if tools:
            params["tools"] = [tool.to_dict() for tool in tools]
            params["tool_choice"] = "auto"

        try:
            response = await self._client.chat.completions.create(**params)
        except Exception as e:
            raise LLMException(
                f"OpenAI API request failed: {str(e)}",
                {"original_error": str(e)},
            ) from e

        # Parse response
        choice = response.choices[0]
        content = choice.message.content or ""
        tool_calls = []

        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                import json

                tool_calls.append(
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=json.loads(tc.function.arguments),
                    )
                )

        return Response(
            message=Message(
                role=Message.Role.ASSISTANT,
                content=content,
                tool_calls=tool_calls,
            ),
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
            if response.usage
            else {},
            stop_reason=choice.finish_reason,
        )

    async def chat_stream(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        system_prompt: str | None = None,
    ) -> Any:
        """Send a streaming chat request to OpenAI."""
        self._validate_messages(messages)
        messages_with_system = self._prepend_system_prompt(
            messages, system_prompt
        )

        openai_messages = [msg.to_dict() for msg in messages_with_system]

        params: dict[str, Any] = {
            "model": self.model,
            "messages": openai_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": True,
        }

        if tools:
            params["tools"] = [tool.to_dict() for tool in tools]
            params["tool_choice"] = "auto"

        try:
            stream = await self._client.chat.completions.create(**params)
            async for chunk in stream:
                yield chunk
        except Exception as e:
            raise LLMException(
                f"OpenAI streaming request failed: {str(e)}",
                {"original_error": str(e)},
            ) from e
