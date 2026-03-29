"""HTTP API 通道。"""

import asyncio
import json
from typing import Any, Callable

from aiohttp import web

from .base import BaseChannel


class APIChannel(BaseChannel):
    """HTTP API 通道 - RESTful API 交互。

    端点:
    - POST /message - 发送消息
    - GET /status - 获取状态
    - POST /reset - 重置会话
    """

    name = "api"

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8080,
        message_handler: Callable | None = None,
    ):
        """初始化 API 通道。

        Args:
            host: 监听地址
            port: 监听端口
            message_handler: 消息处理回调
        """
        self.host = host
        self.port = port
        self.message_handler = message_handler

        self._app = web.Application()
        self._runner: web.AppRunner | None = None
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._last_response: dict[str, Any] = {}

        self._setup_routes()

    def _setup_routes(self) -> None:
        """设置路由。"""
        self._app.router.add_post("/message", self._handle_message)
        self._app.router.add_get("/status", self._handle_status)
        self._app.router.add_post("/reset", self._handle_reset)

    async def _handle_message(self, request: web.Request) -> web.Response:
        """处理消息请求。"""
        try:
            data = await request.json()
            content = data.get("content", "")

            if not content:
                return web.json_response({"error": "Missing content"}, status=400)

            # 放入消息队列
            await self._message_queue.put({"type": "message", "content": content})

            # 等待响应
            response = self._last_response
            self._last_response = {}

            return web.json_response(response)

        except json.JSONDecodeError:
            return web.json_response({"error": "Invalid JSON"}, status=400)

        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def _handle_status(self, request: web.Request) -> web.Response:
        """处理状态请求。"""
        return web.json_response({
            "status": "running",
            "host": self.host,
            "port": self.port,
            "queue_size": self._message_queue.qsize(),
        })

    async def _handle_reset(self, request: web.Request) -> web.Response:
        """处理重置请求。"""
        while not self._message_queue.empty():
            try:
                self._message_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        return web.json_response({"status": "reset"})

    async def receive(self) -> dict[str, Any]:
        """接收消息。

        Returns:
            消息字典
        """
        return await self._message_queue.get()

    async def send(self, response: dict[str, Any]) -> None:
        """发送响应。

        Args:
            response: 响应字典
        """
        self._last_response = response

    async def send_error(self, error: str) -> None:
        """发送错误消息。

        Args:
            error: 错误描述
        """
        self._last_response = {"error": error}

    async def send_status(self, status: str, details: dict[str, Any] | None = None) -> None:
        """发送状态更新。

        Args:
            status: 状态描述
            details: 详细信息
        """
        self._last_response = {"status": status, "details": details}

    async def start(self) -> None:
        """启动 HTTP 服务器。"""
        self._runner = web.AppRunner(self._app)
        await self._runner.setup()

        site = web.TCPSite(self._runner, self.host, self.port)
        await site.start()

        print(f"API Channel started at http://{self.host}:{self.port}")

    async def stop(self) -> None:
        """停止 HTTP 服务器。"""
        if self._runner:
            await self._runner.cleanup()
            self._runner = None

        print("API Channel stopped.")
