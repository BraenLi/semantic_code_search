"""Base Agent abstraction."""

from abc import ABC, abstractmethod
from typing import Any

from agenttest.agent.state import AgentState, State
from agenttest.capabilities.memory.short_term import ShortTermMemory
from agenttest.capabilities.tools.base import BaseTool
from agenttest.core.config import Config
from agenttest.core.llm.base import BaseLLM
from agenttest.core.types import Message, Response


class BaseAgent(ABC):
    """
    Abstract base class for all Agents.

    Provides:
    - State management
    - Memory management
    - Tool registration
    - LLM interaction
    """

    def __init__(
        self,
        llm: BaseLLM,
        config: Config | None = None,
        name: str | None = None,
    ) -> None:
        self.llm = llm
        self.config = config or Config()
        self.name = name or self.__class__.__name__

        # State management
        self.state = AgentState(
            max_iterations=self.config.llm.max_tokens // 100
        )

        # Memory
        self.memory = ShortTermMemory(
            max_messages=self.config.memory.short_term_max_messages
        )

        # Tools
        self._tools: dict[str, BaseTool] = {}

        # System prompt
        self._system_prompt = self._default_system_prompt()

    def _default_system_prompt(self) -> str:
        """Generate default system prompt."""
        return f"""You are {self.name}, an AI assistant.

You are helpful, harmless, and honest. You will assist users with their tasks
by using the tools available to you.

When using tools:
1. Think carefully about which tool to use
2. Provide clear, accurate arguments
3. Interpret results carefully before responding"""

    @property
    def system_prompt(self) -> str:
        """Get the current system prompt."""
        return self._system_prompt

    @system_prompt.setter
    def system_prompt(self, value: str) -> None:
        """Set the system prompt."""
        self._system_prompt = value

    def register_tool(self, tool: BaseTool) -> None:
        """
        Register a tool with the agent.

        Args:
            tool: The tool to register
        """
        self._tools[tool.name] = tool

    def register_tools(self, tools: list[BaseTool]) -> None:
        """
        Register multiple tools.

        Args:
            tools: List of tools to register
        """
        for tool in tools:
            self.register_tool(tool)

    def unregister_tool(self, tool_name: str) -> bool:
        """
        Unregister a tool.

        Args:
            tool_name: Name of the tool to unregister

        Returns:
            True if tool was unregistered, False if not found
        """
        if tool_name in self._tools:
            del self._tools[tool_name]
            return True
        return False

    def get_tools(self) -> list[BaseTool]:
        """Get all registered tools."""
        return list(self._tools.values())

    def get_tool(self, name: str) -> BaseTool | None:
        """Get a tool by name."""
        return self._tools.get(name)

    async def execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> Any:
        """
        Execute a tool with the given arguments.

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments

        Returns:
            The tool execution result

        Raises:
            ValueError: If tool not found
        """
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")

        return await tool.execute(arguments)

    async def chat(self, message: str) -> Response:
        """
        Send a message and get a response.

        Args:
            message: User message

        Returns:
            Agent response
        """
        # Add user message to memory
        self.memory.add(Message.user(message))

        # Get response from LLM
        response = await self._call_llm()

        # Add assistant message to memory
        self.memory.add(response.message)

        return response

    async def _call_llm(
        self,
        tools: list[BaseTool] | None = None,
    ) -> Response:
        """
        Call the LLM with current conversation history.

        Args:
            tools: Optional list of tools to use (defaults to registered tools)

        Returns:
            LLM response
        """
        tools = tools or self.get_tools()

        return await self.llm.chat(
            messages=self.memory.messages,
            tools=[tool.to_tool() for tool in tools] if tools else None,
            system_prompt=self.system_prompt,
        )

    @abstractmethod
    async def run(self, goal: str) -> str:
        """
        Run the agent to achieve a goal.

        Args:
            goal: The goal to achieve

        Returns:
            Final result message
        """
        pass

    def get_status(self) -> dict[str, Any]:
        """Get current agent status."""
        return {
            "name": self.name,
            "state": self.state.to_dict(),
            "memory_size": self.memory.size,
            "tools": [tool.name for tool in self.get_tools()],
        }
