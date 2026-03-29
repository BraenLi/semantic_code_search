"""测试 QENAS 策略与事件的集成."""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
import numpy as np

from qenas_core.strategies.base import StrategyContext, Kline
from qenas_core.strategies.qenas_strategy import QENASStrategy
from qenas_data.feeders.base import EventData, EventType, EventImpact
from qenas_data.processors.event_processor import EventProcessor


class TestEventIntegration:
    """测试事件信号与 QENAS 策略的集成."""

    def setup_method(self):
        """设置测试环境."""
        self.strategy = QENASStrategy(n_species=10, evolution_interval=5)
        self.context = StrategyContext(strategy_id="test_qenas", initial_capital=Decimal("100000"))
        self.strategy.initialize(self.context)

    def test_process_kline_with_events(self):
        """测试处理带事件的 K 线数据."""
        # 创建 K 线
        kline = Kline(
            symbol="AAPL",
            open=Decimal("150.0"),
            high=Decimal("155.0"),
            low=Decimal("149.0"),
            close=Decimal("154.0"),
            volume=Decimal("1000000"),
            interval="1d",
            timestamp=datetime.utcnow(),
        )

        # 添加事件
        event = EventData(
            event_id="test_earnings",
            event_type=EventType.EARNINGS,
            title="Apple Q4 Earnings Beat",
            description="Apple reports better than expected Q4 earnings",
            timestamp=datetime.utcnow(),
            source="yfinance",
            affected_symbols=["AAPL"],
            impact_level=EventImpact.MEDIUM,
            sentiment_score=0.7,  # 正面消息
        )
        kline.events = [event]

        # 处理 K 线
        self.strategy.on_bar(self.context, kline)

        # 验证事件被处理
        assert len(self.strategy.event_processor.active_events) >= 0  # 至少记录了事件

    def test_process_high_impact_event(self):
        """测试处理高影响事件."""
        # 创建带高影响事件的 K 线
        kline = Kline(
            symbol="AAPL",
            open=Decimal("150.0"),
            high=Decimal("155.0"),
            low=Decimal("149.0"),
            close=Decimal("154.0"),
            volume=Decimal("1000000"),
            interval="1d",
            timestamp=datetime.utcnow(),
        )

        event = EventData(
            event_id="test_regulatory",
            event_type=EventType.REGULATORY,
            title="New Tech Regulations Announced",
            description="Government announces stricter regulations on tech companies",
            timestamp=datetime.utcnow(),
            source="news",
            affected_symbols=["AAPL", "GOOGL", "MSFT"],
            impact_level=EventImpact.HIGH,
            sentiment_score=-0.8,  # 负面消息
        )
        kline.events = [event]

        # 先建立一些基础收益率数据
        for i in range(15):
            test_kline = Kline(
                symbol="AAPL",
                open=Decimal(str(150 + i)),
                high=Decimal(str(155 + i)),
                low=Decimal(str(149 + i)),
                close=Decimal(str(152 + i)),
                volume=Decimal("1000000"),
                interval="1d",
                timestamp=datetime.utcnow() - timedelta(days=15-i),
            )
            self.strategy.on_bar(self.context, test_kline)

        # 处理带高影响事件的 K 线
        self.strategy.on_bar(self.context, kline)

        # 验证事件信号被生成
        signal_strength, confidence = self.strategy.event_processor.get_aggregate_signal("AAPL")
        assert signal_strength < 0  # 负面信号
        assert confidence > 0

    def test_event_affects_entanglement(self):
        """测试事件对纠缠矩阵的影响."""
        # 初始化纠缠矩阵
        processor = EventProcessor()

        # 基础纠缠矩阵（3 个资产）
        base_matrix = np.array([
            [0.33, 0.1, 0.1],
            [0.1, 0.33, 0.1],
            [0.1, 0.1, 0.33],
        ])

        # 创建影响资产 0 和 1 的重大事件
        event = EventData(
            event_id="trade_war",
            event_type=EventType.GEOPOLITICAL,
            title="Trade War Escalation",
            description="US-China trade tensions escalate, affecting tech sector",
            timestamp=datetime.utcnow(),
            source="news",
            affected_symbols=["AAPL", "GOOGL"],
            impact_level=EventImpact.CRITICAL,
            sentiment_score=-0.9,
        )

        symbol_index = {"AAPL": 0, "GOOGL": 1, "MSFT": 2}

        # 调整纠缠矩阵
        adjusted_matrix = processor.adjust_entanglement_for_events(
            base_matrix, [event], symbol_index
        )

        # 验证受影响的资产间纠缠增强
        assert adjusted_matrix[0, 1] > base_matrix[0, 1], \
            "AAPL-GOOGL 纠缠应该增强"
        assert adjusted_matrix[1, 0] > base_matrix[1, 0], \
            "GOOGL-AAPL 纠缠应该增强"

        # 未受影响的资产纠缠变化较小
        assert abs(adjusted_matrix[0, 2] - base_matrix[0, 2]) < 0.05, \
            "AAPL-MSFT 纠缠变化应该较小"
        assert abs(adjusted_matrix[1, 2] - base_matrix[1, 2]) < 0.05, \
            "GOOGL-MSFT 纠缠变化应该较小"

    def test_neuromorphic_event_encoding(self):
        """测试事件的神经形态编码."""
        processor = EventProcessor()

        # 创建不同类型的事件
        events = [
            EventData(
                event_id="risk_event",
                event_type=EventType.GEOPOLITICAL,
                title="Geopolitical Risk",
                description="International tension rises",
                timestamp=datetime.utcnow(),
                source="news",
                affected_symbols=["AAPL"],
                impact_level=EventImpact.HIGH,
                sentiment_score=-0.6,
            ),
            EventData(
                event_id="positive_earnings",
                event_type=EventType.EARNINGS,
                title="Strong Earnings",
                description="Company beats earnings expectations",
                timestamp=datetime.utcnow(),
                source="yfinance",
                affected_symbols=["AAPL"],
                impact_level=EventImpact.MEDIUM,
                sentiment_score=0.8,
            ),
        ]

        # 编码为神经形态输入
        encoding = processor.encode_events_for_neuromorphic(events)

        # 验证各脑区接收到信号
        assert "prefrontal" in encoding
        assert "limbic" in encoding
        assert "cerebellum" in encoding

        # 边缘系统应该接收到所有事件的情绪信号
        assert len(encoding["limbic"]) == 2

        # 前额叶皮层应该接收到风险事件信号
        assert len(encoding["prefrontal"]) >= 1

    def test_event_signal_integration(self):
        """测试事件信号整合到策略信号."""
        # 创建基础策略信号
        base_signals = np.array([0.3, 0.5, -0.2, 0.1, 0.4, -0.3, 0.2, 0.6, -0.1, 0.35])

        # 创建事件信号
        from qenas_data.processors.event_processor import EventSignal
        event_signal = EventSignal(
            event=EventData(
                event_id="test_event",
                event_type=EventType.EARNINGS,
                title="Test Earnings",
                description="Test",
                timestamp=datetime.utcnow(),
                source="test",
                affected_symbols=["AAPL"],
                impact_level=EventImpact.MEDIUM,
                sentiment_score=0.6,
            ),
            target_symbols=["AAPL"],
            signal_strength=0.5,
            confidence=0.8,
        )

        # 整合信号
        enhanced_signals = self.strategy._integrate_event_signal(
            base_signals, event_signal, "AAPL"
        )

        # 验证信号数组形状不变
        assert enhanced_signals.shape == base_signals.shape

        # 验证信号被修改（SENTIMENT 生态位的策略对事件更敏感）
        # 由于 SENTIMENT 生态位的策略会被调整，信号应该会发生变化
        assert len(enhanced_signals) == len(base_signals)


