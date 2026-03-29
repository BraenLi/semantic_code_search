"""Core components of AgentForge."""

from .agent import Agent
from .context import ContextProcessor
from .models.config import ModelConfig
from .models.client import get_client
from .todo import TodoManager, TodoList, TodoItem, TodoStatus
from .task import TaskManager, Task, TaskStatus
from .background import BackgroundManager, BackgroundTask, BackgroundTaskStatus
from .messaging import MessageBus, Message, MessageType, MessagePriority, TeammateManager

__all__ = [
    # Core
    "Agent",
    "ContextProcessor",
    "ModelConfig",
    "get_client",
    # Todo management
    "TodoManager",
    "TodoList",
    "TodoItem",
    "TodoStatus",
    # Task management
    "TaskManager",
    "Task",
    "TaskStatus",
    # Background tasks
    "BackgroundManager",
    "BackgroundTask",
    "BackgroundTaskStatus",
    # Messaging
    "MessageBus",
    "Message",
    "MessageType",
    "MessagePriority",
    "TeammateManager",
]
