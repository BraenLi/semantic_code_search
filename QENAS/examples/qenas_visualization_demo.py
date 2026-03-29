#!/usr/bin/env python3
"""
QENAS 策略可视化示例脚本.

演示如何将回测结果与可视化模块集成，包括：
- 纠缠矩阵热力图
- 事件时间线可视化
- 业绩可视化（权益曲线、回撤、收益分布）
- 统一仪表板状态输出
"""

from datetime import datetime, timedelta
from decimal import Decimal
import numpy as np

from qenas_core.strategies.qenas_strategy import QENASStrategy
from qenas_core.strategies.base import Kline
from qenas_data.feeders.base import EventData, EventType, EventImpact
from qenas_backtest.engine import BacktestEngine
from qenas_viz.dashboard import QENASDashboard
from qenas_viz.performance_viz import BacktestResult


def generate_multi_asset_klines(
    symbols: list[str],
    n_bars: int = 100,
    start_prices: dict[str, float] = None,
    correlation: float = 0.3,
) -> list[Kline]:
    """
    生成多资产模拟 K 线数据（考虑资产间相关性）.

    Args:
        symbols: 交易标的列表
        n_bars: K 线数量
        start_prices: 起始价格字典
        correlation: 资产间基础相关性

    Returns:
        K 线数据列表（按时间排序，每个时间点包含所有资产）
    """
    if start_prices is None:
        start_prices = {
            "AAPL": 150.0,
            "GOOGL": 140.0,
            "MSFT": 380.0,
        }

    np.random.seed(42)
    n_assets = len(symbols)

    # 生成相关收益率矩阵
    # 使用 Cholesky 分解生成相关随机数
    cov_matrix = np.full((n_assets, n_assets), correlation)
    np.fill_diagonal(cov_matrix, 1.0)

    try:
        L = np.linalg.cholesky(cov_matrix)
        uncorrelated = np.random.randn(n_bars, n_assets)
        returns = uncorrelated @ L.T * 0.02  # 2% 日波动率
    except np.linalg.LinAlgError:
        # 如果矩阵不正定，退化为独立随机
        returns = np.random.randn(n_bars, n_assets) * 0.02

    # 计算价格序列
    prices = {symbols[i]: [start_prices[symbols[i]]] for i in range(n_assets)}
    for t in range(1, n_bars):
        for i, symbol in enumerate(symbols):
            prices[symbol].append(prices[symbol][-1] * (1 + returns[t, i]))

    # 生成 K 线数据
    base_date = datetime(2024, 1, 1)
    all_klines = []

    for t in range(n_bars):
        date = base_date + timedelta(days=t)
        for i, symbol in enumerate(symbols):
            price = prices[symbol][t]
            ret = returns[t, i] if t > 0 else 0

            open_price = price
            close_price = price * (1 + ret)
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
                timestamp=date,
            )
            all_klines.append(kline)

    return all_klines


def generate_sample_events(
    symbols: list[str],
    n_events: int = 20,
    start_date: datetime = None,
) -> list[EventData]:
    """
    生成模拟事件数据.

    Args:
        symbols: 交易标的列表
        n_events: 事件数量
        start_date: 起始日期

    Returns:
        事件数据列表
    """
    if start_date is None:
        start_date = datetime(2024, 1, 1)

    np.random.seed(123)

    event_types = [
        EventType.EARNINGS,
        EventType.MACRO_ECONOMIC,
        EventType.REGULATORY,
        EventType.GEOPOLITICAL,
        EventType.DIVIDEND,
    ]

    impact_levels = [
        EventImpact.LOW,
        EventImpact.MEDIUM,
        EventImpact.HIGH,
        EventImpact.CRITICAL,
    ]

    events = []
    for i in range(n_events):
        event_type = np.random.choice(event_types)
        impact_level = np.random.choice(
            impact_levels,
            p=[0.3, 0.4, 0.2, 0.1]  # 权重分布
        )

        # 情感分数与事件类型和影响级别相关
        base_sentiment = np.random.randn() * 0.3
        if impact_level == EventImpact.CRITICAL:
            base_sentiment *= 2
        sentiment_score = np.clip(base_sentiment, -1, 1)

        affected_symbol = np.random.choice(symbols)

        event = EventData(
            event_id=f"event_{i:03d}",
            event_type=event_type,
            title=f"{event_type.value.replace('_', ' ').title()} - {affected_symbol}",
            description=f"模拟事件 {i}: {event_type.value} 影响 {affected_symbol}",
            timestamp=start_date + timedelta(days=np.random.randint(0, 90)),
            source="demo_generator",
            affected_symbols=[affected_symbol],
            impact_level=impact_level,
            sentiment_score=sentiment_score,
        )
        events.append(event)

    # 按时间排序
    events.sort(key=lambda e: e.timestamp)
    return events


