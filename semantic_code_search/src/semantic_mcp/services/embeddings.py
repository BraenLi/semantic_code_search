"""Embedding generation service using OpenAI-compatible API."""

from openai import AsyncOpenAI

from semantic_mcp.config import EmbeddingConfig


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
        """Generate embedding for single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        response = await self.client.embeddings.create(
            model=self.config.model,
            input=text,
        )
        return response.data[0].embedding

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
