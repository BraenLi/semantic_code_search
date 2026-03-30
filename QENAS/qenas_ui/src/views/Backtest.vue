<template>
  <div class="space-y-6">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-white">回测管理</h1>
    </div>

    <!-- 新建回测表单 -->
    <div class="card">
      <h2 class="text-lg font-semibold mb-4">新建回测任务</h2>
      <form @submit.prevent="submitBacktest" class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm text-slate-400 mb-1">策略 ID</label>
            <input
              v-model="form.strategyId"
              type="text"
              class="input w-full"
              placeholder="qenas"
              required
            />
          </div>
          <div>
            <label class="block text-sm text-slate-400 mb-1">初始资金</label>
            <input
              v-model.number="form.initialCapital"
              type="number"
              class="input w-full"
              placeholder="100000"
            />
          </div>
        </div>

        <div>
          <label class="block text-sm text-slate-400 mb-1">标的列表</label>
          <input
            v-model="form.symbols"
            type="text"
            class="input w-full"
            placeholder="AAPL,GOOGL,MSFT,AMZN,META"
            required
          />
          <p class="text-xs text-slate-500 mt-1">用逗号分隔多个标的</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm text-slate-400 mb-1">开始日期</label>
            <input
              v-model="form.startDate"
              type="date"
              class="input w-full"
              required
            />
          </div>
          <div>
            <label class="block text-sm text-slate-400 mb-1">结束日期</label>
            <input
              v-model="form.endDate"
              type="date"
              class="input w-full"
              required
            />
          </div>
        </div>

        <div class="flex items-center justify-end space-x-3">
          <button
            type="button"
            @click="resetForm"
            class="btn-secondary"
          >
            重置
          </button>
          <button
            type="submit"
            class="btn-primary"
            :disabled="running"
          >
            {{ running ? '运行中...' : '开始回测' }}
          </button>
        </div>
      </form>
    </div>

    <!-- 回测任务列表 -->
    <div class="card">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold">回测任务列表</h2>
        <button
          @click="fetchJobs"
          class="text-sm text-blue-400 hover:text-blue-300"
        >
          刷新
        </button>
      </div>

      <div v-if="jobs.length === 0" class="text-center py-8 text-slate-400">
        暂无回测任务
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="job in jobs"
          :key="job.job_id"
          class="bg-slate-700 rounded-lg p-4"
        >
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <div class="flex items-center space-x-2">
                <span class="font-medium text-white">{{ job.strategy_id }}</span>
                <span
                  class="badge"
                  :class="getStatusBadgeClass(job.status)"
                >
                  {{ getStatusLabel(job.status) }}
                </span>
              </div>
              <div class="text-sm text-slate-400 mt-1">
                创建时间：{{ formatTime(job.created_at) }}
                <span v-if="job.completed_at" class="ml-2">
                  | 完成时间：{{ formatTime(job.completed_at) }}
                </span>
              </div>
            </div>

            <div class="flex items-center space-x-4">
              <!-- 进度条 -->
              <div v-if="job.status === 'running'" class="w-32">
                <div class="text-xs text-slate-400 mb-1">进度：{{ job.progress?.toFixed(1) }}%</div>
                <div class="h-2 bg-slate-600 rounded-full">
                  <div
                    class="h-full bg-blue-500 rounded-full transition-all"
                    :style="{ width: (job.progress || 0) + '%' }"
                  ></div>
                </div>
              </div>

              <!-- 操作按钮 -->
              <div class="flex items-center space-x-2">
                <button
                  v-if="job.status === 'completed'"
                  @click="viewResult(job)"
                  class="text-sm text-blue-400 hover:text-blue-300"
                >
                  查看结果
                </button>
                <button
                  v-if="job.status === 'running' || job.status === 'pending'"
                  @click="cancelJob(job.job_id)"
                  class="text-sm text-yellow-400 hover:text-yellow-300"
                >
                  取消
                </button>
                <button
                  @click="deleteJob(job.job_id)"
                  class="text-sm text-red-400 hover:text-red-300"
                >
                  删除
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 回测结果弹窗 -->
    <div
      v-if="showResultModal"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    >
      <div class="card w-full max-w-2xl max-h-[80vh] overflow-y-auto">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold">回测结果</h2>
          <button @click="showResultModal = false" class="text-slate-400 hover:text-white">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div v-if="selectedResult" class="space-y-4">
          <!-- 指标卡片 -->
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div class="bg-slate-700 rounded-lg p-3 text-center">
              <div class="text-xs text-slate-400">总收益</div>
              <div :class="selectedResult.result?.total_return >= 0 ? 'text-green-400' : 'text-red-400'">
                {{ (selectedResult.result?.total_return * 100)?.toFixed(2) }}%
              </div>
            </div>
            <div class="bg-slate-700 rounded-lg p-3 text-center">
              <div class="text-xs text-slate-400">夏普比率</div>
              <div class="text-white">{{ selectedResult.result?.sharpe_ratio?.toFixed(2) }}</div>
            </div>
            <div class="bg-slate-700 rounded-lg p-3 text-center">
              <div class="text-xs text-slate-400">最大回撤</div>
              <div class="text-red-400">{{ (selectedResult.result?.max_drawdown * 100)?.toFixed(2) }}%</div>
            </div>
            <div class="bg-slate-700 rounded-lg p-3 text-center">
              <div class="text-xs text-slate-400">胜率</div>
              <div class="text-white">{{ (selectedResult.result?.win_rate * 100)?.toFixed(1) }}%</div>
            </div>
          </div>

          <!-- 权益曲线图 -->
          <div v-if="selectedResult.result?.equity_curve">
            <EquityCurve
              :equityCurve="selectedResult.result.equity_curve"
              :height="300"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import EquityCurve from '@/components/EquityCurve.vue'
