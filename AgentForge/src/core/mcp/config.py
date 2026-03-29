"""MCP 服务配置管理。"""

import os
import re
from pathlib import Path
from typing import Any

import yaml


class MCPConfig:
    """MCP 服务配置管理。

    配置格式:
    servers:
      filesystem:
        command: npx
        args: ["-y", "@anthropic/mcp-filesystem"]
        env:
          MCP_FILE_ROOT: ./workspace
    """

    def __init__(self, config_path: str | Path | None = None):
        """初始化 MCP 配置。

        Args:
            config_path: 配置文件路径，默认为 config/mcp.yaml
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent.parent / "config" / "mcp.yaml"
        else:
            config_path = Path(config_path)

        self.config_path = config_path
        self.servers: dict[str, dict[str, Any]] = {}
        self._load(config_path)

    def _load(self, config_path: Path) -> None:
        """加载配置文件。

        Args:
            config_path: 配置文件路径

        Raises:
            FileNotFoundError: 配置文件不存在
        """
        if not config_path.exists():
            return

        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        if not config:
            return

        servers_config = config.get("servers", {})
        for name, cfg in servers_config.items():
            self.servers[name] = self._resolve_env(cfg)

    def _resolve_env(self, config: dict[str, Any]) -> dict[str, Any]:
        """解析环境变量占位符。

        支持 ${VAR_NAME} 格式的占位符。

        Args:
            config: 配置字典

        Returns:
            解析后的配置
        """
        result = {}
        for key, value in config.items():
            if isinstance(value, dict):
                result[key] = self._resolve_env(value)
            elif isinstance(value, str):
                result[key] = self._expand_env(value)
            else:
                result[key] = value
        return result

    def _expand_env(self, value: str) -> str:
        """展开环境变量。

        Args:
            value: 包含占位符的字符串

        Returns:
            展开后的字符串
        """

        def replace(match):
            env_var = match.group(1)
            return os.getenv(env_var, match.group(0))

        return re.sub(r"\$\{([^}]+)\}", replace, value)

    def get_server(self, name: str) -> dict[str, Any] | None:
        """获取服务器配置。

        Args:
            name: 服务器名称

        Returns:
            服务器配置，不存在时返回 None
        """
        return self.servers.get(name)

    def list_servers(self) -> list[str]:
        """获取所有服务器名称。

        Returns:
            服务器名称列表
        """
        return list(self.servers.keys())

    def add_server(self, name: str, config: dict[str, Any]) -> None:
        """添加服务器配置。

        Args:
            name: 服务器名称
            config: 服务器配置
        """
        self.servers[name] = config

    def remove_server(self, name: str) -> None:
        """移除服务器配置。

        Args:
            name: 服务器名称
        """
        if name in self.servers:
            del self.servers[name]
