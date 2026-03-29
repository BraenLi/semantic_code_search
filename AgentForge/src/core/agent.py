"""Agent 基类 - 核心 loop 实现。

核心设计原则:
1. Agent 是模型，不是框架 - 代码只是提供 harness
2. 简单循环模式 - while stop_reason == "tool_calls"
3. 工具执行结果反馈给模型
"""

import json
from typing import Any, Callable

from openai import OpenAI

from .models.config import ModelConfig
from .models.client import get_client
from .tools.registry import ToolRegistry


# Callback types
OnToolCallCallback = Callable[[str, dict, Any], None]
OnResponseCallback = Callable[[str], None]


class Agent:
    """Agent 基类 - 核心 loop 实现。

    核心循环模式:
    1. 发送用户消息到模型
    2. 如果返回 tool_calls，执行工具并反馈结果
    3. 重复直到模型返回最终响应

    Attributes:
        model_name: 模型名称
        client: OpenAI SDK client
        tools: 工具列表 (OpenAI tool format)
        tool_registry: ToolRegistry 实例
        system_prompt: 系统提示词
        messages: 消息历史
        logger: LocalLogger 实例
    """

    def __init__(
        self,
        model_name: str | None = None,
        tools: list[dict] | None = None,
        tool_registry: ToolRegistry | None = None,
        system_prompt: str = "",
        config: ModelConfig | None = None,
        max_tokens: int = 8000,
        logger: Any = None,
    ):
        """初始化 Agent。

        Args:
            model_name: 模型名称，None 时使用配置中的默认模型
            tools: 工具列表 (OpenAI tool format)
            tool_registry: ToolRegistry 实例，用于工具查找和执行
            system_prompt: 系统提示词
            config: ModelConfig 实例，None 时自动创建
            max_tokens: 最大 token 数
            logger: LocalLogger 实例
        """
        self.model_name = model_name
        self.client: OpenAI = get_client(model_name, config)
        self.tool_registry = tool_registry
        self.tools = tools or []
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        self.logger = logger
        self.messages: list[dict[str, Any]] = []

        # Callbacks
        self._on_tool_call: OnToolCallCallback | None = None
        self._on_response: OnResponseCallback | None = None

        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})

        # If tool_registry is provided, sync tools from it
        if self.tool_registry:
            self._sync_tools_from_registry()

    def _sync_tools_from_registry(self) -> None:
        """Sync tool definitions from ToolRegistry."""
        if self.tool_registry:
            registry_tools = self.tool_registry.get_openai_tools()
            # Merge with existing tools (registry tools take precedence)
            existing_names = {t.get("function", {}).get("name") for t in self.tools if t.get("type") == "function"}
            for tool in registry_tools:
                tool_name = tool.get("function", {}).get("name")
                if tool_name and tool_name not in existing_names:
                    self.tools.append(tool)

    def set_callbacks(
        self,
        on_tool_call: OnToolCallCallback | None = None,
        on_response: OnResponseCallback | None = None,
    ) -> None:
        """Set callback functions for tool calls and responses.

        Args:
            on_tool_call: Callback for tool calls (tool_name, args, result)
            on_response: Callback for final responses
        """
        self._on_tool_call = on_tool_call
        self._on_response = on_response

    def run(self, query: str, stream: bool = False) -> str:
        """执行 agent loop。

        Args:
            query: 用户查询
            stream: 是否流式输出

        Returns:
            模型最终响应内容
        """
        self.messages.append({"role": "user", "content": query})

        if self.logger:
            self.logger.log_message("user", query)

        while True:
            response = self._call_model(stream=stream)

            if stream:
                # Handle streaming response
                content_chunks = []
                tool_calls_data = []
                for chunk in response:
                    delta = chunk.choices[0].delta

                    if delta.content:
                        content_chunks.append(delta.content)
                        if self._on_response:
                            self._on_response(delta.content)

                    # Collect tool calls from stream
                    if hasattr(delta, "tool_calls") and delta.tool_calls:
                        for tc in delta.tool_calls:
                            idx = tc.index
                            while len(tool_calls_data) <= idx:
                                tool_calls_data.append({"id": "", "name": "", "arguments": ""})
                            if tc.id:
                                tool_calls_data[idx]["id"] = tc.id
                            if tc.function:
                                if tc.function.name:
                                    tool_calls_data[idx]["name"] = tc.function.name
                                if tc.function.arguments:
                                    tool_calls_data[idx]["arguments"] += tc.function.arguments

                message_content = "".join(content_chunks)
                self.messages.append({"role": "assistant", "content": message_content or ""})

                # Check if we have tool calls
                finish_reason = chunk.choices[0].finish_reason if "chunk" in dir() else None
                if tool_calls_data and finish_reason == "tool_calls":
                    # Build tool_calls object for execution
                    from types import SimpleNamespace
                    tool_calls = []
                    for tc in tool_calls_data:
                        tool_calls.append(SimpleNamespace(
                            id=tc["id"],
                            function=SimpleNamespace(
                                name=tc["name"],
                                arguments=tc["arguments"]
                            )
                        ))
                    tool_results = self._execute_tools(tool_calls)
                    self.messages.append({"role": "user", "content": tool_results})
                    continue

                return message_content
            else:
                message = response.choices[0].message
                self.messages.append({"role": "assistant", "content": message.content or ""})

                if self.logger:
                    self.logger.log_message("assistant", message.content or "")

                # 检查是否需要工具调用
                if response.choices[0].finish_reason != "tool_calls":
                    if self._on_response:
                        self._on_response(message.content or "")
                    return message.content or ""

                # 执行工具调用
                tool_results = self._execute_tools(message.tool_calls)
                self.messages.append({"role": "user", "content": tool_results})

    def _call_model(self, stream: bool = False) -> Any:
        """调用模型 API。

        Args:
            stream: 是否流式输出

        Returns:
            模型响应
        """
        return self.client.chat.completions.create(
            model=self.model_name or "",
            messages=self.messages,
            tools=self.tools if self.tools else None,
            max_tokens=self.max_tokens,
            stream=stream,
        )

    def _execute_tools(self, tool_calls: list) -> str:
        """执行工具调用。

        Args:
            tool_calls: 工具调用列表

        Returns:
            工具执行结果 (JSON 格式)
        """
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            call_id = tool_call.id

            # 查找并执行工具
            result = self._find_and_execute_tool(tool_name, tool_args)

            # Callback
            if self._on_tool_call:
                self._on_tool_call(tool_name, tool_args, result)

            # Logger
            if self.logger:
                self.logger.log_tool_call(tool_name, tool_args, result)

            results.append({
                "tool_call_id": call_id,
                "role": "tool",
                "name": tool_name,
                "content": json.dumps(result, ensure_ascii=False),
            })

        return json.dumps(results, ensure_ascii=False)

    def _find_and_execute_tool(self, name: str, args: dict) -> Any:
        """查找并执行工具。

        Args:
            name: 工具名称
            args: 工具参数

        Returns:
            工具执行结果
        """
        # First, try to use ToolRegistry if available
        if self.tool_registry:
            try:
                return self.tool_registry.execute(name, **args)
            except KeyError:
                pass  # Fall through to custom tool handling

        # Subclasses can override this method to register custom tools
        raise ValueError(f"Unknown tool: {name}")

    def register_tool(self, tool: Any) -> None:
        """Register a tool instance.

        If a ToolRegistry is available, registers to it.
        Otherwise, adds to the tools list.

        Args:
            tool: Tool instance with to_openai_tool() method
        """
        if self.tool_registry:
            self.tool_registry.register(tool)
            self._sync_tools_from_registry()
        else:
            if hasattr(tool, "to_openai_tool"):
                self.tools.append(tool.to_openai_tool())
            else:
                self.tools.append(tool)

    def reset(self) -> None:
        """重置消息历史。"""
        self.messages = []
        if self.system_prompt:
            self.messages.append({"role": "system", "content": self.system_prompt})

    def add_tool(self, tool: dict) -> None:
        """添加工具。

        Args:
            tool: 工具定义 (OpenAI tool format)
        """
        self.tools.append(tool)

    def clear_tools(self) -> None:
        """清空所有工具。"""
        self.tools = []
        if self.tool_registry:
            self.tool_registry.clear()
