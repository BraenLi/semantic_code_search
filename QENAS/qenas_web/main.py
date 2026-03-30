"""FastAPI 应用主入口."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from qenas_web.config import settings, get_settings
from qenas_web.api.v1.router import api_router
from qenas_web.websocket.manager import WebSocketManager
from qenas_web.websocket.endpoint import router as websocket_router


# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format=settings.log_format,
)
logger = logging.getLogger(__name__)


# WebSocket 管理器（全局单例）
websocket_manager: WebSocketManager | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理."""
    global websocket_manager

    # 启动时初始化
    logger.info("QENAS Web Service 启动...")
    websocket_manager = WebSocketManager()
    logger.info(f"WebSocket 管理器已初始化，端点：{settings.ws_endpoint}")

    yield

    # 关闭时清理
    logger.info("QENAS Web Service 关闭...")
    if websocket_manager:
        await websocket_manager.disconnect_all()
    websocket_manager = None


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例."""

    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        description=settings.api_description,
        lifespan=lifespan,
    )

    # 配置 CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册 API v1 路由
    app.include_router(api_router, prefix=settings.api_prefix)

    # 注册 WebSocket 路由（不添加 API 前缀）
    app.include_router(websocket_router)

    # 健康检查端点
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "version": settings.api_version}

    # 根路径
    @app.get("/")
    async def root():
        return {
            "name": "QENAS API",
            "description": "量子纠缠生态位自适应网络 - 策略管理和回测 API",
            "docs": "/docs",
            "health": "/health",
        }

    return app


# 创建应用实例
app = create_app()
