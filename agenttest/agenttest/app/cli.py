"""Command-line interface for the Agent system."""

import argparse
import asyncio
import sys
from typing import Any


def create_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="agenttest",
        description="Agent Test - A layered Agent application architecture",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Start an interactive chat session")
    chat_parser.add_argument(
        "--agent",
        type=str,
        default=None,
        help="Agent name to use (default: default agent)",
    )
    chat_parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o",
        help="LLM model to use",
    )

    # Run command
    run_parser = subparsers.add_parser("run", help="Run a specific task or goal")
    run_parser.add_argument(
        "goal",
        type=str,
        help="The goal or task to achieve",
    )
    run_parser.add_argument(
        "--agent",
        type=str,
        default=None,
        help="Agent name to use",
    )

    # Status command
    subparsers.add_parser("status", help="Show agent status")

    # Config command
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_parser.add_argument(
        "--show",
        action="store_true",
        help="Show current configuration",
    )
    config_parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize a new config file",
    )

    # Global options
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to configuration file",
    )

    return parser


async def chat_loop(agent: Any, agent_name: str | None = None) -> None:
    """Run an interactive chat loop."""
    print(f"Starting chat session{f' with {agent_name}' if agent_name else ''}")
    print("Type 'quit' or 'exit' to end the session")
    print("-" * 40)

    while True:
        try:
            user_input = input("\nYou: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit"):
                print("Ending chat session.")
                break

            response = await agent.chat(user_input)
            print(f"\nAssistant: {response.content}")

        except KeyboardInterrupt:
            print("\n\nInterrupted. Ending chat session.")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")


async def run_goal(
    agent: Any,
    goal: str,
    verbose: bool = False,
) -> None:
    """Run a specific goal."""
    print(f"Running goal: {goal}")

    try:
        result = await agent.run(goal)
        print(f"\nResult: {result}")
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)


def show_status(orchestrator: Any) -> None:
    """Show orchestrator status."""
    import json

    status = orchestrator.get_status()
    print(json.dumps(status, indent=2))


def init_config() -> None:
    """Initialize a new configuration file."""
    from pathlib import Path

    config_path = Path("config.yaml")

    if config_path.exists():
        print(f"Configuration file already exists: {config_path}")
        return

    default_config = """# AgentTest Configuration

llm:
  provider: openai
  model: gpt-4o
  temperature: 0.7
  max_tokens: 4096

tools:
  enabled_tools:
    - filesystem
    - bash
  allowed_commands:
    - ls
    - cat
    - echo
    - pwd

memory:
  short_term_max_messages: 100
  long_term_enabled: false

debug: false
log_level: INFO
"""

    config_path.write_text(default_config)
    print(f"Configuration file created: {config_path}")


def show_config() -> None:
    """Show current configuration."""
    from agenttest.core.config import Config

    config = Config.from_env()
    import json

    print(json.dumps(config.to_dict(), indent=2))


def main() -> None:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Import here to avoid circular imports
    from agenttest.agent.base import BaseAgent
    from agenttest.app.orchestrator import Orchestrator
    from agenttest.capabilities.tools.bash import BashTool
    from agenttest.capabilities.tools.filesystem import FileSystemTool
    from agenttest.core.config import Config
    from agenttest.core.llm.openai import OpenAILLM

    # Load configuration
    if args.config:
        config = Config.from_file(args.config)
    else:
        config = Config.from_env()

    # Update config from command line args
    if hasattr(args, "model") and args.model:
        config.llm.model = args.model

    # Create LLM
    llm = OpenAILLM(
        model=config.llm.model,
        api_key=config.llm.api_key,
        temperature=config.llm.temperature,
        max_tokens=config.llm.max_tokens,
    )

    # Create a simple agent for demo
    # In a real application, you would use a more sophisticated agent
    class SimpleAgent(BaseAgent):
        async def run(self, goal: str) -> str:
            from agenttest.agent.loop import AgentLoop

            loop = AgentLoop(self)
            return await loop.run(goal)

    agent = SimpleAgent(llm=llm, config=config, name="Assistant")

    # Register default tools
    agent.register_tool(FileSystemTool())
    agent.register_tool(BashTool())

    # Create orchestrator
    orchestrator = Orchestrator()
    orchestrator.register_agent("assistant", agent, set_default=True)

    # Handle commands
    if args.command == "chat":
        asyncio.run(chat_loop(agent, args.agent))

    elif args.command == "run":
        asyncio.run(run_goal(agent, args.goal, verbose=args.verbose))

    elif args.command == "status":
        show_status(orchestrator)

    elif args.command == "config":
        if args.init:
            init_config()
        elif args.show:
            show_config()
        else:
            print("Use --show or --init")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
