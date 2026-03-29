"""Grep 工具 - 文件内容搜索。"""

import re
from pathlib import Path
from typing import Any

from .base import BaseTool, ToolMetadata


class GrepTool(BaseTool):
    """Grep 工具 - 文件内容搜索。

    使用正则表达式在文件中搜索内容。
    """

    name = "grep"
    description = "Search for patterns in file contents using regular expressions"
    metadata = ToolMetadata(category="file_ops", tags=["search", "find", "content", "regex"])

    def __init__(
        self,
        base_dir: str | None = None,
        max_results: int = 100,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
    ):
        """初始化 Grep 工具。

        Args:
            base_dir: 基础目录，None 表示当前目录
            max_results: 最大返回结果数
            max_file_size: 最大文件大小（字节）
        """
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.max_results = max_results
        self.max_file_size = max_file_size

    def execute(
        self,
        pattern: str,
        path: str | None = None,
        file_pattern: str = "*",
        case_sensitive: bool = True,
        context_lines: int = 0,
        output_mode: str = "content",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """执行 grep 搜索。

        Args:
            pattern: 正则表达式模式
            path: 搜索路径，None 使用 base_dir
            file_pattern: 文件名 glob 模式 (如 '*.py')
            case_sensitive: 是否区分大小写
            context_lines: 上下文行数
            output_mode: 输出模式 ('content', 'files_with_matches', 'count')
            **kwargs: 其他参数

        Returns:
            搜索结果
        """
        search_path = Path(path) if path else self.base_dir

        if not search_path.exists():
            return {
                "success": False,
                "error": f"Path not found: {search_path}",
                "matches": [],
            }

        try:
            # Compile regex
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                regex = re.compile(pattern, flags)
            except re.error as e:
                return {
                    "success": False,
                    "error": f"Invalid regex pattern: {e}",
                    "matches": [],
                }

            matches = []
            files_searched = 0
            total_matches = 0

            # Find files to search
            if search_path.is_file():
                files = [search_path]
            else:
                files = list(search_path.rglob(file_pattern))
                files = [f for f in files if f.is_file()]

            for file_path in files:
                if len(matches) >= self.max_results:
                    break

                # Skip large files
                if file_path.stat().st_size > self.max_file_size:
                    continue

                files_searched += 1

                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()

                    file_matches = []
                    for i, line in enumerate(lines):
                        if regex.search(line):
                            total_matches += 1

                            if output_mode == "content":
                                # Get context
                                start = max(0, i - context_lines)
                                end = min(len(lines), i + context_lines + 1)

                                context = []
                                for j in range(start, end):
                                    context.append({
                                        "line_number": j + 1,
                                        "content": lines[j].rstrip("\n\r"),
                                        "is_match": j == i,
                                    })

                                file_matches.append({
                                    "line_number": i + 1,
                                    "line": line.rstrip("\n\r"),
                                    "context": context if context_lines > 0 else None,
                                })

                            elif output_mode == "count":
                                continue  # Just count, don't store matches

                    if file_matches or (output_mode == "count" and any(regex.search(line) for line in lines)):
                        if output_mode == "files_with_matches":
                            matches.append({"file": str(file_path.relative_to(search_path))})
                        elif output_mode == "count":
                            count = sum(1 for line in lines if regex.search(line))
                            matches.append({
                                "file": str(file_path.relative_to(search_path)),
                                "count": count,
                            })
                        else:
                            matches.append({
                                "file": str(file_path.relative_to(search_path)),
                                "matches": file_matches[: self.max_results - len(matches)],
                            })

                except Exception:
                    # Skip files that can't be read
                    continue

            return {
                "success": True,
                "matches": matches,
                "total_matches": total_matches,
                "files_searched": files_searched,
                "pattern": pattern,
                "output_mode": output_mode,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "matches": [],
            }

    def get_parameters_schema(self) -> dict:
        """获取参数 schema。"""
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Regular expression pattern to search for",
                },
                "path": {
                    "type": "string",
                    "description": "Directory or file to search in",
                },
                "file_pattern": {
                    "type": "string",
                    "description": "Glob pattern to filter files (default: '*')",
                    "default": "*",
                },
                "case_sensitive": {
                    "type": "boolean",
                    "description": "Whether search is case sensitive",
                    "default": True,
                },
                "context_lines": {
                    "type": "integer",
                    "description": "Number of context lines to show around matches",
                    "default": 0,
                },
                "output_mode": {
                    "type": "string",
                    "enum": ["content", "files_with_matches", "count"],
                    "description": "Output format: 'content' shows matching lines, 'files_with_matches' shows file names, 'count' shows match counts",
                    "default": "content",
                },
            },
            "required": ["pattern"],
        }