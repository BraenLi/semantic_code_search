"""QENAS Core - 量子纠缠生态位自适应网络核心引擎."""

from qenas_core.strategies.base import (
    StrategyBase,
    StrategyContext,
    Order,
    Position,
    Kline,
    Tick,
)

from qenas_core.strategies.qenas_strategy import QENASStrategy

from qenas_core.quantum.entanglement import (
    DensityMatrix,
    QuantumEntanglementCalculator,
)

from qenas_core.ecosystem.niche_manager import (
    NicheManager,
    StrategySpecies,
    TimeNiche,
    SignalNiche,
    SpaceNiche,
)

from qenas_core.neuromorphic.snn import (
    LIFNeuron,
    Synapse,
    SpikingNeuralLayer,
    HippocampusMemory,
    BrainRegion,
)

from qenas_core.emergent.decision import (
    KuramotoOscillator,
    EmergentDecisionEngine,
    PercolationAnalyzer,
)

__version__ = "0.1.0"

__all__ = [
    # 基类和数据模型
    "StrategyBase",
    "StrategyContext",
    "Order",
    "Position",
    "Kline",
    "Tick",
    # QENAS 主策略
    "QENASStrategy",
    # 量子纠缠层
    "DensityMatrix",
    "QuantumEntanglementCalculator",
    # 生态位子策略群
    "NicheManager",
    "StrategySpecies",
    "TimeNiche",
    "SignalNiche",
    "SpaceNiche",
    # 神经形态处理器
    "LIFNeuron",
    "Synapse",
    "SpikingNeuralLayer",
    "HippocampusMemory",
    "BrainRegion",
    # 涌现决策引擎
    "KuramotoOscillator",
    "EmergentDecisionEngine",
    "PercolationAnalyzer",
]
