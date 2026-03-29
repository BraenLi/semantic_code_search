"""CLI 通道 - 命令行交互。"""

import asyncio
from typing import Any

from .base import BaseChannel


class CLIChannel(BaseChannel):
    """CLI 通道 - 命令行交互。

    使用方式:
        channel = CLIChannel()
        async with channel:
            while True:
                msg = await channel.receive()
                # 处理消息...
                await channel.send({"content": "response"})
    """

    name = "cli"

    def __init__(self, prompt: str = "> "):
        """初始化 CLI 通道。

        Args:
            prompt: 输入提示符
        """
        self.prompt = prompt
        self._running = False

    async def receive(self) -> dict[str, Any]:
        """接收用户输入。

        Returns:
            消息字典 {type: "message", content: str}
        """
        loop = asyncio.get_event_loop()

        # 使用 run_in_executor 使 input() 异步
        user_input = await loop.run_in_executor(None, input, self.prompt)

        # 检查退出命令
        if user_input.lower() in ["quit", "exit", "/quit", "/exit"]:
            return {"type": "exit"}

        if user_input.lower() in ["clear", "/clear"]:
            return {"type": "clear"}

        if user_input.lower() in ["help", "/help"]:
            return {"type": "help"}

        return {"type": "message", "content": user_input}

    async def send(self, response: dict[str, Any]) -> None:
        """发送响应到控制台。

        Args:
            response: 响应字典 {content: str}
        """
        content = response.get("content", "")
        if content:
            print(f"\n{content}\n")

    async def send_error(self, error: str) -> None:
        """发送错误消息。

        Args:
            error: 错误描述
        """
        print(f"\n[ERROR] {error}\n")

    async def send_status(self, status: str, details: dict[str, Any] | None = None) -> None:
        """发送状态更新。

        Args:
            status: 状态描述
            details: 详细信息
        """
        if details:
            print(f"\n[STATUS] {status}: {details}\n")
        else:
            print(f"\n[STATUS] {status}\n")

    async def start(self) -> None:
        """启动 CLI 通道。"""
        self._running = True
        print("CLI Channel started. Type 'quit' to exit.")

    async def stop(self) -> None:
        """停止 CLI 通道。"""
        self._running = False
        print("CLI Channel stopped.")

    def print_help(self) -> None:
        """打印帮助信息。"""
        help_text = """
Available commands:
  quit, exit, /quit, /exit  - Exit the application
  clear, /clear             - Clear the screen
  help, /help               - Show this help message

Just type your message to interact with the Agent.
"""
        print(help_text)


def main():
    """CLI 入口函数。"""
    import sys

    # 简单的 CLI 循环
    async def run_cli():
        channel = CLIChannel()
        await channel.start()

        print("AgentForge CLI")
        print("Type 'help' for available commands\n")

        try:
            while True:
                msg = await channel.receive()

                if msg.get("type") == "exit":
                    print("Goodbye!")
                    break

                if msg.get("type") == "clear":
                    print("\033[2J\033[H", end="")
                    continue

                if msg.get("type") == "help":
                    channel.print_help()
                    continue

                if msg.get("type") == "message":
                    print(f"\n[Received] {msg['content']}")
                    print("[Info] This is a demo. Integrate with Agent to process messages.\n")

        except KeyboardInterrupt:
            print("\nInterrupted. Goodbye!")
        finally:
            await channel.stop()

    asyncio.run(run_cli())


if __name__ == "__main__":
    main()
