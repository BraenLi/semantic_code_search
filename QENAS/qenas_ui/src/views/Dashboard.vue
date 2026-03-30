<template>
  <div class="space-y-6">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-white">仪表板</h1>
      <div class="flex items-center space-x-2 text-sm text-slate-400">
        <span>最后更新：</span>
        <span>{{ lastUpdateTime }}</span>
      </div>
    </div>

    <!-- 关键指标卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="card">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-sm text-slate-400">纠缠熵</div>
            <div class="text-2xl font-bold text-blue-400 mt-1">
              {{ dashboardData?.entanglement?.entropy?.toFixed(4) ?? '0.0000' }}
            </div>
          </div>
          <div class="w-12 h-12 rounded-lg bg-blue-900/50 flex items-center justify-center">
            <svg class="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-sm text-slate-400">资产数量</div>
            <div class="text-2xl font-bold text-green-400 mt-1">
              {{ dashboardData?.entanglement?.asset_count ?? 0 }}
            </div>
          </div>
          <div class="w-12 h-12 rounded-lg bg-green-900/50 flex items-center justify-center">
            <svg class="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-sm text-slate-400">策略物种</div>
            <div class="text-2xl font-bold text-purple-400 mt-1">
              {{ dashboardData?.ecosystem?.total_species ?? 100 }}
            </div>
          </div>
          <div class="w-12 h-12 rounded-lg bg-purple-900/50 flex items-center justify-center">
            <svg class="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-sm text-slate-400">多样性指数</div>
            <div class="text-2xl font-bold text-yellow-400 mt-1">
              {{ dashboardData?.ecosystem?.diversity_index?.toFixed(3) ?? '0.000' }}
            </div>
          </div>
          <div class="w-12 h-12 rounded-lg bg-yellow-900/50 flex items-center justify-center">
            <svg class="w-6 h-6 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
        </div>
      </div>
    </div>

    <!-- 缠结矩阵和业绩 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <EntanglementMatrix
        :matrix="entanglementMatrix"
        :symbols="symbols"
        :entropy="entropy"
        :loading="loading"
      />
      <EquityCurve
        :equityCurve="equityCurve"
        :metrics="metrics"
        :height="300"
      />
    </div>

    <!-- 事件时间线和生态系统 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <EventTimeline
        :events="events"
        :maxDisplay="5"
      />
      <EcosystemView
        :totalSpecies="100"
        :nicheDistribution="nicheDistribution"
        :fitnessDistribution="fitnessDistribution"
        :diversityIndex="dashboardData?.ecosystem?.diversity_index"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import EntanglementMatrix from '@/components/EntanglementMatrix.vue'
import EquityCurve from '@/components/EquityCurve.vue'
import EventTimeline from '@/components/EventTimeline.vue'
import EcosystemView from '@/components/EcosystemView.vue'
import { visualizationApi } from '@/services/api'
import { useWebSocket } from '@/services/websocket'

const lastUpdateTime = ref(new Date().toLocaleString('zh-CN'))
const dashboardData = ref(null)
const entanglementMatrix = ref(null)
const symbols = ref([])
const entropy = ref(0)
const equityCurve = ref([])
const metrics = ref(null)
const events = ref([])
const nicheDistribution = ref(null)
const fitnessDistribution = ref(null)
const loading = ref(false)

let ws = null

const fetchDashboardData = async () => {
  loading.value = true
  try {
    const data = await visualizationApi.getDashboard()
    dashboardData.value = data

    // 获取详细数据
    const entanglementData = await visualizationApi.getEntanglement()
    entanglementMatrix.value = entanglementData.matrix
    symbols.value = entanglementData.symbols
    entropy.value = entanglementData.entropy

    const performanceData = await visualizationApi.getPerformance()
    equityCurve.value = performanceData.equity_curve
    metrics.value = performanceData.metrics

    const eventData = await visualizationApi.getEvents({ limit: 10 })
    events.value = eventData.events || []

    const ecosystemData = await visualizationApi.getEcosystem()
    nicheDistribution.value = ecosystemData.niche_distribution
    fitnessDistribution.value = ecosystemData.fitness_distribution

    lastUpdateTime.value = new Date().toLocaleString('zh-CN')
  } catch (error) {
    console.error('获取仪表板数据失败:', error)
  } finally {
    loading.value = false
  }
}

const setupWebSocket = () => {
  ws = useWebSocket()

  ws.on('entanglement_update', (message) => {
    entanglementMatrix.value = message.data.matrix
    entropy.value = message.data.entropy
    lastUpdateTime.value = new Date().toLocaleString('zh-CN')
  })

  ws.on('performance_update', (message) => {
    equityCurve.value = message.data.equity_curve
    metrics.value = message.data.metrics
    lastUpdateTime.value = new Date().toLocaleString('zh-CN')
  })

  ws.on('event_alert', (message) => {
    events.value.unshift(message.data)
    if (events.value.length > 50) {
      events.value.pop()
    }
    lastUpdateTime.value = new Date().toLocaleString('zh-CN')
  })

  ws.on('ecosystem_status', (message) => {
    nicheDistribution.value = message.data.niche_distribution
    fitnessDistribution.value = message.data.fitness_distribution
    lastUpdateTime.value = new Date().toLocaleString('zh-CN')
  })
}

onMounted(() => {
  fetchDashboardData()
  setupWebSocket()

  // 定期刷新
  const interval = setInterval(fetchDashboardData, 60000) // 每分钟刷新

  onUnmounted(() => {
    clearInterval(interval)
    ws?.disconnect()
  })
})
</script>
