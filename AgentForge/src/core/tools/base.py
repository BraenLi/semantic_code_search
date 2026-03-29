"""工具基类。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolMetadata:
    """工具元数据。"""

    timeout: int = 60  # 执行超时时间（秒）
    dangerous: bool = False  # 是否为危险工具
    requires_confirmation: bool = False  # 是否需要用户确认
    category: str = "general"  # 工具分类
    tags: list[str] = field(default_factory=list)  # 标签


class BaseTool(ABC):
    """工具基类 - 所有工具必须继承此类。

    Attributes:
        name: 工具名称
        description: 工具描述
        metadata: 工具元数据
    """

    name: str = "base_tool"
    description: str = "Base tool"
    metadata: ToolMetadata = ToolMetadata()

    @abstractmethod
    def execute(self, **kwargs: Any) -> Any:
        """执行工具。

        Args:
            **kwargs: 工具参数

        Returns:
            工具执行结果
        """
        pass

    def validate_params(self, **kwargs: Any) -> tuple[bool, str | None]:
        """验证参数安全性。

        子类可以重写此方法来实现自定义安全验证。

        Args:
            **kwargs: 工具参数

        Returns:
            (是否安全, 错误信息)
        """
        return True, None

    def validate_execution(self, **kwargs: Any) -> tuple[bool, str | None]:
        """验证是否可以执行。

        在执行前调用，用于检查权限、状态等。

        Args:
            **kwargs: 工具参数

        Returns:
            (是否可以执行, 错误信息)
        """
        return self.validate_params(**kwargs)

    def to_openai_tool(self) -> dict:
        """转换为 OpenAI tool format。

        Returns:
            OpenAI tool 格式的字典
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.get_parameters_schema(),
            },
        }

    def get_parameters_schema(self) -> dict:
        """获取参数 schema。

        子类可以重写此方法来定义工具参数的 JSON Schema。

        Returns:
            JSON Schema 格式的参数字典
        """
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    def safe_execute(self, **kwargs: Any) -> Any:
        """安全执行工具。

        先验证参数，再执行工具。

        Args:
            **kwargs: 工具参数

        Returns:
            工具执行结果或错误字典
        """
        is_valid, error = self.validate_execution(**kwargs)
        if not is_valid:
            return {"success": False, "error": error, "error_type": "validation"}

        try:
            result = self.execute(**kwargs)
            return result
        except Exception as e:
            return {"success": False, "error": str(e), "error_type": "execution"}
