"""ChromaDB storage service for vector embeddings."""

import hashlib
from typing import Optional

import chromadb
from chromadb.config import Settings


class StorageService:
    """ChromaDB vector storage wrapper."""

    def __init__(self, db_path: str, collection_name: str = "code_index"):
        """Initialize ChromaDB storage.

        Args:
            db_path: Path to persistent database directory
            collection_name: Name of the collection to use
        """
        self.db_path = db_path
        self.collection_name = collection_name

        # Initialize persistent client
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False),
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Semantic code index"},
        )

    def _compute_hash(self, content: str) -> str:
        """Compute SHA256 hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def add(self, doc_id: str, embedding: list[float], metadata: dict) -> None:
        """Add document to collection.

        Args:
            doc_id: Unique document ID
            embedding: Embedding vector
            metadata: Document metadata (must be JSON serializable)
        """
        self.collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            metadatas=[metadata],
        )

    def get(self, doc_ids: list[str]) -> list[dict]:
        """Get documents by ID.

        Args:
            doc_ids: List of document IDs

        Returns:
            List of document dicts
        """
        result = self.collection.get(ids=doc_ids)
        return self._format_results(result)

    def search(
        self,
        query_embedding: list[float],
        limit: int = 10,
        filter_metadata: Optional[dict] = None,
    ) -> list[dict]:
        """Search for similar documents.

        Args:
            query_embedding: Query embedding vector
            limit: Maximum results to return
            filter_metadata: Optional metadata filter

        Returns:
            List of matching documents with scores
        """
        where = filter_metadata if filter_metadata else None

        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=where,
        )

        return self._format_results(result)

    def delete(self, doc_id: str) -> None:
        """Delete document from collection.

        Args:
            doc_id: Document ID to delete
        """
        self.collection.delete(ids=[doc_id])

    def delete_by_file(self, file_path: str) -> None:
        """Delete all documents for a given file.

        Args:
            file_path: File path to delete
        """
        # Get all documents and filter by file_path
        result = self.collection.get(
            where={"file_path": file_path},
        )

        if result["ids"]:
            self.collection.delete(ids=result["ids"])

    def count(self) -> int:
        """Get total document count."""
        return self.collection.count()

    def _format_results(self, result: dict) -> list[dict]:
        """Format ChromaDB results into consistent structure.

        Args:
            result: Raw ChromaDB query/get result

        Returns:
            Formatted list of document dicts
        """
        documents = []

        if not result["ids"]:
            return documents

        # ChromaDB returns different structures for query vs get:
        # - query: ids = [['id1', 'id2']] (nested list)
        # - get: ids = ['id1', 'id2'] (flat list)
        ids = result["ids"][0] if isinstance(result["ids"][0], list) else result["ids"]
        metadatas = result["metadatas"][0] if result.get("metadatas") and isinstance(result["metadatas"][0], list) else result.get("metadatas")
        embeddings = result["embeddings"][0] if result.get("embeddings") and isinstance(result["embeddings"][0], list) else result.get("embeddings")
        distances = result["distances"][0] if result.get("distances") and isinstance(result["distances"][0], list) else result.get("distances")

        for i, doc_id in enumerate(ids):
            doc = {
                "id": doc_id,
                "embedding": embeddings[i] if embeddings else None,
                "metadata": metadatas[i] if metadatas else {},
                "distance": distances[i] if distances else None,
            }
            documents.append(doc)

        return documents
