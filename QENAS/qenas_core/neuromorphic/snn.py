"""神经形态计算模块 - 脉冲神经网络."""

import numpy as np
from numpy.typing import NDArray
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class BrainRegion(Enum):
    """大脑区域."""
    PREFRONTAL = "prefrontal"  # 前额叶皮层：风险管理
    LIMBIC = "limbic"          # 边缘系统：情绪处理
    CEREBELLUM = "cerebellum"  # 小脑：高频模式识别
    HIPPOCAMPUS = "hippocampus" # 海马体：长期记忆


@dataclass
class LIFNeuron:
    """
    Leaky Integrate-and-Fire 神经元模型.

    膜电位动力学:
    τ dV/dt = -(V - V_rest) + R * I

    当 V > V_threshold 时发放脉冲，然后重置为 V_reset
    """

    tau: float = 20.0          # 时间常数 (ms)
    v_rest: float = -70.0      # 静息电位 (mV)
    v_threshold: float = -55.0 # 发放阈值 (mV)
    v_reset: float = -75.0     # 重置电位 (mV)
    r: float = 1.0             # 膜电阻

    # 当前状态
    v: float = -70.0           # 当前膜电位
    last_spike_time: float = 0.0
    refractory_period: float = 2.0  # 不应期 (ms)

    # 累计电流
    input_current: float = 0.0

    def step(self, dt: float, input_current: float) -> bool:
        """
        执行一个时间步的演化.

        Args:
            dt: 时间步长 (ms)
            input_current: 输入电流

        Returns:
            是否发放脉冲
        """
        # 欧拉方法求解微分方程
        dv = (-(self.v - self.v_rest) + self.r * input_current) / self.tau
        self.v += dv * dt

        # 检查是否发放脉冲
        spiked = False
        if self.v >= self.v_threshold:
            spiked = True
            self.v = self.v_reset
            self.last_spike_time = 0  # 重置不应期计时

        # 不应期处理
        if self.last_spike_time < self.refractory_period:
            self.v = self.v_reset
            self.last_spike_time += dt

        return spiked

    def reset(self) -> None:
        """重置神经元状态."""
        self.v = self.v_rest
        self.input_current = 0.0
        self.last_spike_time = self.refractory_period + 1


@dataclass
class Synapse:
    """
    突触连接.

    支持 STDP (脉冲时间依赖可塑性) 学习.
    """

    weight: float = 0.5        # 突触权重
    tau_plus: float = 20.0     # LTP 时间常数 (ms)
    tau_minus: float = 20.0    # LTD 时间常数 (ms)
    a_plus: float = 0.01       # LTP 学习率
    a_minus: float = 0.012     # LTD 学习率

    # 追踪变量
    pre_trace: float = 0.0     # 突触前追踪
    post_trace: float = 0.0    # 突触后追踪

    def update_traces(self, pre_spike: bool, post_spike: bool, dt: float) -> None:
        """更新追踪变量."""
        # 指数衰减
        self.pre_trace *= np.exp(-dt / self.tau_plus)
        self.post_trace *= np.exp(-dt / self.tau_minus)

        # 脉冲时增加
        if pre_spike:
            self.pre_trace += 1.0
        if post_spike:
            self.post_trace += 1.0

    def apply_stdp(self, pre_spike: bool, post_spike: bool) -> None:
        """
        应用 STDP 学习规则.

        LTP: 突触前脉冲先于突触后脉冲 → 增强
        LTD: 突触后脉冲先于突触前脉冲 → 减弱
        """
        if pre_spike and self.post_trace > 0:
            # LTP
            self.weight += self.a_plus * self.post_trace

        if post_spike and self.pre_trace > 0:
            # LTD
            self.weight -= self.a_minus * self.pre_trace

        # 权重边界
        self.weight = np.clip(self.weight, 0.0, 1.0)