import { backtestApi } from '@/services/api'

const form = ref({
  strategyId: 'qenas',
  symbols: 'AAPL,GOOGL,MSFT,AMZN,META',
  initialCapital: 100000,
  startDate: '',
  endDate: '',
})

const jobs = ref([])
const running = ref(false)
const showResultModal = ref(false)
const selectedResult = ref(null)

const submitBacktest = async () => {
  running.value = true
  try {
    const symbols = form.value.symbols.split(',').map(s => s.trim())
    await backtestApi.run({
      strategy_id: form.value.strategyId,
      symbols: symbols,
      start_date: form.value.startDate,
      end_date: form.value.endDate,
      initial_capital: form.value.initialCapital,
      commission_rate: 0.001,
      slippage_rate: 0.001,
    })
    await fetchJobs()
    resetForm()
  } catch (error) {
    console.error('创建回测失败:', error)
    alert('创建回测失败：' + (error.response?.data?.detail || error.message))
  } finally {
    running.value = false
  }
}

const resetForm = () => {
  form.value = {
    strategyId: 'qenas',
    symbols: 'AAPL,GOOGL,MSFT,AMZN,META',
    initialCapital: 100000,
    startDate: '',
    endDate: '',
  }
}

const fetchJobs = async () => {
  try {
    jobs.value = await backtestApi.list()
  } catch (error) {
    console.error('获取回测列表失败:', error)
  }
}

const cancelJob = async (jobId) => {
  try {
    await backtestApi.cancel(jobId)
    await fetchJobs()
  } catch (error) {
    console.error('取消回测失败:', error)
  }
}

const deleteJob = async (jobId) => {
  if (!confirm('确定要删除此回测任务吗？')) return
  try {
    await backtestApi.delete(jobId)
    await fetchJobs()
  } catch (error) {
    console.error('删除回测失败:', error)
  }
}

const viewResult = async (job) => {
  try {
    selectedResult.value = await backtestApi.getResult(job.job_id)
    showResultModal.value = true
  } catch (error) {
    console.error('获取回测结果失败:', error)
  }
}

const getStatusBadgeClass = (status) => {
  const classes = {
    pending: 'badge-info',
    running: 'badge-warning',
    completed: 'badge-success',
    failed: 'badge-error',
    cancelled: 'bg-slate-600 text-slate-300',
  }
  return classes[status] || classes.pending
}

const getStatusLabel = (status) => {
  const labels = {
    pending: '等待中',
    running: '运行中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消',
  }
  return labels[status] || status
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  return new Date(timestamp).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchJobs()
})
</script>
