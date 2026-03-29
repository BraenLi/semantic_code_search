"""Tests for Agent class."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from core.agent import Agent
from core.tools.registry import ToolRegistry
from core.tools.base import BaseTool


class SimpleTool(BaseTool):
    """Simple test tool."""

    name = "test_tool"
    description = "A test tool"

    def execute(self, value: str = "") -> dict:
        return {"result": f"processed: {value}"}


class TestAgent:
    """Tests for Agent class."""

    def test_agent_initialization(self):
        """Test agent initialization."""
        agent = Agent(
            model_name="test-model",
            system_prompt="You are a helpful assistant.",
        )

        assert agent.model_name == "test-model"
        assert agent.system_prompt == "You are a helpful assistant."
        assert len(agent.messages) == 1
        assert agent.messages[0]["role"] == "system"

    def test_agent_with_tools(self):
        """Test agent with tools."""
        tools = [{"type": "function", "function": {"name": "test", "parameters": {}}}]
        agent = Agent(model_name="test-model", tools=tools)

        assert len(agent.tools) == 1

    def test_agent_with_tool_registry(self):
        """Test agent with ToolRegistry."""
        registry = ToolRegistry()
        registry.register(SimpleTool())

        agent = Agent(model_name="test-model", tool_registry=registry)

        assert agent.tool_registry is registry
        # Tool definitions should be synced
        assert len(agent.tools) >= 1

    def test_agent_add_message(self):
        """Test adding messages."""
        agent = Agent(model_name="test-model")
        agent.messages.append({"role": "user", "content": "Hello"})

        assert len(agent.messages) == 1
        assert agent.messages[0]["content"] == "Hello"

    def test_agent_reset(self):
        """Test resetting messages."""
        agent = Agent(
            model_name="test-model",
            system_prompt="System prompt",
        )
        agent.messages.append({"role": "user", "content": "Hello"})

        agent.reset()

        assert len(agent.messages) == 1
        assert agent.messages[0]["role"] == "system"

    def test_agent_register_tool(self):
        """Test registering a tool."""
        agent = Agent(model_name="test-model")
        tool = SimpleTool()

        agent.register_tool(tool)

        assert len(agent.tools) == 1

    def test_agent_register_tool_with_registry(self):
        """Test registering a tool with ToolRegistry."""
        registry = ToolRegistry()
        agent = Agent(model_name="test-model", tool_registry=registry)
        tool = SimpleTool()

        agent.register_tool(tool)

        assert registry.has_tool("test_tool")
        assert len(agent.tools) >= 1

    def test_agent_callbacks(self):
        """Test callback functions."""
        tool_call_results = []
        response_results = []

        def on_tool_call(name, args, result):
            tool_call_results.append((name, args, result))

        def on_response(content):
            response_results.append(content)

        agent = Agent(model_name="test-model")
        agent.set_callbacks(on_tool_call=on_tool_call, on_response=on_response)

        assert agent._on_tool_call is not None
        assert agent._on_response is not None

    def test_agent_find_and_execute_tool_with_registry(self):
        """Test _find_and_execute_tool with ToolRegistry."""
        registry = ToolRegistry()
        registry.register(SimpleTool())

        agent = Agent(model_name="test-model", tool_registry=registry)

        result = agent._find_and_execute_tool("test_tool", {"value": "hello"})

        assert result == {"result": "processed: hello"}

    def test_agent_find_and_execute_tool_without_registry(self):
        """Test _find_and_execute_tool without ToolRegistry raises error."""
        agent = Agent(model_name="test-model")

        with pytest.raises(ValueError, match="Unknown tool"):
            agent._find_and_execute_tool("unknown_tool", {})


class TestAgentRun:
    """Tests for Agent.run method."""

    @patch("core.agent.get_client")
    def test_agent_run_simple_response(self, mock_get_client):
        """Test agent run with simple response."""
        # Mock the client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello, how can I help?"
        mock_response.choices[0].finish_reason = "stop"
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        agent = Agent(model_name="test-model")
        result = agent.run("Hello")

        assert result == "Hello, how can I help?"
        assert len(agent.messages) == 2  # user + assistant

    @patch("core.agent.get_client")
    def test_agent_run_with_tool_call(self, mock_get_client):
        """Test agent run with tool call."""
        # Mock the client
        mock_client = MagicMock()

        # First response: tool call
        mock_tool_response = MagicMock()
        mock_tool_response.choices = [MagicMock()]
        mock_tool_response.choices[0].message.content = None
        mock_tool_response.choices[0].message.tool_calls = [MagicMock()]
        mock_tool_response.choices[0].message.tool_calls[0].function.name = "test_tool"
        mock_tool_response.choices[0].message.tool_calls[0].function.arguments = '{"value": "test"}'
        mock_tool_response.choices[0].message.tool_calls[0].id = "call_123"
        mock_tool_response.choices[0].finish_reason = "tool_calls"

        # Second response: final answer
        mock_final_response = MagicMock()
        mock_final_response.choices = [MagicMock()]
        mock_final_response.choices[0].message.content = "Done!"
        mock_final_response.choices[0].finish_reason = "stop"

        mock_client.chat.completions.create.side_effect = [mock_tool_response, mock_final_response]
        mock_get_client.return_value = mock_client

        registry = ToolRegistry()
        registry.register(SimpleTool())

        agent = Agent(model_name="test-model", tool_registry=registry)
        result = agent.run("Test")

        assert result == "Done!"