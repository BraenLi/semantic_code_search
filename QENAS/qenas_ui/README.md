# QENAS UI

QENAS 前端界面 - 量子纠缠生态位自适应网络可视化与控制界面

## 技术栈

- **Vue 3** - 渐进式 JavaScript 框架
- **Vite** - 下一代前端构建工具
- **Pinia** - Vue 3 状态管理
- **Vue Router** - 路由管理
- **ECharts** - 数据可视化图表库
- **Tailwind CSS** - 实用优先的 CSS 框架

## 快速开始

### 安装依赖

```bash
npm install
```

### 开发模式

```bash
npm run dev
```

启动后访问 http://localhost:5173

### 构建生产版本

```bash
npm run build
```

### 预览生产构建

```bash
npm run preview
```

### 代码检查

```bash
npm run lint
```

## 项目结构

```
qenas_ui/
├── src/
│   ├── components/          # 可复用组件
│   │   ├── EntanglementMatrix.vue   # 纠缠矩阵热力图
│   │   ├── EventTimeline.vue        # 事件时间线
│   │   ├── EquityCurve.vue          # 权益曲线图
│   │   └── EcosystemView.vue        # 生态系统视图
│   ├── views/               # 页面视图
│   │   ├── Dashboard.vue    # 仪表板
│   │   ├── Backtest.vue     # 回测管理
│   │   ├── Monitoring.vue   # 实时监控
│   │   └── Settings.vue     # 设置页面
│   ├── services/            # API 服务
│   │   ├── api.js           # REST API 客户端
│   │   └── websocket.js     # WebSocket 客户端
│   ├── stores/              # Pinia 状态管理
│   │   └── qenas.js         # QENAS 状态存储
│   ├── router/              # 路由配置
│   │   └── index.js
│   ├── styles/              # 全局样式
│   │   └── main.css
│   ├── App.vue              # 根组件
│   └── main.js              # 入口文件
├── index.html
├── package.json
├── vite.config.js
├── tailwind.config.js
└── postcss.config.js
```

## 主要功能

### 仪表板 (Dashboard)
- 关键指标概览（纠缠熵、资产数量、策略物种、多样性指数）
- 纠缠矩阵可视化
- 权益曲线图
- 事件时间线
- 生态系统状态

### 回测管理 (Backtest)
- 创建新回测任务
- 配置回测参数（策略、标的、日期范围、资金等）
- 查看回测任务列表和进度
- 查看回测结果和绩效指标

### 实时监控 (Monitoring)
- 实时纠缠矩阵更新
- 实时事件流
- 生态系统状态监控
- WebSocket 连接状态

### 设置 (Settings)
- 策略配置（物种数量、同步阈值、进化间隔）
- 交易配置（佣金率、滑点率、仓位限制）
- 数据源配置
- WebSocket 配置

## API 配置

开发模式下，Vite 会代理 API 请求到后端服务：

```javascript
// vite.config.js
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
    '/ws': {
      target: 'ws://localhost:8000',
      ws: true,
    }
  }
}
```

## 组件说明

### EntanglementMatrix
纠缠矩阵热力图组件，使用 ECharts 绘制。

```vue
<EntanglementMatrix
  :matrix="matrixData"
  :symbols="['AAPL', 'GOOGL', 'MSFT']"
  :entropy="1.2345"
  :height="400"
/>
```

### EquityCurve
权益曲线图组件，支持策略与基准对比。

```vue
<EquityCurve
  :equityCurve="equityData"
  :benchmark="benchmarkData"
  :metrics="{ total_return: 0.15, sharpe_ratio: 1.5 }"
  :height="300"
/>
```

### EventTimeline
事件时间线组件，显示重大事件及其影响。

```vue
<EventTimeline
  :events="eventsData"
  :maxDisplay="10"
/>
```

### EcosystemView
生态系统视图组件，显示策略物种分布。

```vue
<EcosystemView
  :totalSpecies="100"
  :nicheDistribution="{ momentum: 25, reversion: 20 }"
  :fitnessDistribution="{ high: 0.15, medium: 0.35 }"
  :diversityIndex="2.5"
/>
```

## 环境变量

创建 `.env` 文件（可选）：

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## 浏览器支持

- Chrome >= 90
- Firefox >= 88
- Safari >= 14
- Edge >= 90

## 开发注意事项

1. 使用 Vue 3 Composition API (`<script setup>`)
2. 组件采用单一职责原则
3. 状态管理使用 Pinia
4. API 调用封装在 services 层
5. 样式使用 Tailwind CSS 为主

## License

MIT
