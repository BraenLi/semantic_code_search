/**
 * WebSocket 客户端服务
 */

class QENASWebSocket {
  constructor() {
    this.ws = null
    this.clientId = null
    this.connected = false
    this.reconnectTimer = null
    this.messageHandlers = new Map()
    this.reconnectInterval = 5000
  }

  /**
   * 连接 WebSocket
   */
  connect(host = window.location.hostname, port = 8000) {
    this.clientId = `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${host}:${port}/ws/qenas/${this.clientId}`

    console.log(`连接 WebSocket: ${wsUrl}`)

    this.ws = new WebSocket(wsUrl)

    this.ws.onopen = () => {
      this.connected = true
      console.log('WebSocket 已连接')
      this.emit('connected', { clientId: this.clientId })
    }

    this.ws.onclose = () => {
      this.connected = false
      console.log('WebSocket 已断开')
      this.emit('disconnected')
      // 自动重连
      this.scheduleReconnect(host, port)
    }

    this.ws.onerror = (error) => {
      console.error('WebSocket 错误:', error)
      this.emit('error', error)
    }

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        this.handleMessage(message)
      } catch (error) {
        console.error('解析 WebSocket 消息失败:', error)
      }
    }
  }

  /**
   * 处理接收到的消息
   */
  handleMessage(message) {
    const { type, data, timestamp } = message

    // 调用注册的处理器
    if (this.messageHandlers.has(type)) {
      this.messageHandlers.get(type).forEach(handler => {
        try {
          handler({ type, data, timestamp })
        } catch (error) {
          console.error(`处理消息 ${type} 失败:`, error)
        }
      })
    }

    // 通用消息处理
    switch (type) {
      case 'connected':
        console.log('服务器响应:', data)
        break
      case 'entanglement_update':
        console.log('纠缠矩阵更新:', data)
        break
      case 'event_alert':
        console.log('事件告警:', data)
        break
      case 'performance_update':
        console.log('业绩更新:', data)
        break
      case 'ecosystem_status':
        console.log('生态系统状态:', data)
        break
    }
  }

  /**
   * 安排重连
   */
  scheduleReconnect(host, port) {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
    }

    this.reconnectTimer = setTimeout(() => {
      console.log('尝试重新连接...')
      this.connect(host, port)
    }, this.reconnectInterval)
  }

  /**
   * 断开连接
   */
  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    if (this.ws) {
      this.ws.close()
      this.ws = null
    }

    this.connected = false
  }

  /**
   * 注册消息处理器
   */
  on(messageType, handler) {
    if (!this.messageHandlers.has(messageType)) {
      this.messageHandlers.set(messageType, [])
    }
    this.messageHandlers.get(messageType).push(handler)

    // 返回取消订阅函数
    return () => this.off(messageType, handler)
  }

  /**
   * 移除消息处理器
   */
  off(messageType, handler) {
    if (this.messageHandlers.has(messageType)) {
      const handlers = this.messageHandlers.get(messageType)
      const index = handlers.indexOf(handler)
      if (index > -1) {
        handlers.splice(index, 1)
      }
    }
  }

  /**
   * 触发事件
   */
  emit(eventType, data) {
    if (this.messageHandlers.has(eventType)) {
      this.messageHandlers.get(eventType).forEach(handler => {
        try {
          handler(data)
        } catch (error) {
          console.error(`触发事件 ${eventType} 失败:`, error)
        }
      })
    }
  }

  /**
   * 订阅主题
   */
  subscribe(topics) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'subscribe',
        topics: Array.isArray(topics) ? topics : [topics],
      }))
    }
  }

  /**
   * 取消订阅主题
   */
  unsubscribe(topics) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'unsubscribe',
        topics: Array.isArray(topics) ? topics : [topics],
      }))
    }
  }

  /**
   * 发送心跳
   */
  ping() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'ping' }))
    }
  }

  /**
   * 获取连接状态
   */
  isConnected() {
    return this.connected && this.ws && this.ws.readyState === WebSocket.OPEN
  }
}

// 单例
let instance = null

export function useWebSocket() {
  if (!instance) {
    instance = new QENASWebSocket()
  }
  return instance
}

export default QENASWebSocket
