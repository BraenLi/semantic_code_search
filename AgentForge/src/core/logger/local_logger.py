"""本地日志记录。"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any


class LocalLogger:
    """本地日志记录器 - 记录 Agent 执行日志到本地文件。

    日志格式:
    - 结构化 JSON 日志
    - 按日期分割文件
    - 支持不同级别
    """

    def __init__(
        self,
        log_dir: str | Path | None = None,
        level: int = logging.INFO,
        format_str: str | None = None,
    ):
        """初始化本地日志记录器。

        Args:
            log_dir: 日志目录，默认为 ./logs
            level: 日志级别
            format_str: 日志格式
        """
        if log_dir is None:
            log_dir = Path(__file__).parent.parent.parent.parent / "logs"
        else:
            log_dir = Path(log_dir)

        log_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir = log_dir

        # 创建 logger
        self.logger = logging.getLogger("agentforge")
        self.logger.setLevel(level)

        # 清除已有的 handlers
        self.logger.handlers.clear()

        # 文件 handler - 按日期分割
        log_file = log_dir / f"agentforge_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)

        # 控制台 handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)

        # 设置格式
        if format_str is None:
            format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        formatter = logging.Formatter(format_str)

        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        # 会话日志 (完整的 Agent 交互记录)
        self.session_logs: list[dict[str, Any]] = []
        self.session_id: str = datetime.now().strftime("%Y%m%d_%H%M%S")

    def debug(self, msg: str, **kwargs: Any) -> None:
        """记录 debug 日志。"""
        self.logger.debug(msg, extra=kwargs)

    def info(self, msg: str, **kwargs: Any) -> None:
        """记录 info 日志。"""
        self.logger.info(msg, extra=kwargs)

    def warning(self, msg: str, **kwargs: Any) -> None:
        """记录 warning 日志。"""
        self.logger.warning(msg, extra=kwargs)

    def error(self, msg: str, **kwargs: Any) -> None:
        """记录 error 日志。"""
        self.logger.error(msg, extra=kwargs)

    def log_event(
        self,
        event_type: str,
        data: dict[str, Any],
        session_id: str | None = None,
    ) -> None:
        """记录结构化事件。

        Args:
            event_type: 事件类型
            data: 事件数据
            session_id: 会话 ID
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "session_id": session_id or self.session_id,
            "data": data,
        }
        self.session_logs.append(event)
        self.logger.info(f"[{event_type}] {json.dumps(data, ensure_ascii=False)}")

    def log_message(
        self,
        role: str,
        content: str,
        message_id: str | None = None,
    ) -> None:
        """记录消息。

        Args:
            role: 消息角色 (user/assistant/system)
            content: 消息内容
            message_id: 消息 ID
        """
        self.log_event("message", {"role": role, "content": content, "message_id": message_id})

    def log_tool_call(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        result: Any | None = None,
        error: str | None = None,
    ) -> None:
        """记录工具调用。

        Args:
            tool_name: 工具名称
            arguments: 调用参数
            result: 执行结果
            error: 错误信息
        """
        self.log_event(
            "tool_call",
            {
                "tool_name": tool_name,
                "arguments": arguments,
                "result": result,
                "error": error,
            },
        )

    def save_session_log(self, filename: str | None = None) -> Path:
        """保存会话日志到文件。

        Args:
            filename: 文件名，None 时自动生成

        Returns:
            日志文件路径
        """
        if filename is None:
            filename = f"session_{self.session_id}.json"

        log_path = self.log_dir / filename
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(self.session_logs, f, ensure_ascii=False, indent=2)

        self.logger.info(f"Session log saved to {log_path}")
        return log_path

    def clear_session(self) -> None:
        """清除当前会话日志。"""
        self.session_logs.clear()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
