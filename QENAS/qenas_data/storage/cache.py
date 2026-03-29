"""数据缓存模块."""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, field
import logging

from qenas_data.feeders.base import KlineData

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """缓存条目."""
    data: List[KlineData]
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    def is_expired(self) -> bool:
        """检查是否过期."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at


class DataCache:
    """
    数据缓存管理器.

    用于缓存 K 线数据，避免重复请求数据源.
    """

    def __init__(
        self,
        ttl_seconds: int = 3600,  # 默认 1 小时过期
        max_size: int = 1000,
    ):
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self._cache: Dict[str, CacheEntry] = {}

    def _make_key(
        self,
        symbol: str,
        interval: str,
        start_date: datetime,
        end_date: datetime,
    ) -> str:
        """生成缓存键."""
        return f"{symbol}:{interval}:{start_date.isoformat()}:{end_date.isoformat()}"

    def get(
        self,
        symbol: str,
        interval: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Optional[List[KlineData]]:
        """
        从缓存获取数据.

        Args:
            symbol: 交易标的
            interval: K 线周期
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            K 线数据列表，如果不存在或已过期则返回 None
        """
        key = self._make_key(symbol, interval, start_date, end_date)

        if key not in self._cache:
            return None

        entry = self._cache[key]
        if entry.is_expired():
            del self._cache[key]
            return None

        logger.debug(f"Cache hit: {key}")
        return entry.data

    def put(
        self,
        symbol: str,
        interval: str,
        start_date: datetime,
        end_date: datetime,
        data: List[KlineData],
    ) -> None:
        """
        将数据存入缓存.

        Args:
            symbol: 交易标的
            interval: K 线周期
            start_date: 开始日期
            end_date: 结束日期
            data: K 线数据
        """
        key = self._make_key(symbol, interval, start_date, end_date)

        # 检查缓存大小
        if len(self._cache) >= self.max_size:
            self._evict_oldest()

        self._cache[key] = CacheEntry(
            data=data,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(seconds=self.ttl_seconds),
        )

        logger.debug(f"Cache put: {key}, {len(data)} bars")

    def _evict_oldest(self) -> None:
        """移除最旧的缓存条目."""
        if not self._cache:
            return

        # 找到最旧的条目
        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].created_at
        )
        del self._cache[oldest_key]

    def clear(self) -> None:
        """清空所有缓存."""
        self._cache.clear()
        logger.info("Cache cleared")

    def invalidate(
        self,
        symbol: str,
        interval: str,
    ) -> None:
        """
        使特定 symbol 和 interval 的缓存失效.

        Args:
            symbol: 交易标的
            interval: K 线周期
        """
        keys_to_delete = [
            k for k in self._cache.keys()
            if k.startswith(f"{symbol}:{interval}:")
        ]

        for key in keys_to_delete:
            del self._cache[key]

        logger.info(f"Invalidated {len(keys_to_delete)} cache entries for {symbol}:{interval}")

    def get_stats(self) -> dict:
        """获取缓存统计信息."""
        now = datetime.utcnow()
        expired_count = sum(
            1 for entry in self._cache.values()
            if entry.is_expired()
        )

        return {
            "total_entries": len(self._cache),
            "max_size": self.max_size,
            "expired_entries": expired_count,
            "ttl_seconds": self.ttl_seconds,
        }
