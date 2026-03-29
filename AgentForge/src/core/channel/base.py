"""通道基类。"""

from abc import ABC, abstractmethod
from typing import Any


class BaseChannel(ABC):
    """消息通道基类 - 定义 Agent 与外界的交互接口。

    通道可以是:
    - CLI (命令行)
    - HTTP API
    - WebSocket
    - 消息队列
    """

    name: str = "base_channel"

    @abstractmethod
    async def receive(self) -> dict[str, Any]:
        """接收消息。

        Returns:
            消息字典 {type, content, ...}
        """
        pass

    @abstractmethod
    async def send(self, response: dict[str, Any]) -> None:
        """发送响应。

        Args:
            response: 响应字典
        """
        pass

    @abstractmethod
    async def send_error(self, error: str) -> None:
        """发送错误消息。

        Args:
            error: 错误描述
        """
        pass

    @abstractmethod
    async def send_status(self, status: str, details: dict[str, Any] | None = None) -> None:
        """发送状态更新。

        Args:
            status: 状态描述
            details: 详细信息
        """
        pass

    async def start(self) -> None:
        """启动通道。"""
        pass

    async def stop(self) -> None:
        """停止通道。"""
        pass

    async def __aenter__(self) -> "BaseChannel":
        """异步上下文管理器入口。"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步上下文管理器出口。"""
        await self.stop()
