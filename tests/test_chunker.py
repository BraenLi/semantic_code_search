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
        # Create a file with enough lines to exceed threshold (>50 lines)
        code = """
def function_one():
    x = 1
    y = 2
    z = 3
    a = 4
    b = 5
    c = 6
    d = 7
    e = 8
    return x + y + z + a + b + c + d + e

def function_two():
    x = 1
    y = 2
    z = 3
    a = 4
    b = 5
    c = 6
    d = 7
    e = 8
    return x * y * z * a * b * c * d * e

def function_three():
    x = 1
    y = 2
    z = 3
    a = 4
    b = 5
    c = 6
    d = 7
    e = 8
    return x - y - z - a - b - c - d - e

def function_four():
    x = 1
    y = 2
    z = 3
    a = 4
    b = 5
    c = 6
    d = 7
    e = 8
    return x / y / z / a / b / c / d / e

def function_five():
    x = 1
    y = 2
    z = 3
    a = 4
    b = 5
    c = 6
    d = 7
    e = 8
    return x % y % z % a % b % c % d % e
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
        code = '''
class DataService:
    """A service for handling data operations."""

    def __init__(self):
        """Initialize the service."""
        self.config = {}
        self.data = None
        self.loaded = False
        self.processed = False

    def load_data(self):
        """Load data from source."""
        x = 1
        y = 2
        z = 3
        a = 4
        b = 5
        c = 6
        d = 7
        e = 8
        f = 9
        g = 10
        return x + y + z + a + b + c + d + e + f + g

    def save_data(self):
        """Save data to destination."""
        x = 1
        y = 2
        z = 3
        a = 4
        b = 5
        c = 6
        d = 7
        e = 8
        f = 9
        g = 10
        return x * y * z * a * b * c * d * e * f * g

    def process(self):
        """Process the loaded data."""
        x = 1
        y = 2
        z = 3
        a = 4
        b = 5
        c = 6
        d = 7
        e = 8
        f = 9
        g = 10
        return x - y - z - a - b - c - d - e - f - g
'''
        chunker = Chunker()
        chunks = chunker.chunk(code, "service.py", "python")

        class_chunks = [c for c in chunks if c.node_type == "class"]
        method_chunks = [c for c in chunks if c.node_type == "method"]

        assert len(class_chunks) >= 1
