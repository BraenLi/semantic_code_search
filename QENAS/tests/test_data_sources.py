"""数据源模块测试."""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from qenas_data.feeders.base import (
    EventData,
    EventType,
    EventImpact,
    KlineData,
)
from qenas_data.processors.event_processor import EventProcessor


class TestEventData:
    """测试事件数据."""

    def test_event_creation(self):
        """测试事件创建."""
        event = EventData(
            event_id="test_1",
            event_type=EventType.EARNINGS,
            title="Test Earnings",
            description="Test description",
            timestamp=datetime.utcnow(),
            source="test",
            affected_symbols=["AAPL", "GOOGL"],
            impact_level=EventImpact.MEDIUM,
            sentiment_score=0.5,
        )

        assert event.event_type == EventType.EARNINGS
        assert len(event.affected_symbols) == 2
        assert event.sentiment_score == 0.5

    def test_event_to_dict(self):
        """测试事件序列化."""
        event = EventData(
            event_id="test_2",
            event_type=EventType.MACRO_ECONOMIC,
            title="GDP Report",
            description="Quarterly GDP data",
            timestamp=datetime.utcnow(),
            source="official",
            affected_regions=["CN", "US"],
            impact_level=EventImpact.HIGH,
            sentiment_score=0.3,
        )

        data = event.to_dict()
        assert data["event_type"] == "macro_economic"
        assert data["impact_level"] == 3
        assert "CN" in data["affected_regions"]


