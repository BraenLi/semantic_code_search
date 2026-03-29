"""Logger module."""

from .local_logger import LocalLogger
from .remote_logger import RemoteLogger

__all__ = ["LocalLogger", "RemoteLogger"]
