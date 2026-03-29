"""Full Agent Example - Complete implementation with all features.

This example demonstrates:
1. Model configuration loading
2. Tool system with registry
3. Skill loading (two-layer pattern)
4. Context management (micro-compact, auto-compact)
5. SubAgent for task decomposition
6. MCP service integration
7. Local and remote logging
8. CLI and API channels

Usage:
    python examples/full_agent.py
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import Agent, ContextProcessor, ModelConfig
from core.channel.cli import CLIChannel
from core.logger.local_logger import LocalLogger
from core.skills.manager import SkillManager
from core.subagent.subagent import SubAgent
from core.tools.bash import BashTool
from core.tools.file_ops import ReadTool, WriteTool, EditTool
from core.tools.registry import ToolRegistry


class FullAgent(Agent):
    """Full-featured Agent with all components."""

    def __init__(
        self,
        model_name: str | None = None,
        enable_skills: bool = True,
        enable_logging: bool = True,
        enable_subagent: bool = True,
        **kwargs,
    ):
        """Initialize FullAgent.

        Args:
            model_name: Model name
            enable_skills: Enable skill system
            enable_logging: Enable logging
            enable_subagent: Enable SubAgent support
            **kwargs: Other Agent parameters
        """
        # Initialize tool registry
        self.tool_registry = ToolRegistry()
        self._setup_tools()

        # Get tool definitions
        tools = self.tool_registry.get_openai_tools()

        # Load model config
        self.model_config = ModelConfig()

        # Initialize skill manager
        self.skill_manager = None
        if enable_skills:
            self.skill_manager = SkillManager()
            # Add load_skill tool definition
            tools.append(self.skill_manager.to_tool_definition())

        # System prompt with skills
        system_prompt = self._build_system_prompt()

        # Initialize parent Agent
        super().__init__(
            model_name=model_name,
            tools=tools,
            system_prompt=system_prompt,
            config=self.model_config,
            **kwargs,
        )

        # Initialize logger
        self.logger = None
        if enable_logging:
            self.logger = LocalLogger()
            self.logger.info("FullAgent initialized")

        # Context management settings
        self.enable_micro_compact = True
        self.enable_auto_compact = True
        self.context_threshold = 50000

        # SubAgent support
        self.enable_subagent = enable_subagent

    def _setup_tools(self) -> None:
        """Setup built-in tools."""
        self.tool_registry.register(BashTool())
        self.tool_registry.register(ReadTool())
        self.tool_registry.register(WriteTool())
        self.tool_registry.register(EditTool())

    def _build_system_prompt(self) -> str:
        """Build system prompt with skills."""
        base_prompt = """You are a powerful AI assistant with access to various tools and skills.

Available tools:
- bash: Execute shell commands
- read_file: Read content from files
- write_file: Write content to files
- edit_file: Edit content in files by replacing strings
"""

        # Add skills description
        if self.skill_manager:
            base_prompt += "\n" + self.skill_manager.get_system_prompt()
            base_prompt += """
- load_skill: Load a skill's full content for detailed guidance
"""

        base_prompt += """
When using tools:
1. Think step by step about what needs to be done
2. Use the appropriate tool for the task
3. Verify results before proceeding
4. Provide clear summaries of what you've done

For complex tasks, you can break them down into subtasks."""

        return base_prompt

    def _find_and_execute_tool(self, name: str, args: dict) -> dict:
        """Find and execute tool.

        Args:
            name: Tool name
            args: Tool arguments

        Returns:
            Tool execution result
        """
        # Handle load_skill specially
        if name == "load_skill" and self.skill_manager:
            result = self.skill_manager.execute_load_skill(name=args.get("name", ""))
        else:
            result = self.tool_registry.execute(name, **args)

        # Log tool execution
        if self.logger:
            self.logger.log_tool_call(name, args, result)

        return result

    def run(self, query: str, stream: bool = False) -> str:
        """Run agent with context management.

        Args:
            query: User query
            stream: Enable streaming

        Returns:
            Model response
        """
        # Log message
        if self.logger:
            self.logger.log_message("user", query)

        # Run agent loop
        response = super().run(query, stream=stream)

        # Log response
        if self.logger:
            self.logger.log_message("assistant", response)

        # Apply context management
        self._manage_context()

        return response

    def _manage_context(self) -> None:
        """Manage context with compression strategies."""
        if self.enable_micro_compact:
            self.messages = ContextProcessor.micro_compact(self.messages)

        if self.enable_auto_compact and len(self.messages) > 10:
            self.messages = ContextProcessor.auto_compact(
                self.messages,
                threshold=self.context_threshold,
            )

    def create_subagent(self, task: str, role: str | None = None) -> SubAgent:
        """Create a SubAgent for task decomposition.

        Args:
            task: Task description
            role: Optional role specialization

        Returns:
            SubAgent instance
        """
        if not self.enable_subagent:
            raise RuntimeError("SubAgent is disabled")

        if role:
            return SubAgent.create_specialized(
                role=role,
                expertise=task,
                parent=self,
                model_name=self.model_name,
                config=self.model_config,
            )
        else:
            return SubAgent(
                parent=self,
                task_description=task,
                model_name=self.model_name,
                config=self.model_config,
            )


def main():
    """Run the full agent example."""
    print("=" * 60)
    print("AgentForge - Full Agent Example")
    print("=" * 60)
    print()
    print("This example demonstrates a complete Agent implementation with:")
    print("- Model configuration loading")
    print("- Tool system with registry")
    print("- Skill loading (two-layer pattern)")
    print("- Context management")
    print("- SubAgent support")
    print("- Local logging")
    print()
    print("Type 'quit' to exit, 'help' for commands.\n")

    # Create full agent
    agent = FullAgent(
        model_name="claude-sonnet-4-6",
        enable_skills=True,
        enable_logging=True,
        enable_subagent=True,
    )

    # Interactive loop
    while True:
        try:
            query = input("> ").strip()

            if not query:
                continue

            if query.lower() in ["quit", "exit"]:
                print("Goodbye!")
                break

            if query.lower() == "help":
                print("""
Commands:
  quit, exit  - Exit the application
  help        - Show this help
  status      - Show agent status
  skills      - List available skills
  clear       - Clear conversation history
""")
                continue

            if query.lower() == "status":
                print(f"Messages in context: {len(agent.messages)}")
                print(f"Tools available: {len(agent.tools)}")
                if agent.skill_manager:
                    print(f"Skills loaded: {agent.skill_manager.loader.list_skills()}")
                continue

            if query.lower() == "skills":
                if agent.skill_manager:
                    print(agent.skill_manager.get_system_prompt())
                else:
                    print("Skills are disabled")
                continue

            if query.lower() == "clear":
                agent.reset()
                print("Conversation history cleared")
                continue

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
