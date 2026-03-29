"""QENAS 核心模块测试."""

import pytest
import numpy as np
from datetime import datetime
from decimal import Decimal


class TestDensityMatrix:
    """测试密度矩阵."""

    def test_from_covariance(self):
        """测试从协方差矩阵构建密度矩阵."""
        from qenas_core.quantum.entanglement import DensityMatrix

        # 创建简单的协方差矩阵
        cov = np.array([
            [1.0, 0.5],
            [0.5, 1.0],
        ])

        rho = DensityMatrix.from_covariance(cov)

        # 验证迹为 1
        assert np.isclose(np.trace(rho.matrix), 1.0)

        # 验证矩阵是对称的
        assert np.allclose(rho.matrix, rho.matrix.T)

    def test_von_neumann_entropy(self):
        """测试冯·诺依曼熵计算."""
        from qenas_core.quantum.entanglement import DensityMatrix

        # 创建最大混合态
        rho = DensityMatrix(matrix=np.eye(2) / 2)
        entropy = rho.von_neumann_entropy()

        # 最大混合态的熵应为 1 (log2(2))
        assert np.isclose(entropy, 1.0, atol=0.01)

    def test_entropy_pure_state(self):
        """测试纯态的熵为零."""
        from qenas_core.quantum.entanglement import DensityMatrix

        # 纯态：|0><0|
        rho = DensityMatrix(matrix=np.array([[1, 0], [0, 0]]))
        entropy = rho.von_neumann_entropy()

        # 纯态的熵应为 0
        assert np.isclose(entropy, 0.0, atol=0.01)


class TestQuantumEntanglementCalculator:
    """测试量子纠缠计算器."""

    def test_compute_entanglement_entropy(self):
        """测试纠缠熵计算."""
        from qenas_core.quantum.entanglement import QuantumEntanglementCalculator

        calc = QuantumEntanglementCalculator()

        # 创建随机收益率数据
        np.random.seed(42)
        returns = np.random.randn(100, 3)

        entropy = calc.compute_entanglement_entropy(returns)

        # 熵应该是正数
        assert entropy > 0

    def test_compute_entanglement_matrix(self):
        """测试纠缠矩阵计算."""
        from qenas_core.quantum.entanglement import QuantumEntanglementCalculator

        calc = QuantumEntanglementCalculator()

        # 创建随机收益率数据
        np.random.seed(42)
        returns = np.random.randn(100, 3)

        matrix = calc.compute_entanglement_matrix(returns)

        # 矩阵应该是对称的
        assert np.allclose(matrix, matrix.T)

        # 矩阵应该是 3x3
        assert matrix.shape == (3, 3)


class TestNicheManager:
    """测试生态位管理器."""

    def test_initialize_ecosystem(self):
        """测试生态系统初始化."""
        from qenas_core.ecosystem.niche_manager import NicheManager

        manager = NicheManager(n_species=50)
        population = manager.initialize_ecosystem(seed=42)

        assert len(population) == 50

        # 验证所有物种都有不同的 ID
        ids = [s.id for s in population]
        assert len(set(ids)) == 50

    def test_compute_niche_overlap(self):
        """测试生态位重叠计算."""
        from qenas_core.ecosystem.niche_manager import (
            NicheManager,
            StrategySpecies,
            TimeNiche,
            SignalNiche,
            SpaceNiche,
        )

        manager = NicheManager(n_species=10)
        manager.initialize_ecosystem()

        # 创建两个相同生态位的物种
        species1 = StrategySpecies(
            id=100,
            time_niche=TimeNiche.SHORT,
            signal_niche=SignalNiche.MOMENTUM,
            space_niche=SpaceNiche.TECH,
        )
        species2 = StrategySpecies(
            id=101,
            time_niche=TimeNiche.SHORT,
            signal_niche=SignalNiche.MOMENTUM,
            space_niche=SpaceNiche.TECH,
        )

        # 完全重叠
        overlap = manager.compute_niche_overlap(species1, [species2])
        assert overlap == 1.0

        # 创建不同生态位的物种
        species3 = StrategySpecies(
            id=102,
            time_niche=TimeNiche.LONG,
            signal_niche=SignalNiche.REVERSION,
            space_niche=SpaceNiche.FINANCE,
        )

        # 无重叠
        overlap = manager.compute_niche_overlap(species1, [species3])
        assert overlap == 0.0

    def test_evolve_ecosystem(self):
        """测试生态系统进化."""
        from qenas_core.ecosystem.niche_manager import NicheManager

        manager = NicheManager(n_species=20)
        manager.initialize_ecosystem(seed=42)

        # 创建绩效数据
        performance_data = {
            i: {"sharpe": np.random.randn()}
            for i in range(20)
        }

        # 进化
        new_population = manager.evolve_ecosystem(performance_data)

        # 种群大小应该保持不变
        assert len(new_population) == 20

        # 获取统计信息
        stats = manager.get_population_stats()
        assert stats["population_size"] == 20


