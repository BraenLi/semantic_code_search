# Semantic Code Search MCP Server Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现一个 Python MCP server，提供基于自然语言的代码库语义搜索功能。

**Architecture:** MCP server 封装单个 `semantic_code_search` tool，内部调用 Indexer/Searcher 服务，使用 tree-sitter 进行 AST 解析，ChromaDB 存储向量，OpenAI 兼容 API 生成 embedding。

**Tech Stack:** Python 3.10+, MCP, ChromaDB, OpenAI API, tree-sitter (python/c/cpp), watchdog, uv

---

## 文件结构

**Create:**
- `pyproject.toml` - uv 项目配置
- `README.md` - 使用说明
- `src/semantic_mcp/__init__.py` - 包初始化
- `src/semantic_mcp/main.py` - MCP server 入口
- `src/semantic_mcp/config.py` - 配置管理
- `src/semantic_mcp/services/__init__.py` - 服务包初始化
- `src/semantic_mcp/services/search.py` - 搜索服务
- `src/semantic_mcp/services/indexer.py` - 索引服务
- `src/semantic_mcp/services/embeddings.py` - Embedding 服务
- `src/semantic_mcp/services/storage.py` - ChromaDB 封装
- `src/semantic_mcp/services/watcher.py` - 文件监听
- `src/semantic_mcp/parser/__init__.py` - 解析器包初始化
- `src/semantic_mcp/parser/ast_parser.py` - AST 解析
- `src/semantic_mcp/parser/chunker.py` - 分块逻辑
- `tests/test_ast_parser.py` - AST 解析测试
- `tests/test_indexer.py` - 索引服务测试
- `tests/test_search.py` - 搜索服务测试
- `.env.example` - 环境变量示例

---

## 任务分解

### Task 1: 项目初始化

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `.env.example`
- Create: `src/semantic_mcp/__init__.py`

- [ ] **Step 1: 创建 pyproject.toml**

```toml
[project]
name = "semantic-mcp"
version = "0.1.0"
description = "Semantic code search MCP server"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "mcp>=1.0.0",
    "chromadb>=0.4.0",
    "openai>=1.0.0",
    "watchdog>=3.0.0",
    "tree-sitter>=0.20.0",
    "tree-sitter-python",
    "tree-sitter-c",
    "tree-sitter-cpp",
    "python-dotenv>=1.0.0",
    "pydantic>=2.0.0",
]

[project.scripts]
semantic-mcp = "semantic_mcp.main:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/semantic_mcp"]

[tool.uv]
dev-dependencies = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
]
```

- [ ] **Step 2: 创建 .env.example**

```bash
# ChromaDB 本地存储路径
SEMANTIC_CHROMA_PATH="./.semantic_index"

# Embedding API 配置 (OpenAI 兼容)
SEMANTIC_EMBEDDING_BASE_URL="https://api.openai.com/v1"
SEMANTIC_EMBEDDING_MODEL="text-embedding-3-small"
SEMANTIC_API_KEY="sk-your-api-key-here"

# 目标代码库目录
SEMANTIC_TARGET_DIR="/path/to/your/codebase"

# 文件匹配模式 (可选)
SEMANTIC_FILE_PATTERNS="*.py,*.c,*.cpp,*.h,*.hpp"
```

- [ ] **Step 3: 创建 src/semantic_mcp/__init__.py**

```python
"""Semantic Code Search MCP Server."""

__version__ = "0.1.0"
```

- [ ] **Step 4: 创建 src/semantic_mcp/services/__init__.py**

```python
"""Services for semantic code search."""
```

- [ ] **Step 5: 创建 src/semantic_mcp/parser/__init__.py**

```python
"""AST parser and chunker for code analysis."""
```

- [ ] **Step 6: 运行 uv sync 验证配置**

```bash
uv sync
```

预期：成功安装所有依赖

- [ ] **Step 7: 创建基础目录结构**

