"""可视化数据服务."""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import numpy as np

logger = logging.getLogger(__name__)


class VisualizationService:
    """
    可视化数据服务.

    提供用于前端可视化的数据格式转换和聚合.
    """

    def __init__(self):
        # 缓存的可视化数据
        self._entanglement_cache: Dict[str, Dict] = {}
        self._event_cache: Dict[str, List[Dict]] = {}
        self._performance_cache: Dict[str, Dict] = {}
        self._ecosystem_cache: Dict[str, Dict] = {}

    def get_entanglement_data(
        self,
        job_id: Optional[str] = None,
        symbol: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取纠缠矩阵数据."""
        # 检查缓存
        cache_key = f"{job_id or 'default'}_{symbol or 'all'}"
        if cache_key in self._entanglement_cache:
            return self._entanglement_cache[cache_key]

        # 生成示例数据（实际实现应从回测结果或实时数据中获取）
        n_assets = 5
        symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "META"][:n_assets]

        # 生成随机对称矩阵
        matrix = np.random.rand(n_assets, n_assets)
        matrix = (matrix + matrix.T) / 2  # 对称化
        np.fill_diagonal(matrix, 1.0)  # 对角线为 1

        # 计算纠缠熵
        eigenvalues = np.linalg.eigvalsh(matrix)
        eigenvalues = eigenvalues[eigenvalues > 1e-10]
        entropy = -np.sum(eigenvalues * np.log2(eigenvalues + 1e-10))

        data = {
            "matrix": matrix.tolist(),
            "symbols": symbols,
            "entropy": float(entropy),
            "timestamp": datetime.utcnow(),
        }

        # 缓存
        self._entanglement_cache[cache_key] = data

        return data

    def get_entanglement_history(
        self,
        job_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """获取纠缠熵历史数据."""
        # 生成示例历史数据
        history = []
        base_entropy = np.random.uniform(1.5, 2.5)

        for i in range(min(limit, 100)):
            timestamp = datetime.utcnow()
            entropy = base_entropy + np.random.randn() * 0.2
            history.append({
                "index": i,
                "timestamp": timestamp.isoformat(),
                "entropy": float(entropy),
            })

        return history

    def get_event_data(
        self,
        job_id: Optional[str] = None,
        event_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """获取事件数据."""
        # 检查缓存
        cache_key = f"{job_id or 'default'}_{event_type or 'all'}"
        if cache_key in self._event_cache:
            events = self._event_cache[cache_key]
            return events[:limit]

        # 生成示例事件数据
        event_types = ["earnings", "announcement", "regulatory", "market_moving"]
        impact_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

        events = []
        for i in range(limit):
            event = {
                "id": f"event_{i}",
                "title": f"事件 {i}",
                "event_type": np.random.choice(event_types),
                "impact_level": np.random.choice(impact_levels),
                "timestamp": datetime.utcnow().isoformat(),
                "description": f"这是事件 {i} 的描述",
                "symbols": ["AAPL", "GOOGL", "MSFT"][:np.random.randint(1, 4)],
            }
            events.append(event)

        # 缓存
        self._event_cache[cache_key] = events

        return events[:limit]

    def get_performance_data(
        self,
        job_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取业绩数据."""
        # 检查缓存
        if job_id and job_id in self._performance_cache:
            return self._performance_cache[job_id]

        # 生成示例业绩数据
        n_periods = 100
        initial_capital = 100000

        # 生成权益曲线（随机游走）
        returns = np.random.randn(n_periods) * 0.02
        equity_curve = [initial_capital]
        for r in returns:
            equity_curve.append(equity_curve[-1] * (1 + r))

        # 计算指标
        metrics = {
            "total_return": (equity_curve[-1] - initial_capital) / initial_capital,
            "sharpe_ratio": float(np.mean(returns) / np.std(returns) * np.sqrt(252)) if np.std(returns) > 0 else 0,
            "max_drawdown": self._calculate_max_drawdown(equity_curve),
            "win_rate": float(np.sum(returns > 0) / len(returns)) if returns.size > 0 else 0,
        }

        data = {
            "equity_curve": [float(e) for e in equity_curve],
            "returns": [float(r) for r in returns],
            "metrics": metrics,
        }

        # 缓存
        if job_id:
            self._performance_cache[job_id] = data

        return data

    def get_ecosystem_status(
        self,
        job_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取生态系统状态."""
        # 检查缓存
        if job_id and job_id in self._ecosystem_cache:
            return self._ecosystem_cache[job_id]

        # 生成示例生态系统数据
        total_species = 100

        # 适应度分布
        fitness_distribution = {
            "high": float(np.random.uniform(0.1, 0.2)),
            "medium": float(np.random.uniform(0.3, 0.4)),
            "low": float(np.random.uniform(0.4, 0.5)),
        }

        # 生态位分布
        niche_distribution = {
            "momentum": np.random.randint(20, 30),
            "reversion": np.random.randint(20, 30),
            "volatility": np.random.randint(15, 25),
            "sentiment": np.random.randint(10, 20),
            "macro": np.random.randint(5, 15),
        }

        # 多样性指数 (Shannon index)
        proportions = np.array(list(niche_distribution.values())) / total_species
        diversity_index = -np.sum(proportions * np.log(proportions + 1e-10))

        data = {
            "total_species": total_species,
            "fitness_distribution": fitness_distribution,
            "niche_distribution": niche_distribution,
            "diversity_index": float(diversity_index),
        }

        # 缓存
        if job_id:
            self._ecosystem_cache[job_id] = data

        return data

    def get_dashboard_data(
        self,
        job_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取仪表板汇总数据."""
        entanglement = self.get_entanglement_data(job_id)
        performance = self.get_performance_data(job_id)
        ecosystem = self.get_ecosystem_status(job_id)

        return {
            "entanglement": {
                "entropy": entanglement["entropy"],
                "asset_count": len(entanglement["symbols"]),
            },
            "performance": performance["metrics"],
            "ecosystem": {
                "total_species": ecosystem["total_species"],
                "diversity_index": ecosystem["diversity_index"],
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _calculate_max_drawdown(self, equity_curve: List[float]) -> float:
        """计算最大回撤."""
        if not equity_curve:
            return 0.0

        peak = equity_curve[0]
        max_dd = 0.0

        for equity in equity_curve:
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak
            if dd > max_dd:
                max_dd = dd

        return float(max_dd)

    def clear_cache(self, job_id: Optional[str] = None) -> None:
        """清空缓存."""
        if job_id:
            self._entanglement_cache.pop(job_id, None)
            self._event_cache.pop(job_id, None)
            self._performance_cache.pop(job_id, None)
            self._ecosystem_cache.pop(job_id, None)
        else:
            self._entanglement_cache.clear()
            self._event_cache.clear()
            self._performance_cache.clear()
            self._ecosystem_cache.clear()
