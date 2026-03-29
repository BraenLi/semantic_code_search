"""Base tool abstraction for the Agent system."""

from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """Abstract base class for all tools."""

    name: str
    description: str

    @property
    @abstractmethod
    def parameters(self) -> dict[str, Any]:
        """
        Get the JSON Schema for the tool parameters.

        Returns:
            JSON Schema dictionary defining the tool's parameters
        """
        pass

    @abstractmethod
    async def execute(self, arguments: dict[str, Any]) -> Any:
        """
        Execute the tool with the given arguments.

        Args:
            arguments: Dictionary of tool arguments

        Returns:
            The result of the tool execution
        """
        pass

    def to_tool(self) -> "Tool":
        """Convert to Core Tool object."""
        from agenttest.core.types import Tool

        return Tool(
            name=self.name,
            description=self.description,
            parameters=self.parameters,
            handler=self.execute,
        )

    def validate_arguments(
        self, arguments: dict[str, Any]
    ) -> tuple[bool, str | None]:
        """
        Validate the tool arguments against the schema.

        Args:
            arguments: Dictionary of tool arguments

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Basic validation - can be extended with jsonschema
        params = self.parameters
        required = params.get("required", [])

        for req in required:
            if req not in arguments:
                return False, f"Missing required argument: {req}"

        return True, None
