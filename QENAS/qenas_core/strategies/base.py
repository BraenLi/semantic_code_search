"""策略基类和上下文管理."""

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Optional, Any


class OrderSide:
    """订单方向."""
    BUY = "buy"
    SELL = "sell"


class OrderType:
    """订单类型."""
    MARKET = "market"
    LIMIT = "limit"


class Order:
    """订单数据类."""

    def __init__(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        order_type: str = OrderType.MARKET,
        limit_price: Optional[Decimal] = None,
        strategy_id: Optional[str] = None,
    ):
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.order_type = order_type
        self.limit_price = limit_price
        self.strategy_id = strategy_id
        self.timestamp = datetime.utcnow()
        self.filled_quantity = Decimal("0")
        self.average_price = Decimal("0")
        self.status = "pending"

    def fill(self, price: Decimal, quantity: Decimal) -> None:
        """更新订单成交信息."""
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        total_cost = self.average_price * self.filled_quantity + price * quantity
        self.filled_quantity += quantity
        self.average_price = total_cost / self.filled_quantity if self.filled_quantity > 0 else Decimal("0")

        if self.filled_quantity >= self.quantity:
            self.status = "filled"
        else:
            self.status = "partial"


class Position:
    """持仓数据类."""

    def __init__(self, symbol: str, strategy_id: Optional[str] = None):
        self.symbol = symbol
        self.strategy_id = strategy_id
        self.quantity = Decimal("0")
        self.average_cost = Decimal("0")
        self.unrealized_pnl = Decimal("0")
        self.realized_pnl = Decimal("0")
        self.created_at = datetime.utcnow()
        self.closed_at: Optional[datetime] = None

    @property
    def is_open(self) -> bool:
        """检查持仓是否打开."""
        return self.quantity != Decimal("0")

    def update_unrealized_pnl(self, current_price: Decimal) -> None:
        """更新未实现盈亏."""
        if self.is_open:
            self.unrealized_pnl = (current_price - self.average_cost) * self.quantity

    def add_to_position(self, quantity: Decimal, price: Decimal) -> None:
        """增加持仓."""
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        total_cost = self.average_cost * self.quantity + price * quantity
        self.quantity += quantity
        self.average_cost = total_cost / self.quantity if self.quantity > 0 else Decimal("0")

    def reduce_position(self, quantity: Decimal, price: Decimal) -> Decimal:
        """减少持仓，返回已实现盈亏."""
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        if quantity > self.quantity:
            raise ValueError(f"Quantity {quantity} exceeds position {self.quantity}")

        realized = (price - self.average_cost) * quantity
        self.realized_pnl += realized
        self.quantity -= quantity

        if self.quantity == Decimal("0"):
            self.closed_at = datetime.utcnow()
            self.average_cost = Decimal("0")

        return realized


class Kline:
    """K 线数据类."""

    def __init__(
        self,
        symbol: str,
        open: Decimal,
        high: Decimal,
        low: Decimal,
        close: Decimal,
        volume: Decimal,
        interval: str,
        timestamp: datetime,
    ):
        self.symbol = symbol
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.interval = interval
        self.timestamp = timestamp

        # 事件标记（该 K 线周期内发生的事件）
        self.events: list = []

        # 验证 OHLC 数据
        if high < low:
            raise ValueError(f"High ({high}) must be >= low ({low})")
        if high < open or high < close:
            raise ValueError(f"High ({high}) must be >= open ({open}) and close ({close})")
        if low > open or low > close:
            raise ValueError(f"Low ({low}) must be <= open ({open}) and close ({close})")

    def __repr__(self) -> str:
        return f"Kline(symbol={self.symbol}, interval={self.interval}, timestamp={self.timestamp}, close={self.close})"


class Tick:
    """Tick 数据类."""

    def __init__(
        self,
        symbol: str,
        price: Decimal,
        quantity: Decimal,
        timestamp: Optional[datetime] = None,
    ):
        self.symbol = symbol
        self.price = price
        self.quantity = quantity
        self.timestamp = timestamp or datetime.utcnow()

    def __repr__(self) -> str:
        return f"Tick(symbol={self.symbol}, price={self.price}, timestamp={self.timestamp})"


