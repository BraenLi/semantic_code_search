"""策略管理服务."""

from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
import logging
import threading

logger = logging.getLogger(__name__)


@dataclass
class StrategyInfo:
    """策略信息."""
    strategy_id: str
    name: str
    strategy_type: str
    status: str  # pending, running, stopped, error
    config: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    error_message: Optional[str] = None


class StrategyService:
    """
    策略管理服务.

    提供策略的 CRUD 操作和运行状态管理.
    """

    def __init__(self):
        # 策略存储：strategy_id -> StrategyInfo
        self._strategies: Dict[str, StrategyInfo] = {}
        # 策略实例存储：strategy_id -> StrategyBase
        self._instances: Dict[str, Any] = {}
        # 线程锁
        self._lock = threading.Lock()

    def list_strategies(self) -> List[StrategyInfo]:
        """获取所有策略列表."""
        with self._lock:
            return list(self._strategies.values())

    def get_strategy(self, strategy_id: str) -> Optional[StrategyInfo]:
        """获取策略信息."""
        with self._lock:
            return self._strategies.get(strategy_id)

    def create_strategy(
        self,
        strategy_id: str,
        name: str,
        strategy_type: str,
        config: Dict[str, Any] = None,
    ) -> StrategyInfo:
        """创建策略."""
        with self._lock:
            if strategy_id in self._strategies:
                raise ValueError(f"策略 {strategy_id} 已存在")

            strategy = StrategyInfo(
                strategy_id=strategy_id,
                name=name,
                strategy_type=strategy_type,
                status="pending",
                config=config or {},
                created_at=datetime.utcnow(),
            )

            self._strategies[strategy_id] = strategy
            logger.info(f"创建策略：{strategy_id}")

            return strategy

    def delete_strategy(self, strategy_id: str) -> bool:
        """删除策略."""
        with self._lock:
            if strategy_id not in self._strategies:
                return False

            # 如果策略正在运行，先停止
            if self._strategies[strategy_id].status == "running":
                self._stop_strategy(strategy_id)

            del self._strategies[strategy_id]
            logger.info(f"删除策略：{strategy_id}")

            return True

    def start_strategy(self, strategy_id: str) -> bool:
        """启动策略."""
        with self._lock:
            if strategy_id not in self._strategies:
                return False

            strategy = self._strategies[strategy_id]
            if strategy.status == "running":
                logger.warning(f"策略 {strategy_id} 已在运行中")
                return True

            # 更新状态
            strategy.status = "running"
            strategy.started_at = datetime.utcnow()

            logger.info(f"启动策略：{strategy_id}")
            return True

    def stop_strategy(self, strategy_id: str) -> bool:
        """停止策略."""
        with self._lock:
            return self._stop_strategy(strategy_id)

    def _stop_strategy(self, strategy_id: str) -> bool:
        """内部停止策略方法."""
        if strategy_id not in self._strategies:
            return False

        strategy = self._strategies[strategy_id]
        if strategy.status != "running":
            return True

        strategy.status = "stopped"
        strategy.stopped_at = datetime.utcnow()

        logger.info(f"停止策略：{strategy_id}")
        return True

    def get_strategy_status(self, strategy_id: str) -> Dict[str, Any]:
        """获取策略运行状态."""
        with self._lock:
            if strategy_id not in self._strategies:
                raise ValueError(f"策略 {strategy_id} 不存在")

            strategy = self._strategies[strategy_id]
            return {
                "strategy_id": strategy.strategy_id,
                "name": strategy.name,
                "status": strategy.status,
                "created_at": strategy.created_at.isoformat() if strategy.created_at else None,
                "started_at": strategy.started_at.isoformat() if strategy.started_at else None,
                "config": strategy.config,
            }

    def update_strategy_config(
        self,
        strategy_id: str,
        config: Dict[str, Any],
    ) -> bool:
        """更新策略配置."""
        with self._lock:
            if strategy_id not in self._strategies:
                return False

            self._strategies[strategy_id].config.update(config)
            logger.info(f"更新策略配置：{strategy_id}")
            return True

    def get_instance(self, strategy_id: str) -> Optional[Any]:
        """获取策略实例."""
        return self._instances.get(strategy_id)

    def set_instance(self, strategy_id: str, instance: Any) -> None:
        """设置策略实例."""
        self._instances[strategy_id] = instance
