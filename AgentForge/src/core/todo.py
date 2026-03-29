"""Todo 管理器 - 管理任务列表。

设计原则:
1. 状态管理: pending, in_progress, completed
2. activeForm 支持 - 显示正在进行的活动
3. 最大 20 条限制
4. 单条 in_progress 约束
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TodoStatus(str, Enum):
    """Todo 状态枚举。"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass
class TodoItem:
    """Todo 条目。"""

    id: str
    content: str
    status: TodoStatus = TodoStatus.PENDING
    active_form: str | None = None  # 正在进行时的活动描述

    def to_dict(self) -> dict[str, Any]:
        """转换为字典。"""
        return {
            "id": self.id,
            "content": self.content,
            "status": self.status.value,
            "active_form": self.active_form,
        }


@dataclass
class TodoList:
    """Todo 列表。"""

    items: list[TodoItem] = field(default_factory=list)
    max_items: int = 20

    def add(self, content: str, active_form: str | None = None) -> TodoItem | None:
        """添加 Todo 条目。

        Args:
            content: 条目内容
            active_form: 活动描述

        Returns:
            新建的 Todo 条目，如果达到上限则返回 None
        """
        if len(self.items) >= self.max_items:
            return None

        # 生成 ID
        todo_id = str(len(self.items) + 1)
        while any(item.id == todo_id for item in self.items):
            todo_id = str(int(todo_id) + 1)

        item = TodoItem(
            id=todo_id,
            content=content,
            status=TodoStatus.PENDING,
            active_form=active_form,
        )
        self.items.append(item)
        return item

    def get(self, todo_id: str) -> TodoItem | None:
        """获取 Todo 条目。

        Args:
            todo_id: 条目 ID

        Returns:
            Todo 条目，不存在则返回 None
        """
        for item in self.items:
            if item.id == todo_id:
                return item
        return None

    def start(self, todo_id: str, active_form: str | None = None) -> bool:
        """开始处理 Todo 条目。

        将状态设为 in_progress。同时会将其他 in_progress 条目设为 pending。

        Args:
            todo_id: 条目 ID
            active_form: 活动描述

        Returns:
            是否成功
        """
        item = self.get(todo_id)
        if item is None:
            return False

        # 确保只有一条 in_progress
        for other in self.items:
            if other.status == TodoStatus.IN_PROGRESS and other.id != todo_id:
                other.status = TodoStatus.PENDING

        item.status = TodoStatus.IN_PROGRESS
        if active_form:
            item.active_form = active_form
        return True

    def complete(self, todo_id: str) -> bool:
        """完成 Todo 条目。

        Args:
            todo_id: 条目 ID

        Returns:
            是否成功
        """
        item = self.get(todo_id)
        if item is None:
            return False

        item.status = TodoStatus.COMPLETED
        item.active_form = None
        return True

    def remove(self, todo_id: str) -> bool:
        """移除 Todo 条目。

        Args:
            todo_id: 条目 ID

        Returns:
            是否成功
        """
        for i, item in enumerate(self.items):
            if item.id == todo_id:
                self.items.pop(i)
                return True
        return False

    def get_active(self) -> TodoItem | None:
        """获取当前正在进行的活动。

        Returns:
            当前 in_progress 的条目，没有则返回 None
        """
        for item in self.items:
            if item.status == TodoStatus.IN_PROGRESS:
                return item
        return None

    def get_pending(self) -> list[TodoItem]:
        """获取所有待处理的条目。

        Returns:
            待处理条目列表
        """
        return [item for item in self.items if item.status == TodoStatus.PENDING]

    def get_completed(self) -> list[TodoItem]:
        """获取所有已完成的条目。

        Returns:
            已完成条目列表
        """
        return [item for item in self.items if item.status == TodoStatus.COMPLETED]

    def clear_completed(self) -> int:
        """清除所有已完成的条目。

        Returns:
            清除的条目数量
        """
        initial_count = len(self.items)
        self.items = [item for item in self.items if item.status != TodoStatus.COMPLETED]
        return initial_count - len(self.items)

    def to_dict_list(self) -> list[dict[str, Any]]:
        """转换为字典列表。

        Returns:
            字典列表
        """
        return [item.to_dict() for item in self.items]


