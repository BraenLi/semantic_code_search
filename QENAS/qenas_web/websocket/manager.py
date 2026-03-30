"""WebSocket 连接管理器."""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
import asyncio
import json
import logging
from datetime import datetime

from qenas_web.config import settings

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    WebSocket 连接管理器.

    管理所有 WebSocket 连接，支持：
    - 多客户端连接
    - 广播消息
    - 个人消息
    - 连接状态监控
    """

    def __init__(self):
        # 活跃连接：client_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        # 订阅主题：topic -> set of client_ids
        self.subscriptions: Dict[str, Set[str]] = {
            "entanglement": set(),
            "events": set(),
            "performance": set(),
            "ecosystem": set(),
        }
        # 连接锁
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, client_id: str) -> bool:
        """
        接受 WebSocket 连接.

        Args:
            websocket: WebSocket 连接
            client_id: 客户端 ID

        Returns:
            是否连接成功
        """
        try:
            await websocket.accept()
            async with self._lock:
                self.active_connections[client_id] = websocket
            logger.info(f"客户端 {client_id} 已连接，当前连接数：{len(self.active_connections)}")
            return True
        except Exception as e:
            logger.error(f"连接客户端 {client_id} 失败：{e}")
            return False

    def disconnect(self, client_id: str) -> None:
        """
        断开 WebSocket 连接.

        Args:
            client_id: 客户端 ID
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]

        # 清理订阅
        for topic in self.subscriptions.values():
            topic.discard(client_id)

        logger.info(f"客户端 {client_id} 已断开，当前连接数：{len(self.active_connections)}")

    async def send_personal(self, client_id: str, message: dict) -> bool:
        """
        发送个人消息.

        Args:
            client_id: 客户端 ID
            message: 消息字典

        Returns:
            是否发送成功
        """
        websocket = self.active_connections.get(client_id)
        if websocket:
            try:
                await websocket.send_json(message)
                return True
            except Exception as e:
                logger.error(f"发送消息到客户端 {client_id} 失败：{e}")
                self.disconnect(client_id)
                return False
        return False

    async def broadcast(self, message: dict, exclude: List[str] = None) -> int:
        """
        广播消息给所有连接的客户端.

        Args:
            message: 消息字典
            exclude: 要排除的客户端 ID 列表

        Returns:
            成功发送的客户端数量
        """
        exclude = exclude or []
        sent_count = 0

        async with self._lock:
            clients_to_remove = []

            for client_id, websocket in self.active_connections.items():
                if client_id in exclude:
                    continue

                try:
                    await websocket.send_json(message)
                    sent_count += 1
                except Exception as e:
                    logger.warning(f"广播消息到客户端 {client_id} 失败：{e}")
                    clients_to_remove.append(client_id)

            # 清理失败的连接
            for client_id in clients_to_remove:
                self.disconnect(client_id)

        logger.debug(f"广播消息完成，成功发送：{sent_count}/{len(self.active_connections)}")
        return sent_count

    async def broadcast_to_topic(self, topic: str, message: dict) -> int:
        """
        广播消息到订阅特定主题的客户端.

        Args:
            topic: 主题名称
            message: 消息字典

        Returns:
            成功发送的客户端数量
        """
        if topic not in self.subscriptions:
            logger.warning(f"未知主题：{topic}")
            return 0

        subscribers = self.subscriptions[topic]
        sent_count = 0

        for client_id in subscribers:
            if await self.send_personal(client_id, message):
                sent_count += 1

        return sent_count

    def subscribe(self, client_id: str, topic: str) -> bool:
        """
        订阅主题.

        Args:
            client_id: 客户端 ID
            topic: 主题名称

        Returns:
            是否订阅成功
        """
        if topic not in self.subscriptions:
            logger.warning(f"未知主题：{topic}")
            return False

        self.subscriptions[topic].add(client_id)
        logger.info(f"客户端 {client_id} 订阅主题：{topic}")
        return True

    def unsubscribe(self, client_id: str, topic: str) -> None:
        """
        取消订阅主题.

        Args:
            client_id: 客户端 ID
            topic: 主题名称
        """
        if topic in self.subscriptions:
            self.subscriptions[topic].discard(client_id)
            logger.info(f"客户端 {client_id} 取消订阅主题：{topic}")

    async def disconnect_all(self) -> None:
        """断开所有连接."""
        async with self._lock:
            for client_id in list(self.active_connections.keys()):
                try:
                    websocket = self.active_connections[client_id]
                    await websocket.close()
                except Exception:
                    pass
            self.active_connections.clear()

        logger.info("所有 WebSocket 连接已断开")

    def get_connection_count(self) -> int:
        """获取当前连接数."""
        return len(self.active_connections)

    def get_subscriber_count(self, topic: str) -> int:
        """获取主题订阅数."""
        return len(self.subscriptions.get(topic, set()))


