"""Embedding generation service using OpenAI-compatible API."""

import asyncio
from typing import Optional

from openai import AsyncOpenAI, APIError, APIConnectionError, RateLimitError

from semantic_mcp.config import EmbeddingConfig


# Retry configuration
MAX_RETRIES = 3
BASE_DELAY = 1.0  # Base delay for exponential backoff (seconds)
MAX_DELAY = 30.0  # Maximum delay between retries


class EmbeddingService:
    """Generates embeddings using OpenAI-compatible API."""

    def __init__(self, config: EmbeddingConfig):
        """Initialize embedding service.

        Args:
            config: Embedding configuration
        """
        self.config = config
        self.client = AsyncOpenAI(
            base_url=config.base_url,
            api_key=config.api_key or "dummy-key",
        )

    async def generate(self, text: str) -> list[float]:
        """Generate embedding for single text with retry logic.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats

        Raises:
            APIError: If all retry attempts fail
        """
        last_exception: Optional[Exception] = None

        for attempt in range(MAX_RETRIES):
            try:
                response = await self.client.embeddings.create(
                    model=self.config.model,
                    input=text,
                )
                return response.data[0].embedding
            except RateLimitError as e:
                last_exception = e
                # Extract retry-after from response headers if available
                retry_after = getattr(e, 'response', {}).get('headers', {}).get('retry-after')
                if retry_after:
                    delay = float(retry_after)
                else:
                    delay = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
                await asyncio.sleep(delay)
            except APIConnectionError as e:
                last_exception = e
                delay = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
                await asyncio.sleep(delay)
            except APIError as e:
                # Non-retryable API error (4xx client errors)
                if hasattr(e, 'status_code') and e.status_code and 400 <= e.status_code < 500:
                    raise
                last_exception = e
                delay = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
                await asyncio.sleep(delay)

        # All retries exhausted
        raise APIError(
            message=f"Failed to generate embedding after {MAX_RETRIES} attempts: {last_exception}",
            body=str(last_exception),
        ) from last_exception

    async def generate_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        embeddings = []
        for text in texts:
            embedding = await self.generate(text)
            embeddings.append(embedding)
        return embeddings

    def create_description(self, chunk_data: dict) -> str:
        """Create natural language description for a code chunk.

        Args:
            chunk_data: Dictionary with node_type, node_name, language, code

        Returns:
            Natural language description for embedding
        """
        node_type = chunk_data.get("node_type", "code")
        node_name = chunk_data.get("node_name", "unknown")
        language = chunk_data.get("language", "unknown")
        code = chunk_data.get("code", "")

        # Create contextual description
        type_label = {
            "function": "Function",
            "class": "Class",
            "method": "Method",
            "struct": "Struct",
            "file": "File",
        }.get(node_type, "Code element")

        # Include first few lines of code for context
        code_preview = code[:200].replace("\n", " ") if code else ""

        return f"{type_label} '{node_name}' in {language}. {code_preview}"
