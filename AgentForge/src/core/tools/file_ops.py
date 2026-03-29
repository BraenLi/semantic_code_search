"""文件操作工具 - 读写文件。"""

import os
from pathlib import Path
from typing import Any

from .base import BaseTool, ToolMetadata


def safe_path(file_path: str, base_dir: str | Path | None = None) -> tuple[Path, str | None]:
    """验证路径安全性，防止路径逃逸。

    Args:
        file_path: 要验证的文件路径
        base_dir: 允许的基础目录，None 表示不限制

    Returns:
        (安全的路径对象, 错误信息) - 错误信息为 None 表示路径安全
    """
    try:
        path = Path(file_path).resolve()

        # 检查是否为绝对路径
        if not path.is_absolute():
            path = Path.cwd() / path
            path = path.resolve()

        # 如果指定了基础目录，检查是否在允许范围内
        if base_dir is not None:
            base = Path(base_dir).resolve()
            try:
                path.relative_to(base)
            except ValueError:
                return path, f"Path '{file_path}' is outside allowed directory: {base}"

        return path, None

    except Exception as e:
        return Path(file_path), str(e)


class ReadTool(BaseTool):
    """读取文件内容。"""

    name = "read_file"
    description = "Read content from a file"
    metadata = ToolMetadata(category="file_ops", tags=["read", "file"])

    def __init__(self, base_dir: str | Path | None = None, max_size: int = 10 * 1024 * 1024):
        """初始化读取工具。

        Args:
            base_dir: 允许读取的基础目录，None 表示不限制
            max_size: 最大文件大小（字节）
        """
        self.base_dir = base_dir
        self.max_size = max_size

    def validate_params(self, **kwargs: Any) -> tuple[bool, str | None]:
        """验证参数安全性。"""
        file_path = kwargs.get("file_path")
        if not file_path:
            return False, "file_path is required"

        path, error = safe_path(file_path, self.base_dir)
        if error:
            return False, error

        return True, None

    def execute(self, file_path: str, max_lines: int | None = None, **kwargs: Any) -> dict[str, Any]:
        """读取文件内容。

        Args:
            file_path: 文件路径
            max_lines: 最大读取行数，None 表示读取全部
            **kwargs: 其他参数

        Returns:
            读取结果 {content, lines}
        """
        # 验证路径安全性
        path, error = safe_path(file_path, self.base_dir)
        if error:
            return {"error": error, "content": "", "success": False}

        try:
            if not path.exists():
                return {"error": f"File not found: {file_path}", "content": "", "success": False}

            if not path.is_file():
                return {"error": f"Not a file: {file_path}", "content": "", "success": False}

            # 检查文件大小
            file_size = path.stat().st_size
            if file_size > self.max_size:
                return {
                    "error": f"File too large: {file_size} bytes (max: {self.max_size})",
                    "content": "",
                    "success": False,
                }

            with open(path, "r", encoding="utf-8") as f:
                if max_lines:
                    lines = []
                    for i, line in enumerate(f):
                        if i >= max_lines:
                            lines.append(f"... ({max_lines} lines shown)")
                            break
                        lines.append(line)
                    content = "".join(lines)
                    total_lines = sum(1 for _ in open(path, "r", encoding="utf-8"))
                else:
                    content = f.read()
                    total_lines = content.count("\n") + 1

            return {
                "content": content,
                "lines": total_lines,
                "path": str(path.absolute()),
                "success": True,
            }
        except Exception as e:
            return {"error": str(e), "content": "", "success": False}

    def get_parameters_schema(self) -> dict:
        """获取参数 schema。"""
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to read",
                },
                "max_lines": {
                    "type": "integer",
                    "description": "Maximum number of lines to read",
                },
            },
            "required": ["file_path"],
        }


