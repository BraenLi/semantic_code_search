"""File system tool for file operations."""

import asyncio
import os
from pathlib import Path
from typing import Any

from agenttest.capabilities.tools.base import BaseTool
from agenttest.core.exceptions import ToolException


class FileSystemTool(BaseTool):
    """Tool for file system operations."""

    name = "filesystem"
    description = (
        "Perform file system operations including reading, writing, "
        "and listing files. Use this tool to interact with files."
    )

    def __init__(
        self,
        root: str | None = None,
        allowed_operations: list[str] | None = None,
    ) -> None:
        self.root = Path(root) if root else None
        self.allowed_operations = allowed_operations or [
            "read",
            "write",
            "list",
            "exists",
        ]

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["read", "write", "list", "exists", "delete"],
                    "description": "The file operation to perform",
                },
                "path": {
                    "type": "string",
                    "description": "The file or directory path",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write (for write operation)",
                },
            },
            "required": ["operation", "path"],
        }

    def _resolve_path(self, path: str) -> Path:
        """Resolve and validate a path."""
        resolved = Path(path)

        if not resolved.is_absolute():
            if self.root:
                resolved = self.root / resolved
            else:
                resolved = Path.cwd() / resolved

        resolved = resolved.resolve()

        # Security check - ensure path is within allowed root
        if self.root:
            try:
                resolved.relative_to(self.root.resolve())
            except ValueError:
                raise ToolException(
                    f"Path is outside allowed root: {path}",
                    {"path": path, "root": str(self.root)},
                )

        return resolved

    async def execute(self, arguments: dict[str, Any]) -> Any:
        """Execute a file system operation."""
        operation = arguments.get("operation")
        path = arguments.get("path")

        if not operation or not path:
            raise ToolException(
                "Missing required arguments: operation and path"
            )

        if operation not in self.allowed_operations:
            raise ToolException(
                f"Operation '{operation}' is not allowed",
                {"allowed": self.allowed_operations},
            )

        try:
            resolved_path = self._resolve_path(path)
        except ToolException:
            raise

        if operation == "read":
            return await self._read(resolved_path)
        elif operation == "write":
            content = arguments.get("content", "")
            return await self._write(resolved_path, content)
        elif operation == "list":
            return await self._list(resolved_path)
        elif operation == "exists":
            return await self._exists(resolved_path)
        elif operation == "delete":
            return await self._delete(resolved_path)
        else:
            raise ToolException(f"Unknown operation: {operation}")

    async def _read(self, path: Path) -> str:
        """Read file content."""
        if not path.exists():
            raise ToolException(f"File does not exist: {path}")
        if path.is_dir():
            raise ToolException(f"Cannot read directory as file: {path}")

        await asyncio.sleep(0)  # Yield to event loop
        return path.read_text(encoding="utf-8")

    async def _write(self, path: Path, content: str) -> str:
        """Write content to file."""
        # Create parent directories if needed
        path.parent.mkdir(parents=True, exist_ok=True)

        await asyncio.sleep(0)
        path.write_text(content, encoding="utf-8")
        return f"Successfully wrote to {path}"

    async def _list(self, path: Path) -> list[dict[str, Any]]:
        """List directory contents."""
        if not path.exists():
            raise ToolException(f"Path does not exist: {path}")
        if not path.is_dir():
            raise ToolException(f"Not a directory: {path}")

        await asyncio.sleep(0)
        result = []
        for item in path.iterdir():
            result.append(
                {
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "path": str(item),
                }
            )
        return result

    async def _exists(self, path: Path) -> bool:
        """Check if path exists."""
        await asyncio.sleep(0)
        return path.exists()

    async def _delete(self, path: Path) -> str:
        """Delete a file or directory."""
        if not path.exists():
            raise ToolException(f"Path does not exist: {path}")

        await asyncio.sleep(0)
        if path.is_dir():
            import shutil

            shutil.rmtree(path)
            return f"Successfully deleted directory: {path}"
        else:
            path.unlink()
            return f"Successfully deleted file: {path}"