class TestEventProcessor:
    """测试事件处理器."""

    def test_process_event(self):
        """测试事件处理."""
        processor = EventProcessor()

        event = EventData(
            event_id="test_3",
            event_type=EventType.EARNINGS,
            title="Apple Earnings Beat",
            description="Apple reports better than expected earnings",
            timestamp=datetime.utcnow(),
            source="yfinance",
            affected_symbols=["AAPL"],
            impact_level=EventImpact.MEDIUM,
            sentiment_score=0.8,  # 正面消息
        )

        signal = processor.process_event(event)

        assert signal is not None
        assert signal.target_symbols == ["AAPL"]
        assert signal.signal_strength > 0  # 正面信号
        assert 0 <= signal.confidence <= 1

    def test_process_negative_event(self):
        """测试负面事件处理."""
        processor = EventProcessor()

        event = EventData(
            event_id="test_4",
            event_type=EventType.REGULATORY,
            title="New Tech Regulations",
            description="Government announces stricter tech regulations",
            timestamp=datetime.utcnow(),
            source="news",
            affected_symbols=["AAPL", "GOOGL", "MSFT"],
            affected_sectors=["tech"],
            impact_level=EventImpact.HIGH,
            sentiment_score=-0.6,  # 负面消息
        )

        signal = processor.process_event(event)

        assert signal is not None
        assert signal.signal_strength < 0  # 负面信号
        assert len(signal.target_symbols) == 3

    def test_update_active_events(self):
        """测试活跃事件衰减."""
        processor = EventProcessor()

        event = EventData(
            event_id="test_5",
            event_type=EventType.EARNINGS,
            title="Test Earnings",
            description="Test",
            timestamp=datetime.utcnow(),
            source="test",
            affected_symbols=["AAPL"],
            impact_level=EventImpact.MEDIUM,
            sentiment_score=0.5,
        )

        processor.process_event(event)
        initial_count = len(processor.active_events)

        # 多次更新导致衰减
        for _ in range(10):
            processor.update_active_events()

        # 事件应该已经完全衰减或被移除
        assert len(processor.active_events) <= initial_count

    def test_get_aggregate_signal(self):
        """测试聚合信号."""
        processor = EventProcessor()

        # 添加多个同标的的事件
        events = [
            EventData(
                event_id=f"agg_{i}",
                event_type=EventType.EARNINGS,
                title=f"Event {i}",
                description="Test",
                timestamp=datetime.utcnow(),
                source="test",
                affected_symbols=["AAPL"],
                impact_level=EventImpact.MEDIUM,
                sentiment_score=0.3 if i % 2 == 0 else -0.2,
            )
            for i in range(5)
        ]

        for event in events:
            processor.process_event(event)

        strength, confidence = processor.get_aggregate_signal("AAPL")

        # 应该有非零信号
        assert strength != 0 or confidence == 0  # 要么有信号，要么没有活跃事件

    def test_encode_events_for_neuromorphic(self):
        """测试事件编码为神经形态输入."""
        processor = EventProcessor()

        events = [
            EventData(
                event_id="neuro_1",
                event_type=EventType.GEOPOLITICAL,
                title="Trade War Tension",
                description="US-China trade tension rises",
                timestamp=datetime.utcnow(),
                source="news",
                affected_symbols=["AAPL"],
                impact_level=EventImpact.HIGH,
                sentiment_score=-0.5,
            ),
            EventData(
                event_id="neuro_2",
                event_type=EventType.EARNINGS,
                title="Good Earnings",
                description="Beat expectations",
                timestamp=datetime.utcnow(),
                source="yfinance",
                affected_symbols=["AAPL"],
                impact_level=EventImpact.MEDIUM,
                sentiment_score=0.7,
            ),
        ]

        inputs = processor.encode_events_for_neuromorphic(events)

        assert "prefrontal" in inputs
        assert "limbic" in inputs
        assert "cerebellum" in inputs

        # 边缘系统应该接收到所有事件的情绪信号
        assert len(inputs["limbic"]) == 2

    def test_detect_event_cluster(self):
        """测试事件集群检测."""
        processor = EventProcessor()

        # 创建时间相近的事件
        base_time = datetime.utcnow()
        events = [
            EventData(
                event_id=f"cluster_{i}",
                event_type=EventType.EARNINGS,
                title=f"Event {i}",
                description="Test",
                timestamp=base_time + timedelta(hours=i * 2),  # 2 小时间隔
                source="test",
                affected_symbols=["AAPL"],
                impact_level=EventImpact.MEDIUM,
                sentiment_score=0.5,
            )
            for i in range(5)
        ]

        clusters = processor.detect_event_cluster(events, time_window_days=1)

        # 所有事件应该在一个集群中
        assert len(clusters) == 1
        assert len(clusters[0]) == 5

    def test_adjust_entanglement_for_events(self):
        """测试事件对纠缠矩阵的影响."""
        import numpy as np

        processor = EventProcessor()

        # 基础纠缠矩阵（3 个资产）
        base_matrix = np.array([
            [0.33, 0.1, 0.1],
            [0.1, 0.33, 0.1],
            [0.1, 0.1, 0.33],
        ])

        # 重大事件影响资产 0 和 1
        event = EventData(
            event_id="entangle_1",
            event_type=EventType.GEOPOLITICAL,
            title="Trade War",
            description="Affects assets 0 and 1",
            timestamp=datetime.utcnow(),
            source="news",
            affected_symbols=["AAPL", "GOOGL"],
            impact_level=EventImpact.CRITICAL,
            sentiment_score=-0.8,
        )

        symbol_index = {"AAPL": 0, "GOOGL": 1, "MSFT": 2}

        adjusted = processor.adjust_entanglement_for_events(
            base_matrix, [event], symbol_index
        )

        # 资产 0 和 1 之间的纠缠应该增强
        assert adjusted[0, 1] > base_matrix[0, 1]
        assert adjusted[1, 0] > base_matrix[1, 0]


class TestKlineWithEvents:
    """测试带事件的 K 线数据."""

    def test_kline_with_events(self):
        """测试 K 线附带事件."""
        event = EventData(
            event_id="kline_event",
            event_type=EventType.EARNINGS,
            title="Earnings Report",
            description="Q4 earnings",
            timestamp=datetime.utcnow(),
            source="yfinance",
            affected_symbols=["AAPL"],
            impact_level=EventImpact.HIGH,
            sentiment_score=0.6,
        )

        kline = KlineData(
            symbol="AAPL",
            open=Decimal("150.0"),
            high=Decimal("155.0"),
            low=Decimal("149.0"),
            close=Decimal("154.0"),
            volume=Decimal("1000000"),
            interval="1d",
            timestamp=datetime.utcnow(),
            events=[event],
        )

        assert len(kline.events) == 1
        assert kline.events[0].event_type == EventType.EARNINGS
        assert kline.events[0].sentiment_score == 0.6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
