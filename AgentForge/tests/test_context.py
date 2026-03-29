"""Tests for ContextProcessor."""

import pytest
import tempfile
from pathlib import Path

from core.context import ContextProcessor


class TestContextProcessor:
    """Tests for ContextProcessor."""

    def test_estimate_tokens_empty(self):
        """Test token estimation for empty string."""
        assert ContextProcessor.estimate_tokens("") == 0

    def test_estimate_tokens_english(self):
        """Test token estimation for English text."""
        # English: ~4 chars per token
        text = "Hello World"  # 11 chars
        tokens = ContextProcessor.estimate_tokens(text)
        assert 2 <= tokens <= 4

    def test_estimate_tokens_chinese(self):
        """Test token estimation for Chinese text."""
        # Chinese: ~1.5 chars per token
        text = "你好世界"  # 4 chars
        tokens = ContextProcessor.estimate_tokens(text)
        assert 2 <= tokens <= 4

    def test_estimate_messages_tokens(self):
        """Test token estimation for messages."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        total = ContextProcessor.estimate_messages_tokens(messages)

        # Should include role tokens (~4 each) + content tokens
        assert total > 0

    def test_micro_compact_no_change(self):
        """Test micro_compact with small message list."""
        messages = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
        ]

        result = ContextProcessor.micro_compact(messages)

        assert result == messages

    def test_micro_compact_large_list(self):
        """Test micro_compact with large message list."""
        messages = [{"role": "user", "content": f"Message {i}"} for i in range(20)]

        result = ContextProcessor.micro_compact(messages, keep_last_n=5)

        assert len(result) == 20
        # First 15 messages should be compacted
        assert "Message 0" in result[0]["content"]

    def test_micro_compact_preserves_system(self):
        """Test micro_compact preserves system messages."""
        messages = [
            {"role": "system", "content": "Important system message"},
        ] + [{"role": "user", "content": f"Message {i}"} for i in range(20)]

        result = ContextProcessor.micro_compact(messages, keep_last_n=5, preserve_system=True)

        assert result[0]["role"] == "system"
        assert result[0]["content"] == "Important system message"

    def test_isolate_subagent(self):
        """Test isolating context for subagent."""
        parent_messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Long conversation..."},
            {"role": "assistant", "content": "Response..."},
        ]

        result = ContextProcessor.isolate_subagent(
            parent_messages,
            task_description="Complete this specific task",
        )

        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert result[1]["role"] == "user"
        assert "specific task" in result[1]["content"]

    def test_merge_subagent_result(self):
        """Test merging subagent result."""
        parent_messages = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "Task"},
        ]

        result = ContextProcessor.merge_subagent_result(
            parent_messages,
            subagent_result="Task completed successfully",
            task_description="Original task",
        )

        assert len(result) == 4
        assert result[2]["role"] == "assistant"
        assert "Original task" in result[2]["content"]
        assert result[3]["role"] == "user"
        assert "Task completed successfully" in result[3]["content"]


class TestTranscriptIO:
    """Tests for transcript save/load."""

    def test_save_transcript(self):
        """Test saving transcript."""
        with tempfile.TemporaryDirectory() as tmpdir:
            messages = [
                {"role": "system", "content": "System"},
                {"role": "user", "content": "Hello"},
            ]

            path = ContextProcessor.save_transcript(
                messages,
                output_path=f"{tmpdir}/transcript.json",
            )

            assert path.exists()

    def test_load_transcript(self):
        """Test loading transcript."""
        with tempfile.TemporaryDirectory() as tmpdir:
            messages = [
                {"role": "system", "content": "System"},
                {"role": "user", "content": "Hello"},
            ]

            path = ContextProcessor.save_transcript(
                messages,
                output_path=f"{tmpdir}/transcript.json",
            )

            loaded = ContextProcessor.load_transcript(path)

            assert len(loaded) == 2
            assert loaded[0]["role"] == "system"

    def test_format_for_display(self):
        """Test formatting messages for display."""
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "Hello World"},
            {"role": "assistant", "content": "Hi there!", "tool_calls": [
                {"function": {"name": "test_tool"}}
            ]},
        ]

        result = ContextProcessor.format_for_display(messages)

        assert "[system]" in result
        assert "[user]" in result
        assert "[tools: test_tool]" in result