"""
Yahoo Finance 数据源.

用于获取美股和港股数据.
依赖：yfinance
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List
import logging

from qenas_data.feeders.base import (
    BaseDataFeeder,
    KlineData,
    EventData,
    EventType,
    EventImpact,
)

logger = logging.getLogger(__name__)


class YahooFinanceFeeder(BaseDataFeeder):
    """
    Yahoo Finance 数据源.

    支持:
    - 美股数据 (AAPL, GOOGL, MSFT, etc.)
    - 港股数据 (0700.HK, 9988.HK, etc.)
    - ETF 数据 (SPY, QQQ, etc.)

    事件数据源:
    - 财报发布 (Earnings)
    - 分红派息 (Dividends)
    - 公司行为 (Mergers, Executive changes)
    """

    def __init__(self):
        super().__init__(market="US/HK", name="yahoo_finance")
        self._ticker_cache = {}

    def connect(self) -> bool:
        """连接到 Yahoo Finance."""
        try:
            import yfinance as yf
            self.is_connected = True
            logger.info("Connected to Yahoo Finance")
            return True
        except ImportError:
            logger.warning("yfinance not installed. Run: pip install yfinance")
            self.is_connected = False
            return False

    def disconnect(self) -> None:
        """断开连接."""
        self.is_connected = False
        logger.info("Disconnected from Yahoo Finance")

    def _get_ticker(self, symbol: str):
        """获取 ticker 对象（带缓存）."""
        if symbol not in self._ticker_cache:
            import yfinance as yf
            self._ticker_cache[symbol] = yf.Ticker(symbol)
        return self._ticker_cache[symbol]

    def fetch_klines(
        self,
        symbol: str,
        interval: str = "1d",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[KlineData]:
        """
        获取 K 线数据.

        Args:
            symbol: 交易标的 (e.g., "AAPL", "0700.HK")
            interval: K 线周期 (1d, 1wk, 1mo, etc.)
            start_date: 开始日期
            end_date: 结束日期
            limit: 最大返回数量

        Returns:
            K 线数据列表
        """
        if not self.is_connected:
            if not self.connect():
                return []

        import yfinance as yf

        # 默认时间范围
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=365)

        try:
            ticker = self._get_ticker(symbol)

            # 获取历史数据
            df = ticker.history(
                start=start_date,
                end=end_date,
                interval=interval,
            )

            if df.empty:
                logger.warning(f"No data found for {symbol}")
                return []

            # 转换为 KlineData 列表
            klines = []
            for timestamp, row in df.iterrows():
                # 处理 timestamp
                if hasattr(timestamp, 'tzinfo') and timestamp.tzinfo is not None:
                    timestamp = timestamp.replace(tzinfo=None)

                kline = KlineData(
                    symbol=symbol,
                    open=Decimal(str(row.get('Open', 0))),
                    high=Decimal(str(row.get('High', 0))),
                    low=Decimal(str(row.get('Low', 0))),
                    close=Decimal(str(row.get('Close', 0))),
                    volume=Decimal(str(row.get('Volume', 0))),
                    interval=interval,
                    timestamp=timestamp,
                    trades_count=0,
                )
                klines.append(kline)

            # 限制数量
            if len(klines) > limit:
                klines = klines[-limit:]

            logger.info(f"Fetched {len(klines)} klines for {symbol}")
            return klines

        except Exception as e:
            logger.error(f"Error fetching klines for {symbol}: {e}")
            return []

    def fetch_latest(
        self,
        symbol: str,
        interval: str = "1d",
    ) -> Optional[KlineData]:
        """获取最新 K 线数据."""
        klines = self.fetch_klines(
            symbol=symbol,
            interval=interval,
            start_date=datetime.now() - timedelta(days=10),
            end_date=datetime.now(),
            limit=1,
        )
        return klines[-1] if klines else None

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

        从 Yahoo Finance 获取公司事件：
        - 财报 (Earnings)
        - 分红 (Dividends)
        - 拆股 (Splits)

        Args:
            symbols: 关注的标的列表
            start_date: 开始日期
            end_date: 结束日期
            event_types: 关注的事件类型
            min_impact: 最小影响级别

        Returns:
            事件数据列表
        """
        if not self.is_connected:
            if not self.connect():
                return []

        if symbols is None:
            logger.warning("No symbols specified for event fetch")
            return []

        events = []
        event_id_counter = 0

        for symbol in symbols:
            try:
                ticker = self._get_ticker(symbol)

                # 获取财报数据
                earnings = ticker.earnings_dates
                if earnings is not None and not earnings.empty:
                    for _, row in earnings.iterrows():
                        event_id_counter += 1
                        event = EventData(
                            event_id=f"yahoo_earnings_{event_id_counter}",
                            event_type=EventType.EARNINGS,
                            title=f"{symbol} Earnings Report",
                            description=f"Earnings per share: {row.get('EPS', 'N/A')}",
                            timestamp=row.name if hasattr(row.name, 'to_pydatetime') else datetime.now(),
                            source="yfinance",
                            affected_symbols=[symbol],
                            impact_level=EventImpact.MEDIUM,
                            sentiment_score=0.0,  # 需要根据实际数据计算
                        )
                        events.append(event)

                # 获取分红数据
                dividends = ticker.dividends
                if dividends is not None and not dividends.empty:
                    # 只获取近期的分红
                    if start_date is None:
                        start_date = datetime.now() - timedelta(days=365)

                    for div_date, div_amount in dividends.items():
                        if div_date.tzinfo:
                            div_date = div_date.replace(tzinfo=None)

                        if start_date and div_date < start_date:
                            continue
                        if end_date and div_date > end_date:
                            break

                        event_id_counter += 1
                        event = EventData(
                            event_id=f"yahoo_dividend_{event_id_counter}",
                            event_type=EventType.DIVIDEND,
                            title=f"{symbol} Dividend",
                            description=f"Dividend amount: ${div_amount}",
                            timestamp=div_date,
                            source="yfinance",
                            affected_symbols=[symbol],
                            impact_level=EventImpact.LOW,
                            sentiment_score=0.1,  # 分红通常是正面信号
                        )
                        events.append(event)

            except Exception as e:
                logger.error(f"Error fetching events for {symbol}: {e}")
                continue

        # 过滤事件类型
        if event_types:
            events = [e for e in events if e.event_type in event_types]

        # 过滤影响级别
        events = [e for e in events if e.impact_level.value >= min_impact.value]

        logger.info(f"Fetched {len(events)} events for {len(symbols)} symbols")
        return events

    def get_company_info(self, symbol: str) -> dict:
        """
        获取公司信息.

        Args:
            symbol: 交易标的

        Returns:
            公司信息字典
        """
        if not self.is_connected:
            if not self.connect():
                return {}

        try:
            ticker = self._get_ticker(symbol)
            info = ticker.info

            return {
                "symbol": symbol,
                "name": info.get("longName", ""),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "market_cap": info.get("marketCap", 0),
                "description": info.get("longBusinessSummary", ""),
                "website": info.get("website", ""),
                "headquarters": info.get("city", "") + ", " + info.get("country", ""),
            }
        except Exception as e:
            logger.error(f"Error getting company info for {symbol}: {e}")
            return {}
