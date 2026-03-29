"""涌现决策引擎 - 基于复杂网络同步理论."""

import numpy as np
from numpy.typing import NDArray
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class KuramotoOscillator:
    """
    Kuramoto 振子模型.

    用于模拟耦合振子动力学：
    dθᵢ/dt = ωᵢ + Σ Kᵢⱼ sin(θⱼ - θᵢ)

    其中：
    - θᵢ: 振子 i 的相位
    - ωᵢ: 振子 i 的固有频率
    - Kᵢⱼ: 振子 i 和 j 之间的耦合强度
    """

    n_oscillators: int
    phases: NDArray[np.float64] = field(default=None)
    frequencies: NDArray[np.float64] = field(default=None)
    coupling_matrix: Optional[NDArray[np.float64]] = field(default=None)

    def __post_init__(self):
        if self.phases is None:
            self.phases = np.random.uniform(0, 2 * np.pi, self.n_oscillators)
        if self.frequencies is None:
            self.frequencies = np.random.normal(0, 0.1, self.n_oscillators)
        if self.coupling_matrix is None:
            self.coupling_matrix = np.ones((self.n_oscillators, self.n_oscillators)) * 0.1

    def set_initial_phases(self, phases: NDArray[np.float64]) -> None:
        """设置初始相位."""
        self.phases = phases.copy()

    def set_coupling_matrix(self, coupling: NDArray[np.float64]) -> None:
        """设置耦合矩阵."""
        self.coupling_matrix = coupling.copy()

    def set_frequencies(self, frequencies: NDArray[np.float64]) -> None:
        """设置固有频率."""
        self.frequencies = frequencies.copy()

    def evolve(self, dt: float) -> None:
        """
        执行一个时间步的演化.

        使用欧拉方法求解 Kuramoto 方程.
        """
        n = self.n_oscillators

        # 计算相位差
        phase_diff = self.phases[:, np.newaxis] - self.phases[np.newaxis, :]

        # 计算耦合项：Σ Kᵢⱼ sin(θⱼ - θᵢ)
        coupling_term = np.sum(
            self.coupling_matrix * np.sin(-phase_diff),
            axis=1
        ) / n

        # 更新相位
        dphase = self.frequencies + coupling_term
        self.phases += dphase * dt

        # 归一化到 [0, 2π)
        self.phases = np.mod(self.phases, 2 * np.pi)

    def calculate_order_parameter(self) -> float:
        """
        计算序参量（同步程度）.

        r = |<e^(iθ)>|

        r = 0: 完全不同步
        r = 1: 完全同步
        """
        complex_order = np.mean(np.exp(1j * self.phases))
        return float(np.abs(complex_order))

    def calculate_average_phase(self) -> float:
        """计算平均相位（集体决策方向）."""
        complex_order = np.mean(np.exp(1j * self.phases))
        return float(np.angle(complex_order))


