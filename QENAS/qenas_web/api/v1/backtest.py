"""回测管理 API."""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
import logging
import uuid

from qenas_web.services.backtest_service import BacktestService, BacktestJob
from qenas_web.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()
backtest_service = BacktestService()


class BacktestRequest(BaseModel):
    """回测请求."""
    strategy_id: str = Field(..., description="策略 ID")
    symbols: List[str] = Field(..., description="标的列表")
    start_date: datetime = Field(..., description="开始日期")
    end_date: datetime = Field(..., description="结束日期")
    initial_capital: float = Field(default=100000.0, description="初始资金")
    commission_rate: float = Field(default=0.001, description="佣金率")
    slippage_rate: float = Field(default=0.001, description="滑点率")
    config: Dict[str, Any] = Field(default_factory=dict, description="策略配置")


class BacktestJobResponse(BaseModel):
    """回测任务响应."""
    job_id: str
    strategy_id: str
    status: str
    progress: float = 0.0
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class BacktestResultResponse(BaseModel):
    """回测结果响应."""
    job_id: str
    strategy_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


@router.post("/qenas", response_model=BacktestJobResponse)
async def run_qenas_backtest(
    request: BacktestRequest,
    background_tasks: BackgroundTasks,
):
    """运行 QENAS 策略回测."""
    try:
        job_id = await backtest_service.run_qenas_backtest(
            strategy_id=request.strategy_id,
            symbols=request.symbols,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=request.initial_capital,
            commission_rate=request.commission_rate,
            slippage_rate=request.slippage_rate,
            config=request.config,
        )

        return BacktestJobResponse(
            job_id=job_id,
            strategy_id=request.strategy_id,
            status="pending",
            progress=0.0,
            created_at=datetime.utcnow(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建回测任务失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[BacktestJobResponse])
async def list_backtest_jobs():
    """获取所有回测任务列表."""
    try:
        jobs = backtest_service.list_jobs()
        return [
            BacktestJobResponse(
                job_id=j.job_id,
                strategy_id=j.strategy_id,
                status=j.status,
                progress=j.progress,
                created_at=j.created_at,
                started_at=j.started_at,
                completed_at=j.completed_at,
                error_message=j.error_message,
            )
            for j in jobs
        ]
    except Exception as e:
        logger.error(f"获取回测列表失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}", response_model=BacktestJobResponse)
async def get_backtest_job(job_id: str):
    """获取回测任务详情."""
    try:
        job = backtest_service.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"回测任务 {job_id} 不存在")

        return BacktestJobResponse(
            job_id=job.job_id,
            strategy_id=job.strategy_id,
            status=job.status,
            progress=job.progress,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            error_message=job.error_message,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取回测任务详情失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}/result", response_model=BacktestResultResponse)
async def get_backtest_result(job_id: str):
    """获取回测结果."""
    try:
        job = backtest_service.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"回测任务 {job_id} 不存在")

        if job.status != "completed":
            return BacktestResultResponse(
                job_id=job_id,
                strategy_id=job.strategy_id,
                status=job.status,
                result=None,
                error_message=job.error_message,
            )

        result = backtest_service.get_result(job_id)
        return BacktestResultResponse(
            job_id=job_id,
            strategy_id=job.strategy_id,
            status=job.status,
            result=result,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取回测结果失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{job_id}")
async def delete_backtest_job(job_id: str):
    """删除回测任务."""
    try:
        success = backtest_service.delete_job(job_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"回测任务 {job_id} 不存在")

        return {"message": f"回测任务 {job_id} 已删除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除回测任务失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{job_id}/cancel")
async def cancel_backtest_job(job_id: str):
    """取消回测任务."""
    try:
        success = backtest_service.cancel_job(job_id)
        if not success:
            raise HTTPException(status_code=400, detail=f"回测任务 {job_id} 无法取消")

        return {"message": f"回测任务 {job_id} 已取消"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消回测任务失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))