```bash
mkdir -p src/semantic_mcp/services src/semantic_mcp/parser tests
```

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml README.md .env.example src/semantic_mcp/__init__.py
git commit -m "feat: initialize project structure"
```

---

### Task 2: 配置管理模块

**Files:**
- Create: `src/semantic_mcp/config.py`

- [ ] **Step 1: 编写 config.py**

```python
"""Configuration management for semantic MCP server."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass
class EmbeddingConfig:
    """Embedding API configuration."""
    base_url: str = "https://api.openai.com/v1"
    model: str = "text-embedding-3-small"
    api_key: Optional[str] = None


@dataclass
class Config:
    """Main configuration for semantic MCP server."""
    chroma_path: str = "./.semantic_index"
    target_dir: str = "."
    file_patterns: list[str] = None
    embedding: EmbeddingConfig = None

    def __post_init__(self):
        if self.file_patterns is None:
            self.file_patterns = ["*.py", "*.c", "*.cpp", "*.h", "*.hpp"]
        if self.embedding is None:
            self.embedding = EmbeddingConfig()

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        chroma_path = os.getenv("SEMANTIC_CHROMA_PATH", "./.semantic_index")
        target_dir = os.getenv("SEMANTIC_TARGET_DIR", ".")

        file_patterns_str = os.getenv("SEMANTIC_FILE_PATTERNS", "*.py,*.c,*.cpp,*.h,*.hpp")
        file_patterns = [p.strip() for p in file_patterns_str.split(",")]

        embedding = EmbeddingConfig(
            base_url=os.getenv("SEMANTIC_EMBEDDING_BASE_URL", "https://api.openai.com/v1"),
            model=os.getenv("SEMANTIC_EMBEDDING_MODEL", "text-embedding-3-small"),
            api_key=os.getenv("SEMANTIC_API_KEY"),
        )

        return cls(
            chroma_path=chroma_path,
            target_dir=target_dir,
            file_patterns=file_patterns,
            embedding=embedding,
        )

    def validate(self) -> list[str]:
        """Validate configuration and return list of errors."""
        errors = []

        if not self.embedding.api_key:
            errors.append("SEMANTIC_API_KEY environment variable is required")

        target_path = Path(self.target_dir)
        if not target_path.exists():
            errors.append(f"Target directory does not exist: {self.target_dir}")
        elif not target_path.is_dir():
            errors.append(f"Target path is not a directory: {self.target_dir}")

        return errors
```

- [ ] **Step 2: Commit**

```bash
git add src/semantic_mcp/config.py
git commit -m "feat: add configuration management"
```

---

### Task 3: AST 解析模块

**Files:**
- Create: `src/semantic_mcp/parser/ast_parser.py`
- Test: `tests/test_ast_parser.py`

- [ ] **Step 1: 编写 test_ast_parser.py**

```python
"""Tests for AST parser."""

import pytest
from semantic_mcp.parser.ast_parser import ASTParser, CodeNode


class TestPythonParser:
    """Test Python code parsing."""

    def test_parse_function(self):
        """Should extract function definitions."""
        code = """
def greet(name: str) -> str:
    return f"Hello, {name}!"
"""
        parser = ASTParser("python")
        nodes = parser.parse(code)

        assert len(nodes) == 1
        node = nodes[0]
        assert node.node_type == "function"
        assert node.node_name == "greet"
        assert node.language == "python"
        assert "greet" in node.code
        assert "name: str" in node.code

    def test_parse_class(self):
        """Should extract class definitions with methods."""
        code = """
class Calculator:
    def add(self, a: int, b: int) -> int:
        return a + b

    def multiply(self, a: int, b: int) -> int:
        return a * b
"""
        parser = ASTParser("python")
        nodes = parser.parse(code)

        # Should find class and methods
        class_nodes = [n for n in nodes if n.node_type == "class"]
        method_nodes = [n for n in nodes if n.node_type == "method"]

        assert len(class_nodes) == 1
        assert class_nodes[0].node_name == "Calculator"
        assert len(method_nodes) == 2

    def test_parse_nested_function(self):
        """Should handle nested functions with correct AST path."""
        code = """
class UserService:
    def authenticate(self, username: str, password: str) -> bool:
        def verify_password(pwd: str) -> bool:
            return pwd == "secret"
        return verify_password(password)
"""
        parser = ASTParser("python")
        nodes = parser.parse(code)

        # Check AST paths are correct
        auth_methods = [n for n in nodes if n.node_name == "authenticate"]
        assert len(auth_methods) == 1
        assert "UserService" in auth_methods[0].ast_path


class TestCParser:
    """Test C code parsing."""

    def test_parse_function(self):
        """Should extract C function definitions."""
        code = """
int add(int a, int b) {
    return a + b;
}
"""
        parser = ASTParser("c")
        nodes = parser.parse(code)

        func_nodes = [n for n in nodes if n.node_type == "function"]
        assert len(func_nodes) >= 1
        assert func_nodes[0].node_name == "add"

    def test_parse_struct(self):
        """Should extract C struct definitions."""
        code = """
