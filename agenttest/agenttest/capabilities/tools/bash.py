"""Bash tool for executing shell commands."""

import asyncio
import shlex
from typing import Any

from agenttest.capabilities.tools.base import BaseTool
from agenttest.core.exceptions import ToolException


class BashTool(BaseTool):
    """Tool for executing bash commands."""

    name = "bash"
    description = (
        "Execute bash shell commands. Use this tool to run system commands, "
        "scripts, and interact with the terminal."
    )

    def __init__(
        self,
        allowed_commands: list[str] | None = None,
        blocked_commands: list[str] | None = None,
        timeout: int = 60,
    ) -> None:
        self.allowed_commands = allowed_commands
        self.blocked_commands = blocked_commands or [
            "rm -rf /",
            "rm -rf ~",
            "mkfs",
            "dd",
        ]
        self.timeout = timeout

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to execute",
                },
                "working_dir": {
                    "type": "string",
                    "description": "Working directory for the command",
                },
            },
            "required": ["command"],
        }

    def _is_command_allowed(self, command: str) -> tuple[bool, str | None]:
        """Check if command is allowed."""
        # Check blocked commands
        for blocked in self.blocked_commands:
            if blocked in command:
                return False, f"Command contains blocked operation: {blocked}"

        # If allowed_commands is specified, check against it
        if self.allowed_commands:
            # Check if command starts with any allowed command
            cmd_parts = shlex.split(command)
            cmd_name = cmd_parts[0] if cmd_parts else ""

            if not any(
                cmd_name == allowed or cmd_name.startswith(allowed + " ")
                for allowed in self.allowed_commands
            ):
                return (
                    False,
                    f"Command not in allowed list: {self.allowed_commands}",
                )

        return True, None

    async def execute(self, arguments: dict[str, Any]) -> Any:
        """Execute a bash command."""
        command = arguments.get("command")
        working_dir = arguments.get("working_dir")

        if not command:
            raise ToolException("Missing required argument: command")

        # Security checks
        is_allowed, error = self._is_command_allowed(command)
        if not is_allowed:
            raise ToolException(error)

        try:
            result = await asyncio.wait_for(
                self._run_command(command, working_dir),
                timeout=self.timeout,
            )
            return result
        except asyncio.TimeoutError:
            raise ToolException(
                f"Command timed out after {self.timeout} seconds",
                {"command": command, "timeout": self.timeout},
            )

    async def _run_command(
        self, command: str, working_dir: str | None = None
    ) -> dict[str, Any]:
        """Run a command and return stdout, stderr, returncode."""
        cwd = working_dir if working_dir else None

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )

            stdout, stderr = await process.communicate()

            return {
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
                "returncode": process.returncode,
            }

        except Exception as e:
            raise ToolException(
                f"Failed to execute command: {str(e)}",
                {"command": command},
            )
