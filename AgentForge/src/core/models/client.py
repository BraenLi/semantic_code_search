"""OpenAI SDK client factory."""

import os
from typing import Any

from openai import OpenAI

from .config import ModelConfig


def get_client(
    model_name: str | None = None,
    config: ModelConfig | None = None,
    override_base_url: str | None = None,
    override_api_key: str | None = None,
) -> OpenAI:
    """通过模型配置返回 OpenAI SDK client。

    支持：
    - Anthropic (通过 /v1 路径适配)
    - OpenAI
    - 国内厂商 (DeepSeek/Kimi/GLM/MiniMax)

    Args:
        model_name: 模型名称，None 时使用配置中的默认模型
        config: ModelConfig 实例，None 时自动创建
        override_base_url: 覆盖 base_url
        override_api_key: 覆盖 api_key

    Returns:
        OpenAI SDK client 实例

    Raises:
        ValueError: 模型配置不存在或 API Key 未设置
    """
    if config is None:
        config = ModelConfig()

    model_cfg = config.get(model_name)

    if override_base_url:
        base_url = override_base_url
    else:
        base_url = model_cfg.get("base_url", "https://api.openai.com/v1")

    if override_api_key:
        api_key = override_api_key
    else:
        api_key_env = model_cfg.get("api_key_env", "OPENAI_API_KEY")
        api_key = os.getenv(api_key_env)
        if not api_key:
            raise ValueError(f"API key not set: {api_key_env}")

    return OpenAI(api_key=api_key, base_url=base_url)
