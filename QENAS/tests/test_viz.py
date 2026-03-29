"""可视化模块测试."""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
import numpy as np

from qenas_data.feeders.base import EventData, EventType, EventImpact
from qenas_viz.entanglement_viz import EntanglementVisualizer
from qenas_viz.event_viz import EventTimelineVisualizer
from qenas_viz.performance_viz import PerformanceVisualizer, BacktestResult
from qenas_viz.dashboard import QENASDashboard


class TestEntanglementVisualizer:
    """测试纠缠矩阵可视化."""

    def test_visualizer_initialization(self):
        """测试可视化器初始化."""
        viz = EntanglementVisualizer(["AAPL", "GOOGL", "MSFT"])

        assert viz.symbol_labels == ["AAPL", "GOOGL", "MSFT"]
        assert len(viz.entropy_history) == 0
        assert len(viz.matrix_history) == 0

    def test_record_history(self):
        """测试历史记录."""
        viz = EntanglementVisualizer(["AAPL", "GOOGL"])

        # 创建测试矩阵
        matrix = np.array([
            [0.5, 0.2],
            [0.2, 0.5],
        ])

        viz.record_history(matrix, entropy=0.5)

        assert len(viz.matrix_history) == 1
        assert len(viz.entropy_history) == 1
        assert viz.get_latest_entropy() == 0.5

    def test_plot_entanglement_matrix_text_mode(self):
        """测试纠缠矩阵热力图（文本模式）."""
        viz = EntanglementVisualizer(["AAPL", "GOOGL", "MSFT"])

        matrix = np.array([
            [0.33, 0.1, 0.1],
            [0.1, 0.33, 0.1],
            [0.1, 0.1, 0.33],
        ])

        # 文本模式输出
        result = viz._text_heatmap(matrix, "Test Matrix")

        assert "Test Matrix" in result
        assert "AAPL" in result
        assert "GOOGL" in result
        assert "MSFT" in result

    def test_plot_network_text_mode(self):
        """测试网络图（文本模式）."""
        viz = EntanglementVisualizer(["AAPL", "GOOGL", "MSFT"])

        matrix = np.array([
            [0.33, 0.5, 0.1],
            [0.5, 0.33, 0.1],
            [0.1, 0.1, 0.33],
        ])

        result = viz._text_network(matrix, threshold=0.3, title="Test Network")

        assert "Test Network" in result
        assert "AAPL -- GOOGL" in result  # 超过阈值的连接


class TestEventTimelineVisualizer:
    """测试事件时间线可视化."""

    def test_visualizer_initialization(self):
        """测试可视化器初始化."""
        viz = EventTimelineVisualizer()
        assert len(viz.events) == 0

    def test_add_events(self):
        """测试添加事件."""
        viz = EventTimelineVisualizer()

        events = [
            EventData(
                event_id="test_1",
                event_type=EventType.EARNINGS,
                title="Test Earnings 1",
                description="Test",
                timestamp=datetime.utcnow() - timedelta(days=2),
                source="test",
                affected_symbols=["AAPL"],
                impact_level=EventImpact.MEDIUM,
                sentiment_score=0.5,
            ),
            EventData(
                event_id="test_2",
                event_type=EventType.REGULATORY,
                title="Test Regulation",
                description="Test",
                timestamp=datetime.utcnow() - timedelta(days=1),
                source="test",
                affected_symbols=["GOOGL"],
                impact_level=EventImpact.HIGH,
                sentiment_score=-0.6,
            ),
        ]

        viz.add_events(events)

        assert len(viz.events) == 2

    def test_get_event_summary(self):
        """测试获取事件摘要."""
        viz = EventTimelineVisualizer()

        events = [
            EventData(
                event_id=f"test_{i}",
                event_type=EventType.EARNINGS,
                title=f"Test {i}",
                description="Test",
                timestamp=datetime.utcnow() - timedelta(days=i),
                source="test",
                affected_symbols=["AAPL"],
                impact_level=EventImpact.MEDIUM if i % 2 == 0 else EventImpact.HIGH,
                sentiment_score=0.3 if i % 2 == 0 else -0.3,
            )
            for i in range(5)
        ]

        viz.add_events(events)
        summary = viz.get_event_summary()

        assert summary["total_events"] == 5
        assert "earnings" in summary["type_distribution"]
        assert abs(summary["avg_sentiment"]) < 0.1  # 接近零（正负相抵）

    def test_text_timeline(self):
        """测试文本时间线."""
        viz = EventTimelineVisualizer()

        event = EventData(
            event_id="test",
            event_type=EventType.EARNINGS,
            title="Apple Q4 Earnings Beat",
            description="Test",
            timestamp=datetime.utcnow(),
            source="test",
            affected_symbols=["AAPL"],
            impact_level=EventImpact.MEDIUM,
            sentiment_score=0.7,
        )

        viz.add_events([event])
        result = viz._text_timeline(viz.events, "Test Timeline")

        assert "Test Timeline" in result
        assert "Apple Q4 Earnings Beat" in result


