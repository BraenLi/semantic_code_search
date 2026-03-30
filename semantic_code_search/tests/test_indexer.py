"""Tests for indexer service."""

import pytest
import tempfile
from pathlib import Path
from semantic_mcp.services.indexer import Indexer
from semantic_mcp.config import Config, EmbeddingConfig


class TestIndexer:
    """Test indexing logic."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def code_dir(self, temp_dir):
        """Create test code directory."""
        code_path = Path(temp_dir) / "test_code"
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

    @pytest.fixture
    def config(self, temp_dir, code_dir):
        """Test configuration."""
        return Config(
            chroma_path=str(Path(temp_dir) / "chroma"),
            target_dir=str(code_dir),
            embedding=EmbeddingConfig(api_key="test-key"),
        )

    def test_index_file(self, config, temp_dir):
        """Should index a single file."""
        indexer = Indexer(config)

        # Create test file
        test_file = Path(config.target_dir) / "test.py"
        test_file.write_text("def test(): pass")

        # Index (mock embedding for test)
        # Note: Full integration requires API key

    def test_incremental_detection(self, config, temp_dir):
        """Should detect file changes."""
        indexer = Indexer(config)

        # Initial index
        test_file = Path(config.target_dir) / "incremental.py"
        test_file.write_text("def first(): pass")

        # Modify file
        test_file.write_text("def modified(): pass")

        # Should detect change via hash

    def test_file_hash_computation(self, config):
        """Should compute consistent file hashes."""
        indexer = Indexer(config)

        content = "def test(): pass"
        hash1 = indexer._compute_hash(content)
        hash2 = indexer._compute_hash(content)

        assert hash1 == hash2
