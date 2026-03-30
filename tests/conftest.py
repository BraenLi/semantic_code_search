"""Shared test fixtures for semantic MCP tests."""

import pytest
import tempfile
from pathlib import Path

from semantic_mcp.config import Config, EmbeddingConfig


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def temp_path(temp_dir) -> Path:
    """Create temporary directory as Path object."""
    return Path(temp_dir)


@pytest.fixture
def test_embedding_config() -> EmbeddingConfig:
    """Create test embedding configuration."""
    return EmbeddingConfig(
        base_url="https://api.openai.com/v1",
        model="text-embedding-3-small",
        api_key="test-key",
    )


@pytest.fixture
def test_config(temp_dir) -> Config:
    """Create test configuration."""
    return Config(
        chroma_path=str(Path(temp_dir) / "chroma"),
        target_dir=str(temp_dir),
        embedding=EmbeddingConfig(api_key="test-key"),
    )


@pytest.fixture
def code_dir(temp_path: Path) -> Path:
    """Create test code directory with sample files."""
    code_path = temp_path / "test_code"
    code_path.mkdir()

    # Create test Python file
    py_file = code_path / "utils.py"
    py_file.write_text("""
def helper_function(x, y):
    return x + y

def another_function(data):
    return list(data)
""")

    return code_path
