"""回测业绩可视化.

提供权益曲线、回撤分析、收益分布等可视化功能.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass
import numpy as np
from numpy.typing import NDArray

# 尝试导入 matplotlib
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


@dataclass
class BacktestResult:
    """回测结果数据类."""
    timestamps: List[datetime]
    equity_curve: List[float]  # 权益曲线
    returns: List[float]  # 收益率序列
    benchmark: Optional[List[float]] = None  # 基准（可选）
    max_drawdown: float = 0.0  # 最大回撤
    sharpe_ratio: float = 0.0  # 夏普比率
    total_return: float = 0.0  # 总收益率
    win_rate: float = 0.0  # 胜率
    trades: List[Dict] = None  # 交易记录


class PerformanceVisualizer:
    """
    业绩可视化器.

    功能:
    - 权益曲线图
    - 回撤分析图
    - 收益分布直方图
    - 滚动指标图
    """

    def __init__(self):
        """初始化可视化器."""
        self.results: Optional[BacktestResult] = None

    def set_results(self, results: BacktestResult) -> None:
        """
        设置回测结果.

        Args:
            results: 回测结果数据
        """
        self.results = results

    def plot_equity_curve(
        self,
        results: Optional[BacktestResult] = None,
        title: str = "权益曲线",
        save_path: Optional[str] = None,
        show: bool = True,
    ) -> Optional[Any]:
        """
        绘制权益曲线.

        Args:
            results: 回测结果（不提供则使用内部结果）
            title: 图表标题
            save_path: 保存路径
            show: 是否显示

        Returns:
            figure 对象
        """
        r = results or self.results

        if not r or not r.equity_curve:
            print("没有回测结果数据可绘制")
            return None

        if not HAS_MATPLOTLIB:
            return self._text_equity_curve(r, title)

        fig, ax = plt.subplots(figsize=(14, 7))

        # 绘制策略权益曲线
        ax.plot(r.timestamps, r.equity_curve, 'b-', linewidth=1.5, label='策略')

        # 绘制基准（如果有）
        if r.benchmark:
            ax.plot(r.timestamps, r.benchmark, 'g--', linewidth=1.5, label='基准', alpha=0.7)

        # 添加初始资金线
        initial_capital = r.equity_curve[0] if r.equity_curve else 100000
        ax.axhline(y=initial_capital, color='gray', linestyle='-', alpha=0.3)

        # 标注关键点
        max_equity = max(r.equity_curve)
        min_equity = min(r.equity_curve)
        final_equity = r.equity_curve[-1]

        ax.annotate(f'最大值：{max_equity:.0f}',
                   xy=(r.timestamps[r.equity_curve.index(max_equity)], max_equity),
                   xytext=(10, 10), textcoords='offset points',
                   bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.7),
                   arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))

        ax.set_xlabel('时间')
        ax.set_ylabel('权益')
        ax.set_title(f"{title}\n总收益：{r.total_return:.2%} | 夏普比率：{r.sharpe_ratio:.2f} | 最大回撤：{r.max_drawdown:.2%}")
        ax.legend()
        ax.grid(True, alpha=0.3)

        # 格式化 x 轴日期
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.xticks(rotation=45, ha='right')

        fig.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            return None

        if show:
            plt.show()
            return None

        return fig

    def plot_drawdown(
        self,
        results: Optional[BacktestResult] = None,
        title: str = "回撤分析",
        save_path: Optional[str] = None,
        show: bool = True,
    ) -> Optional[Any]:
        """
        绘制回撤分析图.

        Args:
            results: 回测结果
            title: 图表标题
            save_path: 保存路径
            show: 是否显示

        Returns:
            figure 对象
        """
        r = results or self.results

        if not r or not r.equity_curve:
            print("没有回测结果数据可绘制")
            return None

        if not HAS_MATPLOTLIB:
            return self._text_drawdown(r, title)

        # 计算回撤曲线
        equity = np.array(r.equity_curve)
        running_max = np.maximum.accumulate(equity)
        drawdown = (equity - running_max) / running_max

        fig, axes = plt.subplots(2, 1, figsize=(14, 10), sharex=True,
                                gridspec_kw={'height_ratios': [2, 1]})

        # 上圖：权益曲线
        axes[0].plot(r.timestamps, equity, 'b-', linewidth=1.5)
        axes[0].fill_between(r.timestamps, running_max, equity,
                            where=equity < running_max, alpha=0.3, color='red',
                            label='回撤区域')
        axes[0].set_ylabel('权益')
        axes[0].set_title(f"{title}\n最大回撤：{r.max_drawdown:.2%}")
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        # 下图：回撤曲线
        axes[1].plot(r.timestamps, drawdown * 100, 'r-', linewidth=1.5)
        axes[1].fill_between(r.timestamps, 0, drawdown * 100, alpha=0.5, color='red')
        axes[1].set_xlabel('时间')
        axes[1].set_ylabel('回撤 (%)')
        axes[1].grid(True, alpha=0.3)

        # 标注最大回撤
        max_dd_idx = np.argmin(drawdown)
        axes[1].annotate(f'最大回撤：{drawdown[max_dd_idx]:.2%}',
                        xy=(r.timestamps[max_dd_idx], drawdown[max_dd_idx] * 100),
                        xytext=(10, 10), textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.7),
                        arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))

        axes[1].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        axes[1].xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.xticks(rotation=45, ha='right')

        fig.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            return None

        if show:
            plt.show()
            return None

        return fig

    def plot_returns_distribution(
        self,
        results: Optional[BacktestResult] = None,
        title: str = "收益率分布",
        save_path: Optional[str] = None,
        show: bool = True,
    ) -> Optional[Any]:
        """
        绘制收益率分布直方图.

        Args:
            results: 回测结果
            title: 图表标题
            save_path: 保存路径
            show: 是否显示

        Returns:
            figure 对象
        """
        r = results or self.results

        if not r or not r.returns:
            print("没有回测结果数据可绘制")
            return None

        if not HAS_MATPLOTLIB:
            return self._text_returns_distribution(r, title)

        returns = np.array(r.returns)

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        # 左图：收益率直方图
        n, bins, patches = axes[0].hist(returns, bins=30, edgecolor='black', alpha=0.7, color='skyblue')

        # 添加正态分布拟合曲线
        mu, sigma = np.mean(returns), np.std(returns)
        from scipy import stats
        x = np.linspace(mu - 4*sigma, mu + 4*sigma, 100)
        pdf = stats.norm.pdf(x, mu, sigma) * len(returns) * (bins[1] - bins[0])
        axes[0].plot(x, pdf, 'r-', linewidth=2, label=f'正态拟合\nμ={mu:.4f}\nσ={sigma:.4f}')
        axes[0].axvline(x=0, color='green', linestyle='--', alpha=0.7, label='零收益')
        axes[0].set_xlabel('收益率')
        axes[0].set_ylabel('频数')
        axes[0].set_title('收益率分布')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        # 右图：Q-Q 图
        stats.probplot(returns, dist="norm", plot=axes[1])
        axes[1].set_title('Q-Q 图')
        axes[1].grid(True, alpha=0.3)

        fig.suptitle(title)
        fig.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            return None

        if show:
            plt.show()
            return None

        return fig

    def plot_rolling_metrics(
        self,
        results: Optional[BacktestResult] = None,
        window: int = 20,
        title: str = "滚动指标",
        save_path: Optional[str] = None,
        show: bool = True,
    ) -> Optional[Any]:
        """
        绘制滚动指标图（滚动夏普比率、滚动波动率）.

        Args:
            results: 回测结果
            window: 滚动窗口大小（交易日）
            title: 图表标题
            save_path: 保存路径
            show: 是否显示

        Returns:
            figure 对象
        """
        r = results or self.results

        if not r or not r.returns:
            print("没有回测结果数据可绘制")
            return None

        if not HAS_MATPLOTLIB:
            return self._text_rolling_metrics(r, window, title)

        returns = np.array(r.returns)
        timestamps = r.timestamps[1:]  # 收益率比权益少一个点

        # 计算滚动指标
        rolling_sharpe = []
        rolling_vol = []
        rolling_return = []

        for i in range(window, len(returns)):
            window_returns = returns[i-window:i]
            rolling_sharpe.append(np.mean(window_returns) / np.std(window_returns) * np.sqrt(252) if np.std(window_returns) > 0 else 0)
            rolling_vol.append(np.std(window_returns) * np.sqrt(252))
            rolling_return.append(np.prod(1 + window_returns) - 1)

        fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)

        # 滚动夏普比率
        axes[0].plot(timestamps[window:], rolling_sharpe, 'b-', linewidth=1.5)
        axes[0].axhline(y=1, color='green', linestyle='--', alpha=0.5, label='Sharpe=1')
        axes[0].axhline(y=0, color='gray', linestyle='-', alpha=0.3)
        axes[0].set_ylabel('夏普比率')
        axes[0].set_title(f'{title} (窗口：{window} 天)')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        # 滚动波动率
        axes[1].plot(timestamps[window:], rolling_vol, 'r-', linewidth=1.5)
        axes[1].axhline(y=0.2, color='orange', linestyle='--', alpha=0.5, label='20%')
        axes[1].set_ylabel('年化波动率')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)

        # 滚动收益率
        axes[2].plot(timestamps[window:], rolling_return, 'g-', linewidth=1.5)
        axes[2].axhline(y=0, color='gray', linestyle='-', alpha=0.3)
        axes[2].set_xlabel('时间')
        axes[2].set_ylabel('滚动收益')
        axes[2].grid(True, alpha=0.3)

        axes[2].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        axes[2].xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.xticks(rotation=45, ha='right')

        fig.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            return None

        if show:
            plt.show()
            return None

        return fig

    def _text_equity_curve(self, r: BacktestResult, title: str) -> str:
        """文本模式权益曲线."""
        lines = [f"\n{title}", "=" * 60]
        lines.append(f"初始权益：{r.equity_curve[0]:.2f}")
        lines.append(f"最终权益：{r.equity_curve[-1]:.2f}")
        lines.append(f"总收益率：{r.total_return:.2%}")
        lines.append(f"夏普比率：{r.sharpe_ratio:.2f}")
        lines.append(f"最大回撤：{r.max_drawdown:.2%}")
        lines.append("-" * 60)

        # 采样显示
        n = len(r.equity_curve)
        step = max(n // 20, 1)
        for i in range(0, n, step):
            lines.append(f"  {r.timestamps[i].strftime('%Y-%m-%d')}: {r.equity_curve[i]:.2f}")

        return "\n".join(lines)

    def _text_drawdown(self, r: BacktestResult, title: str) -> str:
        """文本模式回撤."""
        equity = np.array(r.equity_curve)
        running_max = np.maximum.accumulate(equity)
        drawdown = (equity - running_max) / running_max

        lines = [f"\n{title}", "=" * 60]
        lines.append(f"最大回撤：{r.max_drawdown:.2%}")

        # 找出前 5 大回撤
        top_5_indices = np.argsort(drawdown)[:5][::-1]
        lines.append("\n前 5 大回撤:")
        for idx in top_5_indices:
            lines.append(f"  {r.timestamps[idx].strftime('%Y-%m-%d')}: {drawdown[idx]:.2%}")

        return "\n".join(lines)

    def _text_returns_distribution(self, r: BacktestResult, title: str) -> str:
        """文本模式收益分布."""
        returns = np.array(r.returns)

        lines = [f"\n{title}", "=" * 60]
        lines.append(f"均值：{np.mean(returns):.4f}")
        lines.append(f"标准差：{np.std(returns):.4f}")
        lines.append(f"偏度：{self._safe_skew(returns):.4f}")
        lines.append(f"峰度：{self._safe_kurtosis(returns):.4f}")
        lines.append(f"正收益天数：{np.sum(returns > 0)} / {len(returns)}")
        lines.append(f"负收益天数：{np.sum(returns < 0)} / {len(returns)}")

        return "\n".join(lines)

    def _text_rolling_metrics(self, r: BacktestResult, window: int, title: str) -> str:
        """文本模式滚动指标."""
        returns = np.array(r.returns)

        lines = [f"\n{title}", "=" * 60]
        lines.append(f"滚动窗口：{window} 天")

        # 最新滚动指标
        if len(returns) >= window:
            recent = returns[-window:]
            roll_sharpe = np.mean(recent) / np.std(recent) * np.sqrt(252) if np.std(recent) > 0 else 0
            roll_vol = np.std(recent) * np.sqrt(252)
            roll_ret = np.prod(1 + recent) - 1

            lines.append(f"\n最新滚动指标:")
            lines.append(f"  夏普比率：{roll_sharpe:.2f}")
            lines.append(f"  波动率：{roll_vol:.2%}")
            lines.append(f"  收益率：{roll_ret:.2%}")

        return "\n".join(lines)

    def _safe_skew(self, x: NDArray) -> float:
        """安全计算偏度."""
        try:
            from scipy.stats import skew
            return float(skew(x))
        except Exception:
            return 0.0

    def _safe_kurtosis(self, x: NDArray) -> float:
        """安全计算峰度."""
        try:
            from scipy.stats import kurtosis
            return float(kurtosis(x))
        except Exception:
            return 0.0
