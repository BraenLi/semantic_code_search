"""策略管理 API."""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import logging

from qenas_web.services.strategy_service import StrategyService, StrategyInfo
from qenas_web.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()
strategy_service = StrategyService()


class CreateStrategyRequest(BaseModel):
    """创建策略请求."""
    strategy_id: str = Field(..., description="策略 ID")
    name: str = Field(..., description="策略名称")
    strategy_type: str = Field(default="qenas", description="策略类型")
    config: dict = Field(default_factory=dict, description="策略配置")


class StrategyResponse(BaseModel):
    """策略响应."""
    strategy_id: str
    name: str
    strategy_type: str
    status: str
    created_at: Optional[datetime] = None
    config: dict = Field(default_factory=dict)

    class Config:
        from_attributes = True


@router.get("", response_model=List[StrategyResponse])
async def list_strategies():
    """获取所有策略列表."""
    try:
        strategies = strategy_service.list_strategies()
        return [
            StrategyResponse(
                strategy_id=s.strategy_id,
                name=s.name,
                strategy_type=s.strategy_type,
                status=s.status,
                created_at=s.created_at,
                config=s.config,
            )
            for s in strategies
        ]
    except Exception as e:
        logger.error(f"获取策略列表失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(strategy_id: str):
    """获取单个策略详情."""
    try:
        strategy = strategy_service.get_strategy(strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail=f"策略 {strategy_id} 不存在")

        return StrategyResponse(
            strategy_id=strategy.strategy_id,
            name=strategy.name,
            strategy_type=strategy.strategy_type,
            status=strategy.status,
            created_at=strategy.created_at,
            config=strategy.config,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取策略详情失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=StrategyResponse)
async def create_strategy(request: CreateStrategyRequest):
    """创建新策略."""
    try:
        strategy = strategy_service.create_strategy(
            strategy_id=request.strategy_id,
            name=request.name,
            strategy_type=request.strategy_type,
            config=request.config,
        )

        return StrategyResponse(
            strategy_id=strategy.strategy_id,
            name=strategy.name,
            strategy_type=strategy.strategy_type,
            status=strategy.status,
            created_at=strategy.created_at,
            config=strategy.config,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建策略失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{strategy_id}/start")
async def start_strategy(strategy_id: str, background_tasks: BackgroundTasks):
    """启动策略."""
    try:
        success = strategy_service.start_strategy(strategy_id)
        if not success:
            raise HTTPException(status_code=400, detail=f"策略 {strategy_id} 启动失败")

        return {"message": f"策略 {strategy_id} 已启动"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动策略失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{strategy_id}/stop")
async def stop_strategy(strategy_id: str):
    """停止策略."""
    try:
        success = strategy_service.stop_strategy(strategy_id)
        if not success:
            raise HTTPException(status_code=400, detail=f"策略 {strategy_id} 停止失败")

        return {"message": f"策略 {strategy_id} 已停止"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"停止策略失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{strategy_id}")
async def delete_strategy(strategy_id: str):
    """删除策略."""
    try:
        success = strategy_service.delete_strategy(strategy_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"策略 {strategy_id} 不存在")

        return {"message": f"策略 {strategy_id} 已删除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除策略失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{strategy_id}/status")
async def get_strategy_status(strategy_id: str):
    """获取策略运行状态."""
    try:
        status = strategy_service.get_strategy_status(strategy_id)
        return status
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取策略状态失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))