def generate_backtest_result(
    timestamps: list[datetime],
    initial_capital: float = 100000,
    seed: int = 42,
) -> BacktestResult:
    """
    生成模拟回测结果.

    Args:
        timestamps: 时间戳列表
        initial_capital: 初始资金
        seed: 随机种子

    Returns:
        BacktestResult 数据类
    """
    np.random.seed(seed)

    n = len(timestamps)

    # 生成收益率序列（略有正向偏置）
    daily_returns = np.random.randn(n - 1) * 0.015 + 0.0005  # 年化约 12%

    # 计算权益曲线
    equity_curve = [initial_capital]
    for ret in daily_returns:
        equity_curve.append(equity_curve[-1] * (1 + ret))

    # 生成基准（市场指数，略低于策略）
    benchmark_returns = np.random.randn(n - 1) * 0.012 + 0.0003
    benchmark = [initial_capital]
    for ret in benchmark_returns:
        benchmark.append(benchmark[-1] * (1 + ret))

    # 计算回撤
    equity = np.array(equity_curve)
    running_max = np.maximum.accumulate(equity)
    drawdown = (equity - running_max) / running_max
    max_drawdown = abs(np.min(drawdown))

    # 计算夏普比率（年化）
    sharpe_ratio = np.mean(daily_returns) / np.std(daily_returns) * np.sqrt(252) if np.std(daily_returns) > 0 else 0

    # 总收益率和胜率
    total_return = (equity_curve[-1] - initial_capital) / initial_capital
    win_rate = np.sum(daily_returns > 0) / len(daily_returns)

    return BacktestResult(
        timestamps=timestamps,
        equity_curve=equity_curve,
        returns=list(daily_returns),
        benchmark=benchmark,
        max_drawdown=max_drawdown,
        sharpe_ratio=sharpe_ratio,
        total_return=total_return,
        win_rate=win_rate,
    )


