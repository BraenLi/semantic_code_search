"""消息总线 - Agent 间消息传递。

设计原则:
1. 点对点消息 - 直接发送给指定 Agent
2. 广播消息 - 发送给所有 Agent
3. Inbox 机制 - 每个 Agent 有独立收件箱
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable


class MessageType(str, Enum):
    """消息类型枚举。"""

    DIRECT = "direct"  # 点对点
    BROADCAST = "broadcast"  # 广播
    REQUEST = "request"  # 请求
    RESPONSE = "response"  # 响应


class MessagePriority(str, Enum):
    """消息优先级枚举。"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Message:
    """消息数据类。"""

    id: str
    sender: str
    receiver: str | None  # None 表示广播
    content: Any
    message_type: MessageType = MessageType.DIRECT
    priority: MessagePriority = MessagePriority.NORMAL
    reply_to: str | None = None  # 回复的消息 ID
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    read_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典。"""
        return {
            "id": self.id,
            "sender": self.sender,
            "receiver": self.receiver,
            "content": self.content,
            "message_type": self.message_type.value,
            "priority": self.priority.value,
            "reply_to": self.reply_to,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "read_at": self.read_at,
        }

    def mark_read(self) -> None:
        """标记为已读。"""
        self.read_at = datetime.now().isoformat()


@dataclass
class Inbox:
    """收件箱。"""

    agent_id: str
    messages: list[Message] = field(default_factory=list)
    max_size: int = 100

    def add(self, message: Message) -> bool:
        """添加消息。

        Args:
            message: 消息对象

        Returns:
            是否成功（收件箱满时返回 False）
        """
        if len(self.messages) >= self.max_size:
            # Remove oldest read message
            for i, msg in enumerate(self.messages):
                if msg.read_at:
                    self.messages.pop(i)
                    break
            else:
                return False  # Inbox full

        self.messages.append(message)
        return True

    def get_unread(self) -> list[Message]:
        """获取未读消息。

        Returns:
            未读消息列表
        """
        return [msg for msg in self.messages if msg.read_at is None]

    def get_all(self) -> list[Message]:
        """获取所有消息。

        Returns:
            所有消息列表
        """
        return self.messages.copy()

    def mark_all_read(self) -> int:
        """标记所有消息为已读。

        Returns:
            标记的消息数量
        """
        count = 0
        for msg in self.messages:
            if msg.read_at is None:
                msg.mark_read()
                count += 1
        return count

    def clear_read(self) -> int:
        """清除已读消息。

        Returns:
            清除的消息数量
        """
        initial_count = len(self.messages)
        self.messages = [msg for msg in self.messages if msg.read_at is None]
        return initial_count - len(self.messages)


class MessageBus:
    """消息总线 - 管理 Agent 间消息传递。

    使用方式:
        bus = MessageBus()
        bus.register("agent1")
        bus.register("agent2")
        bus.send("agent1", "agent2", {"task": "process data"})
        messages = bus.receive("agent2")
    """

    def __init__(self, max_inbox_size: int = 100):
        """初始化消息总线。

        Args:
            max_inbox_size: 收件箱最大容量
        """
        self._inboxes: dict[str, Inbox] = {}
        self._max_inbox_size = max_inbox_size
        self._message_handlers: dict[str, list[Callable[[Message], None]]] = {}
        self._broadcast_handlers: list[Callable[[Message], None]] = []

    def register(self, agent_id: str) -> bool:
        """注册 Agent。

        Args:
            agent_id: Agent ID

        Returns:
            是否成功（已存在则返回 False）
        """
        if agent_id in self._inboxes:
            return False

        self._inboxes[agent_id] = Inbox(agent_id=agent_id, max_size=self._max_inbox_size)
        self._message_handlers[agent_id] = []
        return True

    def unregister(self, agent_id: str) -> bool:
        """注销 Agent。

        Args:
            agent_id: Agent ID

        Returns:
            是否成功
        """
        if agent_id not in self._inboxes:
            return False

        del self._inboxes[agent_id]
        del self._message_handlers[agent_id]
        return True

    def _generate_message_id(self) -> str:
        """生成消息 ID。"""
        return str(uuid.uuid4())[:8]

    def send(
        self,
        sender: str,
        receiver: str,
        content: Any,
        message_type: MessageType = MessageType.DIRECT,
        priority: MessagePriority = MessagePriority.NORMAL,
        reply_to: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str | None:
        """发送消息。

        Args:
            sender: 发送者 ID
            receiver: 接收者 ID
            content: 消息内容
            message_type: 消息类型
            priority: 优先级
            reply_to: 回复的消息 ID
            metadata: 元数据

        Returns:
            消息 ID，失败返回 None
        """
        if receiver not in self._inboxes:
            return None

        message = Message(
            id=self._generate_message_id(),
            sender=sender,
            receiver=receiver,
            content=content,
            message_type=message_type,
            priority=priority,
            reply_to=reply_to,
            metadata=metadata or {},
        )

        inbox = self._inboxes[receiver]
        if inbox.add(message):
            # Call message handlers
            for handler in self._message_handlers.get(receiver, []):
                try:
                    handler(message)
                except Exception:
                    pass
            return message.id

        return None

    def broadcast(
        self,
        sender: str,
        content: Any,
        priority: MessagePriority = MessagePriority.NORMAL,
        exclude: list[str] | None = None,
    ) -> list[str]:
        """广播消息。

        Args:
            sender: 发送者 ID
            content: 消息内容
            priority: 优先级
            exclude: 排除的 Agent ID 列表

        Returns:
            成功发送的消息 ID 列表
        """
        exclude = exclude or []
        message_ids = []

        message = Message(
            id=self._generate_message_id(),
            sender=sender,
            receiver=None,
            content=content,
            message_type=MessageType.BROADCAST,
            priority=priority,
        )

        for agent_id, inbox in self._inboxes.items():
            if agent_id == sender or agent_id in exclude:
                continue

            # Create a copy for each receiver
            msg_copy = Message(
                id=self._generate_message_id(),
                sender=sender,
                receiver=agent_id,
                content=content,
                message_type=MessageType.BROADCAST,
                priority=priority,
            )

            if inbox.add(msg_copy):
                message_ids.append(msg_copy.id)
                # Call handlers
                for handler in self._message_handlers.get(agent_id, []):
                    try:
                        handler(msg_copy)
                    except Exception:
                        pass

        # Call broadcast handlers
        for handler in self._broadcast_handlers:
            try:
                handler(message)
            except Exception:
                pass

        return message_ids

    def request(
        self,
        sender: str,
        receiver: str,
        content: Any,
        timeout: float | None = None,
    ) -> Message | None:
        """发送请求并等待响应。

        Args:
            sender: 发送者 ID
            receiver: 接收者 ID
            content: 消息内容
            timeout: 超时时间（秒）

        Returns:
            响应消息，超时返回 None
        """
        # This is a simplified synchronous request
        # In practice, you'd use async/await or threading
        message_id = self.send(
            sender=sender,
            receiver=receiver,
            content=content,
            message_type=MessageType.REQUEST,
        )
        if message_id is None:
            return None

        # Wait for response (simplified - in practice use proper async)
        # For now, just check inbox for response
        # Real implementation would use threading.Event or asyncio.Event
        return None

    def respond(
        self,
        sender: str,
        original_message_id: str,
        content: Any,
    ) -> str | None:
        """回复消息。

        Args:
            sender: 发送者 ID
            original_message_id: 原消息 ID
            content: 响应内容

        Returns:
            响应消息 ID
        """
        # Find the original message to get the sender
        for agent_id, inbox in self._inboxes.items():
            for msg in inbox.messages:
                if msg.id == original_message_id:
                    return self.send(
                        sender=sender,
                        receiver=msg.sender,
                        content=content,
                        message_type=MessageType.RESPONSE,
                        reply_to=original_message_id,
                    )
        return None

    def receive(self, agent_id: str, unread_only: bool = True) -> list[dict[str, Any]]:
        """接收消息。

        Args:
            agent_id: Agent ID
            unread_only: 是否只获取未读消息

        Returns:
            消息字典列表
        """
        if agent_id not in self._inboxes:
            return []

        inbox = self._inboxes[agent_id]
        messages = inbox.get_unread() if unread_only else inbox.get_all()
        return [msg.to_dict() for msg in messages]

    def mark_read(self, agent_id: str, message_id: str | None = None) -> bool:
        """标记消息为已读。

        Args:
            agent_id: Agent ID
            message_id: 消息 ID，None 表示所有消息

        Returns:
            是否成功
        """
        if agent_id not in self._inboxes:
            return False

        inbox = self._inboxes[agent_id]
        if message_id is None:
            inbox.mark_all_read()
            return True

        for msg in inbox.messages:
            if msg.id == message_id:
                msg.mark_read()
                return True

        return False

    def add_message_handler(self, agent_id: str, handler: Callable[[Message], None]) -> bool:
        """添加消息处理器。

        Args:
            agent_id: Agent ID
            handler: 处理函数

        Returns:
            是否成功
        """
        if agent_id not in self._message_handlers:
            return False
        self._message_handlers[agent_id].append(handler)
        return True

    def add_broadcast_handler(self, handler: Callable[[Message], None]) -> None:
        """添加广播处理器。

        Args:
            handler: 处理函数
        """
        self._broadcast_handlers.append(handler)

    def get_inbox_status(self, agent_id: str) -> dict[str, Any]:
        """获取收件箱状态。

        Args:
            agent_id: Agent ID

        Returns:
            收件箱状态字典
        """
        if agent_id not in self._inboxes:
            return {"error": f"Agent not registered: {agent_id}"}

        inbox = self._inboxes[agent_id]
        unread = inbox.get_unread()
        return {
            "agent_id": agent_id,
            "total_messages": len(inbox.messages),
            "unread_count": len(unread),
            "max_size": inbox.max_size,
        }

    def list_agents(self) -> list[str]:
        """列出所有注册的 Agent。

        Returns:
            Agent ID 列表
        """
        return list(self._inboxes.keys())

    def clear_inbox(self, agent_id: str) -> int:
        """清空收件箱。

        Args:
            agent_id: Agent ID

        Returns:
            清除的消息数量
        """
        if agent_id not in self._inboxes:
            return 0
        count = len(self._inboxes[agent_id].messages)
        self._inboxes[agent_id].messages.clear()
        return count


class TeammateManager:
    """队友管理器 - 管理 Agent 团队协作。

    使用方式:
        team = TeammateManager()
        team.add_teammate("coder", "Code implementation specialist")
        team.add_teammate("reviewer", "Code review specialist")
        team.delegate("coder", "Implement the login feature")
    """

    def __init__(self, message_bus: MessageBus | None = None):
        """初始化队友管理器。

        Args:
            message_bus: 消息总线实例
        """
        self.message_bus = message_bus or MessageBus()
        self._teammates: dict[str, dict[str, Any]] = {}

    def add_teammate(
        self,
        agent_id: str,
        description: str,
        capabilities: list[str] | None = None,
    ) -> bool:
        """添加队友。

        Args:
            agent_id: Agent ID
            description: 描述
            capabilities: 能力列表

        Returns:
            是否成功
        """
        if agent_id in self._teammates:
            return False

        self._teammates[agent_id] = {
            "id": agent_id,
            "description": description,
            "capabilities": capabilities or [],
            "status": "available",
        }
        self.message_bus.register(agent_id)
        return True

    def remove_teammate(self, agent_id: str) -> bool:
        """移除队友。

        Args:
            agent_id: Agent ID

        Returns:
            是否成功
        """
        if agent_id not in self._teammates:
            return False

        del self._teammates[agent_id]
        self.message_bus.unregister(agent_id)
        return True

    def delegate(
        self,
        target: str,
        task: str,
        sender: str = "coordinator",
    ) -> str | None:
        """委托任务。

        Args:
            target: 目标 Agent ID
            task: 任务描述
            sender: 发送者 ID

        Returns:
            消息 ID
        """
        return self.message_bus.send(
            sender=sender,
            receiver=target,
            content={"task": task},
            message_type=MessageType.REQUEST,
        )

    def broadcast_task(
        self,
        task: str,
        sender: str = "coordinator",
        exclude: list[str] | None = None,
    ) -> list[str]:
        """广播任务。

        Args:
            task: 任务描述
            sender: 发送者 ID
            exclude: 排除的 Agent ID 列表

        Returns:
            消息 ID 列表
        """
        return self.message_bus.broadcast(
            sender=sender,
            content={"task": task},
            exclude=exclude,
        )

    def get_teammate(self, agent_id: str) -> dict[str, Any] | None:
        """获取队友信息。

        Args:
            agent_id: Agent ID

        Returns:
            队友信息字典
        """
        return self._teammates.get(agent_id)

    def list_teammates(self) -> list[dict[str, Any]]:
        """列出所有队友。

        Returns:
            队友信息列表
        """
        return list(self._teammates.values())

    def find_by_capability(self, capability: str) -> list[str]:
        """根据能力查找队友。

        Args:
            capability: 能力关键词

        Returns:
            匹配的 Agent ID 列表
        """
        matched = []
        for agent_id, info in self._teammates.items():
            if capability.lower() in [c.lower() for c in info.get("capabilities", [])]:
                matched.append(agent_id)
        return matched

    def set_status(self, agent_id: str, status: str) -> bool:
        """设置队友状态。

        Args:
            agent_id: Agent ID
            status: 状态

        Returns:
            是否成功
        """
        if agent_id not in self._teammates:
            return False
        self._teammates[agent_id]["status"] = status
        return True