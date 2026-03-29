# QENAS 开发日志

## 项目信息

- **项目名称**: QENAS (量子纠缠生态位自适应网络)
- **项目位置**: `/Users/lgen/Users/lgen/QENAS`
- **开始日期**: 2026-03-30
- **状态**: 阶段 4 完成 - 可视化模块

## 配置确认

- **数据源**: A 股 + 美股 + 港股
- **时间尺度**: 日级 (低频)
- **神经形态**: 完整实现 SNN

---

## 开发记录

### 2026-03-30 - 项目启动与核心模块完成

#### 今日完成 (阶段 1)

**项目基础设施:**
- [x] 创建项目目录结构
- [x] 创建 pyproject.toml (依赖配置，uv 管理)
- [x] 创建 README.md
- [x] 创建 .gitignore
- [x] 创建开发日志 QENAS_DEVLOG.md
- [x] 创建 uv.lock

**核心模块 - qenas_core:**
- [x] `qenas_core/strategies/base.py` - 策略基类、订单、持仓、K 线数据模型
- [x] `qenas_core/quantum/entanglement.py` - 量子纠缠计算（密度矩阵、冯·诺依曼熵）
- [x] `qenas_core/ecosystem/niche_manager.py` - 生态位子策略群管理
- [x] `qenas_core/neuromorphic/snn.py` - 脉冲神经网络（LIF 神经元、STDP 学习）
- [x] `qenas_core/emergent/decision.py` - 涌现决策引擎（Kuramoto 振子）
- [x] `qenas_core/strategies/qenas_strategy.py` - QENAS 主策略类

**数据模块 - qenas_data:**
- [x] `qenas_data/feeders/base.py` - 数据源基类
- [x] `qenas_data/storage/cache.py` - 数据缓存管理

**回测模块 - qenas_backtest:**
- [x] `qenas_backtest/engine.py` - 回测引擎
- [x] `qenas_backtest/metrics.py` - 回测指标

**测试模块 - tests:**
- [x] `tests/test_core.py` - 核心模块单元测试

#### 测试结果 (阶段 1)
```
======================== 13 passed, 2 warnings ========================
```

### 2026-03-30 - 阶段 2: 数据源模块 + 事件驱动架构

#### 今日完成 (阶段 2)

**数据源模块 - qenas_data:**

1. **基础数据模型扩展** (`qenas_data/feeders/base.py`):
   - `EventType` - 事件类型枚举 (宏观经济、公司事件、地缘政治等)
   - `EventImpact` - 事件影响级别 (LOW, MEDIUM, HIGH, CRITICAL)
   - `EventData` - 事件数据结构 (支持情感评分、影响范围)
   - `KlineData` - 扩展支持事件列表

2. **Yahoo Finance 数据源** (`qenas_data/feeders/yahoo_feeder.py`):
   - 美股数据 (AAPL, GOOGL, MSFT)
   - 港股数据 (0700.HK, 9988.HK)
   - ETF 数据 (SPY, QQQ)
   - 事件数据：财报、分红、拆股

3. **A 股数据源** (`qenas_data/feeders/ashare_feeder.py`):
   - 沪深 A 股 (000001.SZ, 600000.SH)
   - 支持 akshare 和 baostock 两种数据源
   - 事件数据：财报、分红、宏观经济数据

4. **事件处理器** (`qenas_data/processors/event_processor.py`):
   - `EventProcessor` - 事件处理核心类
   - 事件信号生成
   - 事件衰减跟踪
   - 神经形态编码
   - 事件集群检测
   - 纠缠矩阵调整

**测试模块:**
- [x] `tests/test_data_sources.py` - 数据源和事件处理器测试 (10 个测试)

#### 测试结果 (阶段 2)
```
======================== 10 passed, 16 warnings ========================
```

#### 事件驱动架构设计

**真实世界事件作为数据源的价值：**

QENAS 不仅使用传统的 K 线数据，还将真实世界事件作为重要数据源整合到决策流程中：

