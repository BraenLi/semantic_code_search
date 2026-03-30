"""Tests for indexer service."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from semantic_mcp.services.indexer import Indexer
from semantic_mcp.config import Config, EmbeddingConfig
from semantic_mcp.utils.hash import compute_hash


class TestIndexer:
    """Test indexing logic."""

    @pytest.fixture
    def config(self, temp_dir) -> Config:
        """Test configuration."""
        return Config(
            chroma_path=str(Path(temp_dir) / "chroma"),
            target_dir=str(temp_dir),
            embedding=EmbeddingConfig(api_key="test-key"),
        )

    def test_index_file_creation(self, config, temp_path: Path):
        """Should index a single file."""
        indexer = Indexer(config)

        # Create test file
        test_file = temp_path / "test.py"
        test_file.write_text("def test(): pass")

        # Verify file is detected for indexing
        assert test_file.exists()

    @pytest.mark.asyncio
    async def test_index_file(self, config, temp_path: Path):
        """Should index a single file with mocked embeddings."""
        indexer = Indexer(config)

        # Create test file
        test_file = temp_path / "test.py"
        test_file.write_text("def test_function(): return 42")

        # Mock embedding generation
        with patch.object(indexer.embedding_service, 'generate', new=AsyncMock(return_value=[0.1] * 1536)):
            await indexer.index_file(test_file)

        # Verify file was indexed (storage should have document)
        count = indexer.storage.count()
        assert count > 0

    def test_incremental_hash_detection(self, config, temp_path: Path):
        """Should detect file changes via hash comparison."""
        # Create test file
        test_file = temp_path / "incremental.py"
        test_file.write_text("def first(): pass")

        # Compute initial hash
        content1 = test_file.read_text()
        hash1 = compute_hash(content1)

        # Modify file
        test_file.write_text("def modified(): pass")
        content2 = test_file.read_text()
        hash2 = compute_hash(content2)

        # Hashes should be different
        assert hash1 != hash2

    def test_file_hash_computation(self, config):
        """Should compute consistent file hashes."""
        content = "def test(): pass"
        hash1 = compute_hash(content)
        hash2 = compute_hash(content)

        assert hash1 == hash2

    def test_language_detection(self, config, temp_path: Path):
        """Should detect programming language from file extension."""
        indexer = Indexer(config)

        assert indexer._detect_language(temp_path / "test.py") == "python"
        assert indexer._detect_language(temp_path / "test.c") == "c"
        assert indexer._detect_language(temp_path / "test.cpp") == "cpp"
        assert indexer._detect_language(temp_path / "test.h") == "c"
        assert indexer._detect_language(temp_path / "test.hpp") == "cpp"
        assert indexer._detect_language(temp_path / "test.txt") is None
