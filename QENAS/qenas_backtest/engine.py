"""回测引擎."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict
from dataclasses import dataclass
import logging

from qenas_core.strategies.base import StrategyBase, StrategyContext, Kline, Order
from qenas_backtest.metrics import BacktestMetrics

logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    回测引擎.

    模拟策略在历史数据上的执行.
    """

    def __init__(
        self,
        strategy: StrategyBase,
        initial_capital: Decimal = Decimal("100000"),
    ):
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.context = StrategyContext(
            strategy_id=strategy.strategy_id,
            initial_capital=initial_capital,
        )

        # 回测状态
        self.current_time: Optional[datetime] = None
        self.trades: List[Dict] = []
        self.equity_curve: List[Decimal] = []
        self.kline_history: List[Kline] = []

        # 配置
        self.commission_rate: Decimal = Decimal("0.001")  # 0.1% 佣金
        self.slippage_rate: Decimal = Decimal("0.001")    # 0.1% 滑点

    def set_commission(self, rate: Decimal) -> "BacktestEngine":
        """设置佣金率."""
        self.commission_rate = rate
        return self

    def set_slippage(self, rate: Decimal) -> "BacktestEngine":
        """设置滑点率."""
        self.slippage_rate = rate
        return self

    def run(self, klines: List[Kline]) -> "BacktestResult":
        """
        运行回测.

        Args:
            klines: K 线数据列表（按时间排序）

        Returns:
            回测结果
        """
        if not klines:
            raise ValueError("Klines cannot be empty")

        logger.info(f"开始回测：{len(klines)} 根 K 线")
        logger.info(f"数据范围：{klines[0].timestamp} 到 {klines[-1].timestamp}")

        # 初始化策略
        self.strategy.initialize(self.context)
        self.strategy.on_start(self.context)

        # 处理每根 K 线
        for kline in klines:
            self.current_time = kline.timestamp
            self.kline_history.append(kline)
            self._process_bar(kline)

        # 关闭所有持仓
        self._close_all_positions()

        # 计算指标
        metrics = self._calculate_metrics()

        logger.info(f"回测完成。总收益率：{metrics.total_return:.2%}")

        return BacktestResult(
            strategy_name=self.strategy.name,
            initial_capital=self.initial_capital,
            final_capital=self._calculate_total_equity(),
            total_return=metrics.total_return,
            sharpe_ratio=metrics.sharpe_ratio,
            max_drawdown=metrics.max_drawdown,
            win_rate=metrics.win_rate,
            total_trades=len(self.trades),
            trades=self.trades.copy(),
            equity_curve=self.equity_curve.copy(),
        )

    def _process_bar(self, kline: Kline) -> None:
        """处理单根 K 线."""
        # 更新持仓盈亏
        self._update_positions(kline)

        # 调用策略 on_bar
        self.strategy.on_bar(self.context, kline)

        # 执行订单
        self._execute_orders(kline)

        # 记录权益
        self._record_equity()

    def _update_positions(self, kline: Kline) -> None:
        """更新持仓盈亏."""
        for position in self.context.positions.values():
            if position.is_open:
                position.update_unrealized_pnl(kline.close)

    def _execute_orders(self, kline: Kline) -> None:
        """执行订单."""
        pending_orders = list(self.context.pending_orders.values())

        for order in pending_orders:
            if order.status != "pending":
                continue

            # 模拟订单成交
            fill_price = self._get_fill_price(order, kline)
            if fill_price:
                self._execute_order(order, Decimal(str(fill_price)))

    def _get_fill_price(self, order: Order, kline: Kline) -> Optional[float]:
        """获取模拟成交价格."""
        if order.order_type == "market":
            # 市价单：以下一根 K 线的开盘价成交，加上滑点
            if order.side == "buy":
                return float(kline.open) * (1 + float(self.slippage_rate))
            else:
                return float(kline.open) * (1 - float(self.slippage_rate))

        elif order.order_type == "limit":
            # 限价单：检查是否触发限价
            if order.limit_price is None:
                return None

            limit = float(order.limit_price)
            if order.side == "buy" and float(kline.low) <= limit:
                return limit
            elif order.side == "sell" and float(kline.high) >= limit:
                return limit

        return None

    def _execute_order(self, order: Order, fill_price: Decimal) -> None:
        """执行订单."""
        # 计算佣金
        notional = order.quantity * fill_price
        commission = notional * self.commission_rate

        # 更新持仓
        position = self.context.get_or_create_position(order.symbol)

        if order.side == "buy":
            position.add_to_position(order.quantity, fill_price)
            self.context.cash_available -= notional + commission
        else:
            realized_pnl = position.reduce_position(order.quantity, fill_price)
            self.context.cash_available += notional - commission

            # 记录交易
            self.trades.append({
                "time": self.current_time,
                "symbol": order.symbol,
                "side": order.side,
                "quantity": float(order.quantity),
                "price": float(fill_price),
                "commission": float(commission),
                "realized_pnl": float(realized_pnl),
            })

        # 更新订单状态
        order.fill(fill_price, order.quantity)

        # 从待处理列表中移除
        if order.symbol in self.context.pending_orders:
            del self.context.pending_orders[order.symbol]

    def _close_all_positions(self) -> None:
        """关闭所有持仓."""
        for symbol, position in list(self.context.positions.items()):
            if position.is_open and self.kline_history:
                final_kline = self.kline_history[-1]
                fill_price = final_kline.close
                notional = position.quantity * fill_price
                commission = notional * self.commission_rate

                if position.quantity > 0:
                    self.context.cash_available += notional - commission
                else:
                    self.context.cash_available -= notional + commission

                # 记录平仓交易
                self.trades.append({
                    "time": self.current_time,
                    "symbol": symbol,
                    "side": "close",
                    "quantity": float(abs(position.quantity)),
                    "price": float(fill_price),
                    "commission": float(commission),
                    "realized_pnl": float(position.realized_pnl),
                })

                position.quantity = Decimal("0")
                position.closed_at = self.current_time

    def _record_equity(self) -> None:
        """记录当前权益."""
        total_equity = self._calculate_total_equity()
        self.equity_curve.append(total_equity)

    def _calculate_total_equity(self) -> Decimal:
        """计算总权益."""
        equity = self.context.cash_available
        for position in self.context.positions.values():
            if position.is_open:
                equity += position.quantity * position.average_cost + position.unrealized_pnl
        return equity

    def _calculate_metrics(self) -> BacktestMetrics:
        """计算回测指标."""
        return BacktestMetrics(
            total_return=(self._calculate_total_equity() - self.initial_capital) / self.initial_capital,
            sharpe_ratio=self._calculate_sharpe(),
            max_drawdown=self._calculate_max_drawdown(),
            win_rate=self._calculate_win_rate(),
        )

    def _calculate_sharpe(self) -> Decimal:
        """计算夏普比率."""
        if len(self.equity_curve) < 2:
            return Decimal("0")

        import statistics

        # 计算收益率序列
        returns = []
        for i in range(1, len(self.equity_curve)):
            ret = (self.equity_curve[i] - self.equity_curve[i-1]) / self.equity_curve[i-1]
            returns.append(float(ret))

        if not returns:
            return Decimal("0")

        mean_return = statistics.mean(returns)
        std_return = statistics.stdev(returns) if len(returns) > 1 else 1

        if std_return == 0:
            return Decimal("0")

        # 年化（假设日级数据）
        annual_sharpe = (mean_return * 252) / (std_return * (252 ** 0.5))
        return Decimal(str(annual_sharpe))

    def _calculate_max_drawdown(self) -> Decimal:
        """计算最大回撤."""
        if not self.equity_curve:
            return Decimal("0")

        peak = self.equity_curve[0]
        max_dd = Decimal("0")

        for equity in self.equity_curve:
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak
            if dd > max_dd:
                max_dd = dd

        return max_dd

    def _calculate_win_rate(self) -> Decimal:
        """计算胜率."""
        if not self.trades:
            return Decimal("0")

        wins = sum(1 for t in self.trades if t.get("realized_pnl", 0) > 0)
        return Decimal(str(wins)) / Decimal(str(len(self.trades)))


@dataclass
class BacktestResult:
    """回测结果."""
    strategy_name: str
    initial_capital: Decimal
    final_capital: Decimal
    total_return: Decimal
    sharpe_ratio: Decimal
    max_drawdown: Decimal
    win_rate: Decimal
    total_trades: int
    trades: List[Dict]
    equity_curve: List[Decimal]

    def __repr__(self) -> str:
        return (f"BacktestResult(strategy={self.strategy_name}, "
                f"return={self.total_return:.2%}, sharpe={self.sharpe_ratio:.2f})")
