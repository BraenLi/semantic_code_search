"""QENAS 策略状态仪表板.

整合所有可视化组件，提供统一的策略状态展示.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime

from qenas_viz.entanglement_viz import EntanglementVisualizer
from qenas_viz.event_viz import EventTimelineVisualizer
from qenas_viz.performance_viz import PerformanceVisualizer, BacktestResult


class QENASDashboard:
    """
    QENAS 策略状态仪表板.

    整合:
    - 纠缠矩阵可视化
    - 事件时间线
    - 业绩可视化
    """

    def __init__(self, symbol_labels: Optional[List[str]] = None):
        """
        初始化仪表板.

        Args:
            symbol_labels: 资产标签列表
        """
        self.symbol_labels = symbol_labels or []

        # 初始化各可视化器
        self.entanglement_viz = EntanglementVisualizer(symbol_labels)
        self.event_viz = EventTimelineVisualizer()
        self.performance_viz = PerformanceVisualizer()

        # 策略状态
        self.step_count = 0
        self.is_initialized = False

    def initialize(self, symbols: List[str]) -> None:
        """
        初始化仪表板.

        Args:
            symbols: 交易标的列表
        """
        self.symbol_labels = symbols
        self.entanglement_viz = EntanglementVisualizer(symbols)
        self.is_initialized = True

    def update_entanglement(
        self,
        matrix: Any,
        entropy: Optional[float] = None,
    ) -> None:
        """
        更新纠缠矩阵数据.

        Args:
            matrix: 纠缠矩阵 (numpy array)
            entropy: 纠缠熵
        """
        self.entanglement_viz.record_history(matrix, entropy)
        self.step_count += 1

    def add_events(self, events: List[Any]) -> None:
        """
        添加事件数据.

        Args:
            events: 事件数据列表
        """
        self.event_viz.add_events(events)

    def set_backtest_results(self, results: BacktestResult) -> None:
        """
        设置回测结果.

        Args:
            results: 回测结果
        """
        self.performance_viz.set_results(results)

    def show_entanglement_matrix(
        self,
        save_path: Optional[str] = None,
    ) -> None:
        """显示最新纠缠矩阵热力图."""
        matrix = self.entanglement_viz.get_latest_matrix()
        if matrix is not None:
            self.entanglement_viz.plot_entanglement_matrix(
                matrix,
                title=f"量子纠缠矩阵 (步数：{self.step_count})",
                save_path=save_path,
            )
        else:
            print("暂无纠缠矩阵数据")

    def show_entropy_history(self, save_path: Optional[str] = None) -> None:
        """显示纠缠熵时间序列."""
        self.entanglement_viz.plot_entropy_history(
            title="纠缠熵演化",
            save_path=save_path,
        )

    def show_event_timeline(self, save_path: Optional[str] = None) -> None:
        """显示事件时间线."""
        self.event_viz.plot_timeline(
            title="事件时间线",
            save_path=save_path,
        )

    def show_event_distribution(self, save_path: Optional[str] = None) -> None:
        """显示事件类型分布."""
        self.event_viz.plot_type_distribution(
            title="事件类型分布",
            save_path=save_path,
        )

    def show_equity_curve(self, save_path: Optional[str] = None) -> None:
        """显示权益曲线."""
        self.performance_viz.plot_equity_curve(
            title="权益曲线",
            save_path=save_path,
        )

    def show_drawdown(self, save_path: Optional[str] = None) -> None:
        """显示回撤分析."""
        self.performance_viz.plot_drawdown(
            title="回撤分析",
            save_path=save_path,
        )

    def get_status_report(self) -> Dict[str, Any]:
        """
        获取状态报告.

        Returns:
            状态报告字典
        """
        report = {
            "step_count": self.step_count,
            "entanglement": {
                "latest_entropy": self.entanglement_viz.get_latest_entropy(),
                "history_length": len(self.entanglement_viz.entropy_history),
            },
            "events": self.event_viz.get_event_summary(),
            "performance": {},
        }

        if self.performance_viz.results:
            r = self.performance_viz.results
            report["performance"] = {
                "total_return": r.total_return,
                "sharpe_ratio": r.sharpe_ratio,
                "max_drawdown": r.max_drawdown,
                "win_rate": r.win_rate,
            }

        return report

    def print_status(self) -> None:
        """打印状态报告."""
        report = self.get_status_report()

        print("\n" + "=" * 60)
        print("QENAS 策略状态仪表板")
        print("=" * 60)
        print(f"步数：{report['step_count']}")
        print(f"最新熵值：{report['entanglement']['latest_entropy']:.4f}" if report['entanglement']['latest_entropy'] else "最新熵值：N/A")
        print(f"事件总数：{report['events'].get('total_events', 0)}")
        if report['performance']:
            print(f"总收益：{report['performance'].get('total_return', 0):.2%}")
            print(f"夏普比率：{report['performance'].get('sharpe_ratio', 0):.2f}")
            print(f"最大回撤：{report['performance'].get('max_drawdown', 0):.2%}")
            print(f"胜率：{report['performance'].get('win_rate', 0):.2%}")
        print("=" * 60)

    def save_all_figures(self, output_dir: str = "./output") -> None:
        """
        保存所有图表.

        Args:
            output_dir: 输出目录
        """
        import os
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        self.show_entanglement_matrix(save_path=f"{output_dir}/entanglement_{timestamp}.png")
        self.show_entropy_history(save_path=f"{output_dir}/entropy_{timestamp}.png")
        self.show_event_timeline(save_path=f"{output_dir}/events_{timestamp}.png")
        self.show_event_distribution(save_path=f"{output_dir}/event_dist_{timestamp}.png")
        self.show_equity_curve(save_path=f"{output_dir}/equity_{timestamp}.png")
        self.show_drawdown(save_path=f"{output_dir}/drawdown_{timestamp}.png")

        print(f"所有图表已保存到 {output_dir}/")