**事件类型覆盖：**
| 类型 | 示例 | 影响 |
|------|------|------|
| 宏观经济 | GDP、CPI、利率决议 | 市场整体 |
| 公司事件 | 财报、分红、并购 | 个股 |
| 地缘政治 | 贸易战、选举、冲突 | 行业/地区 |
| 自然灾害 | 地震、飓风、疫情 | 供应链/商品 |
| 政策法规 | 行业监管、税收 | 结构性影响 |

**事件整合方式：**
1. **事件嵌入到生态位**: 创建"事件驱动"策略物种，专门交易事件信号
2. **神经形态输入**: 事件编码为脉冲信号输入到不同脑区
   - 前额叶皮层：风险相关事件
   - 边缘系统：情绪/情感事件
   - 小脑：高频短期事件
3. **调整纠缠矩阵**: 重大事件改变资产间的相关性结构

**核心方法：**
- `EventProcessor.process_event()` - 生成交易信号
- `EventProcessor.encode_events_for_neuromorphic()` - 神经形态编码
- `EventProcessor.adjust_entanglement_for_events()` - 纠缠矩阵调整
- `EventProcessor.detect_event_cluster()` - 事件集群检测

---

## 项目结构 (更新后)

```
QENAS/
├── qenas_core/            # 核心策略引擎
│   ├── quantum/           # 量子纠缠层
│   ├── ecosystem/         # 生态位子策略群
│   ├── neuromorphic/      # 神经形态处理器
│   ├── emergent/          # 涌现决策引擎
│   └── strategies/        # 策略实现
├── qenas_data/            # 数据服务
│   ├── feeders/
│   │   ├── base.py        # 数据源基类 + 事件数据模型
│   │   ├── yahoo_feeder.py # Yahoo Finance (美股/港股)
│   │   └── ashare_feeder.py # A 股数据 (akshare/baostock)
│   ├── storage/
│   │   └── cache.py       # 数据缓存
│   └── processors/
│       └── event_processor.py # 事件处理器
├── qenas_backtest/        # 回测引擎
├── tests/
│   ├── test_core.py       # 核心模块测试 (13 测试)
│   └── test_data_sources.py # 数据源测试 (10 测试)
├── examples/
│   └── qenas_demo.py      # 示例脚本
├── pyproject.toml
├── README.md
└── QENAS_DEVLOG.md
```

---

## 技术讨论：K 线数据 vs 事件数据

### 单纯 K 线数据的局限性

1. **滞后性**: K 线只反映已经发生的价格变动
2. **缺乏因果**: 知道"是什么"但不知道"为什么"
3. **噪声敏感**: 难以区分噪声和真实信号
4. **黑天鹅盲区**: 无法预测突发事件

### 事件数据的价值

1. **前瞻信号**: 事件往往先于价格变动
2. **因果解释**: 提供市场变动的根本原因
3. **情感维度**: 事件情感分析提供额外信号
4. **结构性变化**: 重大事件可能改变市场结构

### QENAS 的多模态数据融合

