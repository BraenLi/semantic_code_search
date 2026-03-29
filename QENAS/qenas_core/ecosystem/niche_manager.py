"""生态位子策略群模块."""

import numpy as np
from numpy.typing import NDArray
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import random


class TimeNiche(Enum):
    """时间生态位."""
    MICRO = "micro"      # 毫秒 - 秒级
    SHORT = "short"      # 分钟 - 小时级
    MEDIUM = "medium"    # 日 - 周级
    LONG = "long"        # 周 - 月级


class SignalNiche(Enum):
    """信号生态位."""
    MOMENTUM = "momentum"
    REVERSION = "reversion"
    VOLATILITY = "volatility"
    SENTIMENT = "sentiment"
    MACRO = "macro"


class SpaceNiche(Enum):
    """空间/资产生态位."""
    TECH = "tech"
    FINANCE = "finance"
    ENERGY = "energy"
    HEALTH = "health"
    CONSUMER = "consumer"
    MATERIALS = "materials"
    UTILITIES = "utilities"
    REAL_ESTATE = "real_estate"


@dataclass
class StrategySpecies:
    """
    策略物种表示.

    每个策略物种占据独特的生态位，具有：
    - 生态位坐标（时间、信号、空间）
    - 适应度分数
    - 资金分配比例
    - 基因编码（策略参数）
    """

    id: int
    time_niche: TimeNiche
    signal_niche: SignalNiche
    space_niche: SpaceNiche
    fitness: float = 1.0
    capital_allocation: float = 0.0
    genome: NDArray[np.float64] = field(default_factory=lambda: np.random.randn(50))
    age: int = 0
    performance_history: list[float] = field(default_factory=list)

    def to_dict(self) -> dict:
        """转换为字典."""
        return {
            "id": self.id,
            "time_niche": self.time_niche.value,
            "signal_niche": self.signal_niche.value,
            "space_niche": self.space_niche.value,
            "fitness": self.fitness,
            "capital_allocation": self.capital_allocation,
            "age": self.age,
            "genome_size": len(self.genome),
        }


