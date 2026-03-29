"""Basic Agent Example - Minimal implementation.

This example demonstrates the core Agent loop pattern:
1. Send user message to model
2. If tool_calls, execute tools and feedback results
3. Repeat until model returns final response

Usage:
    python examples/basic_agent.py
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import Agent, ModelConfig
from core.tools.bash import BashTool
from core.tools.file_ops import ReadTool, WriteTool, EditTool
from core.tools.registry import ToolRegistry


def create_basic_agent():
    """Create a basic agent with file and bash tools."""
    # Create tool registry and register tools
    registry = ToolRegistry()
    registry.register(BashTool())
    registry.register(ReadTool())
    registry.register(WriteTool())
    registry.register(EditTool())

    # Get OpenAI format tool definitions
    tools = registry.get_openai_tools()

    # System prompt
    system_prompt = """You are a helpful AI assistant with access to shell and file operations.

Available tools:
- bash: Execute shell commands
- read_file: Read content from files
- write_file: Write content to files
- edit_file: Edit content in files by replacing strings

When using tools:
1. Think step by step about what needs to be done
2. Use the appropriate tool for the task
3. Verify results before proceeding
4. Provide clear summaries of what you've done"""

    # Create agent
    agent = Agent(
        model_name="claude-sonnet-4-6",  # Will use config default if not found
        tools=tools,
        system_prompt=system_prompt,
        max_tokens=8000,
    )

    # Override _find_and_execute_tool to use our registry
    def find_and_execute_tool(name: str, args: dict):
        return registry.execute(name, **args)

    agent._find_and_execute_tool = find_and_execute_tool

    return agent


def main():
    """Run the basic agent example."""
    print("=" * 60)
    print("AgentForge - Basic Agent Example")
    print("=" * 60)
    print()
    print("This example demonstrates a minimal Agent implementation.")
    print("Type 'quit' to exit.\n")

    # Create agent
    agent = create_basic_agent()

    # Interactive loop
    while True:
        try:
            query = input("> ").strip()

            if not query:
                continue

            if query.lower() in ["quit", "exit"]:
                print("Goodbye!")
                break

            # Run agent
            print("\n[Agent thinking...]")
            response = agent.run(query)
            print(f"\n{response}\n")

        except KeyboardInterrupt:
            print("\nInterrupted. Goodbye!")
            break

        except Exception as e:
            print(f"\n[Error] {e}\n")


if __name__ == "__main__":
    main()
