"""Core exceptions for the Agent system."""


class AgentException(Exception):
    """Base exception for all Agent-related errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary."""
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }


class LLMException(AgentException):
    """Exception raised when LLM operations fail."""

    pass


class ToolException(AgentException):
    """Exception raised when tool execution fails."""

    pass


class ConfigurationException(AgentException):
    """Exception raised when configuration is invalid."""

    pass


class MemoryException(AgentException):
    """Exception raised when memory operations fail."""

    pass


class PlanningException(AgentException):
    """Exception raised when planning operations fail."""

    pass
