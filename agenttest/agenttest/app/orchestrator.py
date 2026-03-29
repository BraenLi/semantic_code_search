"""Multi-Agent orchestrator for coordinating multiple agents."""

from typing import Any

from agenttest.agent.base import BaseAgent
from agenttest.core.types import Message


class Orchestrator:
    """
    Orchestrates multiple agents for complex workflows.

    Features:
    - Agent registration and discovery
    - Task routing to appropriate agents
    - Multi-agent collaboration
    - Result aggregation
    """

    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {}
        self._default_agent: str | None = None

    def register_agent(
        self,
        name: str,
        agent: BaseAgent,
        set_default: bool = False,
    ) -> None:
        """
        Register an agent with the orchestrator.

        Args:
            name: Unique name for the agent
            agent: The agent instance
            set_default: Whether to set as default agent
        """
        self._agents[name] = agent

        if set_default or self._default_agent is None:
            self._default_agent = name

    def unregister_agent(self, name: str) -> bool:
        """
        Unregister an agent.

        Args:
            name: Name of the agent to unregister

        Returns:
            True if agent was unregistered, False if not found
        """
        if name in self._agents:
            del self._agents[name]

            if self._default_agent == name:
                self._default_agent = (
                    next(iter(self._agents.keys()))
                    if self._agents
                    else None
                )

            return True
        return False

    def get_agent(self, name: str) -> BaseAgent | None:
        """Get an agent by name."""
        return self._agents.get(name)

    def get_default_agent(self) -> BaseAgent | None:
        """Get the default agent."""
        if self._default_agent:
            return self._agents.get(self._default_agent)
        return None

    def list_agents(self) -> list[str]:
        """List all registered agent names."""
        return list(self._agents.keys())

    async def route(
        self,
        message: str,
        agent_name: str | None = None,
    ) -> str:
        """
        Route a message to an agent and get response.

        Args:
            message: The user message
            agent_name: Optional agent name (uses default if not specified)

        Returns:
            Agent response

        Raises:
            ValueError: If no agent is available
        """
        if agent_name:
            agent = self.get_agent(agent_name)
            if not agent:
                raise ValueError(f"Agent not found: {agent_name}")
        else:
            agent = self.get_default_agent()
            if not agent:
                raise ValueError("No default agent available")

        response = await agent.chat(message)
        return response.content

    async def run(
        self,
        goal: str,
        agent_name: str | None = None,
    ) -> str:
        """
        Run an agent to achieve a goal.

        Args:
            goal: The goal to achieve
            agent_name: Optional agent name

        Returns:
            Final result
        """
        if agent_name:
            agent = self.get_agent(agent_name)
            if not agent:
                raise ValueError(f"Agent not found: {agent_name}")
        else:
            agent = self.get_default_agent()
            if not agent:
                raise ValueError("No default agent available")

        return await agent.run(goal)

    async def broadcast(
        self,
        message: str,
        exclude: list[str] | None = None,
    ) -> dict[str, str]:
        """
        Send a message to all agents and collect responses.

        Args:
            message: The message to broadcast
            exclude: List of agent names to exclude

        Returns:
            Dictionary mapping agent names to responses
        """
        exclude = exclude or []
        results = {}

        for name, agent in self._agents.items():
            if name not in exclude:
                try:
                    response = await agent.chat(message)
                    results[name] = response.content
                except Exception as e:
                    results[name] = f"Error: {str(e)}"

        return results

    def get_status(self) -> dict[str, Any]:
        """Get orchestrator status."""
        return {
            "agents": {
                name: agent.get_status()
                for name, agent in self._agents.items()
            },
            "default_agent": self._default_agent,
            "total_agents": len(self._agents),
        }