```
┌─────────────────────────────────────────────────────────────┐
│                    QENAS 数据融合架构                        │
├─────────────────────────────────────────────────────────────┤
│  K 线数据 → 量子纠缠层 → 资产关联性                            │
│                                                             │
│  事件数据 → 事件处理器 → 神经形态层 → 情感/风险信号          │
│                                                             │
│  ↓ 融合 ↓                                                    │
│                                                             │
│  生态位子策略群 → 涌现决策引擎 → 交易决策                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 下一步计划

1. **阶段 5**: Web 服务与实时推送
   - [ ] FastAPI 后端架构设计
   - [ ] REST API 接口实现
   - [ ] WebSocket 实时数据推送
   - [ ] Vue3 策略控制面板
   - [ ] 实时纠缠矩阵监控

---

## 里程碑

- [x] M0 (2026-03-30): 项目基础 + 核心模块框架完成 ✅
- [x] M1 (2026-03-30): 数据源模块 + 事件驱动架构完成 ✅
- [x] M2 (2026-03-30): QENAS 策略与事件集成 ✅
- [x] M3 (2026-03-30): 可视化模块完成 ✅
- [ ] M4 (2 周): 完整回测系统 + Web 服务

---

### 2026-03-30 - 阶段 4: 可视化模块

#### 今日完成 (阶段 4)

**可视化模块 - qenas_viz/:**

1. **纠缠矩阵可视化** (`qenas_viz/entanglement_viz.py`):
   - `EntanglementVisualizer` 类
   - `plot_entanglement_matrix()` - 纠缠矩阵热力图
   - `plot_entropy_history()` - 纠缠熵时间序列
   - `plot_network_graph()` - 资产纠缠网络图
   - 支持文本模式降级输出（无 matplotlib 环境）

2. **事件时间线可视化** (`qenas_viz/event_viz.py`):
   - `EventTimelineVisualizer` 类
   - `plot_timeline()` - 事件时间线（按类型分组）
   - `plot_type_distribution()` - 事件类型分布饼图
   - `plot_impact_distribution()` - 影响级别柱状图
   - `plot_sentiment_timeline()` - 情感变化时间线
   - `get_event_summary()` - 事件摘要统计

3. **业绩可视化** (`qenas_viz/performance_viz.py`):
   - `PerformanceVisualizer` 类
   - `BacktestResult` 数据类
   - `plot_equity_curve()` - 权益曲线图
   - `plot_drawdown()` - 回撤分析图
   - `plot_returns_distribution()` - 收益率分布 + Q-Q 图
   - `plot_rolling_metrics()` - 滚动夏普/波动率/收益

4. **统一仪表板** (`qenas_viz/dashboard.py`):
   - `QENASDashboard` 类整合所有可视化组件
   - `update_entanglement()` - 更新纠缠数据
   - `add_events()` - 添加事件数据
   - `set_backtest_results()` - 设置回测结果
   - `print_status()` - 打印状态报告
   - `save_all_figures()` - 批量保存图表

**测试模块 - tests/test_viz.py:**
- [x] 18 个可视化测试全部通过

#### 测试结果 (阶段 4)
```
======================== 48 passed, 93 warnings ========================
```
其中：
- 核心模块测试：13 个
- 数据源测试：10 个
- 事件集成测试：7 个
- 可视化测试：18 个

#### 示例脚本 (2026-03-30)

**新增可视化集成示例** (`examples/qenas_visualization_demo.py`):
- 多资产 K 线数据生成（考虑资产间相关性）
- 事件数据生成（类型、影响级别、情感分数）
- 回测结果与可视化仪表板集成
- 文本模式降级输出演示
- 展示纠缠矩阵、事件时间线、业绩可视化功能

**运行示例**:
```bash
uv run python examples/qenas_visualization_demo.py
```

**输出示例**:
```
当前纠缠矩阵
            AAPL   GOOGL    MSFT
---------------------------------
    AAPL   0.524   0.104   0.103
   GOOGL   0.104   0.607   0.148
    MSFT   0.103   0.148   0.621

事件时间线
  o [2024-01-07] macro_economic: Macro Economic - MSFT [-0.2]
  s [2024-02-06] macro_economic: Macro Economic - MSFT [-0.4]
  ^ [2024-03-30] geopolitical: Geopolitical - GOOGL [-0.0]

权益曲线摘要
  初始权益：100000.00
  最终权益：87826.45
  总收益率：-12.17%
  夏普比率：-2.49
  最大回撤：20.56%
```

#### 可视化功能说明 (补充)

**1. 纠缠矩阵热力图:**
```
        AAPL     GOOGL      MSFT