class EmergentDecisionEngine:
    """
    涌现决策引擎.

    基于 Kuramoto 振子的同步动力学产生集体决策.
    """

    def __init__(
        self,
        n_strategies: int,
        sync_threshold: float = 0.75,
    ):
        self.n_strategies = n_strategies
        self.sync_threshold = sync_threshold

        # 初始化振子系统
        self.oscillators = KuramotoOscillator(n_oscillators=n_strategies)

        # 历史记录
        self.order_parameter_history: list[float] = []
        self.decision_history: list[str] = []

    def map_strategies_to_oscillators(
        self,
        signals: NDArray[np.float64],
        weights: Optional[NDArray[np.float64]] = None,
    ) -> None:
        """
        将策略信号映射到振子初始相位.

        Args:
            signals: 策略信号强度数组
            weights: 策略权重（用于设置频率）
        """
        if len(signals) != self.n_strategies:
            raise ValueError(
                f"Signals length ({len(signals)}) must match n_strategies ({self.n_strategies})"
            )

        # 将信号映射到相位 [-π, π]
        # 强买信号 → 接近 π/2
        # 强卖信号 → 接近 -π/2
        # 中性信号 → 接近 0
        phases = np.arctan(signals) * 2 / np.pi * np.pi / 2

        self.oscillators.set_initial_phases(phases)

        # 权重影响频率（高权重策略有更高"影响力"）
        if weights is not None:
            frequencies = weights * 0.1
            self.oscillators.set_frequencies(frequencies)

    def set_coupling_from_entanglement(
        self,
        entanglement_matrix: NDArray[np.float64],
    ) -> None:
        """
        从量子纠缠矩阵设置耦合强度.

        Args:
            entanglement_matrix: 纠缠强度矩阵
        """
        if entanglement_matrix.shape[0] != self.n_strategies:
            raise ValueError(
                f"Entanglement matrix size ({entanglement_matrix.shape[0]}) "
                f"must match n_strategies ({self.n_strategies})"
            )

        self.oscillators.set_coupling_matrix(entanglement_matrix)

    def simulate_dynamics(
        self,
        n_steps: int = 100,
        dt: float = 0.01,
    ) -> float:
        """
        模拟振子动力学演化.

        Args:
            n_steps: 演化步数
            dt: 时间步长

        Returns:
            最终序参量（同步度）
        """
        for _ in range(n_steps):
            self.oscillators.evolve(dt)

        order_param = self.oscillators.calculate_order_parameter()
        self.order_parameter_history.append(order_param)
        return order_param

    def detect_critical_transition(
        self,
        threshold: float = 1.5,
        lookback: int = 10,
    ) -> bool:
        """
        检测临界相变（市场结构突变预警）.

        基于"临界 slowing down"现象：
        - 方差增加
        - 自相关增加

        Args:
            threshold: 临界阈值
            lookback: 回溯窗口

        Returns:
            是否检测到临界相变
        """
        if len(self.order_parameter_history) < lookback + 1:
            return False

        history = np.array(self.order_parameter_history[-lookback:])

        # 计算方差
        variance = np.var(history)

        # 计算自相关
        if len(history) > 1:
            autocorr = np.corrcoef(history[:-1], history[1:])[0, 1]
            if np.isnan(autocorr):
                autocorr = 0.0
        else:
            autocorr = 0.0

        # 临界 slowing down 指标
        # 高方差 + 高自相关 → 接近临界点
        critical_indicator = variance / (1 - autocorr + 1e-10)

        return critical_indicator > threshold

    def make_decision(self) -> dict:
        """
        基于集体相位做出决策.

        Returns:
            决策字典 {decision, strength, confidence, synchronization}
        """
        order_param = self.oscillators.calculate_order_parameter()
        collective_phase = self.oscillators.calculate_average_phase()

        self.order_parameter_history.append(order_param)

        # 只有当同步度超过阈值时才执行交易
        if order_param < self.sync_threshold:
            decision = "HOLD"
            strength = 0.0
        elif collective_phase > np.pi / 4:
            decision = "BUY"
            strength = order_param * np.sin(collective_phase)
        elif collective_phase < -np.pi / 4:
            decision = "SELL"
            strength = order_param * np.abs(np.sin(collective_phase))
        else:
            decision = "HOLD"
            strength = 0.0

        result = {
            "decision": decision,
            "strength": float(strength),
            "confidence": float(order_param),
            "synchronization": float(order_param),
            "collective_phase": float(collective_phase),
        }

        self.decision_history.append(decision)
        return result

    def reset(self) -> None:
        """重置引擎状态."""
        self.oscillators = KuramotoOscillator(n_oscillators=self.n_strategies)
        self.order_parameter_history.clear()
        self.decision_history.clear()


class PercolationAnalyzer:
    """
    渗流理论分析器.

    用于分析市场网络的连通性和风险传播.
    """

    def __init__(self, n_nodes: int):
        self.n_nodes = n_nodes
        self.adjacency_matrix: Optional[NDArray[np.float64]] = None

    def set_connectivity(self, matrix: NDArray[np.float64]) -> None:
        """设置网络连接（如纠缠矩阵）."""
        self.adjacency_matrix = matrix.copy()

    def calculate_giant_component_size(
        self,
        threshold: float = 0.5,
    ) -> float:
        """
        计算最大连通分量的大小.

        Args:
            threshold: 连接阈值

        Returns:
            最大连通分量占总节点的比例
        """
        if self.adjacency_matrix is None:
            raise ValueError("Connectivity matrix not set")

        # 二值化邻接矩阵
        binary = (self.adjacency_matrix > threshold).astype(int)

        # 简化的连通分量计算（BFS）
        visited = np.zeros(self.n_nodes, dtype=bool)
        max_component_size = 0

        for start in range(self.n_nodes):
            if visited[start]:
                continue

            # BFS
            queue = [start]
            component_size = 0
            visited[start] = True

            while queue:
                node = queue.pop(0)
                component_size += 1

                for neighbor in range(self.n_nodes):
                    if binary[node, neighbor] and not visited[neighbor]:
                        visited[neighbor] = True
                        queue.append(neighbor)

            max_component_size = max(max_component_size, component_size)

        return max_component_size / self.n_nodes

    def detect_systemic_risk(
        self,
        threshold: float = 0.5,
        critical_fraction: float = 0.7,
    ) -> bool:
        """
        检测系统性风险.

        如果最大连通分量过大，表示风险容易在整个系统中传播.

        Args:
            threshold: 连接阈值
            critical_fraction: 临界比例

        Returns:
            是否存在系统性风险
        """
        giant_component = self.calculate_giant_component_size(threshold)
        return giant_component > critical_fraction
