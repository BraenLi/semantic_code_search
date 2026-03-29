"""Unit tests for filesystem tool."""

import os
import tempfile
from pathlib import Path

import pytest

from agenttest.capabilities.tools.filesystem import FileSystemTool
from agenttest.core.exceptions import ToolException


class TestFileSystemTool:
    """Tests for FileSystemTool class."""

    def test_parameters(self) -> None:
        """Test tool parameters schema."""
        tool = FileSystemTool()
        params = tool.parameters
        assert params["type"] == "object"
        assert "operation" in params["properties"]
        assert "path" in params["properties"]
        assert "operation" in params["required"]
        assert "path" in params["required"]

    def test_read_file(self) -> None:
        """Test reading a file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as f:
            f.write("Hello, World!")
            f.flush()

            tool = FileSystemTool()
            import asyncio

            result = asyncio.run(tool.execute({
                "operation": "read",
                "path": f.name,
            }))

            assert result == "Hello, World!"
            os.unlink(f.name)

    def test_read_nonexistent_file(self) -> None:
        """Test reading a nonexistent file raises error."""
        tool = FileSystemTool()
        import asyncio

        with pytest.raises(ToolException, match="does not exist"):
            asyncio.run(tool.execute({
                "operation": "read",
                "path": "/nonexistent/file.txt",
            }))

    def test_write_file(self) -> None:
        """Test writing to a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.txt")

            tool = FileSystemTool()
            import asyncio

            result = asyncio.run(tool.execute({
                "operation": "write",
                "path": filepath,
                "content": "Test content",
            }))

            assert "Successfully wrote" in result
            assert Path(filepath).read_text() == "Test content"

    def test_list_directory(self) -> None:
        """Test listing a directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some test files
            Path(os.path.join(tmpdir, "file1.txt")).touch()
            Path(os.path.join(tmpdir, "file2.txt")).touch()

            tool = FileSystemTool()
            import asyncio

            result = asyncio.run(tool.execute({
                "operation": "list",
                "path": tmpdir,
            }))

            assert isinstance(result, list)
            assert len(result) == 2

    def test_exists(self) -> None:
        """Test checking if path exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = FileSystemTool()
            import asyncio

            result = asyncio.run(tool.execute({
                "operation": "exists",
                "path": tmpdir,
            }))
            assert result is True

            result = asyncio.run(tool.execute({
                "operation": "exists",
                "path": "/nonexistent/path",
            }))
            assert result is False

    def test_delete_file(self) -> None:
        """Test deleting a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.txt")
            Path(filepath).write_text("content")

            tool = FileSystemTool()
            import asyncio

            result = asyncio.run(tool.execute({
                "operation": "delete",
                "path": filepath,
            }))

            assert "Successfully deleted" in result
            assert not Path(filepath).exists()

    def test_root_restriction(self) -> None:
        """Test root path restriction."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = FileSystemTool(root=tmpdir)
            import asyncio

            # This should work - within root
            result = asyncio.run(tool.execute({
                "operation": "exists",
                "path": "test.txt",
            }))
            assert result is False

            # This should fail - outside root
            with pytest.raises(ToolException, match="outside allowed root"):
                asyncio.run(tool.execute({
                    "operation": "read",
                    "path": "/etc/passwd",
                }))

    def test_operation_not_allowed(self) -> None:
        """Test restricted operations."""
        tool = FileSystemTool(allowed_operations=["read"])
        import asyncio

        with pytest.raises(ToolException, match="not allowed"):
            asyncio.run(tool.execute({
                "operation": "write",
                "path": "test.txt",
                "content": "test",
            }))
