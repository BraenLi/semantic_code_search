# Semantic Code Search MCP Server - 设计文档

**日期**: 2026-03-30
**版本**: v0.1.0

---

## 概述

开发一个 Python MCP server，提供单个 `semantic_code_search` tool，实现基于自然语言的代码库语义搜索。

## 核心需求

- 自然语言查询代码（如"找出所有处理用户认证的函数"）
- 使用 ChromaDB 作为轻量级向量数据库
- 通过外部 API 生成 embedding（OpenAI 兼容协议）
- AST 感知处理，精确到函数/类级别的索引
- 支持增量索引和文件系统监听自动感知代码变化
- 使用 uv 管理项目和打包
- 支持打包成二进制后本地启动

---

## 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                    MCP Server                            │
│  semantic_code_search(query, limit?) → 搜索结果列表       │
└─────────────────────────────────────────────────────────┘
         ↓ 调用
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│    Indexer       │  │    Searcher      │  │    Watcher       │
│  增量索引逻辑     │  │  向量相似度搜索   │  │  文件系统监听     │
└──────────────────┘  └──────────────────┘  └──────────────────┘
         ↓ 使用                  ↓ 使用                 ↓ 监听
┌─────────────────────────────────────────────────────────┐
│  Parser (AST)           │  Embedding        │  Storage   │
│  - Python (tree-sitter)│  OpenAI 兼容 API   │  ChromaDB  │
│  - C/C++ (tree-sitter) │  可配置 base_url   │  本地文件  │
│  函数/类级别分块         │                  │            │
└─────────────────────────────────────────────────────────┘
```

---

## 技术选型

| 组件 | 选择 |
|------|------|
| 语言支持 | Python, C, C++ |
| Embedding | OpenAI 兼容协议 |
| 向量数据库 | ChromaDB Persistent |
| 索引粒度 | 函数/类级别（小文件整体） |
| 返回格式 | 文件名 + 函数名 + 代码片段 + 相似度 |
| 目标目录 | 单一目录（环境变量配置） |

---

## 模块设计

### 1. Parser 模块 (`src/semantic_mcp/parser/`)

**ast_parser.py** - AST 解析
- 使用 tree-sitter 解析 Python、C、C++ 代码
- 提取函数、类、方法、结构体等代码单元
- 返回 AST 节点信息（类型、名称、源码范围、父路径）

**chunker.py** - 分块逻辑
- 小文件（< 50 行）：整体作为一个 chunk
- 大文件：按函数/类分割为多个 chunk
- 为每个 chunk 生成自然语言描述

### 2. Embedding 服务 (`src/semantic_mcp/services/embeddings.py`)

- OpenAI 兼容协议封装
- 支持配置 `base_url`、`api_key`、`model`
- 批量 embedding 生成
- 错误处理与重试逻辑

### 3. Storage 模块 (`src/semantic_mcp/services/storage.py`)

- ChromaDB Persistent Client 封装
- 集合管理（按目标目录隔离）
- 增删改查操作
- 元数据索引（文件名、函数名、AST 路径、时间戳）

### 4. Indexer 服务 (`src/semantic_mcp/services/indexer.py`)

- 全量索引：遍历目录 → 解析 → 分块 → embedding → 存储
- 增量索引：检测文件变化（mtime + hash）
- 删除检测：文件/代码单元被移除时同步删除

### 5. Watcher 服务 (`src/semantic_mcp/services/watcher.py`)

- 使用 watchdog 监听文件系统事件
- 自动触发增量索引（文件创建、修改、删除）
- 防抖处理：批量事件合并

### 6. Search 服务 (`src/semantic_mcp/services/search.py`)

- 自然语言查询 → embedding → 相似度搜索
- 支持过滤（文件类型、函数类型）
- 返回格式化结果（代码片段 + 元数据）

### 7. MCP Server (`src/semantic_mcp/main.py`)

- `semantic_code_search(query, limit=10)` tool
- 配置管理（环境变量 + 配置文件）
- 服务初始化与生命周期管理

---

## 配置管理

**环境变量**:
```bash
SEMANTIC_CHROMA_PATH="./.semantic_index"
SEMANTIC_EMBEDDING_BASE_URL="https://api.openai.com/v1"
SEMANTIC_EMBEDDING_MODEL="text-embedding-3-small"
SEMANTIC_API_KEY="sk-..."
SEMANTIC_TARGET_DIR="/path/to/codebase"
SEMANTIC_FILE_PATTERNS="*.py,*.c,*.cpp,*.h,*.hpp"
```

**配置文件** (可选): `.semconfig.json`
```json
{
  "chroma_path": "./.semantic_index",
  "embedding": {
    "base_url": "https://api.openai.com/v1",
    "model": "text-embedding-3-small"
  },
  "target_dir": "/path/to/codebase",
  "file_patterns": ["*.py", "*.c", "*.cpp", "*.h", "*.hpp"]
}
```

---

## 数据结构

**Chunk 元数据**:
```python
{
    "file_path": str,          # 文件绝对路径
    "relative_path": str,      # 相对于 target_dir 的路径
    "language": str,           # python | c | cpp
    "node_type": str,          # function | class | method | file
    "node_name": str,          # 函数名/类名
    "ast_path": str,           # AST 路径（如 "module/class/function"）
    "start_line": int,
    "end_line": int,
    "start_col": int,
    "end_col": int,
    "code": str,               # 源代码
    "description": str,        # 自然语言描述
    "indexed_at": float,       # 索引时间戳
    "hash": str                # 内容 hash（用于增量检测）
}
```

---

## API 设计

**semantic_code_search(query: str, limit: int = 10) → list[dict]**

返回:
```python
[
    {
        "file": "path/to/file.py",
        "name": "authenticate_user",
        "type": "function",
        "language": "python",
        "score": 0.89,
        "code": "def authenticate_user(...):\\n    ...",
        "description": "Authenticates a user with username and password"
    },
    ...
]
```

---

## 依赖管理

```toml
[project]
name = "semantic-mcp"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "mcp>=1.0.0",
    "chromadb>=0.4.0",
    "openai>=1.0.0",
    "watchdog>=3.0.0",
    "tree-sitter>=0.20.0",
    "tree-sitter-python",
    "tree-sitter-c",
    "tree-sitter-cpp",
    "python-dotenv>=1.0.0",
    "pydantic>=2.0.0",
]

[project.scripts]
semantic-mcp = "semantic_mcp.main:main"

[tool.hatch.build.targets.wheel]
packages = ["src/semantic_mcp"]

[tool.uv]
dev-dependencies = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
]
```

---

## 测试策略

**单元测试**:
- `test_ast_parser.py` - AST 解析正确性
- `test_chunker.py` - 分块逻辑
- `test_indexer.py` - 增量索引检测

**集成测试**:
- 使用真实代码库索引
- 搜索准确性验证

**手动验证**:
- Claude Code 中调用 tool

---

## 打包发布

**开发阶段**: `uv run semantic-mcp`

**打包**: `uv build` + `uv pip install .`

**二进制**: 使用 `uv tool install` 或 `pyinstaller`

**发布**: `uv publish` (PyPI) + `uvx semantic-mcp`

---

## 验证清单

- [ ] 可以索引 Python/C/C++ 代码
- [ ] 函数/类级别精确搜索
- [ ] 增量索引工作正常
- [ ] 文件监听自动更新
- [ ] Claude Code 中可以调用
- [ ] 打包后可独立运行