class TodoManager:
    """Todo 管理器 - 管理 Agent 的任务列表。

    使用方式:
        manager = TodoManager()
        manager.add("实现用户登录功能")
        manager.start("1", "正在实现登录 API")
        manager.complete("1")
    """

    def __init__(self, max_items: int = 20):
        """初始化 Todo 管理器。

        Args:
            max_items: 最大条目数
        """
        self._todo_list = TodoList(max_items=max_items)

    def add(self, content: str, active_form: str | None = None) -> str | None:
        """添加 Todo 条目。

        Args:
            content: 条目内容
            active_form: 活动描述

        Returns:
            新建条目的 ID，如果达到上限则返回 None
        """
        item = self._todo_list.add(content, active_form)
        return item.id if item else None

    def get(self, todo_id: str) -> dict[str, Any] | None:
        """获取 Todo 条目。

        Args:
            todo_id: 条目 ID

        Returns:
            条目字典，不存在则返回 None
        """
        item = self._todo_list.get(todo_id)
        return item.to_dict() if item else None

    def start(self, todo_id: str, active_form: str | None = None) -> bool:
        """开始处理 Todo 条目。

        Args:
            todo_id: 条目 ID
            active_form: 活动描述

        Returns:
            是否成功
        """
        return self._todo_list.start(todo_id, active_form)

    def complete(self, todo_id: str) -> bool:
        """完成 Todo 条目。

        Args:
            todo_id: 条目 ID

        Returns:
            是否成功
        """
        return self._todo_list.complete(todo_id)

    def remove(self, todo_id: str) -> bool:
        """移除 Todo 条目。

        Args:
            todo_id: 条目 ID

        Returns:
            是否成功
        """
        return self._todo_list.remove(todo_id)

    def get_active(self) -> dict[str, Any] | None:
        """获取当前正在进行的活动。

        Returns:
            当前 in_progress 的条目字典，没有则返回 None
        """
        item = self._todo_list.get_active()
        return item.to_dict() if item else None

    def list_all(self) -> list[dict[str, Any]]:
        """列出所有 Todo 条目。

        Returns:
            条目字典列表
        """
        return self._todo_list.to_dict_list()

    def get_active_form(self) -> str | None:
        """获取当前活动的描述。

        Returns:
            活动描述字符串，没有正在进行的活动则返回 None
        """
        item = self._todo_list.get_active()
        if item:
            return item.active_form or f"Working on: {item.content}"
        return None

    def clear_completed(self) -> int:
        """清除所有已完成的条目。

        Returns:
            清除的条目数量
        """
        return self._todo_list.clear_completed()

    def get_status_summary(self) -> dict[str, int]:
        """获取状态摘要。

        Returns:
            各状态的条目数量
        """
        return {
            "pending": len(self._todo_list.get_pending()),
            "in_progress": 1 if self._todo_list.get_active() else 0,
            "completed": len(self._todo_list.get_completed()),
            "total": len(self._todo_list.items),
        }

    def to_tool_definition(self) -> dict:
        """生成工具定义。

        Returns:
            OpenAI tool 格式的工具定义
        """
        return {
            "type": "function",
            "function": {
                "name": "todo",
                "description": "Manage a task list for tracking progress. Use this to organize work into manageable tasks.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["add", "start", "complete", "remove", "list"],
                            "description": "Action to perform: add, start, complete, remove, or list",
                        },
                        "todo_id": {
                            "type": "string",
                            "description": "Todo item ID (for start, complete, remove actions)",
                        },
                        "content": {
                            "type": "string",
                            "description": "Todo content (for add action)",
                        },
                        "active_form": {
                            "type": "string",
                            "description": "Active form description (for start action)",
                        },
                    },
                    "required": ["action"],
                },
            },
        }

    def execute_tool(self, action: str, **kwargs: Any) -> dict[str, Any]:
        """执行 Todo 工具。

        Args:
            action: 操作类型
            **kwargs: 其他参数

        Returns:
            执行结果
        """
        if action == "add":
            content = kwargs.get("content", "")
            active_form = kwargs.get("active_form")
            todo_id = self.add(content, active_form)
            if todo_id:
                return {"success": True, "todo_id": todo_id, "message": f"Added todo: {content}"}
            return {"success": False, "error": "Maximum todo items reached"}

        elif action == "start":
            todo_id = kwargs.get("todo_id")
            active_form = kwargs.get("active_form")
            if not todo_id:
                return {"success": False, "error": "todo_id is required for start action"}
            if self.start(todo_id, active_form):
                return {"success": True, "message": f"Started todo: {todo_id}"}
            return {"success": False, "error": f"Todo not found: {todo_id}"}

        elif action == "complete":
            todo_id = kwargs.get("todo_id")
            if not todo_id:
                return {"success": False, "error": "todo_id is required for complete action"}
            if self.complete(todo_id):
                return {"success": True, "message": f"Completed todo: {todo_id}"}
            return {"success": False, "error": f"Todo not found: {todo_id}"}

        elif action == "remove":
            todo_id = kwargs.get("todo_id")
            if not todo_id:
                return {"success": False, "error": "todo_id is required for remove action"}
            if self.remove(todo_id):
                return {"success": True, "message": f"Removed todo: {todo_id}"}
            return {"success": False, "error": f"Todo not found: {todo_id}"}

        elif action == "list":
            return {
                "success": True,
                "todos": self.list_all(),
                "summary": self.get_status_summary(),
            }

        else:
            return {"success": False, "error": f"Unknown action: {action}"}