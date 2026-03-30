"""回测管理服务."""

from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from decimal import Decimal
import asyncio
import logging
import uuid
import threading

from qenas_core.strategies.qenas_strategy import QENASStrategy
from qenas_backtest.engine import BacktestEngine, BacktestResult

logger = logging.getLogger(__name__)


@dataclass
class BacktestJob:
    """回测任务."""
    job_id: str
    strategy_id: str
    status: str  # pending, running, completed, failed, cancelled
    progress: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    symbols: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)


class BacktestService:
    """
    回测管理服务.

    提供回测任务的创建、执行和结果管理.
    """

    def __init__(self):
        # 回测任务存储：job_id -> BacktestJob
        self._jobs: Dict[str, BacktestJob] = {}
        # 回测结果存储：job_id -> BacktestResult
        self._results: Dict[str, Dict[str, Any]] = {}
        # 运行中的任务：job_id -> asyncio.Task
        self._running_tasks: Dict[str, asyncio.Task] = {}
        # 线程锁
        self._lock = threading.Lock()

    def list_jobs(self) -> List[BacktestJob]:
        """获取所有回测任务列表."""
        with self._lock:
            return list(self._jobs.values())

    def get_job(self, job_id: str) -> Optional[BacktestJob]:
        """获取回测任务."""
        with self._lock:
            return self._jobs.get(job_id)

    def delete_job(self, job_id: str) -> bool:
        """删除回测任务."""
        with self._lock:
            if job_id not in self._jobs:
                return False

            # 取消运行中的任务
            if job_id in self._running_tasks:
                self._running_tasks[job_id].cancel()
                del self._running_tasks[job_id]

            del self._jobs[job_id]

            # 删除结果
            if job_id in self._results:
                del self._results[job_id]

            logger.info(f"删除回测任务：{job_id}")
            return True

    def cancel_job(self, job_id: str) -> bool:
        """取消回测任务."""
        with self._lock:
            if job_id not in self._jobs:
                return False

            job = self._jobs[job_id]
            if job.status not in ("pending", "running"):
                return False

            # 取消运行中的任务
            if job_id in self._running_tasks:
                self._running_tasks[job_id].cancel()
                del self._running_tasks[job_id]

            job.status = "cancelled"
            job.completed_at = datetime.utcnow()

            logger.info(f"取消回测任务：{job_id}")
            return True

    def get_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """获取回测结果."""
        return self._results.get(job_id)

    async def run_qenas_backtest(
        self,
        strategy_id: str,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        initial_capital: float,
        commission_rate: float,
        slippage_rate: float,
        config: Dict[str, Any],
    ) -> str:
        """
        运行 QENAS 回测.

        Args:
            strategy_id: 策略 ID
            symbols: 标的列表
            start_date: 开始日期
            end_date: 结束日期
            initial_capital: 初始资金
            commission_rate: 佣金率
            slippage_rate: 滑点率
            config: 策略配置

        Returns:
            job_id: 回测任务 ID
        """
        job_id = str(uuid.uuid4())

        # 创建回测任务
        job = BacktestJob(
            job_id=job_id,
            strategy_id=strategy_id,
            status="pending",
            symbols=symbols,
            config=config,
        )

        with self._lock:
            self._jobs[job_id] = job

        logger.info(f"创建回测任务：{job_id}, 策略={strategy_id}, 标的={symbols}")

        # 在后台启动回测任务
        loop = asyncio.get_event_loop()
        task = loop.create_task(
            self._execute_backtest(
                job_id=job_id,
                strategy_id=strategy_id,
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                commission_rate=commission_rate,
                slippage_rate=slippage_rate,
                config=config,
            )
        )

        with self._lock:
            self._running_tasks[job_id] = task

        return job_id

    async def _execute_backtest(
        self,
        job_id: str,
        strategy_id: str,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        initial_capital: float,
        commission_rate: float,
        slippage_rate: float,
        config: Dict[str, Any],
    ) -> None:
        """执行回测任务."""
        try:
            # 更新状态
            with self._lock:
                job = self._jobs[job_id]
                job.status = "running"
                job.started_at = datetime.utcnow()

            logger.info(f"开始执行回测：{job_id}")

            # 创建 QENAS 策略
            n_species = config.get("n_species", 100)
            strategy = QENASStrategy(
                strategy_id=strategy_id,
                n_species=n_species,
            )

            # 创建回测引擎
            engine = BacktestEngine(
                strategy=strategy,
                initial_capital=Decimal(str(initial_capital)),
            )
            engine.set_commission(Decimal(str(commission_rate)))
            engine.set_slippage(Decimal(str(slippage_rate)))

            # TODO: 获取历史数据并运行回测
            # 这里需要集成数据服务获取历史 K 线数据
            # klines = await fetch_historical_klines(symbols, start_date, end_date)

            # 模拟回测执行
            await asyncio.sleep(2)  # 模拟执行时间

            # 创建模拟结果
            result = {
                "strategy_name": strategy.name,
                "initial_capital": initial_capital,
                "final_capital": initial_capital * 1.15,  # 模拟 15% 收益
                "total_return": 0.15,
                "sharpe_ratio": 1.5,
                "max_drawdown": 0.08,
                "win_rate": 0.55,
                "total_trades": 50,
                "trades": [],
                "equity_curve": [initial_capital * (1 + i * 0.003) for i in range(100)],
            }

            # 存储结果
            with self._lock:
                self._results[job_id] = result

            # 更新任务状态
            with self._lock:
                job = self._jobs[job_id]
                job.status = "completed"
                job.completed_at = datetime.utcnow()
                job.progress = 100.0

            logger.info(f"回测完成：{job_id}, 收益率={result['total_return']:.2%}")

        except asyncio.CancelledError:
            logger.info(f"回测已取消：{job_id}")
            with self._lock:
                job = self._jobs[job_id]
                job.status = "cancelled"
                job.completed_at = datetime.utcnow()

        except Exception as e:
            logger.error(f"回测失败：{job_id}, 错误：{e}")
            with self._lock:
                job = self._jobs[job_id]
                job.status = "failed"
                job.completed_at = datetime.utcnow()
                job.error_message = str(e)

        finally:
            with self._lock:
                if job_id in self._running_tasks:
                    del self._running_tasks[job_id]