class TestStrategyBase:
    """测试策略基类."""

    def test_strategy_initialization(self):
        """测试策略初始化."""
        from qenas_core.strategies.base import StrategyBase, StrategyContext

        class TestStrategy(StrategyBase):
            def on_init(self, context):
                pass

            def on_bar(self, context, kline):
                pass

        strategy = TestStrategy(strategy_id="test", name="Test Strategy")
        context = StrategyContext(strategy_id="test")

        assert strategy.strategy_id == "test"
        assert strategy.name == "Test Strategy"
        assert not strategy.is_initialized

        strategy.initialize(context)
        assert strategy.is_initialized

    def test_order_creation(self):
        """测试订单创建."""
        from qenas_core.strategies.base import Order, OrderSide, OrderType
        from decimal import Decimal

        order = Order(
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=Decimal("100"),
            order_type=OrderType.MARKET,
        )

        assert order.symbol == "AAPL"
        assert order.side == "buy"
        assert order.quantity == Decimal("100")
        assert order.status == "pending"

    def test_position_management(self):
        """测试持仓管理."""
        from qenas_core.strategies.base import Position
        from decimal import Decimal

        position = Position(symbol="AAPL")

        # 建仓
        position.add_to_position(Decimal("100"), Decimal("150"))
        assert position.quantity == Decimal("100")
        assert position.average_cost == Decimal("150")

        # 加仓
        position.add_to_position(Decimal("100"), Decimal("160"))
        assert position.quantity == Decimal("200")
        assert position.average_cost == Decimal("155")

        # 减仓
        pnl = position.reduce_position(Decimal("100"), Decimal("170"))
        assert position.quantity == Decimal("100")
        assert pnl == Decimal("1500")  # (170 - 155) * 100


class TestKuramotoOscillator:
    """测试 Kuramoto 振子."""

    def test_order_parameter(self):
        """测试序参量计算."""
        from qenas_core.emergent.decision import KuramotoOscillator
        import numpy as np

        # 完全同步
        osc = KuramotoOscillator(n_oscillators=10)
        osc.phases = np.zeros(10)  # 所有相位相同
        order_param = osc.calculate_order_parameter()

        assert np.isclose(order_param, 1.0, atol=0.01)

        # 完全不同步
        osc.phases = np.linspace(0, 2 * np.pi, 10, endpoint=False)
        order_param = osc.calculate_order_parameter()

        assert order_param < 0.5  # 应该比较低


class TestEmergentDecisionEngine:
    """测试涌现决策引擎."""

    def test_make_decision(self):
        """测试决策生成."""
        from qenas_core.emergent.decision import EmergentDecisionEngine
        import numpy as np

        engine = EmergentDecisionEngine(n_strategies=10, sync_threshold=0.5)

        # 设置强买信号
        signals = np.ones(10) * 0.8
        engine.map_strategies_to_oscillators(signals)
        engine.simulate_dynamics(n_steps=50, dt=0.1)

        decision = engine.make_decision()

        assert decision["decision"] in ["BUY", "SELL", "HOLD"]
        assert 0 <= decision["confidence"] <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
