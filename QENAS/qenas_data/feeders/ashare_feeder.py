"""
A 股数据源.

用于获取中国大陆 A 股数据.
依赖：akshare, baostock
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
import logging

from qenas_data.feeders.base import (
    BaseDataFeeder,
    KlineData,
    EventData,
    EventType,
    EventImpact,
)

logger = logging.getLogger(__name__)


class AShareFeeder(BaseDataFeeder):
    """
    A 股数据源.

    支持:
    - 沪深 A 股数据 (000001.SZ, 600000.SH, etc.)
    - ETF 数据
    - 股指期货数据

    事件数据源:
    - 财报发布
    - 分红送配
    - 重大事项
    - 宏观经济数据
    """

    def __init__(self, source: str = "akshare"):
        """
        初始化.

        Args:
            source: 数据源选择 ("akshare" 或 "baostock")
        """
        super().__init__(market="A-Share", name=f"ashare_{source}")
        self.source = source
        self._cache: Dict[str, Any] = {}

    def connect(self) -> bool:
        """连接到数据源."""
        try:
            if self.source == "akshare":
                import akshare as ak
                logger.info("Connected to akshare")
            elif self.source == "baostock":
                import baostock as bs
                lg = bs.login()
                logger.info(f"Connected to baostock: {lg}")
            else:
                logger.warning(f"Unknown source: {self.source}")
                return False

            self.is_connected = True
            return True
        except ImportError as e:
            logger.warning(f"Required package not installed: {e}")
            self.is_connected = False
            return False

    def disconnect(self) -> None:
        """断开连接."""
        if self.source == "baostock":
            try:
                import baostock as bs
                bs.logout()
            except Exception:
                pass
        self.is_connected = False
        logger.info("Disconnected from AShare data source")

    def _format_symbol(self, symbol: str) -> str:
        """
        格式化股票代码.

        Args:
            symbol: 原始股票代码

        Returns:
            格式化后的代码
        """
        # 如果已经有后缀，直接返回
        if symbol.endswith(".SZ") or symbol.endswith(".SH"):
            return symbol.lower()

        # 根据代码前缀添加后缀
        if symbol.startswith("00") or symbol.startswith("20") or symbol.startswith("30"):
            return f"{symbol}.sz"
        elif symbol.startswith("60") or symbol.startswith("68"):
            return f"{symbol}.sh"
        elif symbol.startswith("8") or symbol.startswith("4"):
            return f"{symbol}.bj"  # 北交所
        else:
            return symbol.lower()

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
            symbol: 交易标的 (e.g., "000001.SZ", "600000.SH")
            interval: K 线周期 (1d, 1wk, 1mo)
            start_date: 开始日期
            end_date: 结束日期
            limit: 最大返回数量

        Returns:
            K 线数据列表
        """
        if not self.is_connected:
            if not self.connect():
                return []

        if self.source == "akshare":
            return self._fetch_klines_akshare(symbol, interval, start_date, end_date, limit)
        else:
            return self._fetch_klines_baostock(symbol, interval, start_date, end_date, limit)

    def _fetch_klines_akshare(
        self,
        symbol: str,
        interval: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        limit: int,
    ) -> List[KlineData]:
        """使用 akshare 获取 K 线数据."""
        try:
            import akshare as ak

            # 格式化股票代码
            symbol_formatted = self._format_symbol(symbol)

            # 默认时间范围
            if end_date is None:
                end_date = datetime.now()
            if start_date is None:
                start_date = end_date - timedelta(days=365)

            # 获取历史数据
            df = ak.stock_zh_a_hist(
                symbol=symbol_formatted.replace(".", ""),
                period="daily",
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
                adjust="qfq" if interval == "1d" else "",  # 前复权
            )

            if df.empty:
                logger.warning(f"No data found for {symbol}")
                return []

            # 转换为 KlineData 列表
            klines = []
            for _, row in df.iterrows():
                timestamp = datetime.strptime(str(row["日期"]), "%Y-%m-%d")

                kline = KlineData(
                    symbol=symbol,
                    open=Decimal(str(row.get("开盘", 0))),
                    high=Decimal(str(row.get("最高", 0))),
                    low=Decimal(str(row.get("最低", 0))),
                    close=Decimal(str(row.get("收盘", 0))),
                    volume=Decimal(str(row.get("成交量", 0))),
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
            logger.error(f"Error fetching klines for {symbol} from akshare: {e}")
            return []

    def _fetch_klines_baostock(
        self,
        symbol: str,
        interval: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        limit: int,
    ) -> List[KlineData]:
        """使用 baostock 获取 K 线数据."""
        try:
            import baostock as bs

            # 格式化股票代码
            symbol_formatted = self._format_symbol(symbol)

            # 默认时间范围
            if end_date is None:
                end_date = datetime.now()
            if start_date is None:
                start_date = end_date - timedelta(days=365)

            # 查询字段
            fields = "date,time,open,high,low,close,volume"

            # 获取历史数据
            rs = bs.query_history_k_data_plus(
                symbol_formatted,
                fields,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                frequency="d" if interval == "1d" else "w",
                adjustflag="3",  # 不复权
            )

            data_list = []
            while (rs.error_code == "0") and rs.next():
                data_list.append(rs.get_row_data())

            if not data_list:
                logger.warning(f"No data found for {symbol}")
                return []

            # 转换为 KlineData 列表
            klines = []
            for row in data_list:
                date_str = row[0]
                time_str = row[1] if len(row) > 1 else "00:00:00"
                timestamp = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")

                kline = KlineData(
                    symbol=symbol,
                    open=Decimal(row[2] if row[2] else "0"),
                    high=Decimal(row[3] if row[3] else "0"),
                    low=Decimal(row[4] if row[4] else "0"),
                    close=Decimal(row[5] if row[5] else "0"),
                    volume=Decimal(row[6] if row[6] else "0"),
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
            logger.error(f"Error fetching klines for {symbol} from baostock: {e}")
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
            start_date=datetime.now() - timedelta(days=30),
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
        获取 A 股事件数据.

        事件类型:
        - 财报发布
        - 分红送配
        - 重大事项
        - 宏观经济数据

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

        events = []
        event_id_counter = 0

        # 获取财报事件
        if symbols and (event_types is None or EventType.EARNINGS in event_types):
            earnings_events = self._fetch_earnings_events(symbols, start_date, end_date)
            events.extend(earnings_events)

        # 获取分红事件
        if symbols and (event_types is None or EventType.DIVIDEND in event_types):
            dividend_events = self._fetch_dividend_events(symbols, start_date, end_date)
            events.extend(dividend_events)

        # 获取宏观经济事件
        if event_types is None or EventType.MACRO_ECONOMIC in event_types:
            macro_events = self._fetch_macro_events(start_date, end_date)
            events.extend(macro_events)

        # 过滤影响级别
        events = [e for e in events if e.impact_level.value >= min_impact.value]

        logger.info(f"Fetched {len(events)} A-share events")
        return events

    def _fetch_earnings_events(
        self,
        symbols: List[str],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ) -> List[EventData]:
        """获取财报发布事件."""
        events = []

        try:
            import akshare as ak

            # 获取 A 股财报日程
            df = ak.stock_report_disclosure()

            if df.empty:
                return events

            for _, row in df.iterrows():
                # 检查是否在关注的股票列表中
                stock_code = str(row.get("股票代码", ""))
                if symbols and stock_code not in [s[:6] for s in symbols]:
                    continue

                # 解析日期
                report_date = row.get("预约披露日期")
                if report_date:
                    try:
                        event_date = datetime.strptime(str(report_date), "%Y-%m-%d")

                        # 检查日期范围
                        if start_date and event_date < start_date:
                            continue
                        if end_date and event_date > end_date:
                            continue

                        # 格式化股票代码
                        symbol = self._format_symbol(stock_code)

                        events.append(EventData(
                            event_id=f"ashare_earnings_{len(events)}",
                            event_type=EventType.EARNINGS,
                            title=f"{symbol} 财报披露",
                            description=f"预约披露日期：{report_date}",
                            timestamp=event_date,
                            source="akshare",
                            affected_symbols=[symbol],
                            impact_level=EventImpact.MEDIUM,
                            sentiment_score=0.0,
                        ))
                    except Exception:
                        continue

        except Exception as e:
            logger.error(f"Error fetching earnings events: {e}")

        return events

    def _fetch_dividend_events(
        self,
        symbols: List[str],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ) -> List[EventData]:
        """获取分红事件."""
        events = []

        try:
            import akshare as ak

            for symbol in symbols:
                symbol_code = symbol[:6]

                # 获取分红送股数据
                df = ak.stock_dividend(symbol=symbol_code)

                if df.empty:
                    continue

                for _, row in df.iterrows():
                    # 解析派息日
                    dividend_date = row.get("派息日")
                    if dividend_date:
                        try:
                            event_date = datetime.strptime(str(dividend_date), "%Y-%m-%d")

                            # 检查日期范围
                            if start_date and event_date < start_date:
                                continue
                            if end_date and event_date > end_date:
                                continue

                            events.append(EventData(
                                event_id=f"ashare_dividend_{len(events)}",
                                event_type=EventType.DIVIDEND,
                                title=f"{symbol} 分红派息",
                                description=f"每 10 股派息：{row.get('每 10 股派息', 'N/A')}元",
                                timestamp=event_date,
                                source="akshare",
                                affected_symbols=[symbol],
                                impact_level=EventImpact.LOW,
                                sentiment_score=0.1,
                            ))
                        except Exception:
                            continue

        except Exception as e:
            logger.error(f"Error fetching dividend events: {e}")

        return events

    def _fetch_macro_events(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ) -> List[EventData]:
        """获取宏观经济事件."""
        events = []

        try:
            import akshare as ak

            # 默认时间范围
            if start_date is None:
                start_date = datetime.now() - timedelta(days=90)
            if end_date is None:
                end_date = datetime.now()

            # 获取宏观经济数据
            macro_df = ak.macro_china_gdp_year()  # GDP 数据

            if not macro_df.empty:
                events.append(EventData(
                    event_id="macro_gdp_latest",
                    event_type=EventType.MACRO_ECONOMIC,
                    title="中国 GDP 数据发布",
                    description=f"最新 GDP 数据：{macro_df.iloc[-1].to_dict()}",
                    timestamp=end_date,
                    source="akshare",
                    affected_regions=["CN"],
                    affected_sectors=["all"],
                    impact_level=EventImpact.HIGH,
                    sentiment_score=0.0,
                ))

        except Exception as e:
            logger.error(f"Error fetching macro events: {e}")

        return events

    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取股票基本信息.

        Args:
            symbol: 股票代码

        Returns:
            股票信息字典
        """
        try:
            import akshare as ak

            symbol_code = symbol[:6]

            # 获取个股信息
            df = ak.stock_individual_info_em(symbol=symbol_code)

            if df.empty:
                return None

            info = {}
            for _, row in df.iterrows():
                info[row["item"]] = row["value"]

            return {
                "symbol": symbol,
                "name": info.get("股票简称", ""),
                "code": symbol_code,
                "list_date": info.get("上市日期", ""),
                "sector": info.get("行业", ""),
            }

        except Exception as e:
            logger.error(f"Error getting stock info for {symbol}: {e}")
            return None
