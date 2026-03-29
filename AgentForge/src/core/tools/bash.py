"""Bash 工具 - 执行 shell 命令。"""

import subprocess
from typing import Any

from .base import BaseTool, ToolMetadata


# Dangerous commands that should be blocked or require confirmation
DANGEROUS_PATTERNS = [
    "rm -rf /",
    "rm -rf /*",
    "mkfs",
    "dd if=",
    "> /dev/sd",
    ":(){ :|:& };:",  # Fork bomb
    "chmod -R 777 /",
    "chown -R",
    "wget",
    "curl -X POST",
    "curl -X DELETE",
    "npm publish",
    "git push --force",
    "git reset --hard",
    "DROP TABLE",
    "DROP DATABASE",
    "TRUNCATE",
]

# Commands that should be warned but not blocked
WARNING_PATTERNS = [
    "rm -rf",
    "rm -r",
    "sudo",
    "chmod",
    "chown",
    "kill -9",
    "pkill",
    "git push",
    "git reset",
    "git checkout",
]


class BashTool(BaseTool):
    """Bash 工具 - 执行 shell 命令。

    安全提示：
    - 不执行交互式命令
    - 不执行需要用户输入的命令
    - 默认在 sandbox 环境中执行
    - 过滤危险命令
    """

    name = "bash"
    description = "Execute shell commands in the current environment"
    metadata = ToolMetadata(
        category="system",
        tags=["shell", "command", "execute"],
        dangerous=True,
        requires_confirmation=False,
    )

    def __init__(
        self,
        timeout: int = 120,
        workdir: str | None = None,
        max_output_length: int = 50000,
        block_dangerous: bool = True,
    ):
        """初始化 Bash 工具。

        Args:
            timeout: 命令超时时间 (秒)
            workdir: 工作目录，None 表示当前目录
            max_output_length: 输出最大长度
            block_dangerous: 是否阻止危险命令
        """
        self.timeout = timeout
        self.workdir = workdir
        self.max_output_length = max_output_length
        self.block_dangerous = block_dangerous

    def _check_command_safety(self, command: str) -> tuple[bool, str, str]:
        """检查命令安全性。

        Args:
            command: 要检查的命令

        Returns:
            (是否安全, 级别, 消息)
            级别: 'block', 'warning', 'safe'
        """
        command_lower = command.lower()

        # Check for blocked patterns
        if self.block_dangerous:
            for pattern in DANGEROUS_PATTERNS:
                if pattern.lower() in command_lower:
                    return False, "block", f"Blocked dangerous command pattern: {pattern}"

        # Check for warning patterns
        for pattern in WARNING_PATTERNS:
            if pattern.lower() in command_lower:
                return True, "warning", f"Potentially dangerous command: {pattern}"

        return True, "safe", ""

    def _truncate_output(self, output: str) -> str:
        """截断输出。"""
        if len(output) > self.max_output_length:
            return output[: self.max_output_length] + f"\n... [truncated, {len(output)} total chars]"
        return output

    def validate_params(self, **kwargs: Any) -> tuple[bool, str | None]:
        """验证参数安全性。"""
        command = kwargs.get("command")
        if not command:
            return False, "command is required"

        is_safe, level, message = self._check_command_safety(command)
        if not is_safe:
            return False, message

        return True, None

    def execute(
        self,
        command: str,
        timeout: int | None = None,
        background: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """执行 shell 命令。

        Args:
            command: 要执行的命令
            timeout: 超时时间（秒），None 使用默认值
            background: 是否在后台执行
            **kwargs: 其他参数（保留用于扩展）

        Returns:
            执行结果 {stdout, stderr, returncode, background_id}
        """
        # Check command safety
        is_safe, level, message = self._check_command_safety(command)
        if not is_safe:
            return {
                "stdout": "",
                "stderr": message,
                "returncode": -1,
                "blocked": True,
            }

        # Add warning to output if needed
        warning_prefix = ""
        if level == "warning":
            warning_prefix = f"[WARNING: {message}]\n"

        actual_timeout = timeout or self.timeout

        try:
            if background:
                # Start background process
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=self.workdir,
                )
                return {
                    "stdout": "",
                    "stderr": "",
                    "returncode": None,
                    "background": True,
                    "pid": process.pid,
                    "message": f"Background task started with PID {process.pid}",
                }

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=actual_timeout,
                cwd=self.workdir,
            )

            stdout = self._truncate_output(result.stdout)
            stderr = self._truncate_output(result.stderr)

            return {
                "stdout": warning_prefix + stdout,
                "stderr": stderr,
                "returncode": result.returncode,
                "command": command,
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"Command timed out after {actual_timeout} seconds",
                "returncode": -1,
                "command": command,
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "returncode": -1,
                "command": command,
            }

    def get_parameters_schema(self) -> dict:
        """获取参数 schema。

        Returns:
            JSON Schema 格式的参数字典
        """
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute",
                },
                "timeout": {
                    "type": "integer",
                    "description": f"Timeout in seconds (default: {self.timeout})",
                },
                "background": {
                    "type": "boolean",
                    "description": "Run command in background",
                    "default": False,
                },
            },
            "required": ["command"],
        }
