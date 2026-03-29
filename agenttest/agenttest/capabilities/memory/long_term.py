"""Long-term memory using vector storage."""

import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agenttest.core.exceptions import MemoryException


@dataclass
class MemoryDocument:
    """A document stored in long-term memory."""

    id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryDocument":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            content=data["content"],
            metadata=data.get("metadata", {}),
            embedding=data.get("embedding"),
        )


class LongTermMemory:
    """
    Long-term memory using vector storage.

    This is a simplified in-memory implementation.
    For production use, consider using ChromaDB, Pinecone, or similar.
    """

    def __init__(
        self,
        storage_path: str | None = None,
        embedding_model: str | None = None,
    ) -> None:
        self.storage_path = Path(storage_path) if storage_path else None
        self.embedding_model = embedding_model
        self._documents: dict[str, MemoryDocument] = {}
        self._index: dict[str, list[float]] = {}  # id -> embedding

        # Lazy load embeddings
        self._embeddings_available = False

        if self.storage_path:
            self._load_from_disk()

    async def add(
        self,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Add content to long-term memory.

        Args:
            content: The content to store
            metadata: Optional metadata

        Returns:
            The ID of the stored document
        """
        doc_id = str(uuid.uuid4())
        document = MemoryDocument(
            id=doc_id,
            content=content,
            metadata=metadata or {},
        )

        # Generate embedding if available
        if self._embeddings_available:
            document.embedding = await self._generate_embedding(content)
            self._index[doc_id] = document.embedding  # type: ignore

        self._documents[doc_id] = document

        # Persist to disk if configured
        if self.storage_path:
            self._save_to_disk()

        return doc_id

    async def search(
        self,
        query: str,
        limit: int = 5,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[MemoryDocument]:
        """
        Search for relevant documents.

        Args:
            query: The search query
            limit: Maximum number of results
            filter_metadata: Optional metadata filters

        Returns:
            List of relevant documents, ordered by relevance
        """
        if not self._documents:
            return []

        # If embeddings are available, use semantic search
        if self._embeddings_available:
            return await self._semantic_search(query, limit, filter_metadata)

        # Fallback to keyword search
        return self._keyword_search(query, limit, filter_metadata)

    async def _semantic_search(
        self,
        query: str,
        limit: int,
        filter_metadata: dict[str, Any] | None,
    ) -> list[MemoryDocument]:
        """Perform semantic search using embeddings."""
        try:
            query_embedding = await self._generate_embedding(query)
        except Exception:
            # Fallback to keyword search if embedding fails
            return self._keyword_search(query, limit, filter_metadata)

        # Calculate similarities
        import numpy as np

        query_vec = np.array(query_embedding)
        similarities = {}

        for doc_id, doc in self._documents.items():
            if filter_metadata and not self._matches_filter(
                doc.metadata, filter_metadata
            ):
                continue

            if doc.embedding:
                doc_vec = np.array(doc.embedding)
                similarity = np.dot(query_vec, doc_vec) / (
                    np.linalg.norm(query_vec) * np.linalg.norm(doc_vec)
                )
                similarities[doc_id] = similarity

        # Sort by similarity
        sorted_ids = sorted(
            similarities.keys(), key=lambda x: similarities[x], reverse=True
        )[:limit]

        return [self._documents[doc_id] for doc_id in sorted_ids]

    def _keyword_search(
        self,
        query: str,
        limit: int,
        filter_metadata: dict[str, Any] | None,
    ) -> list[MemoryDocument]:
        """Perform simple keyword search."""
        query_lower = query.lower()
        results = []

        for doc in self._documents.values():
            if filter_metadata and not self._matches_filter(
                doc.metadata, filter_metadata
            ):
                continue

            if query_lower in doc.content.lower():
                results.append(doc)

        return results[:limit]

    def _matches_filter(
        self,
        metadata: dict[str, Any],
        filter_metadata: dict[str, Any],
    ) -> bool:
        """Check if document metadata matches filter."""
        for key, value in filter_metadata.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True

    async def _generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for text."""
        if not self.embedding_model:
            raise MemoryException("No embedding model configured")

        # Try to use sentence-transformers if available
        try:
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer(self.embedding_model)
            embedding = model.encode(text, convert_to_numpy=True)
            return embedding.tolist()  # type: ignore
        except ImportError:
            # Fallback: simple hash-based pseudo-embedding
            return self._simple_embedding(text)

    def _simple_embedding(self, text: str) -> list[float]:
        """Generate a simple hash-based embedding."""
        # This is a placeholder - not suitable for real semantic search
        import hashlib

        hash_bytes = hashlib.md5(text.encode()).digest()
        return [float(b) / 255.0 for b in hash_bytes] * 10  # 160-dim vector

    def get(self, doc_id: str) -> MemoryDocument | None:
        """Get a document by ID."""
        return self._documents.get(doc_id)

    def delete(self, doc_id: str) -> bool:
        """
        Delete a document by ID.

        Returns:
            True if document was deleted, False if not found
        """
        if doc_id in self._documents:
            del self._documents[doc_id]
            if doc_id in self._index:
                del self._index[doc_id]

            if self.storage_path:
                self._save_to_disk()

            return True
        return False

    def clear(self) -> None:
        """Clear all documents."""
        self._documents.clear()
        self._index.clear()

        if self.storage_path:
            self._save_to_disk()

    @property
    def documents(self) -> list[MemoryDocument]:
        """Get all documents."""
        return list(self._documents.values())

    def _save_to_disk(self) -> None:
        """Save documents to disk."""
        if not self.storage_path:
            return

        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            doc_id: doc.to_dict()
            for doc_id, doc in self._documents.items()
        }

        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)

    def _load_from_disk(self) -> None:
        """Load documents from disk."""
        if not self.storage_path or not self.storage_path.exists():
            return

        with open(self.storage_path, "r") as f:
            data = json.load(f)

        for doc_id, doc_data in data.items():
            self._documents[doc_id] = MemoryDocument.from_dict(doc_data)