typedef struct {
    char* name;
    int age;
} Person;
"""
        parser = ASTParser("c")
        nodes = parser.parse(code)

        struct_nodes = [n for n in nodes if n.node_type == "struct"]
        assert len(struct_nodes) >= 1


class TestCppParser:
    """Test C++ code parsing."""

    def test_parse_class(self):
        """Should extract C++ class definitions."""
        code = """
class Rectangle {
private:
    int width;
    int height;
public:
    int area() {
        return width * height;
    }
};
"""
        parser = ASTParser("cpp")
        nodes = parser.parse(code)

        class_nodes = [n for n in nodes if n.node_type == "class"]
        assert len(class_nodes) >= 1
```

- [ ] **Step 2: 编写 ast_parser.py**

```python
"""AST parser for multiple languages using tree-sitter."""

from dataclasses import dataclass
from typing import Optional

import tree_sitter_python as tspython
import tree_sitter_c as tsc
import tree_sitter_cpp as tscpp
from tree_sitter import Language, Parser as TSParser


@dataclass
class CodeNode:
    """Represents a parsed code element (function, class, etc.)."""
    node_type: str  # function, class, method, struct
    node_name: str
    code: str
    language: str
    start_line: int
    end_line: int
    start_col: int
    end_col: int
    ast_path: str = ""
    parent: Optional["CodeNode"] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "node_type": self.node_type,
            "node_name": self.node_name,
            "code": self.code,
            "language": self.language,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "start_col": self.start_col,
            "end_col": self.end_col,
            "ast_path": self.ast_path,
        }


# Tree-sitter language queries for extracting code elements
QUERY_TEMPLATES = {
    "python": """
    (function_definition
        name: (identifier) @name
        parameters: (parameters) @params
        body: (block) @body) @function

    (class_definition
        name: (identifier) @name
        body: (block
            (function_definition
                name: (identifier) @method_name) @method)) @class
    """,
    "c": """
    (function_definition
        declarator: (function_declarator
            declarator: (identifier) @name) @params
        body: (compound_statement) @body) @function

    (struct_specifier
        name: (type_identifier) @name
        body: (field_declaration_list)) @struct
    """,
    "cpp": """
    (function_definition
        declarator: (function_declarator
            declarator: (identifier) @name) @params
        body: (compound_statement) @body) @function

    (class_specifier
        name: (type_identifier) @name
        body: (field_declaration_list)) @class

    (struct_specifier
        name: (type_identifier) @name
        body: (field_declaration_list)) @struct
    """,
}


class ASTParser:
    """Multi-language AST parser using tree-sitter."""

    def __init__(self, language: str):
        """Initialize parser for given language.

        Args:
            language: One of 'python', 'c', 'cpp'
        """
        self.language = language
        self.parser = TSParser()

        # Set language
        if language == "python":
            self.parser.set_language(Language(tspython.language()))
        elif language == "c":
            self.parser.set_language(Language(tsc.language()))
        elif language == "cpp":
            self.parser.set_language(Language(tscpp.language()))
        else:
            raise ValueError(f"Unsupported language: {language}")

        # Load query
        query_source = QUERY_TEMPLATES.get(language, "")
        self.query = self.parser.language.query(query_source) if query_source else None

    def parse(self, code: str) -> list[CodeNode]:
        """Parse code and extract functions, classes, etc.

        Args:
            code: Source code string

        Returns:
            List of CodeNode objects
        """
        if not self.query:
            return []

        # Parse the code
        tree = self.parser.parse(bytes(code, "utf8"))

        # Execute query
        captures = self.query.captures(tree.root_node)

        nodes = []
        node_map = {}  # Track nodes by capture name

        for node, capture_name in captures:
            code_node = self._create_code_node(node, capture_name)
            if code_node:
                nodes.append(code_node)
                node_map[capture_name] = node

        # Build parent relationships and AST paths
        self._build_relationships(nodes, node_map)

        return nodes

    def _create_code_node(self, node, capture_name: str) -> Optional[CodeNode]:
        """Create CodeNode from tree-sitter node."""
        if capture_name not in ("function", "class", "method", "struct"):
            return None

        # Get node name
        name_node = None
        for child in node.children:
            for capture, name in self.query.captures(child):
                if name in ("name", "method_name"):
                    name_node = capture
                    break

        if not name_node:
            return None

        code_bytes = node.text
        code_str = code_bytes.decode("utf8") if isinstance(code_bytes, bytes) else code_bytes

        # Get start position
        start_point = node.start_point
        end_point = node.end_point

        return CodeNode(
            node_type=capture_name,
            node_name=name_node.text.decode("utf8") if isinstance(name_node.text, bytes) else name_node.text,
            code=code_str,
            language=self.language,
            start_line=start_point[0],
            end_line=end_point[0],
            start_col=start_point[1],
            end_col=end_point[1],
            ast_path=capture_name,
        )

    def _build_relationships(self, nodes: list[CodeNode], node_map: dict):
        """Build parent relationships and AST paths."""
        # Simple implementation: set AST path based on node type
        for node in nodes:
            if node.node_type == "method":
                # Find parent class
                for other in nodes:
                    if other.node_type == "class" and other.start_line < node.start_line:
                        node.ast_path = f"{other.node_name}/{node.node_type}"
                        node.parent = other
                        break
```

- [ ] **Step 3: 运行测试验证**

```bash
uv run pytest tests/test_ast_parser.py -v
```

预期：所有测试通过

- [ ] **Step 4: Commit**

```bash
git add src/semantic_mcp/parser/ast_parser.py tests/test_ast_parser.py
git commit -m "feat: implement AST parser for Python/C/C++"
```

---

### Task 4: 分块模块

**Files:**
- Create: `src/semantic_mcp/parser/chunker.py`
- Test: `tests/test_chunker.py`

- [ ] **Step 1: 编写 test_chunker.py**

```python
"""Tests for code chunker."""

import pytest
from semantic_mcp.parser.chunker import Chunker, CodeChunk


class TestChunker:
    """Test code chunking logic."""

    def test_small_file_as_single_chunk(self):
        """Files under threshold should be single chunk."""
        code = """
