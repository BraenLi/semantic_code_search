"""纠缠矩阵可视化.

提供纠缠矩阵热力图、纠缠熵时间序列等可视化功能.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import numpy as np
from numpy.typing import NDArray

# 尝试导入 matplotlib，如果不可用则使用降级模式
try:
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class EntanglementVisualizer:
    """
    纠缠矩阵可视化器.

    功能:
    - 绘制纠缠矩阵热力图
    - 绘制纠缠熵时间序列
    - 绘制资产网络图
    """

    def __init__(self, symbol_labels: Optional[List[str]] = None):
        """
        初始化可视化器.

        Args:
            symbol_labels: 资产标签列表，如 ["AAPL", "GOOGL", "MSFT"]
        """
        self.symbol_labels = symbol_labels or []
        self.entropy_history: List[float] = []
        self.matrix_history: List[NDArray[np.float64]] = []

    def plot_entanglement_matrix(
        self,
        matrix: NDArray[np.float64],
        title: str = "量子纠缠矩阵",
        save_path: Optional[str] = None,
        show: bool = True,
    ) -> Optional[Any]:
        """
        绘制纠缠矩阵热力图.

        Args:
            matrix: NxN 纠缠矩阵
            title: 图表标题
            save_path: 保存路径（可选）
            show: 是否显示图表

        Returns:
            figure 对象（如果保存则不返回）
        """
        if not HAS_MATPLOTLIB:
            return self._text_heatmap(matrix, title)

        n = matrix.shape[0]
        labels = self.symbol_labels[:n] if self.symbol_labels else [f"Asset {i}" for i in range(n)]

        fig, ax = plt.subplots(figsize=(10, 8))

        # 创建热力图
        im = ax.imshow(matrix, cmap='coolwarm', vmin=0, vmax=1)

        # 设置标签
        ax.set_xticks(np.arange(n))
        ax.set_yticks(np.arange(n))
        ax.set_xticklabels(labels, rotation=45, ha='right')
        ax.set_yticklabels(labels)

        # 旋转标签避免重叠
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

        # 添加颜色条
        cbar = ax.figure.colorbar(im, ax=ax)
        cbar.ax.set_ylabel('纠缠强度', rotation=-90, va="bottom", labelpad=20)

        # 添加数值标签
        for i in range(n):
            for j in range(n):
                text = ax.text(j, i, f'{matrix[i, j]:.3f}',
                              ha="center", va="center", color="black", fontsize=8)

        ax.set_title(title)
        fig.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            return None

        if show:
            plt.show()
            return None

        return fig

    def _text_heatmap(self, matrix: NDArray[np.float64], title: str) -> str:
        """文本模式热力图（降级方案）."""
        n = matrix.shape[0]
        labels = self.symbol_labels[:n] if self.symbol_labels else [f"A{i}" for i in range(n)]

        # 表头
        header = " " * 8 + "".join(f"{l:>8}" for l in labels)
        lines = [header, "-" * len(header)]

        # 数据行
        for i, row in enumerate(matrix):
            row_str = f"{labels[i]:>8}" + "".join(f"{v:>8.3f}" for v in row)
            lines.append(row_str)

        return f"\n{title}\n" + "\n".join(lines)

    def plot_entropy_history(
        self,
        entropy_values: Optional[List[float]] = None,
        title: str = "纠缠熵时间序列",
        save_path: Optional[str] = None,
        show: bool = True,
    ) -> Optional[Any]:
        """
        绘制纠缠熵时间序列.

        纠缠熵衡量系统的复杂度：
        - 低熵：系统处于有序状态
        - 高熵：系统处于无序/复杂状态
        - 熵的突变：可能预示市场结构变化

        Args:
            entropy_values: 熵值列表（如果不提供则使用内部历史）
            title: 图表标题
            save_path: 保存路径
            show: 是否显示

        Returns:
            figure 对象
        """
        values = entropy_values or self.entropy_history

        if not values:
            print("没有熵值数据可绘制")
            return None

        if not HAS_MATPLOTLIB:
            return self._text_line_chart(values, "时间步", "熵值", title)

        fig, ax = plt.subplots(figsize=(12, 6))

        x = range(len(values))
        ax.plot(x, values, 'b-', linewidth=2, marker='o', markersize=3)

        # 添加平均值线
        avg = np.mean(values)
        ax.axhline(y=avg, color='r', linestyle='--', alpha=0.7, label=f'平均值：{avg:.4f}')

        # 添加标准差带
        std = np.std(values)
        ax.fill_between(x, avg - std, avg + std, alpha=0.3, color='blue', label=f'±1σ: {std:.4f}')

        ax.set_xlabel('时间步')
        ax.set_ylabel('冯·诺依曼熵')
        ax.set_title(title)
        ax.legend()
        ax.grid(True, alpha=0.3)

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            return None

        if show:
            plt.show()
            return None

        return fig

    def plot_network_graph(
        self,
        matrix: NDArray[np.float64],
        threshold: float = 0.3,
        title: str = "资产纠缠网络",
        save_path: Optional[str] = None,
        show: bool = True,
    ) -> Optional[Any]:
        """
        绘制资产纠缠网络图.

        只显示超过阈值的纠缠连接.

        Args:
            matrix: 纠缠矩阵
            threshold: 显示连接的阈值
            title: 图表标题
            save_path: 保存路径
            show: 是否显示

        Returns:
            figure 对象
        """
        if not HAS_MATPLOTLIB:
            return self._text_network(matrix, threshold, title)

        try:
            import networkx as nx
        except ImportError:
            return self._text_network(matrix, threshold, title)

        n = matrix.shape[0]
        labels = self.symbol_labels[:n] if self.symbol_labels else [f"A{i}" for i in range(n)]

        # 创建图
        G = nx.Graph()

        # 添加节点
        for i in range(n):
            G.add_node(i, label=labels[i])

        # 添加边（只添加超过阈值的）
        for i in range(n):
            for j in range(i + 1, n):
                if matrix[i, j] > threshold:
                    G.add_edge(i, j, weight=matrix[i, j])

        fig, ax = plt.subplots(figsize=(12, 10))

        # 使用弹簧布局
        pos = nx.spring_layout(G, k=2/n**0.5, seed=42)

        # 绘制节点
        node_sizes = [1000 + 500 * G.degree[i] for i in range(n)]
        nx.draw_networkx_nodes(G, pos, node_size=node_sizes,
                              node_color='lightblue', alpha=0.8, ax=ax)

        # 绘制边（根据权重设置宽度）
        edges = G.edges()
        weights = [G[u][v]['weight'] * 5 for u, v in edges]
        nx.draw_networkx_edges(G, pos, width=weights, alpha=0.6, ax=ax)

        # 绘制标签
        nx.draw_networkx_labels(G, pos,
                               labels={i: labels[i] for i in range(n)},
                               font_size=10, ax=ax)

        # 添加边权重标签
        edge_labels = {(i, j): f"{matrix[i,j]:.2f}" for i, j in edges if matrix[i,j] > threshold}
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels,
                                    font_size=8, ax=ax)

        ax.set_title(title)
        ax.axis('off')
        fig.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            return None

        if show:
            plt.show()
            return None

        return fig

    def _text_network(self, matrix: NDArray[np.float64], threshold: float, title: str) -> str:
        """文本模式网络图."""
        n = matrix.shape[0]
        labels = self.symbol_labels[:n] if self.symbol_labels else [f"A{i}" for i in range(n)]

        lines = [f"\n{title}", "=" * 40]
        lines.append(f"阈值：{threshold:.2f}")
        lines.append("-" * 40)

        connections = []
        for i in range(n):
            for j in range(i + 1, n):
                if matrix[i, j] > threshold:
                    connections.append(f"  {labels[i]} -- {labels[j]}: {matrix[i,j]:.3f}")

        if connections:
            lines.extend(connections)
        else:
            lines.append("  无超过阈值的连接")

        return "\n".join(lines)

    def record_history(
        self,
        matrix: NDArray[np.float64],
        entropy: Optional[float] = None,
    ) -> None:
        """
        记录历史数据.

        Args:
            matrix: 纠缠矩阵
            entropy: 纠缠熵（可选，如果不提供则自动计算）
        """
        self.matrix_history.append(matrix.copy())

        if entropy is None:
            # 计算冯·诺依曼熵
            eigenvalues = np.linalg.eigvalsh(matrix)
            eigenvalues = eigenvalues[eigenvalues > 1e-10]  # 过滤接近零的特征值
            entropy = -np.sum(eigenvalues * np.log2(eigenvalues + 1e-10))

        self.entropy_history.append(float(entropy))

    def get_latest_matrix(self) -> Optional[NDArray[np.float64]]:
        """获取最新的纠缠矩阵."""
        return self.matrix_history[-1] if self.matrix_history else None

    def get_latest_entropy(self) -> Optional[float]:
        """获取最新的纠缠熵."""
        return self.entropy_history[-1] if self.entropy_history else None

    def clear_history(self) -> None:
        """清空历史记录."""
        self.matrix_history.clear()
        self.entropy_history.clear()
