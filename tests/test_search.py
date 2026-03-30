"""Tests for search service."""

import pytest
import tempfile
from pathlib import Path
from semantic_mcp.services.search import SearchService
from semantic_mcp.config import Config, EmbeddingConfig


class TestSearchService:
    """Test semantic search functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def config(self, temp_dir):
        """Test configuration."""
        return Config(
            chroma_path=str(Path(temp_dir) / "chroma"),
            target_dir=str(temp_dir),
            embedding=EmbeddingConfig(api_key="test-key"),
        )

    @pytest.mark.skip(reason="Integration test requires API setup")
    def test_search_returns_formatted_results(self, config):
        """Should return properly formatted results."""
        # Integration test - requires valid embedding API
        service = SearchService(config)
        results = service.search("test query", limit=5)
        assert isinstance(results, list)
        for result in results:
            assert "file" in result
            assert "name" in result
            assert "type" in result
            assert "code" in result

    @pytest.mark.skip(reason="Integration test requires API setup")
    def test_search_with_limit(self, config):
        """Should respect limit parameter."""
        # Integration test - requires valid embedding API
        service = SearchService(config)
        results = service.search("test query", limit=3)
        assert len(results) <= 3

    @pytest.mark.skip(reason="Integration test requires API setup")
    def test_search_with_language_filter(self, config):
        """Should filter by language."""
        # Integration test - requires valid embedding API
        service = SearchService(config)
        results = service.search("test query", language="python")
        for result in results:
            assert result["language"] == "python"
