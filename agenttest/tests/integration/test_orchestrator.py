"""Integration tests for orchestrator and multi-agent coordination."""

import pytest

from agenttest.agent.base import BaseAgent
from agenttest.agent.state import State
from agenttest.app.orchestrator import Orchestrator
from agenttest.core.config import Config
from agenttest.core.llm.base import BaseLLM
from agenttest.core.types import Message, Response


class MockLLM(BaseLLM):
    """Mock LLM for testing."""

    def __init__(self, responses: list[str] | None = None) -> None:
        super().__init__(model="test")
        self.responses = responses or ["Hello!", "How can I help?"]
        self.call_count = 0

    async def chat(
        self,
        messages: list[Message],
        tools: list | None = None,
        system_prompt: str | None = None,
    ) -> Response:
        self.call_count += 1
        response_text = (
            self.responses[self.call_count % len(self.responses)]
            if self.responses
            else "Hello"
        )
        return Response(
            message=Message.assistant(response_text),
            model=self.model,
        )

    async def chat_stream(
        self,
        messages: list[Message],
        tools: list | None = None,
        system_prompt: str | None = None,
    ):
        yield Message.assistant("streamed")


class MockAgent(BaseAgent):
    """Mock agent for testing."""

    def __init__(
        self,
        name: str | None = None,
        response: str = "Agent response",
    ) -> None:
        llm = MockLLM()
        super().__init__(llm=llm, name=name)
        self._response = response

    async def run(self, goal: str) -> str:
        self.state.start(goal)
        try:
            self.state.complete()
            return self._response
        except Exception as e:
            self.state.fail(str(e))
            raise


class TestOrchestrator:
    """Tests for Orchestrator class."""

    def test_register_agent(self) -> None:
        """Test registering an agent."""
        orchestrator = Orchestrator()
        agent = MockAgent(name="test_agent")
        orchestrator.register_agent("test_agent", agent)

        assert orchestrator.get_agent("test_agent") is agent

    def test_register_agent_sets_default(self) -> None:
        """Test that first agent becomes default."""
        orchestrator = Orchestrator()
        agent1 = MockAgent(name="agent1")
        agent2 = MockAgent(name="agent2")

        orchestrator.register_agent("agent1", agent1)
        assert orchestrator._default_agent == "agent1"

        orchestrator.register_agent("agent2", agent2)
        assert orchestrator._default_agent == "agent1"

        # Register with set_default
        agent3 = MockAgent(name="agent3")
        orchestrator.register_agent("agent3", agent3, set_default=True)
        assert orchestrator._default_agent == "agent3"

    def test_unregister_agent(self) -> None:
        """Test unregistering an agent."""
        orchestrator = Orchestrator()
        agent = MockAgent(name="test")
        orchestrator.register_agent("test", agent)

        result = orchestrator.unregister_agent("test")
        assert result is True
        assert orchestrator.get_agent("test") is None

    def test_unregister_nonexistent_agent(self) -> None:
        """Test unregistering nonexistent agent."""
        orchestrator = Orchestrator()
        result = orchestrator.unregister_agent("nonexistent")
        assert result is False

    def test_list_agents(self) -> None:
        """Test listing agents."""
        orchestrator = Orchestrator()
        orchestrator.register_agent("agent1", MockAgent(name="agent1"))
        orchestrator.register_agent("agent2", MockAgent(name="agent2"))

        agents = orchestrator.list_agents()
        assert set(agents) == {"agent1", "agent2"}

    def test_get_default_agent(self) -> None:
        """Test getting default agent."""
        orchestrator = Orchestrator()
        assert orchestrator.get_default_agent() is None

        agent = MockAgent(name="default")
        orchestrator.register_agent("default", agent)
        assert orchestrator.get_default_agent() is agent

    @pytest.mark.asyncio
    async def test_route_message(self) -> None:
        """Test routing a message to an agent."""
        orchestrator = Orchestrator()
        agent = MockAgent(name="test", response="Hello there!")
        orchestrator.register_agent("test", agent)

        response = await orchestrator.route("Hello", agent_name="test")
        assert response == "Hello there!"

    @pytest.mark.asyncio
    async def test_route_to_default_agent(self) -> None:
        """Test routing to default agent."""
        orchestrator = Orchestrator()
        agent = MockAgent(name="default", response="Default response")
        orchestrator.register_agent("default", agent)

        response = await orchestrator.route("Hi")
        assert response == "Default response"

    @pytest.mark.asyncio
    async def test_route_to_nonexistent_agent(self) -> None:
        """Test routing to nonexistent agent."""
        orchestrator = Orchestrator()
        with pytest.raises(ValueError, match="Agent not found"):
            await orchestrator.route("Hi", agent_name="nonexistent")

    @pytest.mark.asyncio
    async def test_run_goal(self) -> None:
        """Test running a goal."""
        orchestrator = Orchestrator()
        agent = MockAgent(name="test", response="Goal achieved!")
        orchestrator.register_agent("test", agent)

        result = await orchestrator.run("Test goal", agent_name="test")
        assert result == "Goal achieved!"

    @pytest.mark.asyncio
    async def test_broadcast(self) -> None:
        """Test broadcasting message to all agents."""
        orchestrator = Orchestrator()
        agent1 = MockAgent(name="agent1", response="Agent 1 says hi")
        agent2 = MockAgent(name="agent2", response="Agent 2 says hi")
        orchestrator.register_agent("agent1", agent1)
        orchestrator.register_agent("agent2", agent2)

        results = await orchestrator.broadcast("Hello everyone!")
        assert "agent1" in results
        assert "agent2" in results

    @pytest.mark.asyncio
    async def test_broadcast_with_exclude(self) -> None:
        """Test broadcasting with excluded agents."""
        orchestrator = Orchestrator()
        agent1 = MockAgent(name="agent1", response="Agent 1")
        agent2 = MockAgent(name="agent2", response="Agent 2")
        orchestrator.register_agent("agent1", agent1)
        orchestrator.register_agent("agent2", agent2)

        results = await orchestrator.broadcast(
            "Hello", exclude=["agent1"]
        )
        assert "agent1" not in results
        assert "agent2" in results

    def test_get_status(self) -> None:
        """Test getting orchestrator status."""
        orchestrator = Orchestrator()
        agent = MockAgent(name="test")
        orchestrator.register_agent("test", agent)

        status = orchestrator.get_status()
        assert "agents" in status
        assert "test" in status["agents"]
        assert status["total_agents"] == 1
