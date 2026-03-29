"""Tests for tools."""

import pytest
import tempfile
from pathlib import Path

from core.tools.base import BaseTool, ToolMetadata
from core.tools.registry import ToolRegistry
from core.tools.bash import BashTool
from core.tools.file_ops import ReadTool, WriteTool, EditTool, safe_path
from core.tools.glob import GlobTool, GlobMatcher
from core.tools.grep import GrepTool


class SimpleTool(BaseTool):
    """Simple test tool."""

    name = "simple"
    description = "A simple test tool"

    def execute(self, value: str = "") -> dict:
        return {"value": value}


class TestBaseTool:
    """Tests for BaseTool."""

    def test_tool_metadata(self):
        """Test tool metadata."""
        tool = SimpleTool()
        tool.metadata = ToolMetadata(timeout=30, dangerous=True)

        assert tool.metadata.timeout == 30
        assert tool.metadata.dangerous is True

    def test_to_openai_tool(self):
        """Test converting to OpenAI tool format."""
        tool = SimpleTool()
        result = tool.to_openai_tool()

        assert result["type"] == "function"
        assert result["function"]["name"] == "simple"
        assert result["function"]["description"] == "A simple test tool"

    def test_safe_execute(self):
        """Test safe execute."""
        tool = SimpleTool()
        result = tool.safe_execute(value="test")

        assert result == {"value": "test"}

    def test_safe_execute_with_validation_error(self):
        """Test safe execute with validation error."""
        tool = SimpleTool()

        def validate_params(**kwargs):
            if not kwargs.get("value"):
                return False, "value is required"
            return True, None

        tool.validate_params = validate_params
        result = tool.safe_execute()

        assert result["success"] is False
        assert "value is required" in result["error"]


class TestToolRegistry:
    """Tests for ToolRegistry."""

    def test_register_tool(self):
        """Test registering a tool."""
        registry = ToolRegistry()
        tool = SimpleTool()

        registry.register(tool)

        assert registry.has_tool("simple")
        assert registry.get("simple") is tool

    def test_register_duplicate_tool(self):
        """Test registering duplicate tool raises error."""
        registry = ToolRegistry()
        tool1 = SimpleTool()
        tool2 = SimpleTool()

        registry.register(tool1)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(tool2)

    def test_unregister_tool(self):
        """Test unregistering a tool."""
        registry = ToolRegistry()
        tool = SimpleTool()
        registry.register(tool)

        registry.unregister("simple")

        assert not registry.has_tool("simple")

    def test_execute_tool(self):
        """Test executing a tool."""
        registry = ToolRegistry()
        tool = SimpleTool()
        registry.register(tool)

        result = registry.execute("simple", value="test")

        assert result == {"value": "test"}

    def test_get_openai_tools(self):
        """Test getting OpenAI tool definitions."""
        registry = ToolRegistry()
        registry.register(SimpleTool())

        tools = registry.get_openai_tools()

        assert len(tools) == 1
        assert tools[0]["function"]["name"] == "simple"

    def test_get_dangerous_tools(self):
        """Test getting dangerous tools."""
        registry = ToolRegistry()

        safe_tool = SimpleTool()
        safe_tool.name = "safe"

        dangerous_tool = SimpleTool()
        dangerous_tool.name = "dangerous"
        dangerous_tool.metadata = ToolMetadata(dangerous=True)

        registry.register(safe_tool)
        registry.register(dangerous_tool)

        dangerous = registry.get_dangerous_tools()

        assert "dangerous" in dangerous
        assert "safe" not in dangerous


class TestBashTool:
    """Tests for BashTool."""

    def test_simple_command(self):
        """Test executing a simple command."""
        tool = BashTool(timeout=10)
        result = tool.execute("echo 'hello'")

        assert result["returncode"] == 0
        assert "hello" in result["stdout"]

    def test_command_timeout(self):
        """Test command timeout."""
        tool = BashTool(timeout=1)
        result = tool.execute("sleep 5")

        assert result["returncode"] == -1
        assert "timed out" in result["stderr"]

    def test_dangerous_command_blocked(self):
        """Test blocking dangerous commands."""
        tool = BashTool(block_dangerous=True)
        result = tool.execute("rm -rf /")

        assert result.get("blocked") is True

    def test_background_execution(self):
        """Test background execution."""
        tool = BashTool()
        result = tool.execute("sleep 1", background=True)

        assert result.get("background") is True
        assert "pid" in result