class NicheManager:
    """
    生态位管理器.

    负责：
    - 初始化策略物种群
    - 计算生态位重叠
    - 管理策略进化
    - 资金分配
    """

    def __init__(
        self,
        n_species: int = 100,
        genome_size: int = 50,
    ):
        self.n_species = n_species
        self.genome_size = genome_size
        self.population: list[StrategySpecies] = []
        self.generation = 0

    def initialize_ecosystem(self, seed: Optional[int] = None) -> list[StrategySpecies]:
        """
        初始化策略生态系统.

        Args:
            seed: 随机种子

        Returns:
            策略物种种群
        """
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        self.population = []

        for i in range(self.n_species):
            species = StrategySpecies(
                id=i,
                time_niche=random.choice(list(TimeNiche)),
                signal_niche=random.choice(list(SignalNiche)),
                space_niche=random.choice(list(SpaceNiche)),
                fitness=1.0,
                capital_allocation=1.0 / self.n_species,
                genome=np.random.randn(self.genome_size),
                age=0,
            )
            self.population.append(species)

        return self.population

    def compute_niche_overlap(
        self,
        target: StrategySpecies,
        population: Optional[list[StrategySpecies]] = None
    ) -> float:
        """
        计算目标策略与其他策略的生态位重叠度.

        Args:
            target: 目标策略物种
            population: 种群（默认为当前种群）

        Returns:
            生态位重叠度 (0-1)
        """
        pop = population or self.population
        overlaps = []

        for other in pop:
            if other.id == target.id:
                continue

            # 计算各维度重叠
            time_overlap = 1.0 if target.time_niche == other.time_niche else 0.0
            signal_overlap = 1.0 if target.signal_niche == other.signal_niche else 0.0
            space_overlap = 1.0 if target.space_niche == other.space_niche else 0.0

            # 加权平均
            total_overlap = (time_overlap + signal_overlap + space_overlap) / 3
            overlaps.append(total_overlap)

        return np.mean(overlaps) if overlaps else 0.0

    def compute_genome_similarity(
        self,
        genome1: NDArray[np.float64],
        genome2: NDArray[np.float64]
    ) -> float:
        """
        计算两个基因组的相似度.

        Args:
            genome1: 基因组 1
            genome2: 基因组 2

        Returns:
            相似度 (0-1)
        """
        # 使用余弦相似度
        norm1 = np.linalg.norm(genome1)
        norm2 = np.linalg.norm(genome2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        cosine_sim = np.dot(genome1, genome2) / (norm1 * norm2)
        return float((cosine_sim + 1) / 2)  # 归一化到 [0, 1]

    def evolve_ecosystem(
        self,
        performance_data: dict[int, dict],
        survival_rate: float = 0.7,
        mutation_rate: float = 0.1,
        mutation_strength: float = 0.5,
    ) -> list[StrategySpecies]:
        """
        基于适应度的策略进化.

        Args:
            performance_data: 各策略的绩效数据
            survival_rate: 存活率
            mutation_rate: 变异率
            mutation_strength: 变异强度

        Returns:
            新一代种群
        """
        if not self.population:
            raise ValueError("Population is empty. Call initialize_ecosystem first.")

        # 1. 更新适应度
        self._update_fitness(performance_data)

        # 2. 自然选择：按适应度排序
        sorted_population = sorted(self.population, key=lambda x: x.fitness, reverse=True)
        n_survivors = int(len(sorted_population) * survival_rate)
        survivors = sorted_population[:n_survivors]

        # 3. 繁殖：产生新策略
        n_offspring = len(self.population) - n_survivors
        offspring = self._breed(survivors, n_offspring, mutation_rate, mutation_strength)

        # 4. 更新年龄
        for species in survivors:
            species.age += 1

        # 5. 重新分配资金
        self._allocate_capital()

        # 6. 更新种群
        self.population = survivors + offspring
        self.generation += 1

        return self.population

    def _update_fitness(self, performance_data: dict[int, dict]) -> None:
        """
        更新策略适应度.

        适应度 = 夏普比率 × (1 - 生态位重叠惩罚)
        """
        for species in self.population:
            # 获取绩效数据
            perf = performance_data.get(species.id, {})
            sharpe = perf.get("sharpe", 0.0)

            # 计算生态位重叠惩罚
            niche_overlap = self.compute_niche_overlap(species)
            penalty = 0.5 * niche_overlap

            # 调整后的适应度
            species.fitness = max(0.1, sharpe * (1 - penalty))

            # 记录绩效历史
            species.performance_history.append(sharpe)

    def _breed(
        self,
        parents: list[StrategySpecies],
        n_offspring: int,
        mutation_rate: float,
        mutation_strength: float,
    ) -> list[StrategySpecies]:
        """
        繁殖新策略.

        Args:
            parents: 父本种群
            n_offspring: 后代数量
            mutation_rate: 变异率
            mutation_strength: 变异强度

        Returns:
            后代种群
        """
        offspring = []
        max_id = max(s.id for s in self.population) + 1

        for _ in range(n_offspring):
            # 选择两个父本（基于适应度的轮盘赌选择）
            parent1, parent2 = self._select_parents(parents)

            # 交叉
            child_genome = self._crossover(parent1.genome, parent2.genome)

            # 变异
            child_genome = self._mutate(child_genome, mutation_rate, mutation_strength)

            # 生态位继承（从父本中随机选择一个）
            if random.random() < 0.5:
                time_niche = parent1.time_niche
                signal_niche = parent1.signal_niche
                space_niche = parent1.space_niche
            else:
                time_niche = parent2.time_niche
                signal_niche = parent2.signal_niche
                space_niche = parent2.space_niche

            child = StrategySpecies(
                id=max_id + len(offspring),
                time_niche=time_niche,
                signal_niche=signal_niche,
                space_niche=space_niche,
                fitness=1.0,
                capital_allocation=0.0,
                genome=child_genome,
                age=0,
            )
            offspring.append(child)

        return offspring

    def _select_parents(
        self,
        parents: list[StrategySpecies]
    ) -> tuple[StrategySpecies, StrategySpecies]:
        """基于适应度的轮盘赌选择."""
        fitnesses = np.array([p.fitness for p in parents])
        fitnesses = np.maximum(fitnesses, 0.01)  # 确保正数
        probabilities = fitnesses / np.sum(fitnesses)

        indices = np.random.choice(len(parents), size=2, replace=True, p=probabilities)
        return parents[indices[0]], parents[indices[1]]

    def _crossover(
        self,
        genome1: NDArray[np.float64],
        genome2: NDArray[np.float64]
    ) -> NDArray[np.float64]:
        """均匀交叉."""
        mask = np.random.rand(len(genome1)) > 0.5
        return np.where(mask, genome1, genome2)

    def _mutate(
        self,
        genome: NDArray[np.float64],
        rate: float,
        strength: float
    ) -> NDArray[np.float64]:
        """高斯变异."""
        mask = np.random.rand(len(genome)) < rate
        mutation = np.random.randn(len(genome)) * strength
        mutated = genome.copy()
        mutated[mask] += mutation[mask]
        return mutated

    def _allocate_capital(self) -> None:
        """
        基于适应度的资金分配（Softmax）.

        考虑生态位独特性进行调整.
        """
        if not self.population:
            return

        # 计算调整后的适应度
        adjusted_fitnesses = []
        for species in self.population:
            niche_uniqueness = 1 - self.compute_niche_overlap(species)
            adjusted = species.fitness * (0.5 + 0.5 * niche_uniqueness)
            adjusted_fitnesses.append(adjusted)

        # Softmax 分配
        fitnesses = np.array(adjusted_fitnesses)
        fitnesses = np.maximum(fitnesses, 0.01)  # 确保正数
        exp_fitness = np.exp(fitnesses - np.max(fitnesses))  # 数值稳定
        allocations = exp_fitness / np.sum(exp_fitness)

        # 更新资金分配
        for i, species in enumerate(self.population):
            species.capital_allocation = float(allocations[i])

    def get_population_stats(self) -> dict:
        """获取种群统计信息."""
        if not self.population:
            return {}

        return {
            "generation": self.generation,
            "population_size": len(self.population),
            "avg_fitness": np.mean([s.fitness for s in self.population]),
            "max_fitness": max(s.fitness for s in self.population),
            "min_fitness": min(s.fitness for s in self.population),
            "time_niche_diversity": len(set(s.time_niche for s in self.population)),
            "signal_niche_diversity": len(set(s.signal_niche for s in self.population)),
            "space_niche_diversity": len(set(s.space_niche for s in self.population)),
            "total_capital_allocated": sum(s.capital_allocation for s in self.population),
        }
