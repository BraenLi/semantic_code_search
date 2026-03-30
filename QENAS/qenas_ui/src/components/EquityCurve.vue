<template>
  <div class="card">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-semibold text-white">{{ title }}</h3>
      <div class="flex items-center space-x-4">
        <div v-if="metrics" class="grid grid-cols-3 gap-4">
          <div class="text-center">
            <div class="text-xs text-slate-400">总收益</div>
            <div :class="getReturnClass(metrics.total_return)">
              {{ (metrics.total_return * 100)?.toFixed(2) }}%
            </div>
          </div>
          <div class="text-center">
            <div class="text-xs text-slate-400">夏普比率</div>
            <div class="text-white font-mono">{{ metrics.sharpe_ratio?.toFixed(2) ?? 'N/A' }}</div>
          </div>
          <div class="text-center">
            <div class="text-xs text-slate-400">最大回撤</div>
            <div class="text-red-400 font-mono">{{ (metrics.max_drawdown * 100)?.toFixed(2) }}%</div>
          </div>
        </div>
      </div>
    </div>

    <div ref="chartRef" class="w-full" :style="{ height: height + 'px' }"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  title: {
    type: String,
    default: '权益曲线',
  },
  equityCurve: {
    type: Array,
    default: null,
  },
  benchmark: {
    type: Array,
    default: null,
  },
  metrics: {
    type: Object,
    default: null,
  },
  height: {
    type: Number,
    default: 300,
  },
})

const chartRef = ref(null)
let chartInstance = null

const initChart = () => {
  if (!chartRef.value) return

  chartInstance = echarts.init(chartRef.value)

  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const date = params[0]?.name
        let result = `<div class="font-semibold">${date}</div>`
        params.forEach(param => {
          const color = param.color
          const value = param.value
          const formatted = typeof value === 'number' ? value.toFixed(2) : value
          result += `<div style="display: flex; align-items: center; margin-top: 4px;">
            <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background-color: ${color}; margin-right: 8px;"></span>
            ${param.seriesName}: ${formatted}
          </div>`
        })
        return result
      },
    },
    legend: {
      data: ['策略', '基准'],
      textStyle: {
        color: '#94a3b8',
      },
      bottom: 0,
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: generateXAxisData(),
      axisLabel: {
        color: '#94a3b8',
        maxRotation: 45,
      },
      axisLine: {
        lineStyle: {
          color: '#475569',
        },
      },
    },
    yAxis: {
      type: 'value',
      scale: true,
      axisLabel: {
        color: '#94a3b8',
        formatter: (value) => {
          if (value >= 1000000) return (value / 1000000).toFixed(1) + 'M'
          if (value >= 1000) return (value / 1000).toFixed(0) + 'K'
          return value.toString()
        },
      },
      splitLine: {
        lineStyle: {
          color: '#334155',
        },
      },
      axisLine: {
        lineStyle: {
          color: '#475569',
        },
      },
    },
    series: [
      {
        name: '策略',
        type: 'line',
        smooth: true,
        showSymbol: false,
        data: props.equityCurve || [],
        lineStyle: {
          width: 2,
          color: '#0ea5e9',
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(14, 165, 233, 0.3)' },
            { offset: 1, color: 'rgba(14, 165, 233, 0.05)' },
          ]),
        },
      },
      {
        name: '基准',
        type: 'line',
        smooth: true,
        showSymbol: false,
        data: props.benchmark || generateBenchmark(),
        lineStyle: {
          width: 2,
          color: '#f59e0b',
          type: 'dashed',
        },
      },
    ],
  }

  chartInstance.setOption(option)
}

const generateXAxisData = () => {
  const data = props.equityCurve || []
  return data.map((_, i) => `T+${i}`)
}

const generateBenchmark = () => {
  const data = props.equityCurve || []
  if (data.length === 0) return []

  const initial = data[0] || 100000
  const rate = 0.0005 // 假设基准每日增长 0.05%
  return data.map((_, i) => initial * (1 + rate * i))
}

const getReturnClass = (returnVal) => {
  if (returnVal >= 0) return 'text-green-400 font-mono'
  return 'text-red-400 font-mono'
}

const updateChart = () => {
  if (!chartInstance) return

  chartInstance.setOption({
    series: [
      { data: props.equityCurve || [] },
      { data: props.benchmark || generateBenchmark() },
    ],
  })
}

onMounted(() => {
  initChart()

  window.addEventListener('resize', () => {
    chartInstance?.resize()
  })
})

onUnmounted(() => {
  chartInstance?.dispose()
})

watch(() => props.equityCurve, () => {
  updateChart()
}, { deep: true })

watch(() => props.benchmark, () => {
  updateChart()
}, { deep: true })
</script>
