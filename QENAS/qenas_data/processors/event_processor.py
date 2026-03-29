"""
事件处理器.

将真实世界事件整合到 QENAS 策略决策流程中.
"""

from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np
from numpy.typing import NDArray
import logging

from qenas_data.feeders.base import EventData, EventType, EventImpact, KlineData

logger = logging.getLogger(__name__)


@dataclass
class EventSignal:
    """
    事件生成的交易信号.

    属性:
        event: 原始事件数据
        target_symbols: 目标交易标的
        signal_strength: 信号强度 (-1 到 1)
        confidence: 置信度 (0 到 1)
        time_horizon: 影响时间范围 (天数)
        decay_rate: 信号衰减率
    """
    event: EventData
    target_symbols: List[str]
    signal_strength: float
    confidence: float
    time_horizon: int = 5
    decay_rate: float = 0.2
    metadata: Dict = field(default_factory=dict)


class EventProcessor:
    """
    事件处理器.

    功能:
    1. 事件分类和过滤
    2. 事件情感分析
    3. 事件信号生成
    4. 事件影响衰减跟踪
    """

    def __init__(self):
        # 事件对各类资产的历史影响记录
        self.event_impact_history: Dict[str, List[float]] = {}

        # 活跃事件（尚未完全衰减的事件）
        self.active_events: List[Tuple[EventData, float]] = []  # (事件，剩余强度)

        # 事件 - 信号映射配置
        self.event_signal_map = self._default_event_signal_map()

    def _default_event_signal_map(self) -> Dict[EventType, Dict]:
        """默认事件 - 信号映射配置."""
        return {
            EventType.EARNINGS: {
                "base_strength": 0.5,
                "time_horizon": 3,
                "decay_rate": 0.3,
            },
            EventType.DIVIDEND: {
                "base_strength": 0.3,
                "time_horizon": 2,
                "decay_rate": 0.4,
            },
            EventType.MACRO_ECONOMIC: {
                "base_strength": 0.6,
                "time_horizon": 5,
                "decay_rate": 0.15,
            },
            EventType.CENTRAL_BANK: {
                "base_strength": 0.8,
                "time_horizon": 7,
                "decay_rate": 0.1,
            },
            EventType.GEOPOLITICAL: {
                "base_strength": 0.7,
                "time_horizon": 10,
                "decay_rate": 0.08,
            },
            EventType.NATURAL_DISASTER: {
                "base_strength": 0.6,
                "time_horizon": 5,
                "decay_rate": 0.15,
            },
            EventType.REGULATORY: {
                "base_strength": 0.5,
                "time_horizon": 7,
                "decay_rate": 0.12,
            },
        }

    def process_event(self, event: EventData) -> Optional[EventSignal]:
        """
        处理单个事件，生成交易信号.

        Args:
            event: 事件数据

        Returns:
            事件信号，如果事件不产生信号则返回 None
        """
        # 获取事件类型的配置
        config = self.event_signal_map.get(event.event_type, {})
        base_strength = config.get("base_strength", 0.3)
        time_horizon = config.get("time_horizon", 5)
        decay_rate = config.get("decay_rate", 0.2)

        # 根据影响级别调整强度
        impact_multiplier = {
            EventImpact.LOW: 0.5,
            EventImpact.MEDIUM: 1.0,
            EventImpact.HIGH: 1.5,
            EventImpact.CRITICAL: 2.0,
        }
        multiplier = impact_multiplier.get(event.impact_level, 1.0)

        # 计算信号强度
        signal_strength = base_strength * multiplier * event.sentiment_score
        signal_strength = np.clip(signal_strength, -1.0, 1.0)

        # 计算置信度
        confidence = self._calculate_confidence(event)

        # 确定目标标的
        target_symbols = event.affected_symbols if event.affected_symbols else []

        if not target_symbols:
            logger.debug(f"No target symbols for event: {event.title}")
            return None

        # 创建信号
        signal = EventSignal(
            event=event,
            target_symbols=target_symbols,
            signal_strength=signal_strength,
            confidence=confidence,
            time_horizon=time_horizon,
            decay_rate=decay_rate,
            metadata={
                "event_type": event.event_type.value,
                "impact_level": event.impact_level.value,
            },
        )

        # 添加到活跃事件列表
        self.active_events.append((event, signal_strength))

        return signal

    def _calculate_confidence(self, event: EventData) -> float:
        """
        计算事件信号的置信度.

        基于:
        - 事件来源可靠性
        - 事件影响范围
        - 历史相似度
        """
        confidence = 0.5  # 基础置信度

        # 来源可靠性
        source_reliability = {
            "yfinance": 0.8,
            "akshare": 0.85,
            "baostock": 0.85,
            "official": 1.0,
        }
        confidence *= source_reliability.get(event.source, 0.7)

        # 影响范围
        n_affected = len(event.affected_symbols) + len(event.affected_sectors)
        if n_affected > 5:
            confidence *= 1.2
        elif n_affected > 2:
            confidence *= 1.1

        # 事件数据完整性
        if event.description and len(event.description) > 50:
            confidence *= 1.1

        return np.clip(confidence, 0.0, 1.0)

    def update_active_events(self) -> List[Tuple[EventData, float]]:
        """
        更新活跃事件（应用衰减）.

        Returns:
            更新后的活跃事件列表
        """
        updated = []
        for event, strength in self.active_events:
            # 获取衰减率
            config = self.event_signal_map.get(event.event_type, {})
            decay_rate = config.get("decay_rate", 0.2)

            # 应用衰减
            new_strength = strength * (1 - decay_rate)

            # 保留仍有影响的事件
            if abs(new_strength) > 0.05:
                updated.append((event, new_strength))

        self.active_events = updated
        return updated

    def get_aggregate_signal(self, symbol: str) -> Tuple[float, float]:
        """
        获取某标的的聚合事件信号.

        Args:
            symbol: 交易标的

        Returns:
            (信号强度，置信度)
        """
        signals = []
        confidences = []

        for event, strength in self.active_events:
            if symbol in event.affected_symbols:
                signals.append(strength)
                confidences.append(0.5)  # 简化处理

        if not signals:
            return (0.0, 0.0)

        # 加权平均
        total_strength = sum(signals)
        avg_confidence = sum(confidences) / len(confidences)

        return (total_strength, avg_confidence)

    def process_klines_with_events(
        self,
        klines: List[KlineData],
        events: List[EventData],
    ) -> List[KlineData]:
        """
        将事件整合到 K 线数据中.

        Args:
            klines: K 线数据列表
            events: 事件数据列表

        Returns:
            带有事件标记的 K 线数据列表
        """
        # 创建事件时间索引
        event_by_date: Dict[datetime.date, List[EventData]] = {}
        for event in events:
            date = event.timestamp.date()
            if date not in event_by_date:
                event_by_date[date] = []
            event_by_date[date].append(event)

        # 处理每个 K 线
        result = []
        for kline in klines:
            # 复制 K 线（避免修改原数据）
            kline_copy = KlineData(
                symbol=kline.symbol,
                open=kline.open,
                high=kline.high,
                low=kline.low,
                close=kline.close,
                volume=kline.volume,
                interval=kline.interval,
                timestamp=kline.timestamp,
                trades_count=kline.trades_count,
            )

            # 添加该日期的事件
            date = kline.timestamp.date()
            if date in event_by_date:
                kline_copy.events = event_by_date[date].copy()

            result.append(kline_copy)

        return result

    def encode_events_for_neuromorphic(
        self,
        events: List[EventData],
    ) -> Dict[str, NDArray[np.float64]]:
        """
        将事件编码为神经形态输入.

        不同脑区接收不同类型的事件信号:
        - 前额叶皮层：风险相关事件
        - 边缘系统：情绪/ sentiment 相关事件
        - 小脑：高频/短期事件
        - 海马体：历史相似事件

        Args:
            events: 事件数据列表

        Returns:
            各脑区的输入信号
        """
        # 初始化各区域输入
        prefrontal_input = []  # 风险信号
        limbic_input = []      # 情绪信号
        cerebellum_input = []  # 高频信号

        for event in events:
            # 前额叶皮层：风险评估
            if event.event_type in [
                EventType.GEOPOLITICAL,
                EventType.NATURAL_DISASTER,
                EventType.REGULATORY,
                EventType.CENTRAL_BANK,
            ]:
                risk_score = event.impact_level.value / 4.0  # 归一化
                prefrontal_input.append(risk_score)

            # 边缘系统：情绪信号
            limbic_input.append(event.sentiment_score)

            # 小脑：短期事件（时间敏感）
            if event.event_type in [
                EventType.EARNINGS,
                EventType.DIVIDEND,
            ]:
                cerebellum_input.append(event.sentiment_score * event.impact_level.value)

        # 转换为 numpy 数组
        return {
            "prefrontal": np.array(prefrontal_input) if prefrontal_input else np.zeros(1),
            "limbic": np.array(limbic_input) if limbic_input else np.zeros(1),
            "cerebellum": np.array(cerebellum_input) if cerebellum_input else np.zeros(1),
        }

    def detect_event_cluster(
        self,
        events: List[EventData],
        time_window_days: int = 3,
    ) -> List[List[EventData]]:
        """
        检测事件集群（多个相关事件集中发生）.

        事件集群通常意味着更大的市场影响.

        Args:
            events: 事件数据列表
            time_window_days: 时间窗口（天）

        Returns:
            事件集群列表
        """
        if not events:
            return []

        # 按时间排序
        sorted_events = sorted(events, key=lambda e: e.timestamp)

        clusters = []
        current_cluster = [sorted_events[0]]

        for event in sorted_events[1:]:
            # 检查是否在当前集群的时间窗口内
            time_diff = (event.timestamp - current_cluster[-1].timestamp).days

            if time_diff <= time_window_days:
                current_cluster.append(event)
            else:
                # 开始新集群
                if len(current_cluster) >= 2:
                    clusters.append(current_cluster)
                current_cluster = [event]

        # 处理最后一个集群
        if len(current_cluster) >= 2:
            clusters.append(current_cluster)

        return clusters

    def adjust_entanglement_for_events(
        self,
        base_entanglement_matrix: NDArray[np.float64],
        events: List[EventData],
        symbol_index: Dict[str, int],
    ) -> NDArray[np.float64]:
        """
        根据事件调整纠缠矩阵.

        重大事件可能改变资产间的相关性结构.

        Args:
            base_entanglement_matrix: 基础纠缠矩阵
            events: 事件数据列表
            symbol_index: 符号到索引的映射

        Returns:
            调整后的纠缠矩阵
        """
        adjusted = base_entanglement_matrix.copy()

        for event in events:
            # 只处理高影响事件
            if event.impact_level not in [EventImpact.HIGH, EventImpact.CRITICAL]:
                continue

            # 获取受影响的资产索引
            affected_indices = []
            for symbol in event.affected_symbols:
                if symbol in symbol_index:
                    affected_indices.append(symbol_index[symbol])

            if len(affected_indices) < 2:
                continue

            # 增加受影响资产间的纠缠强度
            # 重大事件通常会增强资产间的联动性
            impact_factor = 1.0 + (event.impact_level.value * 0.1)

            for i in affected_indices:
                for j in affected_indices:
                    if i != j:
                        adjusted[i, j] = min(1.0, adjusted[i, j] * impact_factor)

        # 重新归一化矩阵
        trace = np.trace(adjusted)
        if trace > 0:
            adjusted = adjusted / trace

        return adjusted