class TestFileTools:
    """Tests for file tools."""

    def test_safe_path(self):
        """Test safe_path function."""
        path, error = safe_path("/tmp/test.txt")
        assert error is None
        assert str(path) == "/tmp/test.txt"

    def test_safe_path_with_base_dir(self):
        """Test safe_path with base directory restriction."""
        path, error = safe_path("/etc/passwd", base_dir="/tmp")
        assert error is not None
        assert "outside allowed directory" in error

    def test_write_and_read(self):
        """Test write and read tools."""
        with tempfile.TemporaryDirectory() as tmpdir:
            write_tool = WriteTool()
            read_tool = ReadTool()

            # Write file
            write_result = write_tool.execute(
                file_path=f"{tmpdir}/test.txt",
                content="Hello, World!",
            )
            assert write_result["success"] is True

            # Read file
            read_result = read_tool.execute(file_path=f"{tmpdir}/test.txt")
            assert read_result["success"] is True
            assert read_result["content"] == "Hello, World!"

    def test_read_max_lines(self):
        """Test reading with max lines."""
        with tempfile.TemporaryDirectory() as tmpdir:
            write_tool = WriteTool()
            read_tool = ReadTool()

            # Write multi-line file
            content = "\n".join([f"Line {i}" for i in range(10)])
            write_tool.execute(file_path=f"{tmpdir}/test.txt", content=content)

            # Read with limit
            result = read_tool.execute(file_path=f"{tmpdir}/test.txt", max_lines=5)

            assert "lines shown" in result["content"]

    def test_edit_tool(self):
        """Test edit tool."""
        with tempfile.TemporaryDirectory() as tmpdir:
            write_tool = WriteTool()
            edit_tool = EditTool()

            # Write initial file
            write_tool.execute(
                file_path=f"{tmpdir}/test.txt",
                content="Hello World",
            )

            # Edit file
            result = edit_tool.execute(
                file_path=f"{tmpdir}/test.txt",
                old_string="World",
                new_string="Python",
            )

            assert result["success"] is True
            assert result["replacements_made"] == 1

            # Verify edit
            read_tool = ReadTool()
            content = read_tool.execute(file_path=f"{tmpdir}/test.txt")
            assert content["content"] == "Hello Python"

    def test_edit_replace_all(self):
        """Test edit tool with replace_all."""
        with tempfile.TemporaryDirectory() as tmpdir:
            write_tool = WriteTool()
            edit_tool = EditTool()

            # Write file with repeated pattern
            write_tool.execute(
                file_path=f"{tmpdir}/test.txt",
                content="foo bar foo bar foo",
            )

            # Replace all
            result = edit_tool.execute(
                file_path=f"{tmpdir}/test.txt",
                old_string="foo",
                new_string="baz",
                replace_all=True,
            )

            assert result["replacements_made"] == 3


class TestGlobTool:
    """Tests for GlobTool."""

    def test_glob_search(self):
        """Test glob search."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some files
            Path(tmpdir, "test.py").touch()
            Path(tmpdir, "test.txt").touch()
            Path(tmpdir, "subdir").mkdir()
            Path(tmpdir, "subdir", "nested.py").touch()

            tool = GlobTool(base_dir=tmpdir)
            result = tool.execute("**/*.py")

            assert result["success"] is True
            assert len(result["files"]) == 2


class TestGrepTool:
    """Tests for GrepTool."""

    def test_grep_search(self):
        """Test grep search."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            test_file = Path(tmpdir, "test.txt")
            test_file.write_text("Hello World\nHello Python\nGoodbye")

            tool = GrepTool(base_dir=tmpdir)
            result = tool.execute("Hello", path=tmpdir)

            assert result["success"] is True
            assert result["total_matches"] == 2

    def test_grep_output_modes(self):
        """Test grep output modes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir, "test.txt")
            test_file.write_text("Hello World\nHello Python")

            tool = GrepTool(base_dir=tmpdir)

            # files_with_matches mode
            result = tool.execute("Hello", path=tmpdir, output_mode="files_with_matches")
            assert len(result["matches"]) == 1
            assert "file" in result["matches"][0]

            # count mode
            result = tool.execute("Hello", path=tmpdir, output_mode="count")
            assert result["matches"][0]["count"] == 2