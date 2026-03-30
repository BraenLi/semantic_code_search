"""WebSocket 端点 API."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import logging

from qenas_web.websocket.manager import manager as ws_manager
from qenas_web.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/qenas/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    topics: str = Query(default="entanglement,events,performance,ecosystem"),
):
    """
    WebSocket 连接端点.

    Args:
        client_id: 客户端唯一标识
        topics: 订阅的主题列表（逗号分隔）
    """
    # 连接 WebSocket
    connected = await ws_manager.connect(websocket, client_id)
    if not connected:
        return

    # 解析并订阅主题
    topic_list = [t.strip() for t in topics.split(",")]
    ws_manager.subscribe(client_id, topic_list)

    # 发送欢迎消息
    await websocket.send_json({
        "type": "connected",
        "client_id": client_id,
        "topics": topic_list,
        "message": f"已连接到 QENAS WebSocket，订阅主题：{topic_list}",
    })

    try:
        # 保持连接并处理客户端消息
        while True:
            data = await websocket.receive_text()

            # 处理客户端发送的消息
            try:
                message = eval(data)
                msg_type = message.get("type")

                if msg_type == "subscribe":
                    # 订阅新主题
                    new_topics = message.get("topics", [])
                    for topic in new_topics:
                        ws_manager.subscribe(client_id, topic)
                    await websocket.send_json({
                        "type": "subscribed",
                        "topics": new_topics,
                    })

                elif msg_type == "unsubscribe":
                    # 取消订阅
                    topics_to_remove = message.get("topics", [])
                    for topic in topics_to_remove:
                        ws_manager.unsubscribe(client_id, topic)
                    await websocket.send_json({
                        "type": "unsubscribed",
                        "topics": topics_to_remove,
                    })

                elif msg_type == "ping":
                    # 心跳检测
                    await websocket.send_json({"type": "pong"})

            except Exception as e:
                logger.error(f"处理客户端消息失败：{e}")

    except WebSocketDisconnect:
        logger.info(f"客户端 {client_id} 断开连接")
    except Exception as e:
        logger.error(f"WebSocket 错误：{e}")
    finally:
        ws_manager.disconnect(client_id)