def small_function():
    return 42
"""
        chunker = Chunker()
        chunks = chunker.chunk(code, "test.py", "python")

        assert len(chunks) == 1
        assert chunks[0].node_type == "file"

    def test_large_file_split_by_function(self):
        """Large files should be split by function/class."""
        code = """
def function_one():
    return 1

def function_two():
    return 2

def function_three():
    return 3

def function_four():
    return 4

def function_five():
    return 5
"""
        chunker = Chunker()
        chunks = chunker.chunk(code, "test.py", "python")

        # Should have individual function chunks
        func_chunks = [c for c in chunks if c.node_type == "function"]
        assert len(func_chunks) >= 3

    def test_chunk_includes_metadata(self):
        """Chunks should include proper metadata."""
        code = """
def calculate_total(items):
    return sum(items)
"""
        chunker = Chunker()
        chunks = chunker.chunk(code, "utils.py", "python")

        assert len(chunks) > 0
        chunk = chunks[0]
        assert chunk.file_path == "utils.py"
        assert chunk.language == "python"
        assert chunk.code is not None

    def test_class_methods_grouped(self):
        """Class methods should be properly associated."""
        code = """
class DataService:
    def load_data(self):
        pass

    def save_data(self):
        pass

    def process(self):
        pass
"""
        chunker = Chunker()
        chunks = chunker.chunk(code, "service.py", "python")

        class_chunks = [c for c in chunks if c.node_type == "class"]
        method_chunks = [c for c in chunks if c.node_type == "method"]

        assert len(class_chunks) >= 1
```

- [ ] **Step 2: 编写 chunker.py**

```python
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

        # Large files: split by function/class
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
```

- [ ] **Step 3: Commit**

```bash
git add src/semantic_mcp/parser/chunker.py tests/test_chunker.py
git commit -m "feat: implement code chunker with AST-based splitting"
```

---

### Task 5: Embedding 服务

**Files:**
- Create: `src/semantic_mcp/services/embeddings.py`
- Test: `tests/test_embeddings.py`

- [ ] **Step 1: 编写 test_embeddings.py**

```python
"""Tests for embedding service."""

import os
import pytest
from unittest.mock import AsyncMock, patch
from semantic_mcp.services.embeddings import EmbeddingService, EmbeddingConfig


class TestEmbeddingService:
    """Test embedding generation."""

    @pytest.fixture
    def config(self):
        """Test configuration."""
        return EmbeddingConfig(
            base_url="https://api.openai.com/v1",
            model="text-embedding-3-small",
            api_key=os.getenv("TEST_API_KEY", "test-key"),
        )

    @pytest.fixture
    def service(self, config):
        """Create embedding service."""
        return EmbeddingService(config)

    @pytest.mark.asyncio
    async def test_generate_embedding(self, service):
        """Should generate embedding for text."""
        # This test requires API access - skip if no key
        if not service.config.api_key:
            pytest.skip("No API key available")

        text = "This is a test function for authentication"
        embedding = await service.generate(text)

        assert embedding is not None
        assert len(embedding) > 0
        assert isinstance(embedding[0], float)

    @pytest.mark.asyncio
    async def test_generate_batch(self, service):
        """Should generate embeddings for multiple texts."""
        if not service.config.api_key:
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
        assert "python" in description
        assert "function" in description
```

- [ ] **Step 2: 编写 embeddings.py**

```python
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
```

- [ ] **Step 3: Commit**

```bash
git add src/semantic_mcp/services/embeddings.py tests/test_embeddings.py
git commit -m "feat: implement embedding service with OpenAI-compatible API"
```

---

### Task 6: Storage 服务 (ChromaDB)

**Files:**
- Create: `src/semantic_mcp/services/storage.py`
- Test: `tests/test_storage.py`

- [ ] **Step 1: 编写 test_storage.py**

```python
"""Tests for ChromaDB storage service."""

import pytest
import tempfile
from pathlib import Path
from semantic_mcp.services.storage import StorageService


class TestStorageService:
    """Test ChromaDB storage operations."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

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
```

- [ ] **Step 2: 编写 storage.py**

```python
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

        if not result["ids"] or not result["ids"][0]:
            return documents

        for i, doc_id in enumerate(result["ids"][0]):
            doc = {
                "id": doc_id,
                "embedding": result["embeddings"][i] if result["embeddings"] else None,
                "metadata": result["metadatas"][i] if result["metadatas"] else {},
                "distance": result["distances"][i][0] if result.get("distances") else None,
            }
            documents.append(doc)

        return documents
