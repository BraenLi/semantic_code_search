"""Unit tests for agent state management."""

import pytest

from agenttest.agent.state import AgentState, State


class TestAgentState:
    """Tests for AgentState class."""

    def test_initial_state(self) -> None:
        """Test initial state is IDLE."""
        state = AgentState()
        assert state.state == State.IDLE
        assert state.is_idle is True
        assert state.is_running is False

    def test_start_transitions_to_running(self) -> None:
        """Test start transitions to running state."""
        state = AgentState()
        state.start(goal="Test goal")
        assert state.state == State.RUNNING
        assert state.is_running is True
        assert state.current_goal == "Test goal"

    def test_start_while_running_raises_error(self) -> None:
        """Test that starting while already running raises error."""
        state = AgentState()
        state.start()
        with pytest.raises(RuntimeError, match="already running"):
            state.start()

    def test_pause_from_running(self) -> None:
        """Test pausing from running state."""
        state = AgentState()
        state.start()
        state.pause()
        assert state.state == State.PAUSED

    def test_resume_from_paused(self) -> None:
        """Test resuming from paused state."""
        state = AgentState()
        state.start()
        state.pause()
        state.resume()
        assert state.state == State.RUNNING

    def test_resume_from_wrong_state_raises_error(self) -> None:
        """Test that resuming from non-paused state raises error."""
        state = AgentState()
        with pytest.raises(RuntimeError, match="Cannot resume"):
            state.resume()

    def test_complete(self) -> None:
        """Test completing the agent."""
        state = AgentState()
        state.start()
        state.complete()
        assert state.state == State.COMPLETED
        assert state.is_completed is True
        assert state.current_goal is None

    def test_fail(self) -> None:
        """Test failing the agent."""
        state = AgentState()
        state.start()
        state.fail("Something went wrong")
        assert state.state == State.ERROR
        assert state.has_error is True
        assert state.error == "Something went wrong"

    def test_increment_iteration(self) -> None:
        """Test incrementing iteration count."""
        state = AgentState(max_iterations=10)
        for i in range(1, 11):
            count = state.increment_iteration()
            assert count == i

    def test_max_iterations_exceeded(self) -> None:
        """Test that exceeding max iterations raises error."""
        state = AgentState(max_iterations=2)
        state.increment_iteration()
        state.increment_iteration()
        with pytest.raises(RuntimeError, match="Maximum iterations"):
            state.increment_iteration()

    def test_reset(self) -> None:
        """Test resetting state to idle."""
        state = AgentState()
        state.start(goal="Test")
        state.increment_iteration()
        state.reset()
        assert state.state == State.IDLE
        assert state.current_goal is None
        assert state.iteration_count == 0

    def test_to_dict(self) -> None:
        """Test serializing state to dictionary."""
        state = AgentState(max_iterations=100)
        state.start(goal="Test")
        d = state.to_dict()
        assert d["state"] == "running"
        assert d["current_goal"] == "Test"
        assert d["iteration_count"] == 0

    def test_from_dict(self) -> None:
        """Test deserializing state from dictionary."""
        data = {
            "state": "running",
            "current_goal": "Test goal",
            "iteration_count": 5,
            "max_iterations": 50,
        }
        state = AgentState.from_dict(data)
        assert state.state == State.RUNNING
        assert state.current_goal == "Test goal"
        assert state.iteration_count == 5