---------------------------------
AAPL    0.330    0.100    0.100
GOOGL   0.100    0.330    0.100
MSFT    0.100    0.100    0.330
```

**2. 事件时间线:**
- 按事件类型分组显示
- 影响级别决定点大小
- 情感分数决定颜色

**3. 权益曲线:**
- 策略 vs 基准对比
- 标注最大值/最小值
- 集成关键指标（夏普、回撤、总收益）

**4. 文本模式降级:**
- 在无 matplotlib 环境下自动切换到文本输出
- 保持核心信息展示

#### 今日完成 (阶段 3)

**核心策略集成 - qenas_core/strategies/qenas_strategy.py:**

1. **导入 EventProcessor**:
   - 添加 `EventProcessor` 和 `EventSignal` 导入
   - 添加 `EventData` 和 `EventType` 导入

2. **初始化事件处理器**:
   ```python
   self.event_processor = EventProcessor()
   ```

3. **扩展 on_bar 方法流程**:
   - 新增步骤 3: 处理 K 线附带的事件
   - 新增步骤 5: 整合事件信号到子策略信号
   - 新增步骤 6: 神经形态处理（整合事件）

4. **新增方法**:
   - `_process_kline_events()` - 处理 K 线附带事件，生成事件信号
   - `_integrate_event_signal()` - 将事件信号整合到策略信号中
   - `_process_neuromorphic()` - 扩展支持事件编码输入

**策略基类扩展 - qenas_core/strategies/base.py:**
- `Kline` 类添加 `events` 属性，支持附带事件列表

**测试模块 - tests/test_event_integration.py:**
- [x] `test_process_kline_with_events` - 测试带事件的 K 线处理
- [x] `test_process_high_impact_event` - 测试高影响事件处理
- [x] `test_event_affects_entanglement` - 测试事件对纠缠矩阵的影响
- [x] `test_neuromorphic_event_encoding` - 测试神经形态编码
- [x] `test_event_signal_integration` - 测试事件信号整合
- [x] `test_detect_event_cluster` - 测试事件集群检测
- [x] `test_multiple_event_clusters` - 测试多集群检测

#### 测试结果 (阶段 3)
```
======================== 30 passed, 43 warnings ========================
```
其中：
- 核心模块测试：13 个
- 数据源测试：10 个
- 事件集成测试：7 个

#### 架构设计：事件驱动的 QENAS 决策流程

**更新后的处理流程:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    QENAS 主循环 (on_bar)                         │
├─────────────────────────────────────────────────────────────────┤
│  1. 更新收益率窗口                                               │
│  2. 计算量子纠缠矩阵                                             │
│  3. 处理 K 线附带事件 → EventProcessor                            │
│  4. 获取子策略信号                                               │
│  5. 整合事件信号 → SENTIMENT 生态位增强                            │
│  6. 神经形态处理 → 前额叶/边缘系统/小脑输入事件编码                  │
│  7. 设置 Kuramoto 振子参数                                        │
│  8. 模拟动力学 → 检测临界相变                                     │
│  9. 生成决策 (BUY/SELL/HOLD)                                     │
│  10. 执行交易                                                    │
│  11. 生态系统进化 (定期)                                          │
└─────────────────────────────────────────────────────────────────┘
```

**事件信号整合机制:**

1. **事件驱动型策略物种**:
   - `SignalNiche.SENTIMENT` 生态位的策略对事件信号更敏感
   - 整合公式：`enhanced = 0.7 * base + 0.3 * event_signal`

2. **神经形态事件编码**:
   - **前额叶皮层**: 接收风险事件（地缘政治、监管、央行决策）
   - **边缘系统**: 接收所有事件的情绪信号（sentiment_score）
   - **小脑**: 接收短期事件（财报、分红）

3. **纠缠矩阵动态调整**:
   - 高影响事件（HIGH/CRITICAL）增强受影响资产间的纠缠
   - 调整公式：`adjusted[i,j] = base[i,j] * (1 + impact_level * 0.1)`

#### 关键代码修改

**qenas_core/strategies/qenas_strategy.py:**
```python
def _process_kline_events(self, kline, entanglement_matrix):
    """处理 K 线附带的事件."""
    events = getattr(kline, 'events', [])
    if not events:
        return None

    # 处理每个事件生成信号
    for event in events:
        signal = self.event_processor.process_event(event)

    # 高影响事件调整纠缠矩阵
    if high_impact_events:
        entanglement_matrix = self.event_processor.adjust_entanglement_for_events(
            entanglement_matrix, high_impact_events, self._symbol_to_index
        )
```

#### 测试覆盖

事件集成测试覆盖以下场景：
- 普通事件处理（EARNINGS, MEDIUM 影响）
- 高影响事件处理（REGULATORY, HIGH 影响，负面情感）
- 事件对纠缠矩阵的动态调整
- 多脑区神经形态编码
- 事件信号与策略信号的整合
- 事件集群检测（单集群和多集群）
