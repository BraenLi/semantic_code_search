"""可视化数据 API."""

from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import logging
from datetime import datetime

from qenas_web.services.visualization_service import VisualizationService

logger = logging.getLogger(__name__)

router = APIRouter()
viz_service = VisualizationService()


class EntanglementMatrixResponse(BaseModel):
    """纠缠矩阵响应."""
    matrix: List[List[float]]
    symbols: List[str]
    entropy: float
    timestamp: datetime


class EventDataResponse(BaseModel):
    """事件数据响应."""
    events: List[Dict[str, Any]]
    total_count: int


class PerformanceDataResponse(BaseModel):
    """业绩数据响应."""
    equity_curve: List[float]
    returns: List[float]
    metrics: Dict[str, Any]


class EcosystemStatusResponse(BaseModel):
    """生态系统状态响应."""
    total_species: int
    fitness_distribution: Dict[str, float]
    niche_distribution: Dict[str, int]
    diversity_index: float


@router.get("/entanglement")
async def get_entanglement_matrix(
    job_id: Optional[str] = None,
    symbol: Optional[str] = None,
):
    """获取纠缠矩阵数据."""
    try:
        data = viz_service.get_entanglement_data(job_id, symbol)
        return EntanglementMatrixResponse(**data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取纠缠矩阵失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entanglement/history")
async def get_entanglement_history(
    job_id: Optional[str] = None,
    limit: int = 100,
):
    """获取纠缠熵历史数据."""
    try:
        history = viz_service.get_entanglement_history(job_id, limit)
        return {"history": history, "count": len(history)}
    except Exception as e:
        logger.error(f"获取纠缠历史失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events")
async def get_events(
    job_id: Optional[str] = None,
    event_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
):
    """获取事件数据."""
    try:
        events = viz_service.get_event_data(
            job_id,
            event_type,
            start_date,
            end_date,
            limit,
        )
        return EventDataResponse(events=events, total_count=len(events))
    except Exception as e:
        logger.error(f"获取事件数据失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance")
async def get_performance_data(job_id: Optional[str] = None):
    """获取业绩数据."""
    try:
        data = viz_service.get_performance_data(job_id)
        return PerformanceDataResponse(**data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取业绩数据失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ecosystem")
async def get_ecosystem_status(job_id: Optional[str] = None):
    """获取生态系统状态."""
    try:
        status = viz_service.get_ecosystem_status(job_id)
        return EcosystemStatusResponse(**status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取生态系统状态失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_dashboard_data(job_id: Optional[str] = None):
    """获取仪表板汇总数据."""
    try:
        data = viz_service.get_dashboard_data(job_id)
        return data
    except Exception as e:
        logger.error(f"获取仪表板数据失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))