class StrategyContext:
    """
    策略执行上下文.

    提供对以下内容的访问:
    - 当前持仓
    - 账户状态
    - 订单管理
    - 市场数据
    """

    def __init__(self, strategy_id: str, initial_capital: Decimal = Decimal("100000")):
        self.strategy_id = strategy_id
        self.initial_capital = initial_capital
        self.cash_available = initial_capital
        self.positions: dict[str, Position] = {}
        self.pending_orders: dict[str, Order] = {}
        self.is_trading = False
        self.strategy_config: dict[str, Any] = {}

    def get_position(self, symbol: str) -> Optional[Position]:
        """获取持仓."""
        return self.positions.get(symbol)

    def get_or_create_position(self, symbol: str) -> Position:
        """获取或创建持仓."""
        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol, self.strategy_id)
        return self.positions[symbol]

    def update_position(self, position: Position) -> None:
        """更新持仓."""
        self.positions[position.symbol] = position

    def submit_order(self, order: Order) -> None:
        """提交订单."""
        if order.strategy_id is None:
            order.strategy_id = self.strategy_id
        self.pending_orders[order.symbol] = order

    def cancel_order(self, order_id: str) -> Optional[Order]:
        """取消订单."""
        order = self.pending_orders.get(order_id)
        if order:
            order.status = "cancelled"
        return order

    def get_open_orders(self, symbol: Optional[str] = None) -> list[Order]:
        """获取未成交订单."""
        orders = [o for o in self.pending_orders.values() if o.status == "pending"]
        if symbol:
            orders = [o for o in orders if o.symbol == symbol]
        return orders

    def buy(self, symbol: str, quantity: Decimal, price: Optional[Decimal] = None,
            order_type: str = OrderType.MARKET) -> Order:
        """创建买入订单."""
        order = Order(
            symbol=symbol,
            side=OrderSide.BUY,
            quantity=quantity,
            order_type=order_type,
            limit_price=price if order_type == OrderType.LIMIT else None,
            strategy_id=self.strategy_id,
        )
        self.submit_order(order)
        return order

    def sell(self, symbol: str, quantity: Decimal, price: Optional[Decimal] = None,
             order_type: str = OrderType.MARKET) -> Order:
        """创建卖出订单."""
        order = Order(
            symbol=symbol,
            side=OrderSide.SELL,
            quantity=quantity,
            order_type=order_type,
            limit_price=price if order_type == OrderType.LIMIT else None,
            strategy_id=self.strategy_id,
        )
        self.submit_order(order)
        return order

    def close_position(self, symbol: str) -> Optional[Order]:
        """平仓."""
        position = self.get_position(symbol)
        if position and position.is_open:
            quantity = abs(position.quantity)
            side = OrderSide.SELL if position.quantity > 0 else OrderSide.BUY
            order = Order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                strategy_id=self.strategy_id,
            )
            self.submit_order(order)
            return order
        return None

    def total_equity(self, prices: dict[str, Decimal]) -> Decimal:
        """计算总权益."""
        equity = self.cash_available
        for symbol, position in self.positions.items():
            if position.is_open and symbol in prices:
                equity += position.quantity * prices[symbol]
        return equity


class StrategyBase(ABC):
    """
    策略基类.

    子类必须实现:
    - on_init: 初始化策略参数
    - on_bar: 处理 K 线事件
    - on_tick: 处理 Tick 事件 (可选)
    """

    def __init__(self, strategy_id: str = "strategy", name: str = "Base Strategy"):
        self.strategy_id = strategy_id
        self.name = name
        self.is_initialized = False

    @abstractmethod
    def on_init(self, context: StrategyContext) -> None:
        """
        初始化策略参数.

        在策略启动时调用一次.
        """
        pass

    @abstractmethod
    def on_bar(self, context: StrategyContext, kline: Kline) -> None:
        """
        处理 K 线事件.

        在收到新的 K 线数据时调用.
        """
        pass

    def on_tick(self, context: StrategyContext, tick: Tick) -> None:
        """
        处理 Tick 事件.

        在收到新的 Tick 数据时调用 (可选).
        """
        pass

    def on_start(self, context: StrategyContext) -> None:
        """策略启动时调用."""
        pass

    def on_stop(self, context: StrategyContext) -> None:
        """策略停止时调用."""
        pass

    def initialize(self, context: StrategyContext) -> None:
        """初始化策略."""
        self.on_init(context)
        self.is_initialized = True
