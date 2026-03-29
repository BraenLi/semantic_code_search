#!/usr/bin/env python3
"""
QENAS 策略示例脚本.

演示如何使用 QENAS 策略进行回测.
"""

from datetime import datetime
from decimal import Decimal
import numpy as np

from qenas_core.strategies.qenas_strategy import QENASStrategy
from qenas_core.strategies.base import StrategyContext, Kline
from qenas_backtest.engine import BacktestEngine


def generate_sample_data(
    symbol: str = "AAPL",
    n_bars: int = 200,
    start_price: float = 150.0,
) -> list[Kline]:
    """
    生成模拟 K 线数据.

    Args:
        symbol: 交易标的
        n_bars: K 线数量
        start_price: 起始价格

    Returns:
        K 线数据列表
    """
    np.random.seed(42)

    # 生成随机收益率
    returns = np.random.randn(n_bars) * 0.02  # 2% 日波动率

    # 计算价格序列
    prices = [start_price]
    for ret in returns[1:]:
        prices.append(prices[-1] * (1 + ret))

    # 生成 K 线数据
    klines = []
    base_date = datetime(2024, 1, 1)

    for i, price in enumerate(prices):
        open_price = price
        close_price = price * (1 + returns[i])
        high_price = max(open_price, close_price) * (1 + abs(np.random.randn() * 0.01))
        low_price = min(open_price, close_price) * (1 - abs(np.random.randn() * 0.01))
        volume = Decimal(str(np.random.uniform(1000000, 10000000)))

        kline = Kline(
            symbol=symbol,
            open=Decimal(str(open_price)),
            high=Decimal(str(high_price)),
            low=Decimal(str(low_price)),
            close=Decimal(str(close_price)),
            volume=volume,
            interval="1d",
            timestamp=base_date + __import__("datetime").timedelta(days=i),
        )
        klines.append(kline)

    return klines


def main():
    """主函数."""
    print("=" * 60)
    print("QENAS 策略回测示例")
    print("=" * 60)

    # 生成模拟数据
    print("\n生成模拟 K 线数据...")
    klines = generate_sample_data(symbol="AAPL", n_bars=100)
    print(f"生成 {len(klines)} 根 K 线")
    print(f"数据范围：{klines[0].timestamp.date()} 到 {klines[-1].timestamp.date()}")

    # 创建策略
    print("\n创建 QENAS 策略...")
    strategy = QENASStrategy(
        strategy_id="qenas_demo",
        name="QENAS 演示策略",
        n_species=20,  # 使用较少的策略物种以加快演示速度
        evolution_interval=10,  # 每 10 步进化一次
    )

    # 创建回测引擎
    print("\n初始化回测引擎...")
    engine = BacktestEngine(
        strategy=strategy,
        initial_capital=Decimal("100000"),
    )
    engine.set_commission(Decimal("0.001"))  # 0.1% 佣金
    engine.set_slippage(Decimal("0.001"))    # 0.1% 滑点

    # 运行回测
    print("\n运行回测...")
    print("-" * 40)

    result = engine.run(klines)

    # 输出结果
    print("-" * 40)
    print("\n回测结果:")
    print(f"  策略名称：{result.strategy_name}")
    print(f"  初始资金：{result.initial_capital:,.2f}")
    print(f"  最终资金：{result.final_capital:,.2f}")
    print(f"  总收益率：{result.total_return:.2%}")
    print(f"  夏普比率：{result.sharpe_ratio:.2f}")
    print(f"  最大回撤：{result.max_drawdown:.2%}")
    print(f"  胜率：{result.win_rate:.2%}")
    print(f"  交易次数：{result.total_trades}")

    # 获取策略状态
    status = strategy.get_status()
    print(f"\n策略状态:")
    print(f"  执行步数：{status['step_count']}")
    if status['entanglement_entropy']:
        print(f"  纠缠熵：{status['entanglement_entropy']:.4f}")

    print("\n" + "=" * 60)
    print("回测完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
