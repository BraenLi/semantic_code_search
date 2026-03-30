"""Search service for semantic code queries."""

from semantic_mcp.config import Config
from semantic_mcp.services.embeddings import EmbeddingService
from semantic_mcp.services.storage import StorageService


class SearchService:
    """Semantic search for code."""

    def __init__(self, config: Config):
        """Initialize search service.

        Args:
            config: Application configuration
        """
        self.config = config
        self.embedding_service = EmbeddingService(config.embedding)
        self.storage = StorageService(
            db_path=config.chroma_path,
            collection_name="code_index",
        )

    async def search(
        self,
        query: str,
        limit: int = 10,
        language: str | None = None,
        node_type: str | None = None,
    ) -> list[dict]:
        """Search for code matching natural language query.

        Args:
            query: Natural language query
            limit: Maximum results to return
            language: Optional language filter (python, c, cpp)
            node_type: Optional node type filter (function, class, etc.)

        Returns:
            List of search results
        """
        # Generate query embedding
        query_embedding = await self.embedding_service.generate(query)

        # Build metadata filter
        filter_metadata = {}
        if language:
            filter_metadata["language"] = language
        if node_type:
            filter_metadata["node_type"] = node_type

        # Search
        results = self.storage.search(
            query_embedding=query_embedding,
            limit=limit,
            filter_metadata=filter_metadata if filter_metadata else None,
        )

        # Format results
        formatted = []
        for result in results:
            metadata = result.get("metadata", {})
            formatted.append({
                "file": metadata.get("relative_path", metadata.get("file_path", "")),
                "name": metadata.get("node_name", ""),
                "type": metadata.get("node_type", ""),
                "language": metadata.get("language", ""),
                "score": self._compute_score(result.get("distance")),
                "code": metadata.get("code", ""),
                "description": metadata.get("description", ""),
                "start_line": metadata.get("start_line", 0),
                "end_line": metadata.get("end_line", 0),
            })

        return formatted

    def _compute_score(self, distance: float | None) -> float:
        """Convert distance to similarity score.

        Args:
            distance: Distance from query (lower is more similar)

        Returns:
            Similarity score (0-1, higher is more similar)
        """
        if distance is None:
            return 0.0

        # ChromaDB uses cosine distance by default
        # Convert to similarity score
        similarity = 1.0 - distance
        return max(0.0, min(1.0, similarity))
