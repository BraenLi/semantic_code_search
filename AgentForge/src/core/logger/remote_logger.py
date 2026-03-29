"""远程日志记录 - 云端回传。"""

import json
from typing import Any

import httpx


class RemoteLogger:
    """远程日志记录器 - 将日志发送到远程 API。

    使用场景:
    - 集中式日志收集
    - 多实例日志聚合
    - 实时监控和告警
    """

    def __init__(
        self,
        endpoint: str,
        api_key: str | None = None,
        batch_size: int = 10,
        timeout: float = 5.0,
    ):
        """初始化远程日志记录器。

        Args:
            endpoint: 日志接收端点 URL
            api_key: API Key (可选)
            batch_size: 批量发送大小
            timeout: 请求超时时间 (秒)
        """
        self.endpoint = endpoint
        self.api_key = api_key
        self.batch_size = batch_size
        self.timeout = timeout

        self._buffer: list[dict[str, Any]] = []
        self._client = httpx.AsyncClient(timeout=timeout)

    async def log(
        self,
        level: str,
        message: str,
        **kwargs: Any,
    ) -> None:
        """记录日志。

        Args:
            level: 日志级别
            message: 日志消息
            **kwargs: 额外字段
        """
        log_entry = {
            "level": level,
            "message": message,
            "extra": kwargs,
        }

        self._buffer.append(log_entry)

        # 达到批量大小时发送
        if len(self._buffer) >= self.batch_size:
            await self._flush()

    async def debug(self, message: str, **kwargs: Any) -> None:
        """记录 debug 日志。"""
        await self.log("debug", message, **kwargs)

    async def info(self, message: str, **kwargs: Any) -> None:
        """记录 info 日志。"""
        await self.log("info", message, **kwargs)

    async def warning(self, message: str, **kwargs: Any) -> None:
        """记录 warning 日志。"""
        await self.log("warning", message, **kwargs)

    async def error(self, message: str, **kwargs: Any) -> None:
        """记录 error 日志。"""
        await self.log("error", message, **kwargs)

    async def _flush(self) -> None:
        """刷新缓冲区。"""
        if not self._buffer:
            return

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            response = await self._client.post(
                self.endpoint,
                json={"logs": self._buffer},
                headers=headers,
            )
            response.raise_for_status()
            self._buffer.clear()
        except Exception as e:
            # 发送失败，保留在缓冲区
            print(f"Failed to send logs: {e}")

    async def close(self) -> None:
        """关闭记录器并刷新剩余日志。"""
        await self._flush()
        await self._client.aclose()

    async def __aenter__(self) -> "RemoteLogger":
        """异步上下文管理器入口。"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步上下文管理器出口。"""
        await self.close()
