"""Agent state management."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class State(str, Enum):
    """Agent state enumeration."""

    IDLE = "idle"
    RUNNING = "running"
    WAITING = "waiting"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class AgentState:
    """
    Manages the state of an Agent.

    Tracks:
    - Current state (idle, running, waiting, etc.)
    - Current task/goal
    - Iteration count
    - Error information
    - Custom state data
    """

    state: State = State.IDLE
    current_goal: str | None = None
    iteration_count: int = 0
    max_iterations: int = 50
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.max_iterations <= 0:
            raise ValueError("max_iterations must be positive")

    def start(self, goal: str | None = None) -> None:
        """
        Transition to running state.

        Args:
            goal: Optional goal description
        """
        if self.state == State.RUNNING:
            raise RuntimeError("Agent is already running")

        self.state = State.RUNNING
        self.current_goal = goal
        self.error = None
        self.iteration_count = 0

    def pause(self) -> None:
        """Transition to paused state."""
        if self.state not in (State.RUNNING, State.WAITING):
            raise RuntimeError(f"Cannot pause from state: {self.state}")
        self.state = State.PAUSED

    def resume(self) -> None:
        """Resume from paused state."""
        if self.state != State.PAUSED:
            raise RuntimeError(f"Cannot resume from state: {self.state}")
        self.state = State.RUNNING

    def wait(self) -> None:
        """Transition to waiting state (e.g., waiting for user input)."""
        if self.state != State.RUNNING:
            raise RuntimeError(f"Cannot wait from state: {self.state}")
        self.state = State.WAITING

    def complete(self) -> None:
        """Transition to completed state."""
        self.state = State.COMPLETED
        self.current_goal = None

    def fail(self, error: str) -> None:
        """
        Transition to error state.

        Args:
            error: Error description
        """
        self.state = State.ERROR
        self.error = error
        self.current_goal = None

    def increment_iteration(self) -> int:
        """
        Increment iteration count.

        Returns:
            New iteration count

        Raises:
            RuntimeError: If max iterations exceeded
        """
        self.iteration_count += 1

        if self.iteration_count > self.max_iterations:
            raise RuntimeError(
                f"Maximum iterations ({self.max_iterations}) exceeded"
            )

        return self.iteration_count

    def reset(self) -> None:
        """Reset state to idle."""
        self.state = State.IDLE
        self.current_goal = None
        self.error = None
        self.iteration_count = 0

    @property
    def is_running(self) -> bool:
        """Check if agent is running."""
        return self.state == State.RUNNING

    @property
    def is_idle(self) -> bool:
        """Check if agent is idle."""
        return self.state == State.IDLE

    @property
    def is_completed(self) -> bool:
        """Check if agent has completed."""
        return self.state == State.COMPLETED

    @property
    def has_error(self) -> bool:
        """Check if agent has an error."""
        return self.state == State.ERROR

    def to_dict(self) -> dict[str, Any]:
        """Serialize state to dictionary."""
        return {
            "state": self.state.value,
            "current_goal": self.current_goal,
            "iteration_count": self.iteration_count,
            "max_iterations": self.max_iterations,
            "error": self.error,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentState":
        """Deserialize state from dictionary."""
        return cls(
            state=State(data.get("state", "idle")),
            current_goal=data.get("current_goal"),
            iteration_count=data.get("iteration_count", 0),
            max_iterations=data.get("max_iterations", 50),
            error=data.get("error"),
            metadata=data.get("metadata", {}),
        )
