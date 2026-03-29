# AgentForge

A modular agent development framework for building and assembling agent components quickly.

## Features

- **Minimal Core**: Agent loop kept lean, functionality extended through components
- **Configuration-Driven**: Manage models, tools, MCP services via configuration files
- **Component Isolation**: Clear boundaries for SubAgent, Skill, Tool
- **Progressive Loading**: Load skills and context on-demand to save tokens

## Installation

```bash
# Using uv (recommended)
uv pip install -e .

# Or using pip
pip install -e .
```

## Quick Start

### Basic Agent

```python
from core import Agent
from core.tools.bash import BashTool
from core.tools.file_ops import ReadTool, WriteTool
from core.tools.registry import ToolRegistry

# Setup tools
registry = ToolRegistry()
registry.register(BashTool())
registry.register(ReadTool())
registry.register(WriteTool())

# Create agent
agent = Agent(
    model_name="claude-sonnet-4-6",
    tools=registry.get_openai_tools(),
    system_prompt="You are a helpful assistant.",
)

# Override tool execution
def find_and_execute_tool(name, args):
    return registry.execute(name, **args)

agent._find_and_execute_tool = find_and_execute_tool

# Run
response = agent.run("What files are in the current directory?")
print(response)
```

### Full-Featured Agent

```bash
# Run the full example
python examples/full_agent.py
```

## Project Structure

```
agentforge/
├── config/
│   ├── models.yaml         # Model configurations
│   ├── mcp.yaml            # MCP service configurations
│   └── .env.example        # Environment variables template
│
├── src/
│   ├── __init__.py         # Package init
│   ├── core/
│   │   ├── agent.py        # Base Agent class (core loop)
│   │   ├── context.py      # Context management
│   │   ├── models/         # Model configuration & client
│   │   ├── skills/         # Skill loader & manager
│   │   ├── tools/          # Tool system
│   │   ├── mcp/            # MCP support
│   │   ├── subagent/       # SubAgent implementation
│   │   ├── channel/        # CLI & API channels
│   │   └── logger/         # Local & remote logging
│   └── agents/             # Custom agents
│
├── examples/
│   ├── basic_agent.py      # Minimal example
│   └── full_agent.py       # Complete example
│
└── skills/
    └── skill_template.md   # Skill template
```

## Configuration

### Models (config/models.yaml)

```yaml
default_model: claude-sonnet-4-6

models:
  claude-sonnet-4-6:
    provider: anthropic
    base_url: https://api.anthropic.com/v1
    api_key_env: ANTHROPIC_API_KEY
    max_tokens: 8000

  gpt-4o:
    provider: openai
    base_url: https://api.openai.com/v1
    api_key_env: OPENAI_API_KEY
    max_tokens: 4096
```

### Environment Variables

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp config/.env.example .env
```

## Core Components

### Agent Loop

The core Agent loop follows a simple pattern:

```python
while True:
    response = client.chat.completions.create(...)
    if response.finish_reason != "tool_calls":
        return response.content
    results = execute_tools(response.tool_calls)
    messages.append({"role": "user", "content": results})
```

### Two-Layer Skill Loading

1. **Layer 1**: Short descriptions in system prompt
2. **Layer 2**: Full content loaded on-demand via `load_skill` tool

### Context Management

- **Micro-compact**: Replace old tool results with placeholders
- **Auto-compact**: LLM summarization when token threshold exceeded
- **SubAgent isolation**: Separate context for subtasks

### Tools

Built-in tools:
- `bash` - Execute shell commands
- `read_file` - Read file content
- `write_file` - Write file content
- `edit_file` - Edit file by string replacement

Create custom tools:

```python
from core.tools.base import BaseTool

class MyTool(BaseTool):
    name = "my_tool"
    description = "My custom tool"

    def execute(self, param1: str, **kwargs):
        return {"result": "success"}
```

## Usage Examples

### Run CLI Channel

```bash
python examples/basic_agent.py
```

### Run Full Agent

```bash
python examples/full_agent.py
```

### Use SubAgent

```python
from core.subagent import SubAgent

# Create subagent for specialized task
subagent = SubAgent.create_specialized(
    role="Code Reviewer",
    expertise="Python best practices and security",
    parent=parent_agent,
)

result = subagent.run("Review this code for security issues...")
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/ examples/
ruff check src/ examples/
```

## License

MIT
