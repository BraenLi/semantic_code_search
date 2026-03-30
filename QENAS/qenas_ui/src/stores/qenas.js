import { defineStore } from 'pinia'

export default defineStore('qenas', {
  state: () => ({
    // WebSocket 连接状态
    wsConnected: false,
    wsClient: null,

    // 策略列表
    strategies: [],
    currentStrategy: null,

    // 回测任务
    backtestJobs: [],
    currentJob: null,

    // 实时数据
    entanglementMatrix: null,
    entropy: 0,
    ecosystemStatus: null,
    performanceData: null,
  }),

  actions: {
    // WebSocket 连接
    connectWebSocket() {
      const clientId = `client_${Date.now()}`
      const wsUrl = `ws://${window.location.hostname}:5173/ws/qenas/${clientId}`

      this.wsClient = new WebSocket(wsUrl)

      this.wsClient.onopen = () => {
        this.wsConnected = true
        console.log('WebSocket 已连接')
      }

      this.wsClient.onclose = () => {
        this.wsConnected = false
        console.log('WebSocket 已断开')
        // 自动重连
        setTimeout(() => this.connectWebSocket(), 5000)
      }

      this.wsClient.onmessage = (event) => {
        const message = JSON.parse(event.data)
        this.handleWebSocketMessage(message)
      }

      this.wsClient.onerror = (error) => {
        console.error('WebSocket 错误:', error)
      }
    },

    handleWebSocketMessage(message) {
      switch (message.type) {
        case 'entanglement_update':
          this.entanglementMatrix = message.data.matrix
          this.entropy = message.data.entropy
          break
        case 'event_alert':
          console.log('事件告警:', message.data)
          break
        case 'performance_update':
          this.performanceData = message.data
          break
        case 'ecosystem_status':
          this.ecosystemStatus = message.data
          break
      }
    },

    disconnectWebSocket() {
      if (this.wsClient) {
        this.wsClient.close()
        this.wsClient = null
        this.wsConnected = false
      }
    },

    // API 调用
    async fetchStrategies() {
      try {
        const response = await fetch('/api/v1/strategies')
        this.strategies = await response.json()
      } catch (error) {
        console.error('获取策略列表失败:', error)
      }
    },

    async fetchBacktestJobs() {
      try {
        const response = await fetch('/api/v1/backtest')
        this.backtestJobs = await response.json()
      } catch (error) {
        console.error('获取回测任务失败:', error)
      }
    },

    async fetchDashboardData() {
      try {
        const response = await fetch('/api/v1/visualization/dashboard')
        return await response.json()
      } catch (error) {
        console.error('获取仪表板数据失败:', error)
        return null
      }
    },
  },
})