# 全局 WebSocket 管理器实例
manager = ConnectionManager()


class WebSocketManager:
    """
    QENAS WebSocket 管理器.

    提供高级消息推送功能：
    - 纠缠矩阵更新
    - 事件告警
    - 业绩更新
    - 生态系统状态
    """

    def __init__(self):
        self.connection_manager = ConnectionManager()

    async def connect(self, websocket: WebSocket, client_id: str) -> bool:
        """连接 WebSocket."""
        return await self.connection_manager.connect(websocket, client_id)

    def disconnect(self, client_id: str) -> None:
        """断开连接."""
        self.connection_manager.disconnect(client_id)

    def subscribe(self, client_id: str, topics: List[str]) -> None:
        """订阅主题."""
        for topic in topics:
            self.connection_manager.subscribe(client_id, topic)

    def unsubscribe(self, client_id: str, topics: List[str]) -> None:
        """取消订阅."""
        for topic in topics:
            self.connection_manager.unsubscribe(client_id, topic)

    async def broadcast_entanglement_update(
        self,
        matrix: List[List[float]],
        symbols: List[str],
        entropy: float,
    ) -> int:
        """
        广播纠缠矩阵更新.

        Args:
            matrix: 纠缠矩阵
            symbols: 资产符号列表
            entropy: 纠缠熵

        Returns:
            成功发送的客户端数量
        """
        message = {
            "type": "entanglement_update",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "matrix": matrix,
                "symbols": symbols,
                "entropy": entropy,
            },
        }
        return await self.connection_manager.broadcast_to_topic("entanglement", message)

    async def broadcast_event_alert(
        self,
        event: dict,
    ) -> int:
        """
        广播事件告警.

        Args:
            event: 事件数据

        Returns:
            成功发送的客户端数量
        """
        message = {
            "type": "event_alert",
            "timestamp": datetime.utcnow().isoformat(),
            "data": event,
        }
        return await self.connection_manager.broadcast_to_topic("events", message)

    async def broadcast_performance_update(
        self,
        equity_curve: List[float],
        returns: List[float],
        metrics: dict,
    ) -> int:
        """
        广播业绩更新.

        Args:
            equity_curve: 权益曲线
            returns: 收益率序列
            metrics: 绩效指标

        Returns:
            成功发送的客户端数量
        """
        message = {
            "type": "performance_update",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "equity_curve": equity_curve,
                "returns": returns,
                "metrics": metrics,
            },
        }
        return await self.connection_manager.broadcast_to_topic("performance", message)

    async def broadcast_ecosystem_status(
        self,
        status: dict,
    ) -> int:
        """
        广播生态系统状态.

        Args:
            status: 生态系统状态数据

        Returns:
            成功发送的客户端数量
        """
        message = {
            "type": "ecosystem_status",
            "timestamp": datetime.utcnow().isoformat(),
            "data": status,
        }
        return await self.connection_manager.broadcast_to_topic("ecosystem", message)

    async def disconnect_all(self) -> None:
        """断开所有连接."""
        await self.connection_manager.disconnect_all()

    def get_connection_count(self) -> int:
        """获取连接数."""
        return self.connection_manager.get_connection_count()