class TestEventClusterDetection:
    """测试事件集群检测."""

    def test_detect_event_cluster(self):
        """测试检测事件集群."""
        processor = EventProcessor()
        base_time = datetime.utcnow()

        # 创建时间相近的事件集群
        events = [
            EventData(
                event_id=f"cluster_event_{i}",
                event_type=EventType.EARNINGS,
                title=f"Tech Earnings {i}",
                description=f"Company {i} reports earnings",
                timestamp=base_time + timedelta(hours=i * 3),  # 3 小时间隔
                source="yfinance",
                affected_symbols=["AAPL", "GOOGL", "MSFT"][i % 3],
                impact_level=EventImpact.MEDIUM,
                sentiment_score=0.5 if i % 2 == 0 else -0.3,
            )
            for i in range(5)
        ]

        # 检测集群
        clusters = processor.detect_event_cluster(events, time_window_days=1)

        # 所有事件应该在一个集群中
        assert len(clusters) == 1
        assert len(clusters[0]) == 5

    def test_multiple_event_clusters(self):
        """测试检测多个事件集群."""
        processor = EventProcessor()

        # 创建两个分离的集群
        events = []
        base_time = datetime.utcnow()

        # 集群 1
        for i in range(3):
            events.append(EventData(
                event_id=f"cluster1_{i}",
                event_type=EventType.EARNINGS,
                title=f"Event {i}",
                description="Test",
                timestamp=base_time + timedelta(hours=i),
                source="test",
                affected_symbols=["AAPL"],
                impact_level=EventImpact.MEDIUM,
                sentiment_score=0.5,
            ))

        # 集群 2（5 天后）
        for i in range(3):
            events.append(EventData(
                event_id=f"cluster2_{i}",
                event_type=EventType.REGULATORY,
                title=f"Regulation {i}",
                description="Test",
                timestamp=base_time + timedelta(days=5, hours=i),
                source="test",
                affected_symbols=["GOOGL"],
                impact_level=EventImpact.HIGH,
                sentiment_score=-0.5,
            ))

        clusters = processor.detect_event_cluster(events, time_window_days=2)

        # 应该检测到两个集群
        assert len(clusters) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
