"""回测指标."""

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Dict


@dataclass
class BacktestMetrics:
    """回测指标集合."""

    total_return: Decimal       # 总收益率
    sharpe_ratio: Decimal       # 夏普比率
    max_drawdown: Decimal       # 最大回撤
    win_rate: Decimal           # 胜率

    def to_dict(self) -> dict:
        """转换为字典."""
        return {
            "total_return": float(self.total_return),
            "total_return_pct": f"{self.total_return:.2%}",
            "sharpe_ratio": float(self.sharpe_ratio),
            "max_drawdown": float(self.max_drawdown),
            "max_drawdown_pct": f"{self.max_drawdown:.2%}",
            "win_rate": float(self.win_rate),
            "win_rate_pct": f"{self.win_rate:.2%}",
        }

    def __repr__(self) -> str:
        return (f"BacktestMetrics(return={self.total_return:.2%}, "
                f"sharpe={self.sharpe_ratio:.2f}, max_dd={self.max_drawdown:.2%}, "
                f"win_rate={self.win_rate:.2%})")
