"""Glob 工具 - 文件模式匹配搜索。"""

import fnmatch
from pathlib import Path
from typing import Any

from .base import BaseTool, ToolMetadata


class GlobTool(BaseTool):
    """Glob 工具 - 文件模式匹配搜索。

    使用 glob 模式匹配查找文件。
    """

    name = "glob"
    description = "Find files using glob pattern matching (e.g., '**/*.py')"
    metadata = ToolMetadata(category="file_ops", tags=["search", "find", "files"])

    def __init__(self, base_dir: str | None = None, max_results: int = 1000):
        """初始化 Glob 工具。

        Args:
            base_dir: 基础目录，None 表示当前目录
            max_results: 最大返回结果数
        """
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.max_results = max_results

    def execute(
        self,
        pattern: str,
        path: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """执行 glob 搜索。

        Args:
            pattern: Glob 模式 (如 '**/*.py', 'src/**/*.ts')
            path: 搜索路径，None 使用 base_dir
            **kwargs: 其他参数

        Returns:
            搜索结果 {files, count, pattern}
        """
        search_path = Path(path) if path else self.base_dir

        if not search_path.exists():
            return {
                "success": False,
                "error": f"Path not found: {search_path}",
                "files": [],
                "count": 0,
            }

        try:
            # Use rglob for recursive search if pattern starts with **
            matches = list(search_path.glob(pattern))

            # Limit results
            if len(matches) > self.max_results:
                matches = matches[: self.max_results]
                truncated = True
            else:
                truncated = False

            # Sort by modification time (most recent first)
            matches.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)

            # Convert to relative paths if possible
            files = []
            for match in matches:
                try:
                    rel_path = match.relative_to(search_path)
                    files.append(str(rel_path))
                except ValueError:
                    files.append(str(match))

            return {
                "success": True,
                "files": files,
                "count": len(files),
                "pattern": pattern,
                "truncated": truncated,
                "base_path": str(search_path),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "files": [],
                "count": 0,
            }

    def get_parameters_schema(self) -> dict:
        """获取参数 schema。"""
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern (e.g., '**/*.py', 'src/**/*.ts')",
                },
                "path": {
                    "type": "string",
                    "description": "Directory to search in (default: current directory)",
                },
            },
            "required": ["pattern"],
        }


class GlobMatcher:
    """Glob 匹配器 - 用于匹配路径。"""

    @staticmethod
    def match(path: str, pattern: str) -> bool:
        """检查路径是否匹配 glob 模式。

        Args:
            path: 路径字符串
            pattern: Glob 模式

        Returns:
            是否匹配
        """
        return fnmatch.fnmatch(path, pattern)

    @staticmethod
    def filter_paths(paths: list[str], pattern: str) -> list[str]:
        """过滤匹配的路径。

        Args:
            paths: 路径列表
            pattern: Glob 模式

        Returns:
            匹配的路径列表
        """
        return [p for p in paths if GlobMatcher.match(p, pattern)]