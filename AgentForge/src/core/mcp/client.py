"""MCP 客户端 - 连接和管理 MCP 服务。"""

import asyncio
import json
import os
import subprocess
from typing import Any

from .config import MCPConfig


class MCPClient:
    """MCP 客户端 - 连接和管理 MCP 服务。

    MCP (Model Context Protocol) 是一个开放协议，用于连接 AI 模型与外部数据源。
    """

    def __init__(self, config: MCPConfig | None = None):
        """初始化 MCP 客户端。

        Args:
            config: MCP 配置，None 时自动创建
        """
        self.config = config or MCPConfig()
        self._servers: dict[str, subprocess.Popen] = {}
        self._running: bool = False

    async def start_server(self, name: str) -> bool:
        """启动 MCP 服务。

        Args:
            name: 服务名称

        Returns:
            是否启动成功
        """
        server_config = self.config.get_server(name)
        if not server_config:
            print(f"Server not found: {name}")
            return False

        if name in self._servers:
            print(f"Server already running: {name}")
            return True

        try:
            command = server_config.get("command", "npx")
            args = server_config.get("args", [])
            env = server_config.get("env", {})

            # 合并环境变量
            full_env = {**os.environ, **env}

            # 启动服务
            cmd = [command] + args
            process = subprocess.Popen(
                cmd,
                env=full_env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self._servers[name] = process
            self._running = True

            print(f"MCP server '{name}' started: {' '.join(cmd)}")
            return True

        except Exception as e:
            print(f"Failed to start MCP server '{name}': {e}")
            return False

    def stop_server(self, name: str) -> bool:
        """停止 MCP 服务。

        Args:
            name: 服务名称

        Returns:
            是否停止成功
        """
        if name not in self._servers:
            print(f"Server not running: {name}")
            return False

        process = self._servers[name]
        process.terminate()
        process.wait(timeout=5)

        del self._servers[name]
        print(f"MCP server '{name}' stopped")
        return True

    def stop_all(self) -> None:
        """停止所有服务。"""
        for name in list(self._servers.keys()):
            self.stop_server(name)
        self._running = False

    def is_running(self, name: str) -> bool:
        """检查服务是否运行。

        Args:
            name: 服务名称

        Returns:
            是否运行中
        """
        return name in self._servers

    def get_running_servers(self) -> list[str]:
        """获取所有运行中的服务。

        Returns:
            运行中的服务名称列表
        """
        return list(self._servers.keys())

    async def send_request(self, server_name: str, method: str, params: dict | None = None) -> Any:
        """发送请求到 MCP 服务。

        Args:
            server_name: 服务名称
            method: 方法名
            params: 请求参数

        Returns:
            响应结果
        """
        if server_name not in self._servers:
            raise RuntimeError(f"Server not running: {server_name}")

        # 构建 JSON-RPC 请求
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {},
        }

        process = self._servers[server_name]

        # 发送请求
        request_json = json.dumps(request)
        process.stdin.write((request_json + "\n").encode())
        process.stdin.flush()

        # 读取响应 (简化实现，实际应该异步读取)
        response_line = process.stdout.readline()
        if response_line:
            response = json.loads(response_line.decode())
            return response.get("result")

        return None

    def __enter__(self) -> "MCPClient":
        """上下文管理器入口。"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """上下文管理器出口。"""
        self.stop_all()
