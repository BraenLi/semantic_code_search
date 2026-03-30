"""Indexer service for managing code index."""

import hashlib
import os
from fnmatch import fnmatch
from pathlib import Path
from typing import Optional

from semantic_mcp.config import Config
from semantic_mcp.parser.chunker import Chunker, CodeChunk
from semantic_mcp.services.embeddings import EmbeddingService
from semantic_mcp.services.storage import StorageService


class Indexer:
    """Manages code indexing including full and incremental indexing."""

    def __init__(self, config: Config):
        """Initialize indexer.

        Args:
            config: Application configuration
        """
        self.config = config
        self.chunker = Chunker(small_file_threshold=config.small_file_threshold)
        self.embedding_service = EmbeddingService(config.embedding)
        self.storage = StorageService(
            db_path=config.chroma_path,
            collection_name="code_index",
        )

        # Track indexed files and their hashes
        self._indexed_files: dict[str, str] = {}

    async def index_all(self) -> dict:
        """Perform full indexing of target directory.

        Returns:
            Statistics about indexed files
        """
        stats = {"indexed": 0, "skipped": 0, "errors": 0}

        target_path = Path(self.config.target_dir)

        for file_path in self._iter_code_files(target_path):
            try:
                await self._index_file(file_path)
                stats["indexed"] += 1
            except Exception as e:
                stats["errors"] += 1
                print(f"Error indexing {file_path}: {e}")

        return stats

    async def _index_file(self, file_path: Path) -> None:
        """Index a single file.

        Args:
            file_path: Path to file to index

        Raises:
            ValueError: If file is not under target directory
        """
        # Read file content
        content = file_path.read_text(encoding="utf-8")

        # Compute hash
        content_hash = self._compute_hash(content)

        # Check if already indexed with same content
        if self._indexed_files.get(str(file_path)) == content_hash:
            return  # No change

        # Get relative path (may raise ValueError if file not under target_dir)
        rel_path = str(file_path.relative_to(self.config.target_dir))

        # Determine language
        language = self._detect_language(file_path)
        if not language:
            return

        # Delete old entries for this file
        self.storage.delete_by_file(str(file_path))

        # Chunk the code
        chunks = self.chunker.chunk(content, rel_path, language)

        # Generate embeddings and store
        for chunk in chunks:
            description = self.embedding_service.create_description({
                "node_type": chunk.node_type,
                "node_name": chunk.node_name,
                "language": chunk.language,
                "code": chunk.code,
            })

            embedding = await self.embedding_service.generate(description)

            # Create document ID
            doc_id = self._create_doc_id(file_path, chunk)

            # Store
            metadata = chunk.to_metadata()
            metadata["hash"] = content_hash
            metadata["description"] = description
            metadata["code"] = chunk.code  # Store code for search results

            self.storage.add(doc_id, embedding, metadata)

        # Track as indexed
        self._indexed_files[str(file_path)] = content_hash

    def _iter_code_files(self, root: Path) -> list[Path]:
        """Iterate over code files matching patterns.

        Args:
            root: Root directory to search

        Returns:
            List of matching file paths
        """
        files = []
        for pattern in self.config.file_patterns:
            files.extend(root.rglob(pattern))
        return files

    def _detect_language(self, file_path: Path) -> Optional[str]:
        """Detect programming language from file extension.

        Args:
            file_path: Path to source file

        Returns:
            Language string or None if not supported
        """
        ext = file_path.suffix.lower()
        mapping = {
            ".py": "python",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
            ".hpp": "cpp",
        }
        return mapping.get(ext)

    def _compute_hash(self, content: str) -> str:
        """Compute SHA256 hash of content.

        Args:
            content: File content

        Returns:
            Hash string
        """
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _create_doc_id(self, file_path: Path, chunk: CodeChunk) -> str:
        """Create unique document ID.

        Args:
            file_path: Source file path
            chunk: Code chunk

        Returns:
            Unique document ID
        """
        return f"{file_path}:{chunk.start_line}:{chunk.node_name}"

    async def index_file(self, file_path: Path) -> None:
        """Index or re-index a single file.

        Args:
            file_path: Path to file to index
        """
        await self._index_file(file_path)

    def remove_file(self, file_path: Path) -> None:
        """Remove file from index.

        Args:
            file_path: Path to file to remove
        """
        self.storage.delete_by_file(str(file_path))
        self._indexed_files.pop(str(file_path), None)
