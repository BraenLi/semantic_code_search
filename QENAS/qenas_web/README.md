# QENAS Web Service

QENAS 后端 Web 服务 - 基于 FastAPI 的 REST API 和 WebSocket 服务

## 技术栈

- **FastAPI** - 现代高性能 Web 框架
- **Uvicorn** - ASGI 服务器
- **WebSockets** - 实时双向通信
- **Pydantic** - 数据验证

## 快速开始

### 安装依赖

```bash
pip install qenas[web]
# 或者
pip install fastapi uvicorn[standard] websockets python-multipart
```

### 启动服务

```bash
# 开发模式
uvicorn qenas_web.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn qenas_web.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 访问 API 文档

启动后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 端点

### 策略管理

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/v1/strategies` | 获取策略列表 |
| GET | `/api/v1/strategies/{id}` | 获取策略详情 |
| POST | `/api/v1/strategies` | 创建新策略 |
| POST | `/api/v1/strategies/{id}/start` | 启动策略 |
| POST | `/api/v1/strategies/{id}/stop` | 停止策略 |
| DELETE | `/api/v1/strategies/{id}` | 删除策略 |
| GET | `/api/v1/strategies/{id}/status` | 获取策略状态 |

### 回测管理

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/v1/backtest/qenas` | 运行 QENAS 回测 |
| GET | `/api/v1/backtest` | 获取回测任务列表 |
| GET | `/api/v1/backtest/{job_id}` | 获取回测任务详情 |
| GET | `/api/v1/backtest/{job_id}/result` | 获取回测结果 |
| POST | `/api/v1/backtest/{job_id}/cancel` | 取消回测任务 |
| DELETE | `/api/v1/backtest/{job_id}` | 删除回测任务 |

### 可视化数据

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/v1/visualization/entanglement` | 获取纠缠矩阵 |
| GET | `/api/v1/visualization/entanglement/history` | 获取纠缠历史 |
| GET | `/api/v1/visualization/events` | 获取事件数据 |
| GET | `/api/v1/visualization/performance` | 获取业绩数据 |
| GET | `/api/v1/visualization/ecosystem` | 获取生态系统状态 |
| GET | `/api/v1/visualization/dashboard` | 获取仪表板数据 |

### WebSocket

| 端点 | 描述 |
|------|------|
| `/ws/qenas/{client_id}` | WebSocket 连接端点 |

## WebSocket 使用

### 连接

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/qenas/client_123?topics=entanglement,events');

ws.onopen = () => {
  console.log('WebSocket 已连接');
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('收到消息:', message);
};
```

### 消息类型

**服务器推送的消息类型：**

- `entanglement_update` - 纠缠矩阵更新
- `event_alert` - 事件告警
- `performance_update` - 业绩更新
- `ecosystem_status` - 生态系统状态

**客户端发送的消息类型：**

- `subscribe` - 订阅主题
- `unsubscribe` - 取消订阅
- `ping` - 心跳检测

### 消息格式

```json
{
  "type": "entanglement_update",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "matrix": [[1.0, 0.5], [0.5, 1.0]],
    "symbols": ["AAPL", "GOOGL"],
    "entropy": 1.5
  }
}
```

## 项目结构

```
qenas_web/
├── __init__.py
├── main.py                # FastAPI 应用入口
├── config/
│   ├── __init__.py
│   └── settings.py        # 配置管理
├── api/
│   ├── __init__.py
│   └── v1/
│       ├── __init__.py
│       ├── router.py      # API 路由汇总
│       ├── strategies.py  # 策略 API
│       ├── backtest.py    # 回测 API
│       └── visualization.py # 可视化 API
├── services/
│   ├── __init__.py
│   ├── strategy_service.py    # 策略服务
│   ├── backtest_service.py    # 回测服务
│   └── visualization_service.py # 可视化服务
└── websocket/
    ├── __init__.py
    ├── manager.py         # WebSocket 管理器
    └── endpoint.py        # WebSocket 端点
```

## 配置说明

通过环境变量或 `.env` 文件配置：

```python
# 服务配置
QENAS_HOST=0.0.0.0
QENAS_PORT=8000
QENAS_DEBUG=true

# API 配置
QENAS_API_PREFIX=/api/v1

# WebSocket 配置
QENAS_WS_ENDPOINT=/ws/qenas

# 回测配置
QENAS_DEFAULT_INITIAL_CAPITAL=100000
```

## 开发指南

### 添加新 API 端点

1. 在 `api/v1/` 下创建新的路由文件
2. 在 `router.py` 中注册路由
3. 在 `services/` 下实现业务逻辑

### 添加 WebSocket 消息类型

1. 在 `WebSocketManager` 中添加新的广播方法
2. 在端点中处理消息发送
3. 在前端添加对应的消息处理器

## 测试

```bash
# 运行 API 测试
pytest tests/test_api.py

# 运行 WebSocket 测试
pytest tests/test_websocket.py
```

## 健康检查

```bash
curl http://localhost:8000/health
# 返回：{"status": "healthy", "version": "0.1.0"}
```

## License

MIT
