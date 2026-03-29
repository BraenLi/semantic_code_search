"""SubAgent - 子 Agent 实现。

设计原则:
1. 上下文隔离 - SubAgent 有独立的消息历史
2. 任务分发 - 父 Agent 可以将复杂任务分解给 SubAgent
3. 结果合并 - SubAgent 的结果整合回父上下文
"""

from typing import Any

from ..agent import Agent
from ..context import ContextProcessor


class SubAgent(Agent):
    """子 Agent 类 - 用于任务分发和上下文隔离。

    使用场景:
    1. 复杂任务分解 - 将大任务拆分为小任务
    2. 专业化处理 - 不同 SubAgent 专注不同领域
    3. 并行执行 - 多个 SubAgent 可以同时处理不同任务
    4. 上下文管理 - 避免长对话污染主上下文
    """

    def __init__(
        self,
        parent: Agent | None = None,
        model_name: str | None = None,
        tools: list[dict] | None = None,
        system_prompt: str = "",
        task_description: str = "",
        **kwargs,
    ):
        """初始化 SubAgent。

        Args:
            parent: 父 Agent 实例
            model_name: 模型名称
            tools: 工具列表
            system_prompt: 系统提示词
            task_description: 任务描述
            **kwargs: 其他 Agent 参数
        """
        super().__init__(
            model_name=model_name,
            tools=tools,
            system_prompt=system_prompt,
            **kwargs,
        )

        self.parent = parent
        self.task_description = task_description

        # 如果有父 Agent，初始化隔离的上下文
        if parent is not None:
            self._init_isolated_context()

    def _init_isolated_context(self) -> None:
        """从父 Agent 初始化隔离的上下文。"""
        if self.parent:
            self.messages = ContextProcessor.isolate_subagent(
                self.parent.messages,
                self.task_description,
            )

    def run(self, query: str, stream: bool = False) -> str:
        """执行子 Agent 循环。

        Args:
            query: 用户查询 (会附加到任务描述后)
            stream: 是否流式输出

        Returns:
            模型最终响应内容
        """
        # 如果有额外的查询，添加到上下文
        if query:
            full_query = f"{self.task_description}\n\n{query}" if self.task_description else query
        else:
            full_query = self.task_description

        return super().run(full_query, stream=stream)

    def get_result(self) -> dict[str, Any]:
        """获取 SubAgent 执行结果。

        Returns:
            执行结果字典
        """
        return {
            "task": self.task_description,
            "messages": self.messages.copy(),
            "last_response": self.messages[-1].get("content", "") if self.messages else "",
        }

    def merge_to_parent(self) -> None:
        """将 SubAgent 结果合并到父 Agent 上下文。

        Raises:
            RuntimeError: 没有父 Agent
        """
        if self.parent is None:
            raise RuntimeError("No parent agent to merge to")

        ContextProcessor.merge_subagent_result(
            self.parent.messages,
            self.messages[-1].get("content", "") if self.messages else "",
            self.task_description,
        )

    @classmethod
    def create_specialized(
        cls,
        role: str,
        expertise: str,
        tools: list[dict] | None = None,
        **kwargs,
    ) -> "SubAgent":
        """创建一个专业化的 SubAgent。

        Args:
            role: 角色名称 (如 "代码审查员", "技术作家")
            expertise: 专业领域描述
            tools: 工具列表
            **kwargs: 其他参数

        Returns:
            SubAgent 实例
        """
        system_prompt = f"""You are a {role} specializing in {expertise}.

Responsibilities:
- Focus on tasks related to {expertise}
- Provide expert-level analysis and solutions
- Stay in character as a {role}

When you complete a task, provide a clear summary of your findings or actions."""

        return cls(system_prompt=system_prompt, tools=tools, **kwargs)
