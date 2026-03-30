<template>
  <div class="space-y-6">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-white">设置</h1>
    </div>

    <!-- 策略配置 -->
    <div class="card">
      <h2 class="text-lg font-semibold mb-4">策略配置</h2>
      <form @submit.prevent="saveStrategyConfig" class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm text-slate-400 mb-1">策略物种数量</label>
            <input
              v-model.number="strategyConfig.nSpecies"
              type="number"
              class="input w-full"
              min="10"
              max="500"
            />
            <p class="text-xs text-slate-500 mt-1">生态位子策略的数量 (10-500)</p>
          </div>
          <div>
            <label class="block text-sm text-slate-400 mb-1">同步阈值</label>
            <input
              v-model.number="strategyConfig.syncThreshold"
              type="number"
              step="0.01"
              class="input w-full"
              min="0.1"
              max="0.99"
            />
            <p class="text-xs text-slate-500 mt-1">Kuramoto 同步检测阈值 (0.1-0.99)</p>
          </div>
          <div>
            <label class="block text-sm text-slate-400 mb-1">进化间隔</label>
            <input
              v-model.number="strategyConfig.evolutionInterval"
              type="number"
              class="input w-full"
              min="1"
              max="100"
            />
            <p class="text-xs text-slate-500 mt-1">生态系统进化的时间步间隔 (1-100)</p>
          </div>
          <div>
            <label class="block text-sm text-slate-400 mb-1">最大收益率窗口</label>
            <input
              v-model.number="strategyConfig.maxReturnsWindow"
              type="number"
              class="input w-full"
              min="10"
              max="200"
            />
            <p class="text-xs text-slate-500 mt-1">用于纠缠计算的收益率窗口大小</p>
          </div>
        </div>

        <div class="flex items-center justify-end">
          <button type="submit" class="btn-primary">
            保存配置
          </button>
        </div>
      </form>
    </div>

    <!-- 交易配置 -->
    <div class="card">
      <h2 class="text-lg font-semibold mb-4">交易配置</h2>
      <form @submit.prevent="saveTradingConfig" class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm text-slate-400 mb-1">佣金率</label>
            <input
              v-model.number="tradingConfig.commissionRate"
              type="number"
              step="0.0001"
              class="input w-full"
              min="0"
            />
            <p class="text-xs text-slate-500 mt-1">交易佣金比例 (如 0.001 表示 0.1%)</p>
          </div>
          <div>
            <label class="block text-sm text-slate-400 mb-1">滑点率</label>
            <input
              v-model.number="tradingConfig.slippageRate"
              type="number"
              step="0.0001"
              class="input w-full"
              min="0"
            />
            <p class="text-xs text-slate-500 mt-1">模拟滑点比例</p>
          </div>
          <div>
            <label class="block text-sm text-slate-400 mb-1">单笔最大仓位</label>
            <input
              v-model.number="tradingConfig.maxPositionSize"
              type="number"
              step="0.01"
              class="input w-full"
              min="0.01"
              max="1"
            />
            <p class="text-xs text-slate-500 mt-1">单个标的最大仓位占比 (0.01-1)</p>
          </div>
          <div>
            <label class="block text-sm text-slate-400 mb-1">初始资金</label>
            <input
              v-model.number="tradingConfig.initialCapital"
              type="number"
              class="input w-full"
              min="1000"
            />
            <p class="text-xs text-slate-500 mt-1">账户初始资金</p>
          </div>
        </div>

        <div class="flex items-center justify-end">
          <button type="submit" class="btn-primary">
            保存配置
          </button>
        </div>
      </form>
    </div>

    <!-- 数据源配置 -->
    <div class="card">
      <h2 class="text-lg font-semibold mb-4">数据源配置</h2>
      <form @submit.prevent="saveDataConfig" class="space-y-4">
        <div>
          <label class="block text-sm text-slate-400 mb-1">数据源类型</label>
          <select v-model="dataConfig.source" class="input w-full">
            <option value="akshare">AKShare (A 股)</option>
            <option value="baostock">BaoStock (A 股)</option>
            <option value="yfinance">Yahoo Finance (美股/港股)</option>
          </select>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm text-slate-400 mb-1">数据刷新间隔</label>
            <select v-model="dataConfig.refreshInterval" class="input w-full">
              <option value="60">1 分钟</option>
              <option value="300">5 分钟</option>
              <option value="900">15 分钟</option>
              <option value="3600">1 小时</option>
              <option value="86400">1 天</option>
            </select>
          </div>
          <div>
            <label class="block text-sm text-slate-400 mb-1">缓存过期时间</label>
            <select v-model="dataConfig.cacheExpiry" class="input w-full">
              <option value="300">5 分钟</option>
              <option value="900">15 分钟</option>
              <option value="1800">30 分钟</option>
              <option value="3600">1 小时</option>
              <option value="86400">1 天</option>
            </select>
          </div>
        </div>

        <div class="flex items-center justify-end">
          <button type="submit" class="btn-primary">
            保存配置
          </button>
        </div>
      </form>
    </div>

    <!-- WebSocket 配置 -->
    <div class="card">
      <h2 class="text-lg font-semibold mb-4">WebSocket 配置</h2>
      <form @submit.prevent="saveWebSocketConfig" class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm text-slate-400 mb-1">WebSocket 主机</label>
            <input
              v-model="wsConfig.host"
              type="text"
              class="input w-full"
              placeholder="localhost"
            />
          </div>
          <div>
            <label class="block text-sm text-slate-400 mb-1">WebSocket 端口</label>
            <input
              v-model.number="wsConfig.port"
              type="number"
              class="input w-full"
              placeholder="8000"
            />
          </div>
        </div>

        <div>
          <label class="block text-sm text-slate-400 mb-1">订阅主题</label>
          <div class="flex flex-wrap gap-2">
            <label
              v-for="topic in availableTopics"
              :key="topic"
              class="flex items-center space-x-2 bg-slate-700 px-3 py-1.5 rounded"
            >
              <input
                type="checkbox"
                :checked="wsConfig.topics.includes(topic)"
                @change="toggleTopic(topic)"
                class="rounded border-slate-600 text-blue-600 focus:ring-blue-500"
              />
              <span class="text-sm text-slate-300">{{ getTopicLabel(topic) }}</span>
            </label>
          </div>
        </div>

        <div class="flex items-center justify-end">
          <button type="submit" class="btn-primary">
            保存配置
          </button>
        </div>
      </form>
    </div>

    <!-- 系统信息 -->
    <div class="card">
      <h2 class="text-lg font-semibold mb-4">系统信息</h2>
      <div class="space-y-2 text-sm">
        <div class="flex justify-between">
          <span class="text-slate-400">API 版本</span>
          <span class="text-white">v0.1.0</span>
        </div>
        <div class="flex justify-between">
          <span class="text-slate-400">前端版本</span>
          <span class="text-white">v0.1.0</span>
        </div>
        <div class="flex justify-between">
          <span class="text-slate-400">服务状态</span>
          <span :class="apiHealthy ? 'text-green-400' : 'text-red-400'">
            {{ apiHealthy ? '正常' : '未知' }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const strategyConfig = ref({
  nSpecies: 100,
  syncThreshold: 0.75,
  evolutionInterval: 20,
  maxReturnsWindow: 50,
})

const tradingConfig = ref({
  commissionRate: 0.001,
  slippageRate: 0.001,
  maxPositionSize: 0.1,
  initialCapital: 100000,
})

const dataConfig = ref({
  source: 'yfinance',
  refreshInterval: 60,
  cacheExpiry: 300,
})

const wsConfig = ref({
  host: 'localhost',
  port: 8000,
  topics: ['entanglement', 'events', 'performance', 'ecosystem'],
})

const availableTopics = ['entanglement', 'events', 'performance', 'ecosystem']
const apiHealthy = ref(true)

const getTopicLabel = (topic) => {
  const labels = {
    entanglement: '纠缠矩阵',
    events: '事件告警',
    performance: '业绩更新',
    ecosystem: '生态系统',
  }
  return labels[topic] || topic
}

const toggleTopic = (topic) => {
  const index = wsConfig.value.topics.indexOf(topic)
  if (index > -1) {
    wsConfig.value.topics.splice(index, 1)
  } else {
    wsConfig.value.topics.push(topic)
  }
}

const saveStrategyConfig = () => {
  console.log('保存策略配置:', strategyConfig.value)
  alert('策略配置已保存')
}

const saveTradingConfig = () => {
  console.log('保存交易配置:', tradingConfig.value)
  alert('交易配置已保存')
}

const saveDataConfig = () => {
  console.log('保存数据源配置:', dataConfig.value)
  alert('数据源配置已保存')
}

const saveWebSocketConfig = () => {
  console.log('保存 WebSocket 配置:', wsConfig.value)
  alert('WebSocket 配置已保存')
}

onMounted(() => {
  // 检查 API 健康状态
  fetch('/health')
    .then(res => res.json())
    .then(data => {
      apiHealthy.value = data.status === 'healthy'
    })
    .catch(() => {
      apiHealthy.value = false
    })
})
</script>