def main():
    """主函数 - 演示完整的可视化流程."""
    print("=" * 60)
    print("QENAS 策略可视化示例")
    print("=" * 60)

    # ========== 步骤 1: 生成多资产数据 ==========
    print("\n[步骤 1] 生成多资产模拟 K 线数据...")
    symbols = ["AAPL", "GOOGL", "MSFT"]
    klines = generate_multi_asset_klines(symbols, n_bars=60)
    print(f"  资产：{symbols}")
    print(f"  时间跨度：{klines[0].timestamp.date()} 到 {klines[-1].timestamp.date()}")
    print(f"  总 K 线数：{len(klines)} ({len(klines) // len(symbols)} 天 x {len(symbols)} 资产)")

    # ========== 步骤 2: 生成事件数据 ==========
    print("\n[步骤 2] 生成模拟事件数据...")
    events = generate_sample_events(symbols, n_events=15)
    print(f"  事件总数：{len(events)}")

    # 事件类型统计
    from collections import Counter
    type_counts = Counter(e.event_type.value for e in events)
    for etype, count in type_counts.most_common(3):
        print(f"    - {etype}: {count}")

    # ========== 步骤 3: 运行策略回测 ==========
    print("\n[步骤 3] 运行 QENAS 策略回测...")
    strategy = QENASStrategy(
        strategy_id="qenas_viz_demo",
        name="QENAS 可视化演示",
        n_species=10,
        evolution_interval=20,
    )

    engine = BacktestEngine(
        strategy=strategy,
        initial_capital=Decimal("100000"),
    )
    engine.set_commission(Decimal("0.001"))
    engine.set_slippage(Decimal("0.001"))

    # 运行回测（只使用第一个资产的 K 线）
    aapl_klines = [k for k in klines if k.symbol == "AAPL"]
    result = engine.run(aapl_klines)

    print(f"  初始资金：{result.initial_capital:,.2f}")
    print(f"  最终资金：{result.final_capital:,.2f}")
    print(f"  总收益率：{result.total_return:.2%}")
    print(f"  夏普比率：{result.sharpe_ratio:.2f}")
    print(f"  最大回撤：{result.max_drawdown:.2%}")

    # ========== 步骤 4: 创建可视化仪表板 ==========
    print("\n[步骤 4] 创建可视化仪表板...")
    dashboard = QENASDashboard(symbols)

    # 获取策略的纠缠矩阵
    status = strategy.get_status()
    entanglement_matrix = status.get('entanglement_matrix')

    if entanglement_matrix is not None:
        # 计算纠缠熵
        eigenvalues = np.linalg.eigvalsh(entanglement_matrix)
        eigenvalues = eigenvalues[eigenvalues > 1e-10]
        entropy = -np.sum(eigenvalues * np.log2(eigenvalues + 1e-10))

        dashboard.update_entanglement(entanglement_matrix, entropy=entropy)
        print(f"  纠缠矩阵已记录 (熵：{entropy:.4f})")
    else:
        # 使用模拟纠缠矩阵
        n = len(symbols)
        mock_matrix = np.random.rand(n, n) * 0.3 + np.eye(n) * 0.4
        mock_matrix = (mock_matrix + mock_matrix.T) / 2
        dashboard.update_entanglement(mock_matrix, entropy=1.2)
        print("  使用模拟纠缠矩阵")

    # 添加事件数据
    dashboard.add_events(events)
    print(f"  事件数据已添加 ({len(events)} 条)")

    # 生成并设置回测结果
    timestamps = [klines[i * len(symbols)].timestamp for i in range(len(klines) // len(symbols))]
    viz_result = generate_backtest_result(timestamps, initial_capital=100000)
    dashboard.set_backtest_results(viz_result)
    print(f"  回测结果已设置 (总收益：{viz_result.total_return:.2%})")

    # ========== 步骤 5: 打印状态报告 ==========
    print("\n[步骤 5] 策略状态报告")
    print("-" * 60)
    dashboard.print_status()

    # ========== 步骤 6: 独立可视化演示 ==========
    print("\n[步骤 6] 独立可视化演示...")

    # 6.1 纠缠矩阵可视化
    print("\n  6.1 纠缠矩阵热力图（文本模式）:")
    print("-" * 40)
    viz = dashboard.entanglement_viz
    matrix = viz.get_latest_matrix()
    if matrix is not None:
        text_heatmap = viz._text_heatmap(matrix, "当前纠缠矩阵")
        print(text_heatmap)

    # 6.2 事件时间线
    print("\n  6.2 事件时间线（文本模式）:")
    print("-" * 40)
    event_viz = dashboard.event_viz
    text_timeline = event_viz._text_timeline(event_viz.events, "事件时间线")
    print(text_timeline)

    # 6.3 业绩摘要
    print("\n  6.3 业绩摘要（文本模式）:")
    print("-" * 40)
    perf_viz = dashboard.performance_viz
    if perf_viz.results:
        text_equity = perf_viz._text_equity_curve(perf_viz.results, "权益曲线摘要")
        print(text_equity)

    # ========== 步骤 7: 获取统计摘要 ==========
    print("\n[步骤 7] 统计摘要")
    print("-" * 60)

    event_summary = event_viz.get_event_summary()
    print(f"事件统计:")
    print(f"  总事件数：{event_summary.get('total_events', 0)}")
    print(f"  平均情感：{event_summary.get('avg_sentiment', 0):.3f}")
    print(f"  类型分布：{event_summary.get('type_distribution', {})}")

    print(f"\n纠缠统计:")
    print(f"  最新熵值：{viz.get_latest_entropy():.4f}")
    print(f"  矩阵历史：{len(viz.matrix_history)}")

    # ========== 完成 ==========
    print("\n" + "=" * 60)
    print("可视化演示完成!")
    print("=" * 60)
    print("\n提示:")
    print("  - 安装 matplotlib 可查看图形化输出：pip install matplotlib")
    print("  - 安装 networkx 可查看网络图：pip install networkx")
    print("  - 运行完整示例：python examples/qenas_visualization_demo.py")


if __name__ == "__main__":
    main()
