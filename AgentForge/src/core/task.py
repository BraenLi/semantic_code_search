"""任务管理器 - 基于文件的持久化任务管理。

设计原则:
1. 文件持久化 - 任务保存在 JSON 文件中
2. 任务依赖 - 支持 blockedBy/blocks 关系
3. 任务认领 - owner 机制
4. 状态管理 - pending, in_progress, completed, deleted
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class TaskStatus(str, Enum):
    """任务状态枚举。"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELETED = "deleted"


@dataclass
class Task:
    """任务数据类。"""

    id: str
    subject: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    owner: str | None = None
    active_form: str | None = None
    blocked_by: list[str] = field(default_factory=list)  # IDs of tasks that block this one
    blocks: list[str] = field(default_factory=list)  # IDs of tasks this one blocks
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典。"""
        return {
            "id": self.id,
            "subject": self.subject,
            "description": self.description,
            "status": self.status.value,
            "owner": self.owner,
            "active_form": self.active_form,
            "blocked_by": self.blocked_by,
            "blocks": self.blocks,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Task":
        """从字典创建任务。"""
        return cls(
            id=data["id"],
            subject=data["subject"],
            description=data["description"],
            status=TaskStatus(data.get("status", "pending")),
            owner=data.get("owner"),
            active_form=data.get("active_form"),
            blocked_by=data.get("blocked_by", []),
            blocks=data.get("blocks", []),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            metadata=data.get("metadata", {}),
        )


class TaskManager:
    """任务管理器 - 管理持久化的任务。

    使用方式:
        manager = TaskManager()
        task_id = manager.create("实现登录", "实现用户登录 API")
        manager.start(task_id)
        manager.complete(task_id)
    """

    def __init__(self, storage_path: str | Path | None = None):
        """初始化任务管理器。

        Args:
            storage_path: 任务存储路径，默认为 .agentforge/tasks.json
        """
        if storage_path is None:
            storage_path = Path.cwd() / ".agentforge" / "tasks.json"
        else:
            storage_path = Path(storage_path)

        self.storage_path = storage_path
        self.tasks: dict[str, Task] = {}
        self._load()

    def _load(self) -> None:
        """从文件加载任务。"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for task_data in data.get("tasks", []):
                    task = Task.from_dict(task_data)
                    self.tasks[task.id] = task
            except (json.JSONDecodeError, KeyError):
                self.tasks = {}

    def _save(self) -> None:
        """保存任务到文件。"""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "tasks": [task.to_dict() for task in self.tasks.values()],
            "updated_at": datetime.now().isoformat(),
        }
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _generate_id(self) -> str:
        """生成任务 ID。"""
        max_id = 0
        for task_id in self.tasks:
            try:
                num = int(task_id)
                max_id = max(max_id, num)
            except ValueError:
                pass
        return str(max_id + 1)

    def create(
        self,
        subject: str,
        description: str,
        active_form: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """创建任务。

        Args:
            subject: 任务标题
            description: 任务描述
            active_form: 活动描述
            metadata: 元数据

        Returns:
            任务 ID
        """
        task_id = self._generate_id()
        task = Task(
            id=task_id,
            subject=subject,
            description=description,
            active_form=active_form,
            metadata=metadata or {},
        )
        self.tasks[task_id] = task
        self._save()
        return task_id

    def get(self, task_id: str) -> Task | None:
        """获取任务。

        Args:
            task_id: 任务 ID

        Returns:
            任务对象，不存在则返回 None
        """
        return self.tasks.get(task_id)

    def get_dict(self, task_id: str) -> dict[str, Any] | None:
        """获取任务字典。

        Args:
            task_id: 任务 ID

        Returns:
            任务字典，不存在则返回 None
        """
        task = self.get(task_id)
        return task.to_dict() if task else None

    def update(
        self,
        task_id: str,
        subject: str | None = None,
        description: str | None = None,
        active_form: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """更新任务。

        Args:
            task_id: 任务 ID
            subject: 新标题
            description: 新描述
            active_form: 新活动描述
            metadata: 要合并的元数据

        Returns:
            是否成功
        """
        task = self.get(task_id)
        if task is None:
            return False

        if subject is not None:
            task.subject = subject
        if description is not None:
            task.description = description
        if active_form is not None:
            task.active_form = active_form
        if metadata is not None:
            task.metadata.update(metadata)

        task.updated_at = datetime.now().isoformat()
        self._save()
        return True

    def start(self, task_id: str, owner: str | None = None) -> bool:
        """开始处理任务。

        Args:
            task_id: 任务 ID
            owner: 认领者

        Returns:
            是否成功
        """
        task = self.get(task_id)
        if task is None:
            return False

        # 检查是否有未完成的依赖
        for blocker_id in task.blocked_by:
            blocker = self.get(blocker_id)
            if blocker and blocker.status != TaskStatus.COMPLETED:
                return False  # 有阻塞任务未完成

        task.status = TaskStatus.IN_PROGRESS
        if owner:
            task.owner = owner
        task.updated_at = datetime.now().isoformat()
        self._save()
        return True

    def complete(self, task_id: str) -> bool:
        """完成任务。

        Args:
            task_id: 任务 ID

        Returns:
            是否成功
        """
        task = self.get(task_id)
        if task is None:
            return False

        task.status = TaskStatus.COMPLETED
        task.active_form = None
        task.updated_at = datetime.now().isoformat()
        self._save()
        return True

    def delete(self, task_id: str) -> bool:
        """删除任务。

        Args:
            task_id: 任务 ID

        Returns:
            是否成功
        """
        task = self.get(task_id)
        if task is None:
            return False

        task.status = TaskStatus.DELETED
        task.updated_at = datetime.now().isoformat()
        self._save()
        return True

    def claim(self, task_id: str, owner: str) -> bool:
        """认领任务。

        Args:
            task_id: 任务 ID
            owner: 认领者

        Returns:
            是否成功
        """
        task = self.get(task_id)
        if task is None:
            return False

        task.owner = owner
        task.updated_at = datetime.now().isoformat()
        self._save()
        return True

    def add_dependency(self, task_id: str, depends_on: str) -> bool:
        """添加任务依赖。

        Args:
            task_id: 任务 ID
            depends_on: 依赖的任务 ID

        Returns:
            是否成功
        """
        task = self.get(task_id)
        dependency = self.get(depends_on)
        if task is None or dependency is None:
            return False

        if depends_on not in task.blocked_by:
            task.blocked_by.append(depends_on)
        if task_id not in dependency.blocks:
            dependency.blocks.append(task_id)

        self._save()
        return True

    def remove_dependency(self, task_id: str, depends_on: str) -> bool:
        """移除任务依赖。

        Args:
            task_id: 任务 ID
            depends_on: 依赖的任务 ID

        Returns:
            是否成功
        """
        task = self.get(task_id)
        dependency = self.get(depends_on)
        if task is None or dependency is None:
            return False

        if depends_on in task.blocked_by:
            task.blocked_by.remove(depends_on)
        if task_id in dependency.blocks:
            dependency.blocks.remove(task_id)

        self._save()
        return True

    def get_blocked_tasks(self, task_id: str) -> list[Task]:
        """获取被指定任务阻塞的任务。

        Args:
            task_id: 任务 ID

        Returns:
            被阻塞的任务列表
        """
        task = self.get(task_id)
        if task is None:
            return []

        return [self.tasks[tid] for tid in task.blocks if tid in self.tasks]

    def get_blocking_tasks(self, task_id: str) -> list[Task]:
        """获取阻塞指定任务的任务。

        Args:
            task_id: 任务 ID

        Returns:
            阻塞的任务列表
        """
        task = self.get(task_id)
        if task is None:
            return []

        return [self.tasks[tid] for tid in task.blocked_by if tid in self.tasks]

    def list_all(self, status: TaskStatus | None = None) -> list[dict[str, Any]]:
        """列出所有任务。

        Args:
            status: 筛选状态，None 表示所有状态

        Returns:
            任务字典列表
        """
        tasks = []
        for task in self.tasks.values():
            if task.status == TaskStatus.DELETED:
                continue
            if status is None or task.status == status:
                tasks.append(task.to_dict())
        return tasks

    def get_available(self) -> list[dict[str, Any]]:
        """获取可用的任务（无阻塞且未认领）。

        Returns:
            可用任务列表
        """
        available = []
        for task in self.tasks.values():
            if task.status != TaskStatus.PENDING:
                continue
            if task.owner is not None:
                continue
            # 检查是否有未完成的依赖
            blocked = False
            for blocker_id in task.blocked_by:
                blocker = self.get(blocker_id)
                if blocker and blocker.status != TaskStatus.COMPLETED:
                    blocked = True
                    break
            if not blocked:
                available.append(task.to_dict())
        return available

    def get_in_progress(self) -> list[dict[str, Any]]:
        """获取进行中的任务。

        Returns:
            进行中任务列表
        """
        return self.list_all(status=TaskStatus.IN_PROGRESS)

    def get_status_summary(self) -> dict[str, int]:
        """获取状态摘要。

        Returns:
            各状态的任务数量
        """
        counts = {status.value: 0 for status in TaskStatus}
        for task in self.tasks.values():
            counts[task.status.value] += 1
        counts["total"] = sum(v for k, v in counts.items() if k != "deleted")
        return counts

    def clear_deleted(self) -> int:
        """清除已删除的任务。

        Returns:
            清除的任务数量
        """
        to_delete = [tid for tid, task in self.tasks.items() if task.status == TaskStatus.DELETED]
        for tid in to_delete:
            del self.tasks[tid]
        self._save()
        return len(to_delete)

    def reload(self) -> None:
        """重新加载任务文件。"""
        self.tasks.clear()
        self._load()