"""Tests for embedding service."""

import pytest
import os
from unittest.mock import AsyncMock, patch

from semantic_mcp.services.embeddings import EmbeddingService, EmbeddingConfig


class TestEmbeddingService:
    """Test embedding generation."""

    @pytest.fixture
    def config(self) -> EmbeddingConfig:
        """Test configuration."""
        return EmbeddingConfig(
            base_url="https://api.openai.com/v1",
            model="text-embedding-3-small",
            api_key=os.getenv("TEST_API_KEY") or "test-key",
        )

    @pytest.fixture
    def service(self, config) -> EmbeddingService:
        """Create embedding service."""
        return EmbeddingService(config)

    @pytest.mark.asyncio
    async def test_generate_embedding(self, service):
        """Should generate embedding for text."""
        # This test requires API access - skip if no key
        if not service.config.api_key or service.config.api_key == "test-key":
            pytest.skip("No API key available")

        text = "This is a test function for authentication"
        embedding = await service.generate(text)

        assert embedding is not None
        assert len(embedding) > 0
        assert isinstance(embedding[0], float)

    @pytest.mark.asyncio
    async def test_generate_batch(self, service):
        """Should generate embeddings for multiple texts."""
        if not service.config.api_key or service.config.api_key == "test-key":
            pytest.skip("No API key available")

        texts = ["function one", "function two"]
        embeddings = await service.generate_batch(texts)

        assert len(embeddings) == 2
        assert all(len(e) > 0 for e in embeddings)

    def test_create_description(self, service):
        """Should create meaningful description for code."""
        chunk_data = {
            "node_type": "function",
            "node_name": "authenticate_user",
            "language": "python",
            "code": "def authenticate_user(username, password):..."
        }

        description = service.create_description(chunk_data)

        assert "authenticate_user" in description
        assert "python" in description.lower()
        assert "Function" in description

    @pytest.mark.asyncio
    async def test_generate_raises_on_invalid_key(self):
        """Should raise ValueError when API key is missing."""
        config = EmbeddingConfig(api_key=None)

        with pytest.raises(ValueError, match="API key is required"):
            EmbeddingService(config)
