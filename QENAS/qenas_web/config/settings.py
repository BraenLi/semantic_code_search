"""配置管理."""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
import os


class Settings(BaseSettings):
    """QENAS Web 服务配置."""

    # 服务配置
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # API 配置
    api_prefix: str = "/api/v1"
    api_title: str = "QENAS API"
    api_version: str = "0.1.0"
    api_description: str = "量子纠缠生态位自适应网络 - 策略管理和回测 API"

    # CORS 配置
    cors_origins: List[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ]
    )

    # WebSocket 配置
    ws_endpoint: str = "/ws/qenas"
    ws_ping_interval: int = 30
    ws_ping_timeout: int = 10

    # 回测配置
    default_initial_capital: float = 100000.0
    default_commission_rate: float = 0.001
    default_slippage_rate: float = 0.001

    # 数据目录
    data_dir: str = Field(
        default_factory=lambda: os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "qenas_data",
            "storage",
        )
    )

    # 日志配置
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    class Config:
        env_prefix = "QENAS_"
        env_file = ".env"
        case_sensitive = False


# 全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例."""
    return settings
