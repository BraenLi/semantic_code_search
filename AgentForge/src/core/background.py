"""后台任务管理器 - 管理异步后台任务执行。

设计原则:
1. 异步命令执行 - 支持长时间运行的任务
2. 任务状态跟踪 - 记录任务状态和结果
3. 通知队列 - 任务完成时通知
"""

import asyncio
import subprocess
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Coroutine


class BackgroundTaskStatus(str, Enum):
    """后台任务状态枚举。"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BackgroundTask:
    """后台任务。"""

    id: str
    command: str
    status: BackgroundTaskStatus = BackgroundTaskStatus.PENDING
    workdir: str | None = None
    timeout: int = 300  # 5 minutes default
    started_at: str | None = None
    completed_at: str | None = None
    stdout: str = ""
    stderr: str = ""
    returncode: int | None = None
    pid: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典。"""
        return {
            "id": self.id,
            "command": self.command,
            "status": self.status.value,
            "workdir": self.workdir,
            "timeout": self.timeout,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "returncode": self.returncode,
            "pid": self.pid,
        }


class BackgroundManager:
    """后台任务管理器。

    使用方式:
        manager = BackgroundManager()
        task_id = manager.start("npm run build", workdir="/project")
        # ... do other work ...
        result = manager.get_result(task_id)
    """

    def __init__(self, max_output_length: int = 100000):
        """初始化后台任务管理器。

        Args:
            max_output_length: 输出最大长度
        """
        self.tasks: dict[str, BackgroundTask] = {}
        self.max_output_length = max_output_length
        self._processes: dict[str, subprocess.Popen] = {}
        self._async_tasks: dict[str, asyncio.Task] = {}
        self._notifications: list[dict[str, Any]] = []
        self._notification_callbacks: list[Callable[[dict], None]] = []

    def _generate_id(self) -> str:
        """生成任务 ID。"""
        return str(uuid.uuid4())[:8]

    def _truncate_output(self, output: str) -> str:
        """截断输出。"""
        if len(output) > self.max_output_length:
            return output[: self.max_output_length] + f"\n... [truncated, {len(output)} total chars]"
        return output

    def start(
        self,
        command: str,
        workdir: str | None = None,
        timeout: int = 300,
        env: dict[str, str] | None = None,
    ) -> str:
        """启动后台任务。

        Args:
            command: 要执行的命令
            workdir: 工作目录
            timeout: 超时时间（秒）
            env: 环境变量

        Returns:
            任务 ID
        """
        task_id = self._generate_id()
        task = BackgroundTask(
            id=task_id,
            command=command,
            workdir=workdir,
            timeout=timeout,
            status=BackgroundTaskStatus.RUNNING,
            started_at=datetime.now().isoformat(),
        )
        self.tasks[task_id] = task

        # Start the process
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=workdir,
                env=env,
            )
            self._processes[task_id] = process
            task.pid = process.pid
        except Exception as e:
            task.status = BackgroundTaskStatus.FAILED
            task.stderr = str(e)
            task.completed_at = datetime.now().isoformat()
            self._add_notification(task_id, "failed", str(e))

        return task_id

    async def start_async(
        self,
        command: str,
        workdir: str | None = None,
        timeout: int = 300,
        env: dict[str, str] | None = None,
    ) -> str:
        """异步启动后台任务。

        Args:
            command: 要执行的命令
            workdir: 工作目录
            timeout: 超时时间（秒）
            env: 环境变量

        Returns:
            任务 ID
        """
        task_id = self._generate_id()
        task = BackgroundTask(
            id=task_id,
            command=command,
            workdir=workdir,
            timeout=timeout,
            status=BackgroundTaskStatus.RUNNING,
            started_at=datetime.now().isoformat(),
        )
        self.tasks[task_id] = task

        # Create async task
        async_task = asyncio.create_task(
            self._run_async_command(task_id, command, workdir, timeout, env)
        )
        self._async_tasks[task_id] = async_task

        return task_id

    async def _run_async_command(
        self,
        task_id: str,
        command: str,
        workdir: str | None,
        timeout: int,
        env: dict[str, str] | None,
    ) -> None:
        """异步运行命令。"""
        task = self.tasks.get(task_id)
        if not task:
            return

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=workdir,
                env=env,
            )
            task.pid = process.pid

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
                task.stdout = self._truncate_output(stdout.decode() if stdout else "")
                task.stderr = self._truncate_output(stderr.decode() if stderr else "")
                task.returncode = process.returncode
                task.status = BackgroundTaskStatus.COMPLETED
                self._add_notification(task_id, "completed", "Task finished successfully")
            except asyncio.TimeoutError:
                process.kill()
                task.status = BackgroundTaskStatus.FAILED
                task.stderr = f"Task timed out after {timeout} seconds"
                self._add_notification(task_id, "timeout", task.stderr)

        except Exception as e:
            task.status = BackgroundTaskStatus.FAILED
            task.stderr = str(e)
            self._add_notification(task_id, "failed", str(e))

        finally:
            task.completed_at = datetime.now().isoformat()

    def get(self, task_id: str) -> BackgroundTask | None:
        """获取后台任务。

        Args:
            task_id: 任务 ID

        Returns:
            后台任务对象，不存在则返回 None
        """
        return self.tasks.get(task_id)

    def get_dict(self, task_id: str) -> dict[str, Any] | None:
        """获取后台任务字典。

        Args:
            task_id: 任务 ID

        Returns:
            任务字典，不存在则返回 None
        """
        task = self.get(task_id)
        return task.to_dict() if task else None

    def get_result(self, task_id: str, wait: bool = True, timeout: float | None = None) -> dict[str, Any]:
        """获取任务结果。

        Args:
            task_id: 任务 ID
            wait: 是否等待任务完成
            timeout: 等待超时时间（秒）

        Returns:
            任务结果字典
        """
        task = self.get(task_id)
        if task is None:
            return {"error": f"Task not found: {task_id}"}

        if wait and task.status == BackgroundTaskStatus.RUNNING:
            self._wait_for_task(task_id, timeout)
            task = self.get(task_id)  # Refresh

        return task.to_dict() if task else {"error": "Task disappeared"}

    def _wait_for_task(self, task_id: str, timeout: float | None = None) -> None:
        """等待任务完成。"""
        process = self._processes.get(task_id)
        if process is None:
            return

        task = self.tasks.get(task_id)
        if task is None:
            return

        try:
            stdout, stderr = process.communicate(timeout=timeout or task.timeout)
            task.stdout = self._truncate_output(stdout)
            task.stderr = self._truncate_output(stderr)
            task.returncode = process.returncode
            task.status = BackgroundTaskStatus.COMPLETED if process.returncode == 0 else BackgroundTaskStatus.FAILED
            task.completed_at = datetime.now().isoformat()
            self._add_notification(task_id, "completed", "Task finished")
        except subprocess.TimeoutExpired:
            process.kill()
            task.status = BackgroundTaskStatus.FAILED
            task.stderr = f"Task timed out after {timeout or task.timeout} seconds"
            task.completed_at = datetime.now().isoformat()
            self._add_notification(task_id, "timeout", task.stderr)
        finally:
            del self._processes[task_id]

    def cancel(self, task_id: str) -> bool:
        """取消任务。

        Args:
            task_id: 任务 ID

        Returns:
            是否成功
        """
        task = self.get(task_id)
        if task is None or task.status != BackgroundTaskStatus.RUNNING:
            return False

        # Kill the process
        process = self._processes.get(task_id)
        if process:
            process.kill()
            del self._processes[task_id]

        # Cancel async task
        async_task = self._async_tasks.get(task_id)
        if async_task:
            async_task.cancel()
            del self._async_tasks[task_id]

        task.status = BackgroundTaskStatus.CANCELLED
        task.completed_at = datetime.now().isoformat()
        self._add_notification(task_id, "cancelled", "Task was cancelled")

        return True

    def list_running(self) -> list[dict[str, Any]]:
        """列出运行中的任务。

        Returns:
            运行中任务列表
        """
        return [
            task.to_dict()
            for task in self.tasks.values()
            if task.status == BackgroundTaskStatus.RUNNING
        ]

    def list_all(self) -> list[dict[str, Any]]:
        """列出所有任务。

        Returns:
            所有任务列表
        """
        return [task.to_dict() for task in self.tasks.values()]

    def cleanup(self) -> int:
        """清理已完成/失败的任务。

        Returns:
            清理的任务数量
        """
        to_remove = [
            task_id
            for task_id, task in self.tasks.items()
            if task.status in (BackgroundTaskStatus.COMPLETED, BackgroundTaskStatus.FAILED, BackgroundTaskStatus.CANCELLED)
        ]
        for task_id in to_remove:
            del self.tasks[task_id]
            self._processes.pop(task_id, None)
            self._async_tasks.pop(task_id, None)
        return len(to_remove)

    def _add_notification(self, task_id: str, event: str, message: str) -> None:
        """添加通知。"""
        notification = {
            "task_id": task_id,
            "event": event,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }
        self._notifications.append(notification)

        # Call callbacks
        for callback in self._notification_callbacks:
            try:
                callback(notification)
            except Exception:
                pass

    def add_notification_callback(self, callback: Callable[[dict], None]) -> None:
        """添加通知回调。

        Args:
            callback: 回调函数
        """
        self._notification_callbacks.append(callback)

    def get_notifications(self, clear: bool = True) -> list[dict[str, Any]]:
        """获取通知。

        Args:
            clear: 是否清除已获取的通知

        Returns:
            通知列表
        """
        notifications = self._notifications.copy()
        if clear:
            self._notifications.clear()
        return notifications

    def get_status_summary(self) -> dict[str, int]:
        """获取状态摘要。

        Returns:
            各状态的任务数量
        """
        counts = {status.value: 0 for status in BackgroundTaskStatus}
        for task in self.tasks.values():
            counts[task.status.value] += 1
        counts["total"] = len(self.tasks)
        return counts

    async def wait_all(self, timeout: float | None = None) -> None:
        """等待所有运行中的任务完成。

        Args:
            timeout: 总超时时间
        """
        running_tasks = list(self._async_tasks.values())
        if running_tasks:
            try:
                await asyncio.wait(running_tasks, timeout=timeout)
            except Exception:
                pass