class SpikingNeuralLayer:
    """
    脉冲神经层.

    包含一组神经元和它们之间的连接.
    """

    def __init__(
        self,
        n_neurons: int,
        region: BrainRegion,
        connectivity: float = 0.3,
    ):
        self.n_neurons = n_neurons
        self.region = region
        self.connectivity = connectivity

        # 初始化神经元
        self.neurons = [LIFNeuron() for _ in range(n_neurons)]

        # 初始化突触连接（稀疏连接）
        self.synapses: dict[tuple[int, int], Synapse] = {}
        self._initialize_synapses()

        # 脉冲记录
        self.spike_times: list[float] = []
        self.spike_neurons: list[int] = []

    def _initialize_synapses(self) -> None:
        """随机初始化突触连接."""
        for i in range(self.n_neurons):
            for j in range(self.n_neurons):
                if i != j and np.random.rand() < self.connectivity:
                    self.synapses[(i, j)] = Synapse(
                        weight=np.random.uniform(0.3, 0.7)
                    )

    def step(
        self,
        dt: float,
        external_input: Optional[NDArray[np.float64]] = None,
    ) -> list[int]:
        """
        执行一个时间步的演化.

        Args:
            dt: 时间步长 (ms)
            external_input: 外部输入电流

        Returns:
            发放脉冲的神经元索引列表
        """
        spiking_neurons = []

        for i, neuron in enumerate(self.neurons):
            # 获取输入电流
            current = external_input[i] if external_input is not None else 0.0

            # 添加来自其他神经元的突触输入
            for j in range(self.n_neurons):
                if (j, i) in self.synapses:
                    # 检查神经元 j 是否在上一步发放了脉冲
                    if j in self.spike_neurons:
                        current += self.synapses[(j, i)].weight * 10.0

            # 神经元演化
            spiked = neuron.step(dt, current)
            if spiked:
                spiking_neurons.append(i)

        # 更新突触追踪
        for (pre, post), synapse in self.synapses.items():
            pre_spike = pre in spiking_neurons
            post_spike = post in spiking_neurons
            synapse.update_traces(pre_spike, post_spike, dt)

        # 记录脉冲
        current_time = len(self.spike_times) * dt
        for neuron_id in spiking_neurons:
            self.spike_times.append(current_time)
            self.spike_neurons.append(neuron_id)

        return spiking_neurons

    def apply_stdp(self) -> None:
        """对所有突触应用 STDP 学习."""
        for synapse in self.synapses.values():
            # 简化 STDP：基于追踪变量更新权重
            if synapse.pre_trace > 0.1 and synapse.post_trace > 0.1:
                if synapse.pre_trace > synapse.post_trace:
                    synapse.weight += 0.01
                else:
                    synapse.weight -= 0.01
                synapse.weight = np.clip(synapse.weight, 0.0, 1.0)

    def reset(self) -> None:
        """重置层状态."""
        for neuron in self.neurons:
            neuron.reset()
        self.spike_times.clear()
        self.spike_neurons.clear()

    def get_firing_rate(self, window_ms: float = 100.0) -> NDArray[np.float64]:
        """计算每个神经元的发放率."""
        if not self.spike_times:
            return np.zeros(self.n_neurons)

        rates = np.zeros(self.n_neurons)
        for neuron_id in self.spike_neurons:
            rates[neuron_id] += 1

        return rates / (window_ms / 1000.0)  # Hz


class HippocampusMemory:
    """
    海马体记忆模块.

    存储和检索经验.
    """

    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self.memories: list[dict] = []

    def store_experience(
        self,
        state: dict,
        decision: str,
        outcome: Optional[float] = None,
    ) -> None:
        """存储经验."""
        memory = {
            "state": state,
            "decision": decision,
            "outcome": outcome,
            "timestamp": len(self.memories),
        }
        self.memories.append(memory)

        # 限制容量
        if len(self.memories) > self.capacity:
            self.memories.pop(0)

    def retrieve_similar(
        self,
        current_state: dict,
        k: int = 5,
    ) -> list[dict]:
        """检索相似的经验."""
        if not self.memories:
            return []

        # 计算状态相似度
        def state_similarity(s1: dict, s2: dict) -> float:
            # 简单实现：基于共同键的值比较
            common_keys = set(s1.keys()) & set(s2.keys())
            if not common_keys:
                return 0.0

            similarities = []
            for key in common_keys:
                v1, v2 = s1[key], s2[key]
                if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                    # 数值相似度
                    diff = abs(v1 - v2) / (abs(v1) + abs(v2) + 1e-10)
                    similarities.append(1 - diff)
                elif v1 == v2:
                    similarities.append(1.0)
                else:
                    similarities.append(0.0)

            return np.mean(similarities)

        # 排序并返回最相似的 k 个
        scored = []
        for memory in self.memories:
            score = state_similarity(current_state, memory["state"])
            scored.append((score, memory))

        scored.sort(reverse=True, key=lambda x: x[0])
        return [m for _, m in scored[:k]]

    def update_outcome(self, timestamp: int, outcome: float) -> None:
        """更新经验的结局（用于事后学习）."""
        for memory in self.memories:
            if memory["timestamp"] == timestamp:
                memory["outcome"] = outcome
                break
