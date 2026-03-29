"""工具注册表。"""

from typing import Any

from .base import BaseTool, ToolMetadata


class ToolRegistry:
    """工具注册表 - 管理所有可用工具。

    使用方式:
        registry = ToolRegistry()
        registry.register(MyTool())
        tools = registry.get_tools()  # 获取所有工具实例
        tool_defs = registry.get_openai_tools()  # 获取 OpenAI 格式的工具定义
    """

    def __init__(self):
        """初始化工具注册表。"""
        self._tools: dict[str, BaseTool] = {}
        self._categories: dict[str, list[str]] = {}

    def register(self, tool: BaseTool, category: str | None = None) -> None:
        """注册工具。

        Args:
            tool: 工具实例
            category: 工具分类（可选）

        Raises:
            ValueError: 工具名称已存在
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered")
        self._tools[tool.name] = tool

        # Track category
        cat = category or tool.metadata.category
        if cat not in self._categories:
            self._categories[cat] = []
        self._categories[cat].append(tool.name)

    def unregister(self, name: str) -> None:
        """注销工具。

        Args:
            name: 工具名称

        Raises:
            KeyError: 工具不存在
        """
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found")
        tool = self._tools[name]
        # Remove from category
        for cat, tools in self._categories.items():
            if name in tools:
                tools.remove(name)
        del self._tools[name]

    def get(self, name: str) -> BaseTool:
        """获取工具。

        Args:
            name: 工具名称

        Returns:
            工具实例

        Raises:
            KeyError: 工具不存在
        """
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found")
        return self._tools[name]

    def get_metadata(self, name: str) -> ToolMetadata:
        """获取工具元数据。

        Args:
            name: 工具名称

        Returns:
            工具元数据

        Raises:
            KeyError: 工具不存在
        """
        return self.get(name).metadata

    def execute(self, name: str, **kwargs: Any) -> Any:
        """执行工具。

        Args:
            name: 工具名称
            **kwargs: 工具参数

        Returns:
            工具执行结果

        Raises:
            KeyError: 工具不存在
        """
        tool = self.get(name)
        return tool.execute(**kwargs)

    def safe_execute(self, name: str, **kwargs: Any) -> Any:
        """安全执行工具（带验证）。

        Args:
            name: 工具名称
            **kwargs: 工具参数

        Returns:
            工具执行结果
        """
        tool = self.get(name)
        return tool.safe_execute(**kwargs)

    def get_tools(self) -> list[BaseTool]:
        """获取所有工具实例。

        Returns:
            工具实例列表
        """
        return list(self._tools.values())

    def get_openai_tools(self) -> list[dict]:
        """获取所有工具的 OpenAI 格式定义。

        Returns:
            OpenAI tool 格式的列表
        """
        return [tool.to_openai_tool() for tool in self._tools.values()]

    def list_names(self) -> list[str]:
        """获取所有工具名称。

        Returns:
            工具名称列表
        """
        return list(self._tools.keys())

    def get_dangerous_tools(self) -> list[str]:
        """获取所有危险工具名称。

        Returns:
            危险工具名称列表
        """
        return [name for name, tool in self._tools.items() if tool.metadata.dangerous]

    def get_tools_by_category(self, category: str) -> list[BaseTool]:
        """获取指定分类的工具。

        Args:
            category: 分类名称

        Returns:
            该分类下的工具列表
        """
        if category not in self._categories:
            return []
        return [self._tools[name] for name in self._categories[category]]

    def get_categories(self) -> list[str]:
        """获取所有分类。

        Returns:
            分类列表
        """
        return list(self._categories.keys())

    def clear(self) -> None:
        """清空所有工具。"""
        self._tools.clear()
        self._categories.clear()

    def has_tool(self, name: str) -> bool:
        """检查工具是否存在。

        Args:
            name: 工具名称

        Returns:
            是否存在
        """
        return name in self._tools

    def __contains__(self, name: str) -> bool:
        """支持 'in' 操作符。"""
        return name in self._tools

    def __len__(self) -> int:
        """返回工具数量。"""
        return len(self._tools)
