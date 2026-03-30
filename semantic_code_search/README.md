# Semantic Code Search MCP Server

基于自然语言的代码库语义搜索 MCP 服务器。

## 功能

- 使用自然语言搜索代码（如"找出所有处理用户认证的函数"）
- 支持 Python、C、C++ 代码
- 函数/类级别的精确索引
- 自动监听文件变化并增量更新索引

## 安装

```bash
# 使用 uv 安装
uv pip install -e .

# 或者直接运行
uv run semantic-mcp
```

## 配置

设置以下环境变量:

```bash
# ChromaDB 本地存储路径
export SEMANTIC_CHROMA_PATH="./.semantic_index"

# Embedding API 配置
export SEMANTIC_EMBEDDING_BASE_URL="https://api.openai.com/v1"
export SEMANTIC_EMBEDDING_MODEL="text-embedding-3-small"
export SEMANTIC_API_KEY="sk-your-api-key"

# 目标代码库目录
export SEMANTIC_TARGET_DIR="/path/to/your/codebase"

# 可选配置
export SEMANTIC_FILE_PATTERNS="*.py,*.c,*.cpp,*.h,*.hpp"  # 文件匹配模式
export SEMANTIC_SMALL_FILE_THRESHOLD="50"  # 小文件行数阈值（默认 50）
export SEMANTIC_DEBOUNCE_DURATION="1.0"  # 文件监听防抖延迟秒数（默认 1.0）
export SEMANTIC_RESULT_CODE_LIMIT="500"  # 搜索结果代码截断字符数（默认 500）
```

## 使用

### 在 Claude Code 中使用

在 MCP 配置中添加:

```json
{
  "mcpServers": {
    "semantic-code-search": {
      "command": "semantic-mcp"
    }
  }
}
```

### 可用 Tools

1. **semantic_code_search**: 语义搜索代码
   - `query`: 自然语言查询（必需）
   - `limit`: 结果数量限制（默认 10）
   - `language`: 语言过滤（python/c/cpp）
   - `node_type`: 类型过滤（function/class/method/struct）

2. **index_codebase**: 手动触发索引
   - `full`: 是否完全重新索引（默认 false）

## 开发

```bash
# 安装依赖
uv sync

# 运行测试
uv run pytest

# 开发模式运行
uv run semantic-mcp
```

## 打包

```bash
# 构建分发包
uv build

# 安装到系统
uv pip install .

# 使用 uvx 运行
uvx semantic-mcp
```
