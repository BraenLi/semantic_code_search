"""Code chunking logic for dividing files into indexable units."""

from dataclasses import dataclass
from typing import Optional

from semantic_mcp.parser.ast_parser import ASTParser, CodeNode


# Line threshold for small files
SMALL_FILE_THRESHOLD = 50


@dataclass
class CodeChunk:
    """A chunk of code ready for indexing."""
    file_path: str
    relative_path: str
    language: str
    node_type: str
    node_name: str
    code: str
    description: str
    start_line: int
    end_line: int
    ast_path: str

    def to_metadata(self) -> dict:
        """Convert to metadata dict for ChromaDB."""
        return {
            "file_path": self.file_path,
            "relative_path": self.relative_path,
            "language": self.language,
            "node_type": self.node_type,
            "node_name": self.node_name,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "ast_path": self.ast_path,
        }


class Chunker:
    """Divides source files into indexable chunks."""

    def __init__(self, small_file_threshold: int = SMALL_FILE_THRESHOLD):
        """Initialize chunker.

        Args:
            small_file_threshold: Line count threshold for small files
        """
        self.small_file_threshold = small_file_threshold

    def chunk(self, code: str, file_path: str, language: str) -> list[CodeChunk]:
        """Divide code into indexable chunks.

        Args:
            code: Source code
            file_path: Path to the source file
            language: Programming language

        Returns:
            List of CodeChunk objects
        """
        line_count = len(code.splitlines())

        # Small files: treat as single chunk
        if line_count <= self.small_file_threshold:
            return [self._create_file_chunk(code, file_path, language)]

        # Large files: split by AST nodes
        return self._split_by_ast(code, file_path, language)

    def _create_file_chunk(self, code: str, file_path: str, language: str) -> CodeChunk:
        """Create a single chunk for entire file."""
        return CodeChunk(
            file_path=file_path,
            relative_path=file_path,
            language=language,
            node_type="file",
            node_name=file_path.split("/")[-1],
            code=code,
            description=f"Entire file: {file_path}",
            start_line=0,
            end_line=len(code.splitlines()),
            ast_path="file",
        )

    def _split_by_ast(self, code: str, file_path: str, language: str) -> list[CodeChunk]:
        """Split large file by AST nodes."""
        try:
            parser = ASTParser(language)
            nodes = parser.parse(code)
        except Exception:
            # Fallback to single chunk if parsing fails
            return [self._create_file_chunk(code, file_path, language)]

        if not nodes:
            return [self._create_file_chunk(code, file_path, language)]

        chunks = []
        for node in nodes:
            chunk = CodeChunk(
                file_path=file_path,
                relative_path=file_path,
                language=language,
                node_type=node.node_type,
                node_name=node.node_name,
                code=node.code,
                description=self._generate_description(node),
                start_line=node.start_line,
                end_line=node.end_line,
                ast_path=node.ast_path,
            )
            chunks.append(chunk)

        return chunks

    def _generate_description(self, node: CodeNode) -> str:
        """Generate natural language description for a code node."""
        type_labels = {
            "function": "Function",
            "class": "Class",
            "method": "Method",
            "struct": "Struct",
        }

        type_label = type_labels.get(node.node_type, "Code")
        return f"{type_label} '{node.node_name}' in {node.language} code"
