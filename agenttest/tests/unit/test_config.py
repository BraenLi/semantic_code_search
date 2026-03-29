"""Unit tests for configuration."""

import os
import tempfile
from pathlib import Path

import pytest

from agenttest.core.config import Config, LLMConfig, MemoryConfig, ToolConfig
from agenttest.core.exceptions import ConfigurationException


class TestLLMConfig:
    """Tests for LLMConfig class."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = LLMConfig()
        assert config.provider == "openai"
        assert config.model == "gpt-4o"
        assert config.temperature == 0.7
        assert config.max_tokens == 4096

    def test_invalid_provider_raises_error(self) -> None:
        """Test that invalid provider raises error."""
        with pytest.raises(ConfigurationException, match="Unsupported"):
            LLMConfig(provider="invalid")

    def test_invalid_temperature_raises_error(self) -> None:
        """Test that invalid temperature raises error."""
        with pytest.raises(ConfigurationException, match="Temperature"):
            LLMConfig(temperature=3.0)

    def test_negative_max_tokens_raises_error(self) -> None:
        """Test that negative max_tokens raises error."""
        with pytest.raises(ConfigurationException, match="max_tokens"):
            LLMConfig(max_tokens=-100)


class TestConfig:
    """Tests for main Config class."""

    def test_default_config(self) -> None:
        """Test default configuration."""
        config = Config()
        assert config.llm.provider == "openai"
        assert config.memory.short_term_max_messages == 100
        assert config.debug is False

    def test_from_dict(self) -> None:
        """Test creating config from dictionary."""
        data = {
            "llm": {
                "provider": "openai",
                "model": "gpt-4-turbo",
                "temperature": 0.5,
            },
            "memory": {
                "short_term_max_messages": 50,
            },
            "debug": True,
        }
        config = Config.from_dict(data)
        assert config.llm.model == "gpt-4-turbo"
        assert config.llm.temperature == 0.5
        assert config.memory.short_term_max_messages == 50
        assert config.debug is True

    def test_from_env(self) -> None:
        """Test creating config from environment variables."""
        # Clear any existing config
        config = Config.from_env()
        assert config.llm.provider == "openai"

    def test_to_dict(self) -> None:
        """Test converting config to dictionary."""
        config = Config()
        d = config.to_dict()
        assert "llm" in d
        assert "memory" in d
        assert "tools" in d


class TestConfigFromFile:
    """Tests for loading config from file."""

    def test_from_yaml_file(self) -> None:
        """Test loading config from YAML file."""
        yaml_content = """
llm:
  provider: openai
  model: gpt-4o
  temperature: 0.5

memory:
  short_term_max_messages: 200

debug: true
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            f.flush()

            config = Config.from_file(f.name)
            assert config.llm.model == "gpt-4o"
            assert config.llm.temperature == 0.5
            assert config.memory.short_term_max_messages == 200
            assert config.debug is True

            os.unlink(f.name)

    def test_nonexistent_file_raises_error(self) -> None:
        """Test that nonexistent file raises error."""
        with pytest.raises(ConfigurationException, match="not found"):
            Config.from_file("/nonexistent/path/config.yaml")
