"""Configuration management for the Agent system."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from agenttest.core.exceptions import ConfigurationException


@dataclass
class LLMConfig:
    """Configuration for LLM provider."""

    provider: str = "openai"
    model: str = "gpt-4o"
    api_key: str | None = None
    base_url: str | None = None
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 60

    def __post_init__(self) -> None:
        if self.provider not in ("openai", "anthropic"):
            raise ConfigurationException(
                f"Unsupported LLM provider: {self.provider}"
            )
        if not (0 <= self.temperature <= 2):
            raise ConfigurationException(
                f"Temperature must be between 0 and 2, got {self.temperature}"
            )
        if self.max_tokens <= 0:
            raise ConfigurationException(
                f"max_tokens must be positive, got {self.max_tokens}"
            )


@dataclass
class ToolConfig:
    """Configuration for tools."""

    enabled_tools: list[str] = field(default_factory=list)
    filesystem_root: str | None = None
    allowed_commands: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.filesystem_root:
            root = Path(self.filesystem_root)
            if not root.exists():
                raise ConfigurationException(
                    f"Filesystem root does not exist: {self.filesystem_root}"
                )


@dataclass
class MemoryConfig:
    """Configuration for memory systems."""

    short_term_max_messages: int = 100
    long_term_enabled: bool = False
    long_term_storage_path: str | None = None
    embedding_model: str = "all-MiniLM-L6-v2"


@dataclass
class Config:
    """Main configuration for the Agent system."""

    llm: LLMConfig = field(default_factory=LLMConfig)
    tools: ToolConfig = field(default_factory=ToolConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    debug: bool = False
    log_level: str = "INFO"

    @classmethod
    def from_file(cls, path: str | Path) -> "Config":
        """Load configuration from a YAML file."""
        path = Path(path)
        if not path.exists():
            raise ConfigurationException(f"Config file not found: {path}")

        with open(path, "r") as f:
            data = yaml.safe_load(f)

        return cls.from_dict(data or {})

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Config":
        """Create configuration from a dictionary."""
        llm_data = data.get("llm", {})
        tools_data = data.get("tools", {})
        memory_data = data.get("memory", {})

        # Merge with environment variables
        llm_api_key = llm_data.get("api_key") or os.getenv("OPENAI_API_KEY")
        if llm_data.get("provider") == "anthropic":
            llm_api_key = llm_data.get("api_key") or os.getenv("ANTHROPIC_API_KEY")

        return cls(
            llm=LLMConfig(
                provider=llm_data.get("provider", "openai"),
                model=llm_data.get("model", "gpt-4o"),
                api_key=llm_api_key,
                base_url=llm_data.get("base_url"),
                temperature=llm_data.get("temperature", 0.7),
                max_tokens=llm_data.get("max_tokens", 4096),
                timeout=llm_data.get("timeout", 60),
            ),
            tools=ToolConfig(
                enabled_tools=tools_data.get("enabled_tools", []),
                filesystem_root=tools_data.get("filesystem_root"),
                allowed_commands=tools_data.get("allowed_commands", []),
            ),
            memory=MemoryConfig(
                short_term_max_messages=memory_data.get(
                    "short_term_max_messages", 100
                ),
                long_term_enabled=memory_data.get("long_term_enabled", False),
                long_term_storage_path=memory_data.get("long_term_storage_path"),
                embedding_model=memory_data.get(
                    "embedding_model", "all-MiniLM-L6-v2"
                ),
            ),
            debug=data.get("debug", False),
            log_level=data.get("log_level", "INFO"),
        )

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        return cls.from_dict({})

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "llm": {
                "provider": self.llm.provider,
                "model": self.llm.model,
                "temperature": self.llm.temperature,
                "max_tokens": self.llm.max_tokens,
            },
            "tools": {
                "enabled_tools": self.tools.enabled_tools,
                "filesystem_root": self.tools.filesystem_root,
            },
            "memory": {
                "short_term_max_messages": self.memory.short_term_max_messages,
                "long_term_enabled": self.memory.long_term_enabled,
            },
            "debug": self.debug,
            "log_level": self.log_level,
        }
