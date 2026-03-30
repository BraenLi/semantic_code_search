"""API v1 路由汇总."""

from fastapi import APIRouter

from qenas_web.api.v1.strategies import router as strategies_router
from qenas_web.api.v1.backtest import router as backtest_router
from qenas_web.api.v1.visualization import router as visualization_router

# 创建 API 路由器
api_router = APIRouter()

# 注册子路由
api_router.include_router(strategies_router, prefix="/strategies", tags=["strategies"])
api_router.include_router(backtest_router, prefix="/backtest", tags=["backtest"])
api_router.include_router(visualization_router, prefix="/visualization", tags=["visualization"])
