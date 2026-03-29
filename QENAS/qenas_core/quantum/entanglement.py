"""量子纠缠计算模块."""

from dataclasses import dataclass
import numpy as np
from numpy.typing import NDArray
from typing import Optional


@dataclass
class DensityMatrix:
    """
    量子密度矩阵表示.

    用于描述量子系统的状态，支持：
    - 从协方差矩阵构建
    - 特征值分解
    - 偏迹操作
    - 冯·诺依曼熵计算
    """

    matrix: NDArray[np.float64]
    eigenvalues: Optional[NDArray[np.float64]] = None

    def __post_init__(self):
        """验证和初始化."""
        # 验证矩阵是厄米的（对称的，因为是实数）
        if not np.allclose(self.matrix, self.matrix.T):
            raise ValueError("Density matrix must be symmetric (Hermitian)")

        # 验证迹为 1
        trace = np.trace(self.matrix)
        if not np.isclose(trace, 1.0):
            # 归一化
            self.matrix = self.matrix / trace

        # 计算特征值
        self.eigenvalues = np.linalg.eigvalsh(self.matrix)

        # 验证特征值非负（半正定）
        if np.any(self.eigenvalues < -1e-10):
            raise ValueError("Density matrix must be positive semi-definite")

    @property
    def dim(self) -> int:
        """矩阵维度."""
        return self.matrix.shape[0]

    @classmethod
    def from_covariance(cls, cov: NDArray[np.float64]) -> "DensityMatrix":
        """
        从协方差矩阵构建密度矩阵.

        Args:
            cov: 协方差矩阵

        Returns:
            归一化的密度矩阵
        """
        trace = np.trace(cov)
        if trace == 0:
            raise ValueError("Covariance matrix has zero trace")

        rho = cov / trace
        return cls(matrix=rho)

    def von_neumann_entropy(self) -> float:
        """
        计算冯·诺依曼熵.

        S(ρ) = -Tr(ρ log₂ ρ) = -Σ λᵢ log₂ λᵢ

        Returns:
            熵值（以比特为单位）
        """
        if self.eigenvalues is None:
            self.eigenvalues = np.linalg.eigvalsh(self.matrix)

        # 过滤掉零特征值（避免 log(0)）
        nonzero = self.eigenvalues[self.eigenvalues > 1e-15]
        return float(-np.sum(nonzero * np.log2(nonzero)))

    def partial_trace(self, keep: list[int]) -> "DensityMatrix":
        """
        执行偏迹操作，保留指定子系统.

        Args:
            keep: 要保留的子空间索引列表

        Returns:
            约化密度矩阵
        """
        if len(keep) == self.dim:
            return DensityMatrix(matrix=self.matrix.copy())

        if len(keep) == 1:
            # 简化情况：只保留一个自由度
            idx = keep[0]
            return DensityMatrix(matrix=np.array([[self.matrix[idx, idx]]]))

        # 一般情况：提取子矩阵
        keep_array = np.array(keep)
        sub_matrix = self.matrix[np.ix_(keep_array, keep_array)]

        # 归一化
        trace = np.trace(sub_matrix)
        if trace > 0:
            sub_matrix = sub_matrix / trace

        return DensityMatrix(matrix=sub_matrix)

    def quantum_mutual_information(self, subsystem_a: int, subsystem_b: int) -> float:
        """
        计算两个子系统间的量子互信息.

        I(A:B) = S(A) + S(B) - S(AB)

        Args:
            subsystem_a: 子系统 A 的索引
            subsystem_b: 子系统 B 的索引

        Returns:
            量子互信息值
        """
        # S(AB) - 整个系统的熵
        s_ab = self.von_neumann_entropy()

        # S(A) - 子系统 A 的熵
        rho_a = self.partial_trace([subsystem_a])
        s_a = rho_a.von_neumann_entropy()

        # S(B) - 子系统 B 的熵
        rho_b = self.partial_trace([subsystem_b])
        s_b = rho_b.von_neumann_entropy()

        return s_a + s_b - s_ab


class QuantumEntanglementCalculator:
    """
    量子纠缠计算器.

    将资产收益率序列转换为量子纠缠度量.
    """

    def __init__(self):
        self.entanglement_matrix: Optional[NDArray[np.float64]] = None
        self.entropy_history: list[float] = []

    def compute_density_matrix(self, returns: NDArray[np.float64]) -> DensityMatrix:
        """
        从资产收益率计算密度矩阵.

        Args:
            returns: 收益率矩阵 (n_samples, n_assets)

        Returns:
            密度矩阵
        """
        if returns.ndim != 2:
            raise ValueError("Returns must be 2D array (n_samples, n_assets)")

        # 计算协方差矩阵
        cov = np.cov(returns.T)

        # 归一化为密度矩阵
        return DensityMatrix.from_covariance(cov)

    def compute_entanglement_entropy(self, returns: NDArray[np.float64]) -> float:
        """
        计算纠缠熵（冯·诺依曼熵）.

        Args:
            returns: 收益率矩阵

        Returns:
            纠缠熵值
        """
        rho = self.compute_density_matrix(returns)
        entropy = rho.von_neumann_entropy()
        self.entropy_history.append(entropy)
        return entropy

    def compute_entanglement_matrix(self, returns: NDArray[np.float64]) -> NDArray[np.float64]:
        """
        计算两两资产间的纠缠强度矩阵.

        Args:
            returns: 收益率矩阵 (n_samples, n_assets)

        Returns:
            纠缠矩阵 (n_assets, n_assets)
        """
        n_assets = returns.shape[1]

        # 计算密度矩阵
        rho = self.compute_density_matrix(returns)

        # 初始化纠缠矩阵
        self.entanglement_matrix = np.zeros((n_assets, n_assets))

        # 计算两两纠缠强度
        for i in range(n_assets):
            for j in range(i + 1, n_assets):
                mutual_info = rho.quantum_mutual_information(i, j)
                self.entanglement_matrix[i, j] = mutual_info
                self.entanglement_matrix[j, i] = mutual_info

        return self.entanglement_matrix

    def detect_decoherence_spike(
        self,
        threshold: float = 2.0,
        lookback: int = 20
    ) -> bool:
        """
        检测退相干事件（纠缠熵突变）.

        Args:
            threshold: 阈值（标准差倍数）
            lookback: 回溯窗口大小

        Returns:
            是否检测到退相干事件
        """
        if len(self.entropy_history) < lookback + 1:
            return False

        recent = self.entropy_history[-1]
        history = np.array(self.entropy_history[-lookback:-1])

        mean = np.mean(history)
        std = np.std(history)

        if std == 0:
            return False

        # 检测是否超过阈值
        z_score = abs(recent - mean) / std
        return z_score > threshold

    def reset(self) -> None:
        """重置计算器状态."""
        self.entanglement_matrix = None
        self.entropy_history = []
