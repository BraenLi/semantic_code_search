# AgentTest

一个分层化的 Agent 应用架构 (A layered Agent application architecture)。

## 架构设计

```
┌─────────────────────────────────────────┐
│           Application Layer             │  ← 业务逻辑、Workflow 编排
├─────────────────────────────────────────┤
│             Agent Layer                 │  ← Agent 核心、状态管理、决策
├─────────────────────────────────────────┤
│           Capability Layer              │  ← 工具、记忆、规划能力
├─────────────────────────────────────────┤
│            Core Layer                   │  ← LLM 抽象、协议定义、基础类型
└─────────────────────────────────────────┘
```

## 目录结构

```
agenttest/
├── core/              # 核心层：LLM 抽象、类型定义、配置
├── capabilities/      # 能力层：工具、记忆、规划
├── agent/             # Agent 层：状态管理、执行循环
├── app/               # 应用层：编排器、CLI、API
└── tests/             # 测试
```

## 安装

```bash
# 安装依赖
pip install -e .

# 开发模式安装
pip install -e ".[dev]"
```

## 快速开始

### 1. 配置环境变量

```bash
export OPENAI_API_KEY="your-api-key"
```

### 2. 创建配置文件

```bash
agenttest config --init
```

### 3. 运行 CLI

```bash
# 交互式聊天
agenttest chat

# 运行任务
agenttest run "帮我创建一个 Python 项目结构"

# 查看状态
agenttest status
```

### 4. 编程使用

```python
import asyncio
from agenttest import (
    BaseAgent,
    AgentLoop,
    OpenAILLM,
    Config,
    FileSystemTool,
    BashTool,
)

async def main():
    # 创建配置
    config = Config.from_env()

    # 创建 LLM
    llm = OpenAILLM(
        model="gpt-4o",
        api_key=config.llm.api_key,
    )

    # 创建 Agent
    class MyAgent(BaseAgent):
        async def run(self, goal: str) -> str:
            loop = AgentLoop(self)
            return await loop.run(goal)

    agent = MyAgent(llm=llm, config=config, name="Assistant")

    # 注册工具
    agent.register_tool(FileSystemTool())
    agent.register_tool(BashTool())

    # 运行
    result = await agent.run("帮我创建一个测试文件")
    print(result)

asyncio.run(main())
```

## 层级说明

### Core Layer (核心层)

提供最基础的抽象，不依赖上层：

- `llm/` - LLM Provider 抽象（OpenAI、Anthropic 等）
- `types.py` - 基础类型定义（Message, Tool, Response）
- `config.py` - 配置管理
- `exceptions.py` - 异常定义

### Capability Layer (能力层)

提供可插拔的能力模块：

- `tools/` - 工具定义（文件、搜索、API 等）
- `memory/` - 短期记忆（对话历史）、长期记忆（向量存储）
- `planning/` - 任务分解、步骤规划

### Agent Layer (Agent 层)

Agent 核心逻辑：

- `state.py` - 状态管理（Idle/Running/Waiting/Completed）
- `loop.py` - ReAct/Plan-Execute 循环
- `base.py` - Agent 基类

### Application Layer (应用层)

业务逻辑编排：

- `orchestrator.py` - 多 Agent 编排与路由
- `workflows/` - 多 Agent 协作流程
- `api/` - HTTP/gRPC 接口
- `cli/` - 命令行接口

## 测试

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 带覆盖率
pytest --cov=agenttest --cov-report=html
```

## 设计原则

1. **上层依赖下层，下层不依赖上层**
2. **依赖抽象，不依赖具体实现**
3. **每层可独立测试**
4. **工具是可插拔的能力，不是核心组件**
5. **Agent 层是通用框架，业务逻辑在应用层**

## License

MIT
