"""Agent execution loop implementation."""

import json
from typing import Any

from agenttest.agent.base import BaseAgent
from agenttest.agent.state import State
from agenttest.capabilities.memory.short_term import ShortTermMemory
from agenttest.capabilities.tools.base import BaseTool
from agenttest.core.exceptions import ToolException
from agenttest.core.types import Message, Response, ToolCall, ToolResult


class AgentLoop:
    """
    Manages the agent's execution loop.

    Implements the ReAct (Reason + Act) pattern:
    1. Observe: Get current state and messages
    2. Think: LLM decides next action
    3. Act: Execute tool calls if any
    4. Repeat until goal is achieved
    """

    def __init__(
        self,
        agent: BaseAgent,
        max_iterations: int = 50,
    ) -> None:
        self.agent = agent
        self.max_iterations = max_iterations
        self.agent.state.max_iterations = max_iterations

    async def run(self, goal: str) -> str:
        """
        Run the agent loop to achieve a goal.

        Args:
            goal: The goal to achieve

        Returns:
            Final result message
        """
        # Initialize state
        self.agent.state.start(goal)

        try:
            iteration = 0

            while self.agent.state.is_running:
                iteration += 1
                self.agent.state.iteration_count = iteration

                if iteration > self.max_iterations:
                    self.agent.state.fail(
                        f"Maximum iterations ({self.max_iterations}) exceeded"
                    )
                    break

                # Get LLM response
                response = await self.agent._call_llm()

                # Check for tool calls
                if response.has_tool_calls:
                    # Execute tools and add results to memory
                    await self._process_tool_calls(response.tool_calls)
                else:
                    # No tool calls - agent provided final answer
                    if response.content:
                        self.agent.state.complete()
                        return response.content

            # Should not reach here normally
            return self._get_final_result()

        except Exception as e:
            self.agent.state.fail(str(e))
            raise

    async def _process_tool_calls(self, tool_calls: list[ToolCall]) -> None:
        """
        Process tool calls from LLM response.

        Args:
            tool_calls: List of tool calls to execute
        """
        for tool_call in tool_calls:
            result = await self._execute_single_tool(tool_call)
            self._add_tool_result_to_memory(tool_call, result)

    async def _execute_single_tool(self, tool_call: ToolCall) -> ToolResult:
        """
        Execute a single tool call.

        Args:
            tool_call: The tool call to execute

        Returns:
            Tool execution result
        """
        try:
            tool = self.agent.get_tool(tool_call.name)

            if not tool:
                return ToolResult(
                    tool_call_id=tool_call.id,
                    success=False,
                    error=f"Tool not found: {tool_call.name}",
                )

            # Validate arguments
            is_valid, error = tool.validate_arguments(tool_call.arguments)
            if not is_valid:
                return ToolResult(
                    tool_call_id=tool_call.id,
                    success=False,
                    error=error,
                )

            # Execute tool
            result = await tool.execute(tool_call.arguments)

            return ToolResult(
                tool_call_id=tool_call.id,
                success=True,
                result=result,
            )

        except ToolException as e:
            return ToolResult(
                tool_call_id=tool_call.id,
                success=False,
                error=e.message,
            )

        except Exception as e:
            return ToolResult(
                tool_call_id=tool_call.id,
                success=False,
                error=f"Unexpected error: {str(e)}",
            )

    def _add_tool_result_to_memory(
        self,
        tool_call: ToolCall,
        result: ToolResult,
    ) -> None:
        """
        Add tool result to conversation memory.

        Args:
            tool_call: The original tool call
            result: The execution result
        """
        if result.success:
            content = self._format_result(result.result)
        else:
            content = f"Error: {result.error}"

        self.agent.memory.add(
            Message.tool(
                content=content,
                tool_call_id=tool_call.id,
                name=tool_call.name,
            )
        )

    def _format_result(self, result: Any) -> str:
        """
        Format tool result as string.

        Args:
            result: The result to format

        Returns:
            Formatted string
        """
        if result is None:
            return "Tool executed successfully (no output)"

        if isinstance(result, (dict, list)):
            return json.dumps(result, indent=2, default=str)

        return str(result)

    def _get_final_result(self) -> str:
        """Get final result based on agent state."""
        if self.agent.state.has_error:
            return f"Agent failed: {self.agent.state.error}"

        if self.agent.state.is_completed:
            return "Goal achieved"

        return "Agent stopped"

    def pause(self) -> None:
        """Pause the agent loop."""
        self.agent.state.pause()

    def resume(self) -> None:
        """Resume the agent loop."""
        self.agent.state.resume()

    def stop(self) -> None:
        """Stop the agent loop."""
        self.agent.state.complete()
