<template>
  <div class="space-y-6">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-white">实时监控</h1>
      <div class="flex items-center space-x-2">
        <span
          class="w-2 h-2 rounded-full"
          :class="wsConnected ? 'bg-green-500' : 'bg-red-500'"
        ></span>
        <span class="text-sm text-slate-400">
          {{ wsConnected ? '已连接' : '未连接' }}
        </span>
      </div>
    </div>

    <!-- 实时纠缠矩阵 -->
    <div class="card">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold">实时纠缠矩阵</h2>
        <div class="text-sm text-slate-400">
          熵值：<span class="text-blue-400 font-mono">{{ entropy?.toFixed(4) ?? '0.0000' }}</span>
        </div>
      </div>

      <EntanglementMatrix
        :matrix="entanglementMatrix"
        :symbols="symbols"
        :entropy="entropy"
        :height="400"
      />
    </div>

    <!-- 实时事件流 -->
    <div class="card">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold">实时事件流</h2>
        <span class="text-sm text-slate-400">共 {{ events.length }} 个事件</span>
      </div>

      <div class="max-h-96 overflow-y-auto">
        <EventTimeline :events="events" :maxDisplay="events.length" />
      </div>
    </div>

    <!-- 生态系统状态 -->
    <div class="card">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold">生态系统状态</h2>
      </div>

      <EcosystemView
        :totalSpecies="ecosystemStatus?.total_species || 100"
        :nicheDistribution="ecosystemStatus?.niche_distribution"
        :fitnessDistribution="ecosystemStatus?.fitness_distribution"
        :diversityIndex="ecosystemStatus?.diversity_index"
      />
    </div>

    <!-- 性能指标 -->
    <div class="card">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold">实时性能</h2>
      </div>

      <EquityCurve
        :equityCurve="performanceData?.equity_curve"
        :metrics="performanceData?.metrics"
        :height="300"
      />
    </div>

    <!-- WebSocket 连接控制 -->
    <div class="fixed bottom-4 right-4">
      <button
        @click="toggleConnection"
        class="px-4 py-2 rounded-lg shadow-lg text-sm font-medium transition-colors"
        :class="wsConnected ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'"
      >
        {{ wsConnected ? '断开连接' : '重新连接' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import EntanglementMatrix from '@/components/EntanglementMatrix.vue'
import EventTimeline from '@/components/EventTimeline.vue'
import EcosystemView from '@/components/EcosystemView.vue'
import EquityCurve from '@/components/EquityCurve.vue'
import { visualizationApi } from '@/services/api'
import { useWebSocket } from '@/services/websocket'

const wsConnected = ref(false)
const entanglementMatrix = ref(null)
const symbols = ref([])
const entropy = ref(0)
const events = ref([])
const ecosystemStatus = ref(null)
const performanceData = ref(null)

let ws = null

const initializeWebSocket = () => {
  ws = useWebSocket()

  ws.on('connected', () => {
    wsConnected.value = true
  })

  ws.on('disconnected', () => {
    wsConnected.value = false
  })

  ws.on('entanglement_update', (message) => {
    entanglementMatrix.value = message.data.matrix
    symbols.value = message.data.symbols
    entropy.value = message.data.entropy
  })

  ws.on('event_alert', (message) => {
    events.value.unshift(message.data)
    if (events.value.length > 100) {
      events.value.pop()
    }
  })

  ws.on('ecosystem_status', (message) => {
    ecosystemStatus.value = message.data
  })

  ws.on('performance_update', (message) => {
    performanceData.value = message.data
  })
}

const fetchInitialData = async () => {
  try {
    const [entanglement, events_data, ecosystem, performance] = await Promise.all([
      visualizationApi.getEntanglement(),
      visualizationApi.getEvents({ limit: 20 }),
      visualizationApi.getEcosystem(),
      visualizationApi.getPerformance(),
    ])

    entanglementMatrix.value = entanglement.matrix
    symbols.value = entanglement.symbols
    entropy.value = entanglement.entropy
    events.value = events_data.events || []
    ecosystemStatus.value = ecosystem
    performanceData.value = performance
  } catch (error) {
    console.error('获取初始数据失败:', error)
  }
}

const toggleConnection = () => {
  if (wsConnected.value) {
    ws?.disconnect()
  } else {
    ws?.connect()
  }
}

onMounted(() => {
  initializeWebSocket()
  ws?.connect()
  fetchInitialData()
})

onUnmounted(() => {
  ws?.disconnect()
})
</script>