```

- [ ] **Step 3: Commit**

```bash
git add src/semantic_mcp/services/storage.py tests/test_storage.py
git commit -m "feat: implement ChromaDB storage service"
```

---

### Task 7: Indexer 服务

**Files:**
- Create: `src/semantic_mcp/services/indexer.py`
- Test: `tests/test_indexer.py`

- [ ] **Step 1: 编写 test_indexer.py**

```python
"""Tests for indexer service."""

import pytest
import tempfile
from pathlib import Path
from semantic_mcp.services.indexer import Indexer
from semantic_mcp.config import Config, EmbeddingConfig


class TestIndexer:
    """Test indexing logic."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def code_dir(self, temp_dir):
        """Create test code directory."""
        code_path = Path(temp_dir) / "test_code"
        code_path.mkdir()

        # Create test Python file
        py_file = code_path / "utils.py"
        py_file.write_text("""
def helper_function(x, y):
    return x + y

def another_function(data):
    return list(data)
""")

        return code_path

    @pytest.fixture
    def config(self, temp_dir, code_dir):
        """Test configuration."""
        return Config(
            chroma_path=str(Path(temp_dir) / "chroma"),
            target_dir=str(code_dir),
            embedding=EmbeddingConfig(api_key="test-key"),
        )

    def test_index_file(self, config, temp_dir):
        """Should index a single file."""
        indexer = Indexer(config)

        # Create test file
        test_file = Path(config.target_dir) / "test.py"
        test_file.write_text("def test(): pass")

        # Index (mock embedding for test)
        # Note: Full integration requires API key

    def test_incremental_detection(self, config, temp_dir):
        """Should detect file changes."""
        indexer = Indexer(config)

        # Initial index
        test_file = Path(config.target_dir) / "incremental.py"
        test_file.write_text("def first(): pass")

        # Modify file
        test_file.write_text("def modified(): pass")

        # Should detect change via hash

    def test_file_hash_computation(self, config):
        """Should compute consistent file hashes."""
        indexer = Indexer(config)

        content = "def test(): pass"
        hash1 = indexer._compute_hash(content)
        hash2 = indexer._compute_hash(content)

        assert hash1 == hash2
```

- [ ] **Step 2: 编写 indexer.py**

```python
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
        self.chunker = Chunker()
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
        """
        # Read file content
        content = file_path.read_text(encoding="utf-8")

        # Compute hash
        content_hash = self._compute_hash(content)

        # Check if already indexed with same content
        if self._indexed_files.get(str(file_path)) == content_hash:
            return  # No change

        # Get relative path
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
```

- [ ] **Step 3: Commit**

```bash
git add src/semantic_mcp/services/indexer.py tests/test_indexer.py
git commit -m "feat: implement indexer service with incremental support"
```

---

### Task 8: Search 服务

**Files:**
- Create: `src/semantic_mcp/services/search.py`
- Test: `tests/test_search.py`

- [ ] **Step 1: 编写 test_search.py**

```python
"""Tests for search service."""

