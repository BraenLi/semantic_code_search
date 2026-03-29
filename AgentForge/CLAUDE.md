# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AgentForge is a modular agent development framework for building AI agents with tool use capabilities. The core design follows a simple agent loop pattern with configuration-driven model management.

## Commands

```bash
# Install dependencies (using uv - recommended)
uv pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/ examples/
ruff check src/ examples/

# Run examples
python examples/basic_agent.py
python examples/full_agent.py
```

## Architecture

### Core Loop Pattern

The Agent class (`src/core/agent.py`) implements a simple while loop:
1. Call model with messages
2. If `finish_reason == "tool_calls"`, execute tools and append results
3. Repeat until model returns final response

### Two-Layer Skill Loading

Skills use a token-efficient loading pattern:
- **Layer 1**: Short descriptions in system prompt (from markdown frontmatter)
- **Layer 2**: Full content loaded on-demand via `load_skill` tool

### Context Management (`src/core/context.py`)

Three-layer strategy:
1. **Micro-compact**: Replace old tool results with placeholders
2. **Auto-compact**: LLM summarization when token threshold exceeded
3. **SubAgent isolation**: Separate context for subtasks

### Key Modules

```
src/core/
├── agent.py          # Base Agent class (core loop)
├── context.py        # ContextProcessor for message management
├── models/           # Model configuration & client factory
├── tools/            # BaseTool, ToolRegistry, built-in tools
├── skills/           # SkillLoader for markdown-based skills
├── subagent/         # SubAgent for task decomposition
├── mcp/              # MCP (Model Context Protocol) support
├── channel/          # CLI and API interaction channels
└── logger/           # Local and remote logging
```

### Configuration

- `config/models.yaml`: Model endpoints, API keys, token limits
- `config/mcp.yaml`: MCP server configurations (filesystem, github, postgres)
- `.env`: API keys (copy from `config/.env.example`)

### Tool System

Tools extend `BaseTool` and register via `ToolRegistry`:
- Built-in: `bash`, `read_file`, `write_file`, `edit_file`
- Custom tools: Inherit `BaseTool`, implement `execute()` and `to_openai_tool()`

### SubAgent Pattern

`SubAgent` extends `Agent` for task decomposition:
- Context isolated from parent via `ContextProcessor.isolate_subagent()`
- Results merged back via `merge_to_parent()`
- Create specialized agents with `SubAgent.create_specialized(role, expertise)`
