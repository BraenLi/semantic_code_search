"""数据源基类."""

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class EventType(Enum):
    """事件类型."""
    # 宏观经济
    MACRO_ECONOMIC = "macro_economic"
    CENTRAL_BANK = "central_bank"
    ECONOMIC_DATA = "economic_data"

    # 公司事件
    EARNINGS = "earnings"
    MERGER = "merger"
    EXECUTIVE_CHANGE = "executive_change"
    DIVIDEND = "dividend"

    # 地缘政治
    GEOPOLITICAL = "geopolitical"
    ELECTION = "election"
    TRADE_POLICY = "trade_policy"

    # 自然灾害
    NATURAL_DISASTER = "natural_disaster"

    # 行业事件
    INDUSTRY_NEWS = "industry_news"
    REGULATORY = "regulatory"

    # 市场情绪
    MARKET_SENTIMENT = "market_sentiment"


class EventImpact(Enum):
    """事件影响级别."""
    LOW = 1       # 低影响
    MEDIUM = 2    # 中等影响
    HIGH = 3      # 高影响
    CRITICAL = 4  # 临界/重大事件


@dataclass
class EventData:
    """
    事件数据.

    真实世界事件作为数据源，用于：
    - 影响量子纠缠矩阵（改变资产关联性）
    - 输入神经形态处理器（情绪信号）
    - 触发策略生态位调整
    """
    event_id: str
    event_type: EventType
    title: str
    description: str
    timestamp: datetime
    source: str

    # 事件影响范围
    affected_symbols: List[str] = field(default_factory=list)
    affected_sectors: List[str] = field(default_factory=list)
    affected_regions: List[str] = field(default_factory=list)

    # 事件影响级别
    impact_level: EventImpact = EventImpact.MEDIUM

    # 事件极性（对市场的影响方向）
    sentiment_score: float = 0.0  # -1 (极度负面) 到 +1 (极度正面)

    # 事件元数据
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 事件是否已处理
    processed: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> "EventData":
        """从字典创建 EventData."""
        return cls(
            event_id=data.get("event_id", ""),
            event_type=EventType(data.get("event_type", "macro_economic")),
            title=data.get("title", ""),
            description=data.get("description", ""),
            timestamp=data.get("timestamp", datetime.utcnow()),
            source=data.get("source", ""),
            affected_symbols=data.get("affected_symbols", []),
            affected_sectors=data.get("affected_sectors", []),
            affected_regions=data.get("affected_regions", []),
            impact_level=EventImpact(data.get("impact_level", 2)),
            sentiment_score=float(data.get("sentiment_score", 0.0)),
            metadata=data.get("metadata", {}),
        )

    def to_dict(self) -> dict:
        """转换为字典."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "title": self.title,
            "description": self.description,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "affected_symbols": self.affected_symbols,
            "affected_sectors": self.affected_sectors,
            "affected_regions": self.affected_regions,
            "impact_level": self.impact_level.value,
            "sentiment_score": self.sentiment_score,
        }


@dataclass
class KlineData:
    """K 线数据."""
    symbol: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    interval: str
    timestamp: datetime
    trades_count: int = 0

    # 事件标记（该 K 线周期内发生的事件）
    events: List[EventData] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "KlineData":
        """从字典创建 KlineData."""
        return cls(
            symbol=data.get("symbol", ""),
            open=Decimal(str(data.get("open", 0))),
            high=Decimal(str(data.get("high", 0))),
            low=Decimal(str(data.get("low", 0))),
            close=Decimal(str(data.get("close", 0))),
            volume=Decimal(str(data.get("volume", 0))),
            interval=data.get("interval", "1d"),
            timestamp=data.get("timestamp", datetime.utcnow()),
            trades_count=data.get("trades_count", 0),
        )


class BaseDataFeeder(ABC):
    """
    数据源基类.

    子类需要实现:
    - fetch_klines: 获取 K 线数据
    - fetch_latest: 获取最新数据
    - fetch_events: 获取事件数据 (可选)
    """

    def __init__(self, market: str, name: str = ""):
        self.market = market
        self.name = name or f"{market}_feeder"
        self.is_connected = False

    @abstractmethod
    def connect(self) -> bool:
        """连接到数据源."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """断开连接."""
        pass

    @abstractmethod
    def fetch_klines(
        self,
        symbol: str,
        interval: str,
        start_date: datetime,
        end_date: datetime,
        limit: int = 1000,
    ) -> List[KlineData]:
        """
        获取 K 线数据.

        Args:
            symbol: 交易标的
            interval: K 线周期
            start_date: 开始日期
            end_date: 结束日期
            limit: 最大返回数量

        Returns:
            K 线数据列表
        """
        pass

    @abstractmethod
    def fetch_latest(
        self,
        symbol: str,
        interval: str,
    ) -> Optional[KlineData]:
        """
        获取最新 K 线数据.

        Args:
            symbol: 交易标的
            interval: K 线周期

        Returns:
            最新 K 线数据
        """
        pass

    def fetch_events(
        self,
        symbols: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_types: Optional[List[EventType]] = None,
        min_impact: EventImpact = EventImpact.LOW,
    ) -> List[EventData]:
        """
        获取事件数据.

        默认实现返回空列表，子类可以选择性实现.

        Args:
            symbols: 关注的标的列表
            start_date: 开始日期
            end_date: 结束日期
            event_types: 关注的事件类型
            min_impact: 最小影响级别

        Returns:
            事件数据列表
        """
        return []

    def validate_kline(self, kline: KlineData) -> bool:
        """验证 K 线数据有效性."""
        # OHLC 验证
        if kline.high < kline.low:
            logger.warning(f"Invalid OHLC: high < low for {kline}")
            return False

        if kline.high < kline.open or kline.high < kline.close:
            logger.warning(f"Invalid OHLC: high doesn't contain open/close for {kline}")
            return False

        if kline.low > kline.open or kline.low > kline.close:
            logger.warning(f"Invalid OHLC: low doesn't contain open/close for {kline}")
            return False

        # 数量验证
        if kline.volume < 0:
            logger.warning(f"Negative volume for {kline}")
            return False

        return True

    def filter_invalid_klines(self, klines: List[KlineData]) -> List[KlineData]:
        """过滤无效的 K 线数据."""
        return [k for k in klines if self.validate_kline(k)]

    def match_events_to_klines(
        self,
        klines: List[KlineData],
        events: List[EventData],
    ) -> List[KlineData]:
        """
        将事件匹配到 K 线数据.

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

        # 匹配到 K 线
        result = []
        for kline in klines:
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
            date = kline.timestamp.date()
            if date in event_by_date:
                kline_copy.events = event_by_date[date].copy()
            result.append(kline_copy)

        return result
