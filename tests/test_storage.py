"""Tests for ChromaDB storage service."""

import pytest
from semantic_mcp.services.storage import StorageService


class TestStorageService:
    """Test ChromaDB storage operations."""

    @pytest.fixture
    def storage(self, temp_dir):
        """Create storage service with test database."""
        return StorageService(db_path=temp_dir)

    def test_add_document(self, storage):
        """Should add document to collection."""
        doc_id = "test-doc-1"
        embedding = [0.1] * 1536
        metadata = {
            "file_path": "/test/file.py",
            "node_type": "function",
            "node_name": "test_func",
        }

        storage.add(doc_id, embedding, metadata)

        # Verify retrieval
        results = storage.get([doc_id])
        assert len(results) == 1
        assert results[0]["id"] == doc_id

    def test_search(self, storage):
        """Should find similar documents."""
        # Add test documents
        storage.add("doc-1", [0.9] * 1536, {"label": "similar"})
        storage.add("doc-2", [0.1] * 1536, {"label": "different"})

        # Search with query similar to doc-1
        query = [0.85] * 1536
        results = storage.search(query, limit=1)

        assert len(results) == 1
        assert results[0]["id"] == "doc-1"

    def test_delete(self, storage):
        """Should delete document."""
        storage.add("to-delete", [0.5] * 1536, {"label": "test"})
        storage.delete("to-delete")

        results = storage.get(["to-delete"])
        assert len(results) == 0

    def test_collection_isolation(self, temp_dir):
        """Different target dirs should use different collections."""
        storage1 = StorageService(db_path=temp_dir, collection_name="collection_a")
        storage2 = StorageService(db_path=temp_dir, collection_name="collection_b")

        storage1.add("doc-a", [0.1] * 1536, {"source": "a"})
        storage2.add("doc-b", [0.2] * 1536, {"source": "b"})

        # Each should only see their own documents
        results1 = storage1.search([0.1] * 1536, limit=10)
        results2 = storage2.search([0.2] * 1536, limit=10)

        assert all(r["metadata"].get("source") == "a" for r in results1)
        assert all(r["metadata"].get("source") == "b" for r in results2)