class TestPerformanceVisualizer:
    """测试业绩可视化."""

    def test_visualizer_initialization(self):
        """测试可视化器初始化."""
        viz = PerformanceVisualizer()
        assert viz.results is None

    def test_set_results(self):
        """测试设置回测结果."""
        viz = PerformanceVisualizer()

        timestamps = [datetime.utcnow() - timedelta(days=i) for i in range(10)]
        timestamps.reverse()

        results = BacktestResult(
            timestamps=timestamps,
            equity_curve=[100000 + i * 1000 for i in range(10)],
            returns=[0.01] * 9,
            benchmark=[100000 + i * 500 for i in range(10)],
            max_drawdown=0.05,
            sharpe_ratio=1.5,
            total_return=0.1,
            win_rate=0.6,
        )

        viz.set_results(results)

        assert viz.results is not None
        assert viz.results.total_return == 0.1

    def test_text_equity_curve(self):
        """测试文本权益曲线."""
        viz = PerformanceVisualizer()

        timestamps = [datetime.utcnow() - timedelta(days=i) for i in range(10)]
        timestamps.reverse()

        results = BacktestResult(
            timestamps=timestamps,
            equity_curve=[100000 + i * 1000 for i in range(10)],
            returns=[0.01] * 9,
            max_drawdown=0.05,
            sharpe_ratio=1.5,
            total_return=0.1,
            win_rate=0.6,
        )

        result = viz._text_equity_curve(results, "Test Equity")

        assert "Test Equity" in result
        assert "总收益率：10.00%" in result
        assert "夏普比率：1.50" in result

    def test_text_drawdown(self):
        """测试文本回撤分析."""
        viz = PerformanceVisualizer()

        timestamps = [datetime.utcnow() - timedelta(days=i) for i in range(10)]
        timestamps.reverse()

        # 创建一个有回撤的权益曲线
        equity_curve = [100, 110, 120, 115, 125, 130, 120, 135, 140, 150]

        results = BacktestResult(
            timestamps=timestamps,
            equity_curve=equity_curve,
            returns=[0.01] * 9,
            max_drawdown=0.083,  # 约 8.3%
            sharpe_ratio=1.0,
            total_return=0.5,
            win_rate=0.6,
        )

        result = viz._text_drawdown(results, "Test Drawdown")

        assert "Test Drawdown" in result
        assert "最大回撤：8.30%" in result


class TestQENASDashboard:
    """测试仪表板."""

    def test_dashboard_initialization(self):
        """测试仪表板初始化."""
        dashboard = QENASDashboard(["AAPL", "GOOGL", "MSFT"])

        assert dashboard.symbol_labels == ["AAPL", "GOOGL", "MSFT"]
        assert dashboard.step_count == 0
        assert dashboard.is_initialized is False

    def test_dashboard_initialize(self):
        """测试仪表板初始化方法."""
        dashboard = QENASDashboard()
        dashboard.initialize(["AAPL", "GOOGL"])

        assert dashboard.is_initialized is True
        assert dashboard.symbol_labels == ["AAPL", "GOOGL"]

    def test_update_entanglement(self):
        """测试更新纠缠数据."""
        dashboard = QENASDashboard(["AAPL", "GOOGL"])

        matrix = np.array([
            [0.5, 0.2],
            [0.2, 0.5],
        ])

        dashboard.update_entanglement(matrix, entropy=0.5)

        assert dashboard.step_count == 1
        assert dashboard.entanglement_viz.get_latest_entropy() == 0.5

    def test_add_events(self):
        """测试添加事件."""
        dashboard = QENASDashboard(["AAPL"])

        event = EventData(
            event_id="test",
            event_type=EventType.EARNINGS,
            title="Test Event",
            description="Test",
            timestamp=datetime.utcnow(),
            source="test",
            affected_symbols=["AAPL"],
            impact_level=EventImpact.MEDIUM,
            sentiment_score=0.5,
        )

        dashboard.add_events([event])

        assert len(dashboard.event_viz.events) == 1

    def test_get_status_report(self):
        """测试获取状态报告."""
        dashboard = QENASDashboard(["AAPL", "GOOGL"])

        # 添加一些数据
        matrix = np.ones((2, 2)) * 0.5
        dashboard.update_entanglement(matrix, entropy=0.8)

        event = EventData(
            event_id="test",
            event_type=EventType.EARNINGS,
            title="Test",
            description="Test",
            timestamp=datetime.utcnow(),
            source="test",
            affected_symbols=["AAPL"],
            impact_level=EventImpact.MEDIUM,
            sentiment_score=0.5,
        )
        dashboard.add_events([event])

        report = dashboard.get_status_report()

        assert report["step_count"] == 1
        assert report["entanglement"]["latest_entropy"] == 0.8
        assert report["events"]["total_events"] == 1

    def test_print_status(self, capsys):
        """测试打印状态（捕获输出）."""
        dashboard = QENASDashboard(["AAPL"])

        # 添加回测结果
        timestamps = [datetime.utcnow() - timedelta(days=i) for i in range(10)]
        timestamps.reverse()

        results = BacktestResult(
            timestamps=timestamps,
            equity_curve=[100000 + i * 1000 for i in range(10)],
            returns=[0.01] * 9,
            max_drawdown=0.05,
            sharpe_ratio=1.5,
            total_return=0.1,
            win_rate=0.6,
        )
        dashboard.set_backtest_results(results)

        dashboard.print_status()

        captured = capsys.readouterr()
        assert "QENAS 策略状态仪表板" in captured.out
        assert "总收益：10.00%" in captured.out
        assert "夏普比率：1.50" in captured.out


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
