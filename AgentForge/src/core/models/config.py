"""Model configuration management."""

import os
from pathlib import Path
from typing import Any

import yaml


class ModelConfig:
    """模型配置管理 - 支持多模型提供商配置。

    Attributes:
        config_path: 配置文件路径
        models: 模型配置字典 {name -> config}
        default_model: 默认模型名称
    """

    def __init__(self, config_path: str | Path | None = None):
        """初始化模型配置。

        Args:
            config_path: 配置文件路径，默认为 config/models.yaml
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent.parent / "config" / "models.yaml"
        else:
            config_path = Path(config_path)

        self.config_path = config_path
        self.models: dict[str, dict[str, Any]] = {}
        self.default_model: str | None = None
        self._load(config_path)

    def _load(self, config_path: Path) -> None:
        """加载模型配置文件。

        Args:
            config_path: 配置文件路径

        Raises:
            FileNotFoundError: 配置文件不存在
            ValueError: 配置文件格式错误
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Model config not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        if not config:
            raise ValueError(f"Empty model config: {config_path}")

        self.default_model = config.get("default_model")
        models_config = config.get("models", {})

        for name, cfg in models_config.items():
            self.models[name] = cfg

    def get(self, name: str | None = None) -> dict[str, Any]:
        """获取模型配置。

        Args:
            name: 模型名称，None 时使用默认模型

        Returns:
            模型配置字典

        Raises:
            ValueError: 模型不存在
        """
        if name is None:
            if self.default_model is None:
                raise ValueError("No default model configured")
            name = self.default_model

        if name not in self.models:
            raise ValueError(f"Unknown model: {name}")

        return self.models[name]

    def list_models(self) -> list[str]:
        """获取所有可用的模型名称。

        Returns:
            模型名称列表
        """
        return list(self.models.keys())

    def get_api_key(self, model_name: str | None = None) -> str:
        """获取模型的 API Key。

        Args:
            model_name: 模型名称，None 时使用默认模型

        Returns:
            API Key 字符串

        Raises:
            ValueError: 环境变量未设置
        """
        config = self.get(model_name)
        api_key_env = config.get("api_key_env", "OPENAI_API_KEY")
        api_key = os.getenv(api_key_env)

        if not api_key:
            raise ValueError(f"API key not set for {api_key_env}")

        return api_key