import pytest
import tempfile
from pathlib import Path
from semantic_mcp.services.search import SearchService
from semantic_mcp.config import Config, EmbeddingConfig


class TestSearchService:
    """Test semantic search functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def config(self, temp_dir):
        """Test configuration."""
        return Config(
            chroma_path=str(Path(temp_dir) / "chroma"),
            target_dir=str(temp_dir),
            embedding=EmbeddingConfig(api_key="test-key"),
        )

    def test_search_returns_formatted_results(self, config):
        """Should return properly formatted results."""
        # This would require full setup with embeddings
        # Placeholder for integration test
        pass

    def test_search_with_limit(self, config):
        """Should respect limit parameter."""
        pass

    def test_search_with_language_filter(self, config):
        """Should filter by language."""
        pass
```

- [ ] **Step 2: 编写 search.py**

```python
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
```

- [ ] **Step 3: Commit**

```bash
git add src/semantic_mcp/services/search.py tests/test_search.py
git commit -m "feat: implement semantic search service"
```

---

### Task 9: 文件监听服务

**Files:**
- Create: `src/semantic_mcp/services/watcher.py`

- [ ] **Step 1: 编写 watcher.py**

```python
"""File system watcher for automatic index updates."""

import asyncio
from pathlib import Path
from typing import Callable

from watchdog.observers import Observer
from watchdog.events import (
    FileSystemEventHandler,
    FileModifiedEvent,
    FileCreatedEvent,
    FileDeletedEvent,
    DirDeletedEvent,
)

from semantic_mcp.config import Config
from semantic_mcp.services.indexer import Indexer


class CodeChangeHandler(FileSystemEventHandler):
    """Handles file system events for code files."""

    def __init__(
        self,
        indexer: Indexer,
        config: Config,
        on_index_complete: Callable | None = None,
    ):
        """Initialize handler.

        Args:
            indexer: Indexer service
            config: Configuration
            on_index_complete: Optional callback when indexing completes
        """
        self.indexer = indexer
        self.config = config
        self.on_index_complete = on_index_complete
        self._pending_files: set[str] = set()
        self._debounce_task: asyncio.Task | None = None

    def _is_code_file(self, path: str) -> bool:
        """Check if path matches code file patterns."""
        path_obj = Path(path)
        for pattern in self.config.file_patterns:
            if path_obj.match(pattern):
                return True
        return False

    def _schedule_index(self, file_path: Path) -> None:
        """Schedule file for indexing with debounce."""
        self._pending_files.add(str(file_path))

        if self._debounce_task and not self._debounce_task.done():
            self._debounce_task.cancel()

        self._debounce_task = asyncio.create_task(self._debounce_index())

    async def _debounce_index(self) -> None:
        """Wait for batch of changes then index."""
        await asyncio.sleep(1.0)  # 1 second debounce

        if not self._pending_files:
            return

        files_to_index = list(self._pending_files)
        self._pending_files.clear()

        for file_str in files_to_index:
            file_path = Path(file_str)
            if file_path.exists():
                await self.indexer.index_file(file_path)
            else:
                self.indexer.remove_file(file_path)

        if self.on_index_complete:
            self.on_index_complete(files_to_index)

    def on_modified(self, event):
        """Handle file modification."""
        if isinstance(event, FileModifiedEvent) and self._is_code_file(event.src_path):
            self._schedule_index(Path(event.src_path))

    def on_created(self, event):
        """Handle file creation."""
        if isinstance(event, FileCreatedEvent) and self._is_code_file(event.src_path):
            self._schedule_index(Path(event.src_path))

    def on_deleted(self, event):
        """Handle file deletion."""
        if isinstance(event, (FileDeletedEvent, DirDeletedEvent)):
            if self._is_code_file(event.src_path):
                self.indexer.remove_file(Path(event.src_path))


class WatcherService:
    """File system watcher service."""

    def __init__(self, config: Config, indexer: Indexer):
        """Initialize watcher.

        Args:
            config: Configuration
            indexer: Indexer service
        """
        self.config = config
        self.indexer = indexer
        self.observer: Observer | None = None
        self.handler: CodeChangeHandler | None = None

    def start(self, on_index_complete: Callable | None = None) -> None:
        """Start watching for file changes.

        Args:
            on_index_complete: Optional callback when indexing completes
        """
        target_path = Path(self.config.target_dir).resolve()

        self.handler = CodeChangeHandler(
            indexer=self.indexer,
            config=self.config,
            on_index_complete=on_index_complete,
        )

        self.observer = Observer()
        self.observer.schedule(
            self.handler,
            str(target_path),
            recursive=True,
        )
        self.observer.start()

    def stop(self) -> None:
        """Stop watching for file changes."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
