"""Configuration management for semantic MCP server."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass
class EmbeddingConfig:
    """Embedding API configuration."""
    base_url: str = "https://api.openai.com/v1"
    model: str = "text-embedding-3-small"
    api_key: Optional[str] = None


@dataclass
class Config:
    """Main configuration for semantic MCP server."""
    chroma_path: str = "./.semantic_index"
    target_dir: str = "."
    file_patterns: list[str] = None
    embedding: EmbeddingConfig = None
    small_file_threshold: int = 50  # Lines below which file is indexed as single chunk
    debounce_duration: float = 1.0  # Seconds to wait for batch file changes

    def __post_init__(self):
        if self.file_patterns is None:
            self.file_patterns = ["*.py", "*.c", "*.cpp", "*.h", "*.hpp"]
        if self.embedding is None:
            self.embedding = EmbeddingConfig()

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        chroma_path = os.getenv("SEMANTIC_CHROMA_PATH", "./.semantic_index")
        target_dir = os.getenv("SEMANTIC_TARGET_DIR", ".")

        file_patterns_str = os.getenv("SEMANTIC_FILE_PATTERNS", "*.py,*.c,*.cpp,*.h,*.hpp")
        file_patterns = [p.strip() for p in file_patterns_str.split(",")]

        embedding = EmbeddingConfig(
            base_url=os.getenv("SEMANTIC_EMBEDDING_BASE_URL", "https://api.openai.com/v1"),
            model=os.getenv("SEMANTIC_EMBEDDING_MODEL", "text-embedding-3-small"),
            api_key=os.getenv("SEMANTIC_API_KEY"),
        )

        small_file_threshold = int(os.getenv("SEMANTIC_SMALL_FILE_THRESHOLD", "50"))
        debounce_duration = float(os.getenv("SEMANTIC_DEBOUNCE_DURATION", "1.0"))

        return cls(
            chroma_path=chroma_path,
            target_dir=target_dir,
            file_patterns=file_patterns,
            embedding=embedding,
            small_file_threshold=small_file_threshold,
            debounce_duration=debounce_duration,
        )

    def validate(self) -> list[str]:
        """Validate configuration and return list of errors."""
        errors = []

        if not self.embedding.api_key:
            errors.append("SEMANTIC_API_KEY environment variable is required")

        target_path = Path(self.target_dir)
        if not target_path.exists():
            errors.append(f"Target directory does not exist: {self.target_dir}")
        elif not target_path.is_dir():
            errors.append(f"Target path is not not a directory: {self.target_dir}")

        return errors