class WriteTool(BaseTool):
    """写入文件内容。"""

    name = "write_file"
    description = "Write content to a file"
    metadata = ToolMetadata(category="file_ops", tags=["write", "file"])

    def __init__(self, base_dir: str | Path | None = None):
        """初始化写入工具。

        Args:
            base_dir: 允许写入的基础目录，None 表示不限制
        """
        self.base_dir = base_dir

    def validate_params(self, **kwargs: Any) -> tuple[bool, str | None]:
        """验证参数安全性。"""
        file_path = kwargs.get("file_path")
        if not file_path:
            return False, "file_path is required"

        content = kwargs.get("content")
        if content is None:
            return False, "content is required"

        path, error = safe_path(file_path, self.base_dir)
        if error:
            return False, error

        return True, None

    def execute(
        self,
        file_path: str,
        content: str,
        mode: str = "w",
        create_dirs: bool = True,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """写入文件内容。

        Args:
            file_path: 文件路径
            content: 要写入的内容
            mode: 写入模式，"w" 覆盖，"a" 追加
            create_dirs: 是否自动创建目录
            **kwargs: 其他参数

        Returns:
            写入结果 {success, path, bytes_written}
        """
        # 验证路径安全性
        path, error = safe_path(file_path, self.base_dir)
        if error:
            return {"success": False, "error": error}

        # 验证模式
        if mode not in ("w", "a"):
            return {"success": False, "error": f"Invalid mode: {mode}. Use 'w' or 'a'."}

        try:
            if create_dirs:
                path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, mode, encoding="utf-8") as f:
                f.write(content)

            return {
                "success": True,
                "path": str(path.absolute()),
                "bytes_written": len(content.encode("utf-8")),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_parameters_schema(self) -> dict:
        """获取参数 schema。"""
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to write",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write",
                },
                "mode": {
                    "type": "string",
                    "description": "Write mode: 'w' for overwrite, 'a' for append",
                    "default": "w",
                },
            },
            "required": ["file_path", "content"],
        }


class EditTool(BaseTool):
    """编辑文件内容 - 字符串替换。"""

    name = "edit_file"
    description = "Edit content in a file by replacing old_string with new_string"
    metadata = ToolMetadata(category="file_ops", tags=["edit", "file"])

    def __init__(self, base_dir: str | Path | None = None):
        """初始化编辑工具。

        Args:
            base_dir: 允许编辑的基础目录，None 表示不限制
        """
        self.base_dir = base_dir

    def validate_params(self, **kwargs: Any) -> tuple[bool, str | None]:
        """验证参数安全性。"""
        file_path = kwargs.get("file_path")
        if not file_path:
            return False, "file_path is required"

        old_string = kwargs.get("old_string")
        new_string = kwargs.get("new_string")
        if old_string is None or new_string is None:
            return False, "old_string and new_string are required"

        path, error = safe_path(file_path, self.base_dir)
        if error:
            return False, error

        return True, None

    def execute(
        self,
        file_path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """编辑文件内容。

        Args:
            file_path: 文件路径
            old_string: 要替换的字符串
            new_string: 替换后的字符串
            replace_all: 是否替换所有匹配
            **kwargs: 其他参数

        Returns:
            编辑结果 {success, replacements_made}
        """
        # 验证路径安全性
        path, error = safe_path(file_path, self.base_dir)
        if error:
            return {"success": False, "error": error}

        try:
            if not path.exists():
                return {"success": False, "error": f"File not found: {file_path}"}

            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            if old_string not in content:
                return {"success": False, "error": "old_string not found in file"}

            if old_string == new_string:
                return {"success": False, "error": "old_string and new_string are identical"}

            if replace_all:
                new_content = content.replace(old_string, new_string)
                replacements = content.count(old_string)
            else:
                new_content = content.replace(old_string, new_string, 1)
                replacements = 1

            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)

            return {
                "success": True,
                "replacements_made": replacements,
                "path": str(path.absolute()),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_parameters_schema(self) -> dict:
        """获取参数 schema。"""
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to edit",
                },
                "old_string": {
                    "type": "string",
                    "description": "String to find and replace",
                },
                "new_string": {
                    "type": "string",
                    "description": "String to replace with",
                },
                "replace_all": {
                    "type": "boolean",
                    "description": "Replace all occurrences",
                    "default": False,
                },
            },
            "required": ["file_path", "old_string", "new_string"],
        }