```

- [ ] **Step 2: Commit**

```bash
git add src/semantic_mcp/services/watcher.py
git commit -m "feat: implement file watcher for automatic index updates"
```

---

### Task 10: MCP Server 入口

**Files:**
- Create: `src/semantic_mcp/main.py`

- [ ] **Step 1: 编写 main.py**

```python
"""Semantic Code Search MCP Server."""

import asyncio
import sys
from contextlib import asynccontextmanager

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from semantic_mcp.config import Config
from semantic_mcp.services.indexer import Indexer
from semantic_mcp.services.search import SearchService
from semantic_mcp.services.watcher import WatcherService


# Create server instance
app = Server("semantic-code-search")

# Global services
config: Config | None = None
indexer: Indexer | None = None
search_service: SearchService | None = None
watcher: WatcherService | None = None


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="semantic_code_search",
            description="Search code using natural language queries. Finds relevant functions, classes, and code snippets based on semantic meaning.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language description of what code to find (e.g., 'function that handles user authentication')",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 10,
                    },
                    "language": {
                        "type": "string",
                        "description": "Filter by language (python, c, cpp)",
                        "enum": ["python", "c", "cpp"],
                    },
                    "node_type": {
                        "type": "string",
                        "description": "Filter by code element type",
                        "enum": ["function", "class", "method", "struct"],
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="index_codebase",
            description="Index or re-index the target codebase. This is automatically done on startup but can be called manually to force a refresh.",
            inputSchema={
                "type": "object",
                "properties": {
                    "full": {
                        "type": "boolean",
                        "description": "Perform full re-index instead of incremental",
                        "default": False,
                    },
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool invocation."""
    global indexer, search_service

    if name == "semantic_code_search":
        if not search_service:
            return [TextContent(
                type="text",
                text="Error: Search service not initialized. Run index_codebase first.",
            )]

        query = arguments.get("query", "")
        limit = arguments.get("limit", 10)
        language = arguments.get("language")
        node_type = arguments.get("node_type")

        if not query:
            return [TextContent(
                type="text",
                text="Error: 'query' argument is required",
            )]

        # Perform search
        results = await search_service.search(
            query=query,
            limit=limit,
            language=language,
            node_type=node_type,
        )

        # Format results
        if not results:
            return [TextContent(
                type="text",
                text="No results found for your query.",
            )]

        output = f"Found {len(results)} results:\n\n"
        for i, result in enumerate(results, 1):
            output += f"{i}. {result['file']}:{result['start_line']}-{result['end_line']}\n"
            output += f"   {result['type']}: {result['name']}\n"
            output += f"   Score: {result['score']:.2f}\n"
            output += f"   {result['description']}\n"
            output += f"   ```{result['language']}\n{result['code'][:500]}...\n```\n\n"

        return [TextContent(type="text", text=output)]

    elif name == "index_codebase":
        if not indexer:
            return [TextContent(
                type="text",
                text="Error: Indexer not initialized",
            )]

        full = arguments.get("full", False)

        if full:
            # Clear and re-index
            stats = await indexer.index_all()
        else:
            # Incremental (for now, just do full)
            stats = await indexer.index_all()

        return [TextContent(
            type="text",
            text=f"Indexing complete. Indexed {stats['indexed']} files, {stats['errors']} errors.",
        )]

    return [TextContent(
        type="text",
        text=f"Unknown tool: {name}",
    )]


async def initialize_services():
    """Initialize all services."""
    global config, indexer, search_service, watcher

    config = Config.from_env()

    # Validate configuration
    errors = config.validate()
    if errors:
        print("Configuration errors:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)

    # Initialize services
    indexer = Indexer(config)
    search_service = SearchService(config)

    # Perform initial indexing
    print("Indexing codebase...", file=sys.stderr)
    stats = await indexer.index_all()
    print(f"Indexed {stats['indexed']} files", file=sys.stderr)

    # Start file watcher
    watcher = WatcherService(config, indexer)
    watcher.start(on_index_complete=lambda files: print(f"Indexed: {files}", file=sys.stderr))
    print("File watcher started", file=sys.stderr)


async def main():
    """Main entry point."""
    await initialize_services()

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


def run():
    """Synchronous entry point."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
```

- [ ] **Step 2: 更新 pyproject.toml 入口**

确保 `[project.scripts]` 配置正确:
```toml
[project.scripts]
semantic-mcp = "semantic_mcp.main:run"
```

- [ ] **Step 3: 创建 README.md**

```markdown
# Semantic Code Search MCP Server

基于自然语言的代码库语义搜索 MCP 服务器。

## 功能

- 使用自然语言搜索代码（如"找出所有处理用户认证的函数"）
- 支持 Python、C、C++ 代码
- 函数/类级别的精确索引
- 自动监听文件变化并增量更新索引

## 安装

```bash
# 使用 uv 安装
uv pip install -e .

# 或者直接运行
uv run semantic-mcp
```

## 配置

设置以下环境变量:

```bash
# ChromaDB 本地存储路径
export SEMANTIC_CHROMA_PATH="./.semantic_index"

# Embedding API 配置
export SEMANTIC_EMBEDDING_BASE_URL="https://api.openai.com/v1"
export SEMANTIC_EMBEDDING_MODEL="text-embedding-3-small"
export SEMANTIC_API_KEY="sk-your-api-key"

# 目标代码库目录
export SEMANTIC_TARGET_DIR="/path/to/your/codebase"
```

## 使用

### 在 Claude Code 中使用

在 MCP 配置中添加:

```json
{
  "mcpServers": {
    "semantic-code-search": {
      "command": "semantic-mcp"
    }
  }
}
```

### 可用 Tools

1. **semantic_code_search**: 语义搜索代码
   - `query`: 自然语言查询（必需）
   - `limit`: 结果数量限制（默认 10）
   - `language`: 语言过滤（python/c/cpp）
   - `node_type`: 类型过滤（function/class/method/struct）

2. **index_codebase**: 手动触发索引
   - `full`: 是否完全重新索引（默认 false）

## 开发

```bash
# 安装依赖
uv sync

# 运行测试
uv run pytest

# 开发模式运行
uv run semantic-mcp
```

## 打包

```bash
# 构建分发包
uv build

# 安装到系统
uv pip install .

# 使用 uvx 运行
uvx semantic-mcp
```
```

- [ ] **Step 4: Commit**

```bash
git add src/semantic_mcp/main.py README.md pyproject.toml
git commit -m "feat: implement MCP server with semantic_code_search tool"
```

---

### Task 11: 测试与验证

**Files:**
- Modify: `tests/` (补充测试)

- [ ] **Step 1: 运行所有单元测试**

```bash
uv run pytest tests/ -v
```

预期：所有测试通过（需要 API key 的测试会跳过）

- [ ] **Step 2: 手动验证**

```bash
# 设置环境变量
export SEMANTIC_API_KEY="your-key"
export SEMANTIC_TARGET_DIR="/path/to/test/code"

# 运行 server
uv run semantic-mcp
```

- [ ] **Step 3: 在 Claude Code 中测试**

配置 MCP 后，测试查询:
- "找出所有数据库连接的函数"
- "有哪些处理 HTTP 请求的类"

- [ ] **Step 4: Commit**

```bash
git commit -am "test: add integration tests and manual verification"
```

---

### Task 12: 打包发布

- [ ] **Step 1: 构建分发包**

```bash
uv build
```

- [ ] **Step 2: 本地安装测试**

```bash
uv pip install .
which semantic-mcp  # 确认安装
```

- [ ] **Step 3: 测试独立运行**

```bash
semantic-mcp --help  # 或者测试 MCP 协议
```

- [ ] **Step 4: Commit**

```bash
git commit -am "chore: configure packaging and distribution"
```

---

## 验证清单

- [ ] 可以索引 Python/C/C++ 代码
- [ ] 函数/类级别精确搜索
- [ ] 增量索引工作正常
- [ ] 文件监听自动更新
- [ ] Claude Code 中可以调用
- [ ] 打包后可独立运行
