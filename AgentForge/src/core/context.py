"""Context processing module.

上下文管理策略:
1. Layer 1: Micro-compact - 替换旧的 tool_result 为占位符
2. Layer 2: Auto-compact - token 超阈值时 LLM 摘要
3. Layer 3: SubAgent 上下文隔离
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


class ContextProcessor:
    """上下文管理器 - 处理消息压缩和隔离。"""

    # Token estimation constants
    AVG_CHARS_PER_TOKEN_EN = 4.0
    AVG_CHARS_PER_TOKEN_CN = 1.5
    AVG_CHARS_PER_TOKEN = 2.5

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """估算文本的 token 数。

        改进的估算算法：
        - 英文约 4 字符/token
        - 中文约 1.5 字符/token
        - 根据文本中中文字符比例动态计算

        Args:
            text: 输入文本

        Returns:
            估算的 token 数
        """
        if not text:
            return 0

        # Count Chinese characters
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        total_chars = len(text)

        if total_chars == 0:
            return 0

        # Calculate weighted average based on Chinese character ratio
        chinese_ratio = chinese_chars / total_chars
        effective_chars_per_token = (
            ContextProcessor.AVG_CHARS_PER_TOKEN_CN * chinese_ratio +
            ContextProcessor.AVG_CHARS_PER_TOKEN_EN * (1 - chinese_ratio)
        )

        return int(total_chars / effective_chars_per_token)

    @staticmethod
    def estimate_messages_tokens(messages: list[dict[str, Any]]) -> int:
        """估算消息列表的总 token 数。

        Args:
            messages: 消息列表

        Returns:
            估算的总 token 数
        """
        total = 0
        for msg in messages:
            # Count role tokens (approximately 4 tokens per role)
            total += 4
            # Count content tokens
            content = msg.get("content", "")
            if isinstance(content, str):
                total += ContextProcessor.estimate_tokens(content)
            elif isinstance(content, list):
                # Handle structured content
                for item in content:
                    if isinstance(item, dict):
                        total += ContextProcessor.estimate_tokens(str(item))
            # Count tool calls if present
            if msg.get("tool_calls"):
                total += ContextProcessor.estimate_tokens(json.dumps(msg["tool_calls"]))
        return total

    @staticmethod
    def micro_compact(
        messages: list[dict[str, Any]],
        keep_last_n: int = 10,
        preserve_system: bool = True,
    ) -> list[dict[str, Any]]:
        """Layer 1: Micro-compact - 替换旧的 tool_result 为占位符。

        保留最近的 N 条消息，将更早的工具调用结果替换为占位符。
        改进版本：更好地处理 tool_calls 和保持消息连贯性。

        Args:
            messages: 消息列表
            keep_last_n: 保留最近 N 条消息包含完整内容
            preserve_system: 是否始终保留 system 消息

        Returns:
            压缩后的消息列表
        """
        if len(messages) <= keep_last_n:
            return messages

        compacted = []
        system_messages = []

        # Extract system messages if preserve_system
        if preserve_system:
            for msg in messages:
                if msg.get("role") == "system":
                    system_messages.append(msg)

        # Find cutoff index
        cutoff_index = len(messages) - keep_last_n

        for i, msg in enumerate(messages):
            # Always preserve system messages
            if msg.get("role") == "system" and preserve_system:
                compacted.append(msg)
                continue

            if i < cutoff_index:
                # Compact old messages
                if msg.get("role") == "user":
                    content = msg.get("content")
                    if isinstance(content, str):
                        try:
                            parsed = json.loads(content)
                            if isinstance(parsed, list) and all(isinstance(item, dict) for item in parsed):
                                # This is tool result content, replace with placeholder
                                compacted.append({
                                    "role": "user",
                                    "content": f"[{len(parsed)} tool results omitted - run compact for details]",
                                })
                                continue
                        except json.JSONDecodeError:
                            pass
                    compacted.append(msg)
                elif msg.get("role") == "assistant":
                    # Compact assistant messages with tool_calls
                    if msg.get("tool_calls"):
                        tool_names = [tc.get("function", {}).get("name", "unknown") for tc in msg["tool_calls"]]
                        compacted.append({
                            "role": "assistant",
                            "content": msg.get("content") or f"[Tool calls: {', '.join(tool_names)} - compacted]",
                        })
                    else:
                        compacted.append(msg)
                else:
                    compacted.append(msg)
            else:
                compacted.append(msg)

        return compacted

    @staticmethod
    def auto_compact(
        messages: list[dict[str, Any]],
        threshold: int = 50000,
        llm_client: Any | None = None,
        model: str | None = None,
    ) -> list[dict[str, Any]]:
        """Layer 2: Auto-compact - token 超阈值时 LLM 摘要。

        当上下文 token 数超过阈值时，使用 LLM 对早期对话进行摘要。

        Args:
            messages: 消息列表
            threshold: token 阈值
            llm_client: OpenAI SDK client (用于调用 LLM 摘要)
            model: 用于摘要的模型名称

        Returns:
            压缩后的消息列表
        """
        total_tokens = ContextProcessor.estimate_messages_tokens(messages)

        if total_tokens <= threshold:
            return messages

        # 找到中间点，保留头部和尾部
        if len(messages) < 6:
            return messages

        keep_head = 3  # 保留 system + 最初的用户查询
        keep_tail = len(messages) - 3  # 保留最近的 3 轮

        # 需要摘要的部分
        to_summarize = messages[keep_head:keep_tail]

        if llm_client and model:
            # 使用 LLM 进行摘要
            summary_prompt = "请对以下对话进行简要摘要，保留关键信息：\n\n"
            for msg in to_summarize:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                if isinstance(content, str):
                    summary_prompt += f"{role}: {content[:500]}\n"  # Truncate long content
                elif isinstance(content, list):
                    summary_prompt += f"{role}: [structured content]\n"

            try:
                response = llm_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "你是一个对话摘要助手。"},
                        {"role": "user", "content": summary_prompt},
                    ],
                    max_tokens=1000,
                )
                summary = response.choices[0].message.content
            except Exception:
                summary = "[Early conversation summarized due to length limit]"
        else:
            summary = "[Early conversation summarized due to length limit]"

        # 构建新的消息列表
        new_messages = messages[:keep_head]
        new_messages.append({"role": "system", "content": f"Previous conversation summary:\n{summary}"})
        new_messages.extend(messages[keep_tail:])

        return new_messages

    @staticmethod
    def isolate_subagent(parent_messages: list[dict[str, Any]], task_description: str) -> list[dict[str, Any]]:
        """Layer 3: SubAgent 上下文隔离。

        为 SubAgent 创建独立的上下文，只传递必要的信息。

        Args:
            parent_messages: 父 Agent 的消息列表
            task_description: 任务描述

        Returns:
            SubAgent 的初始上下文
        """
        # 提取系统提示
        system_prompt = ""
        for msg in parent_messages:
            if msg.get("role") == "system":
                system_prompt = msg.get("content", "")
                break

        # 创建 SubAgent 的初始上下文
        subagent_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task_description},
        ]

        return subagent_messages

    @staticmethod
    def merge_subagent_result(
        parent_messages: list[dict[str, Any]],
        subagent_result: str,
        task_description: str,
    ) -> list[dict[str, Any]]:
        """将 SubAgent 的结果合并到父上下文。

        Args:
            parent_messages: 父 Agent 的消息列表
            subagent_result: SubAgent 的执行结果
            task_description: 原始任务描述

        Returns:
            更新后的消息列表
        """
        parent_messages.append({
            "role": "assistant",
            "content": f"Delegated task: {task_description}",
        })
        parent_messages.append({
            "role": "user",
            "content": f"SubAgent result:\n{subagent_result}",
        })

        return parent_messages

    @staticmethod
    def save_transcript(
        messages: list[dict[str, Any]],
        output_path: str | Path,
        include_metadata: bool = True,
    ) -> Path:
        """Save message transcript to a file.

        Args:
            messages: Message list to save
            output_path: Output file path
            include_metadata: Whether to include metadata

        Returns:
            Path to the saved file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        transcript_data = {
            "timestamp": datetime.now().isoformat(),
            "message_count": len(messages),
            "total_tokens": ContextProcessor.estimate_messages_tokens(messages),
        }

        if include_metadata:
            transcript_data["messages"] = messages
        else:
            # Save simplified version
            simplified = []
            for msg in messages:
                simplified.append({
                    "role": msg.get("role"),
                    "content_preview": str(msg.get("content", ""))[:200] + "...",
                })
            transcript_data["messages"] = simplified

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(transcript_data, f, ensure_ascii=False, indent=2)

        return output_path

    @staticmethod
    def load_transcript(file_path: str | Path) -> list[dict[str, Any]]:
        """Load message transcript from a file.

        Args:
            file_path: Path to transcript file

        Returns:
            Message list

        Raises:
            FileNotFoundError: File not found
            json.JSONDecodeError: Invalid JSON format
        """
        file_path = Path(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data.get("messages", [])

    @staticmethod
    def format_for_display(messages: list[dict[str, Any]]) -> str:
        """Format messages for display.

        Args:
            messages: Message list

        Returns:
            Formatted string
        """
        lines = []
        for i, msg in enumerate(messages, 1):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if isinstance(content, str):
                content_preview = content[:100] + "..." if len(content) > 100 else content
            else:
                content_preview = "[structured content]"

            # Add tool call info
            if msg.get("tool_calls"):
                tool_names = [tc.get("function", {}).get("name", "?") for tc in msg["tool_calls"]]
                content_preview += f" [tools: {', '.join(tool_names)}]"

            lines.append(f"{i}. [{role}] {content_preview}")

        return "\n".join(lines)
