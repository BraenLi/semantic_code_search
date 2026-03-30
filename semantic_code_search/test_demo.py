#!/usr/bin/env python
"""Demo script to test semantic code search with mock embeddings."""

import asyncio
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

# Setup environment
os.environ['SEMANTIC_CHROMA_PATH'] = tempfile.mkdtemp()
os.environ['SEMANTIC_TARGET_DIR'] = '/Users/lgen/Users/lgen/semantic_code_search/test_codebase'
os.environ['SEMANTIC_API_KEY'] = 'sk-test-key'

from semantic_mcp.config import Config
from semantic_mcp.services.indexer import Indexer
from semantic_mcp.services.search import SearchService


async def mock_generate(self, text: str) -> list[float]:
    """Generate mock embedding based on text hash."""
    # Simple deterministic mock embedding
    import hashlib
    h = hashlib.md5(text.encode()).hexdigest()
    return [ord(c) / 256.0 for c in h[:128]] * 12  # 1536 dim


async def main():
    print("=" * 60)
    print("Semantic Code Search - Demo Test")
    print("=" * 60)

    config = Config.from_env()
    print(f"\nTarget directory: {config.target_dir}")
    print(f"ChromaDB path: {config.chroma_path}")

    # Mock the embedding service
    with patch('semantic_mcp.services.embeddings.EmbeddingService.generate', mock_generate):
        with patch('semantic_mcp.services.embeddings.EmbeddingService.generate_batch',
                   AsyncMock(side_effect=lambda texts: asyncio.gather(*[mock_generate(None, t) for t in texts]))):

            # Initialize indexer
            print("\n--- Indexing codebase ---")
            indexer = Indexer(config)
            stats = await indexer.index_all()
            print(f"Indexed: {stats['indexed']} files, {stats['errors']} errors")

            # Check document count
            doc_count = indexer.storage.count()
            print(f"Total documents in index: {doc_count}")

            # Initialize search service
            search_service = SearchService(config)

            # Test search
            print("\n--- Testing Search ---")
            test_queries = [
                "authentication login password",
                "database connection",
                "session management",
            ]

            for query in test_queries:
                print(f"\nQuery: '{query}'")
                results = await search_service.search(query, limit=3)

                if results:
                    for i, result in enumerate(results, 1):
                        print(f"  {i}. [{result['type']}] {result['name']} in {result['file']}")
                        print(f"     Score: {result['score']:.3f}")
                else:
                    print("  No results found")

    print("\n" + "=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
