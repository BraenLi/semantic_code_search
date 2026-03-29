"""QENAS 主策略类 - 量子纠缠生态位自适应网络."""

import numpy as np
from numpy.typing import NDArray
from typing import Optional
from decimal import Decimal
import logging

from qenas_core.strategies.base import StrategyBase, StrategyContext, Kline, Order
from qenas_core.quantum.entanglement import QuantumEntanglementCalculator
from qenas_core.ecosystem.niche_manager import NicheManager, StrategySpecies, SignalNiche
from qenas_core.neuromorphic.snn import SpikingNeuralLayer, HippocampusMemory, BrainRegion
from qenas_core.emergent.decision import EmergentDecisionEngine, PercolationAnalyzer
from qenas_data.processors.event_processor import EventProcessor, EventSignal
from qenas_data.feeders.base import EventData, EventType

logger = logging.getLogger(__name__)


class QENASStrategy(StrategyBase):
    """
    QENAS: 量子纠缠生态位自适应网络策略.

    核心架构:
    1. 量子纠缠层 - 计算资产间的非线性关联
    2. 生态位子策略群 - 100+ 个策略物种共同进化
    3. 神经形态处理器 - 脉冲神经网络进行信号处理
    4. 涌现决策引擎 - 基于复杂网络同步产生集体决策
    """

    def __init__(
        self,
        strategy_id: str = "qenas",
        name: str = "量子纠缠生态位自适应网络",
        n_species: int = 100,
        sync_threshold: float = 0.75,
        evolution_interval: int = 20,  # 每 20 个时间步进化一次
    ):
        super().__init__(strategy_id, name)

        # 量子纠缠层
        self.entanglement_calculator = QuantumEntanglementCalculator()

        # 生态位子策略群
        self.niche_manager = NicheManager(n_species=n_species)

        # 神经形态处理器 - 四个脑区
        self.snn_layers = {
            BrainRegion.PREFRONTAL: SpikingNeuralLayer(64, BrainRegion.PREFRONTAL),
            BrainRegion.LIMBIC: SpikingNeuralLayer(32, BrainRegion.LIMBIC),
            BrainRegion.CEREBELLUM: SpikingNeuralLayer(128, BrainRegion.CEREBELLUM),
            BrainRegion.HIPPOCAMPUS: SpikingNeuralLayer(16, BrainRegion.HIPPOCAMPUS),
        }
        self.hippocampus = HippocampusMemory(capacity=500)

        # 涌现决策引擎
        self.decision_engine = EmergentDecisionEngine(
            n_strategies=n_species,
            sync_threshold=sync_threshold,
        )

        # 渗流风险分析
        self.percolation_analyzer = PercolationAnalyzer(n_species)

        # 事件处理器（新增）
        self.event_processor = EventProcessor()

        # 策略状态
        self.n_species = n_species
        self.evolution_interval = evolution_interval
        self._step_count = 0
        self._returns_window: list[NDArray[np.float64]] = []
        self._max_returns_window = 50  # 最多保留 50 个时间步的收益率

        # 资产映射
        self._symbol_to_index: dict[str, int] = {}
        self._next_asset_index = 0

    def on_init(self, context: StrategyContext) -> None:
        """初始化策略."""
        logger.info(f"初始化 QENAS 策略：{self.n_species} 个策略物种")

        # 初始化生态系统
        self.niche_manager.initialize_ecosystem(seed=42)

        # 初始化策略配置
        context.strategy_config = {
            "n_species": self.n_species,
            "sync_threshold": self.decision_engine.sync_threshold,
            "evolution_interval": self.evolution_interval,
        }

        logger.info("QENAS 策略初始化完成")

    def on_bar(self, context: StrategyContext, kline: Kline) -> None:
        """
        处理 K 线数据.

        主处理流程:
        1. 更新资产收益率窗口
        2. 计算量子纠缠状态
        3. 获取各子策略信号
        4. 处理事件信号（新增）
        5. 神经形态信号处理（整合事件）
        6. 涌现决策
        7. 执行交易
        8. 定期进化生态系统
        """
        self._step_count += 1

        # 1. 记录资产收益率
        self._update_returns(kline)

        # 2. 更新量子纠缠状态
        entanglement_matrix = self._update_entanglement()

        # 3. 处理 K 线附带的事件（新增）
        event_signal = self._process_kline_events(kline, entanglement_matrix)

        # 4. 获取各子策略信号
        signals, weights = self._get_substrategy_signals(context, kline)

        # 5. 整合事件信号到子策略信号（新增）
        if event_signal is not None:
            signals = self._integrate_event_signal(signals, event_signal, kline.symbol)

        # 6. 神经形态处理（整合事件）
        events = getattr(kline, 'events', [])
        neural_signal = self._process_neuromorphic(kline, events=events)

        # 7. 设置决策引擎参数
        self.decision_engine.map_strategies_to_oscillators(signals, weights)
        if entanglement_matrix is not None:
            self.decision_engine.set_coupling_from_entanglement(entanglement_matrix)

        # 8. 模拟动力学并做决策
        self.decision_engine.simulate_dynamics(n_steps=50, dt=0.1)

        # 检查临界相变
        if self.decision_engine.detect_critical_transition():
            logger.warning("检测到临界相变预警！")
            # 降低风险暴露
            self._reduce_risk_exposure(context)

        # 获取决策
        decision = self.decision_engine.make_decision()
        logger.info(f"决策：{decision['decision']}, 强度：{decision['strength']:.4f}, "
                    f"同步度：{decision['synchronization']:.4f}")

        # 9. 执行交易
        if decision["decision"] != "HOLD" and decision["strength"] > 0.1:
            self._execute_decision(context, kline, decision)

        # 10. 生态系统进化（定期）
        if self._step_count % self.evolution_interval == 0:
            self._evolve_ecosystem(context)

        # 11. 存储经验到海马体
        self._store_experience(kline, decision)

    def on_stop(self, context: StrategyContext) -> None:
        """策略停止时的处理."""
        logger.info(f"QENAS 策略停止，共执行 {self._step_count} 步")

        # 输出种群统计
        stats = self.niche_manager.get_population_stats()
        logger.info(f"种群统计：{stats}")

    def _get_asset_index(self, symbol: str) -> int:
        """获取资产的索引（用于纠缠矩阵）."""
        if symbol not in self._symbol_to_index:
            self._symbol_to_index[symbol] = self._next_asset_index
            self._next_asset_index += 1
        return self._symbol_to_index[symbol]

    def _process_kline_events(
        self,
        kline: Kline,
        entanglement_matrix: Optional[NDArray[np.float64]] = None,
    ) -> Optional[EventSignal]:
        """
        处理 K 线附带的事件.

        Args:
            kline: K 线数据（可能包含 events 列表）
            entanglement_matrix: 当前的纠缠矩阵

        Returns:
            聚合事件信号，如果没有事件则返回 None
        """
        # 检查 K 线是否有附带事件
        events = getattr(kline, 'events', [])
        if not events:
            return None

        logger.info(f"检测到 {len(events)} 个事件：{[e.title for e in events]}")

        # 处理每个事件
        event_signals = []
        for event in events:
            signal = self.event_processor.process_event(event)
            if signal:
                event_signals.append(signal)
                logger.info(f"事件信号：{event.title} -> 强度={signal.signal_strength:.4f}")

        # 更新活跃事件（应用衰减）
        self.event_processor.update_active_events()

        # 如果有高影响事件，调整纠缠矩阵
        if entanglement_matrix is not None and events:
            high_impact_events = [
                e for e in events
                if e.impact_level.value >= 3  # HIGH or CRITICAL
            ]
            if high_impact_events:
                entanglement_matrix = self.event_processor.adjust_entanglement_for_events(
                    entanglement_matrix,
                    high_impact_events,
                    self._symbol_to_index,
                )
                logger.info(f"调整纠缠矩阵，影响事件数：{len(high_impact_events)}")

        # 返回聚合信号
        if event_signals:
            # 返回第一个信号（简化处理）
            return event_signals[0]
        return None

    def _integrate_event_signal(
        self,
        strategy_signals: NDArray[np.float64],
        event_signal: EventSignal,
        target_symbol: str,
    ) -> NDArray[np.float64]:
        """
        将事件信号整合到策略信号中.

        Args:
            strategy_signals: 子策略信号数组
            event_signal: 事件生成的信号
            target_symbol: 目标标的

        Returns:
            整合后的信号数组
        """
        # 创建事件驱动的子策略信号
        event_driven_signal = event_signal.signal_strength * event_signal.confidence

        # 找到与事件相关的策略物种（事件驱动型）
        enhanced_signals = strategy_signals.copy()

        for i, species in enumerate(self.niche_manager.population):
            # 事件驱动型策略对事件信号更敏感
            if species.signal_niche == SignalNiche.SENTIMENT:
                enhanced_signals[i] = (
                    0.7 * strategy_signals[i] +
                    0.3 * event_driven_signal
                )

        logger.debug(f"整合事件信号：强度={event_signal.signal_strength:.4f}")
        return enhanced_signals

    def _process_neuromorphic(
        self,
        kline: Kline,
        events: Optional[list] = None,
    ) -> float:
        """
        神经形态信号处理.

        Args:
            kline: K 线数据
            events: 事件列表（可选）
        """
        dt = 1.0  # ms

        # 准备各脑区输入
        prefrontal_input = np.random.randn(64) * 0.1  # 基础风险信号
        limbic_input = np.random.randn(32) * 0.1      # 基础情绪信号
        cerebellum_input = np.random.randn(128) * 0.1 # 基础模式识别

        # 如果有事件，编码为神经形态输入
        if events:
            event_encoding = self.event_processor.encode_events_for_neuromorphic(events)

            # 叠加事件编码到各脑区
            if "prefrontal" in event_encoding and len(event_encoding["prefrontal"]) > 0:
                risk_idx = min(len(event_encoding["prefrontal"]), 64)
                prefrontal_input[:risk_idx] += event_encoding["prefrontal"][:risk_idx]

            if "limbic" in event_encoding and len(event_encoding["limbic"]) > 0:
                limbic_idx = min(len(event_encoding["limbic"]), 32)
                limbic_input[:limbic_idx] += event_encoding["limbic"][:limbic_idx]

            if "cerebellum" in event_encoding and len(event_encoding["cerebellum"]) > 0:
                cereal_idx = min(len(event_encoding["cerebellum"]), 128)
                cerebellum_input[:cereal_idx] += event_encoding["cerebellum"][:cereal_idx]

        # 前额叶皮层：风险信号
        self.snn_layers[BrainRegion.PREFRONTAL].step(dt, prefrontal_input)

        # 边缘系统：情绪信号
        self.snn_layers[BrainRegion.LIMBIC].step(dt, limbic_input)

        # 小脑：模式识别
        self.snn_layers[BrainRegion.CEREBELLUM].step(dt, cerebellum_input)

        # 应用 STDP 学习
        for layer in self.snn_layers.values():
            layer.apply_stdp()

        # 返回简化的神经信号
        return 0.0  # 占位符

    def _update_returns(self, kline: Kline) -> None:
        """更新收益率窗口."""
        # 简化实现：只记录对数收益率
        if not hasattr(self, '_last_prices'):
            self._last_prices: dict[str, float] = {}

        if kline.symbol in self._last_prices:
            last_price = self._last_prices[kline.symbol]
            log_return = np.log(float(kline.close) / last_price)

            # 为所有资产创建收益率向量
            returns = np.zeros(max(len(self._symbol_to_index), 1))
            asset_idx = self._get_asset_index(kline.symbol)
            returns[asset_idx] = log_return

            self._returns_window.append(returns)

            # 限制窗口大小
            if len(self._returns_window) > self._max_returns_window:
                self._returns_window.pop(0)

        self._last_prices[kline.symbol] = float(kline.close)

    def _update_entanglement(self) -> Optional[NDArray[np.float64]]:
        """更新量子纠缠状态."""
        if len(self._returns_window) < 10:
            return None

        # 堆叠收益率数据
        returns_data = np.array(self._returns_window)

        # 如果只有一种资产，返回单位矩阵
        if returns_data.shape[1] < 2:
            return np.eye(self.n_species) * 0.1

        # 计算纠缠矩阵
        try:
            entanglement = self.entanglement_calculator.compute_entanglement_matrix(returns_data)
            # 调整大小以匹配策略数量
            if entanglement.shape[0] != self.n_species:
                # 使用平均值填充/截断
                if entanglement.shape[0] < self.n_species:
                    enlarged = np.ones((self.n_species, self.n_species)) * 0.1
                    min_size = min(entanglement.shape[0], self.n_species)
                    enlarged[:min_size, :min_size] = entanglement[:min_size, :min_size]
                    entanglement = enlarged
                else:
                    entanglement = entanglement[:self.n_species, :self.n_species]
            return entanglement
        except Exception as e:
            logger.warning(f"计算纠缠矩阵失败：{e}")
            return np.eye(self.n_species) * 0.1

    def _get_substrategy_signals(
        self,
        context: StrategyContext,
        kline: Kline,
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """
        获取各子策略的信号.

        Returns:
            (signals, weights) - 信号强度数组和权重数组
        """
        signals = np.zeros(self.n_species)
        weights = np.zeros(self.n_species)

        for i, species in enumerate(self.niche_manager.population):
            # 根据生态位生成信号（简化实现）
            signal = self._execute_substrategy(species, kline)
            signals[i] = signal
            weights[i] = species.capital_allocation

        # 归一化权重
        weight_sum = np.sum(weights)
        if weight_sum > 0:
            weights = weights / weight_sum

        return signals, weights

    def _execute_substrategy(
        self,
        species: StrategySpecies,
        kline: Kline,
    ) -> float:
        """
        执行单个子策略，返回信号强度.

        根据物种的生态位和基因组生成信号.
        """
        # 简化实现：基于生态位类型和基因组生成信号
        base_signal = 0.0

        # 信号生态位影响
        if species.signal_niche == SignalNiche.MOMENTUM:
            base_signal = np.mean(species.genome[:10]) * 0.5
        elif species.signal_niche == SignalNiche.REVERSION:
            base_signal = -np.mean(species.genome[:10]) * 0.5
        elif species.signal_niche == SignalNiche.VOLATILITY:
            base_signal = np.std(species.genome[:20]) * 0.3
        else:
            base_signal = np.mean(species.genome) * 0.3

        # 添加一些随机性
        noise = np.random.randn() * 0.1

        return float(np.clip(base_signal + noise, -1.0, 1.0))

    def _execute_decision(
        self,
        context: StrategyContext,
        kline: Kline,
        decision: dict,
    ) -> None:
        """执行交易决策."""
        symbol = kline.symbol
        position = context.get_position(symbol)

        if decision["decision"] == "BUY":
            # 计算买入数量
            cash_per_symbol = context.cash_available * Decimal(str(0.1))
            quantity = (cash_per_symbol / kline.close).quantize(Decimal("0.01"))

            if quantity > 0:
                logger.info(f"买入 {symbol}: 价格={kline.close}, 数量={quantity}")
                context.buy(symbol, quantity)

        elif decision["decision"] == "SELL":
            # 卖出
            if position and position.quantity > 0:
                logger.info(f"卖出 {symbol}: 价格={kline.close}, 数量={position.quantity}")
                context.sell(symbol, position.quantity)

    def _reduce_risk_exposure(self, context: StrategyContext) -> None:
        """降低风险暴露."""
        for symbol in list(context.positions.keys()):
            position = context.get_position(symbol)
            if position and position.is_open:
                # 减半仓位
                quantity_to_sell = position.quantity / 2
                if quantity_to_sell > 0:
                    context.sell(symbol, quantity_to_sell)

    def _evolve_ecosystem(self, context: StrategyContext) -> None:
        """进化生态系统."""
        # 收集绩效数据
        performance_data = {}
        for i, species in enumerate(self.niche_manager.population):
            # 简化绩效评估
            sharpe = np.random.randn() * 0.5 + species.fitness * 0.5
            performance_data[species.id] = {"sharpe": sharpe}

        # 进化
        self.niche_manager.evolve_ecosystem(performance_data)

        # 更新决策引擎的策略数量
        self.decision_engine.n_strategies = len(self.niche_manager.population)

        stats = self.niche_manager.get_population_stats()
        logger.info(f"生态系统进化完成：{stats}")

    def _store_experience(self, kline: Kline, decision: dict) -> None:
        """存储经验到海马体."""
        state = {
            "price": float(kline.close),
            "symbol": kline.symbol,
        }
        self.hippocampus.store_experience(
            state=state,
            decision=decision["decision"],
            outcome=None,  # 将在之后回填
        )

    def get_status(self) -> dict:
        """获取策略状态."""
        stats = self.niche_manager.get_population_stats()
        return {
            "step_count": self._step_count,
            "entanglement_entropy": (
                self.entanglement_calculator.entropy_history[-1]
                if self.entanglement_calculator.entropy_history else None
            ),
            "ecosystem_stats": stats,
            "decision_history": self.decision_engine.decision_history[-10:],
        }
