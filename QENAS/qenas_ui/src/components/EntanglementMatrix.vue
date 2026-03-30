<template>
  <div class="card">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-semibold text-white">{{ title }}</h3>
      <div class="text-sm text-slate-400">
        熵值：<span class="text-blue-400 font-mono">{{ entropy?.toFixed(4) ?? 'N/A' }}</span>
      </div>
    </div>

    <div ref="chartRef" class="w-full" :style="{ height: height + 'px' }"></div>

    <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-slate-800 bg-opacity-75">
      <div class="text-blue-400">加载中...</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  title: {
    type: String,
    default: '量子纠缠矩阵',
  },
  matrix: {
    type: Array,
    default: null,
  },
  symbols: {
    type: Array,
    default: () => [],
  },
  entropy: {
    type: Number,
    default: 0,
  },
  height: {
    type: Number,
    default: 400,
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const chartRef = ref(null)
let chartInstance = null

const initChart = () => {
  if (!chartRef.value) return

  chartInstance = echarts.init(chartRef.value)

  const option = {
    tooltip: {
      position: 'top',
      formatter: (params) => {
        return `${params.data[0]} - ${params.data[1]}: ${params.value[2]?.toFixed(3)}`
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: props.symbols,
      splitArea: {
        show: true,
      },
      axisLabel: {
        color: '#94a3b8',
        rotate: 45,
      },
      axisLine: {
        lineStyle: {
          color: '#475569',
        },
      },
    },
    yAxis: {
      type: 'category',
      data: props.symbols,
      splitArea: {
        show: true,
      },
      axisLabel: {
        color: '#94a3b8',
      },
      axisLine: {
        lineStyle: {
          color: '#475569',
        },
      },
    },
    visualMap: {
      min: 0,
      max: 1,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: '0%',
      inRange: {
        color: ['#1e3a5f', '#0ea5e9', '#f0abfc'],
      },
      text: ['高', '低'],
      textStyle: {
        color: '#94a3b8',
      },
    },
    series: [{
      name: '纠缠强度',
      type: 'heatmap',
      data: prepareHeatmapData(),
      label: {
        show: true,
        color: '#1e293b',
        fontSize: 10,
      },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.5)',
        },
      },
    }],
  }

  chartInstance.setOption(option)
}

const prepareHeatmapData = () => {
  if (!props.matrix || props.matrix.length === 0) return []

  const data = []
  for (let i = 0; i < props.matrix.length; i++) {
    for (let j = 0; j < props.matrix[i].length; j++) {
      data.push([j, i, props.matrix[i][j]])
    }
  }
  return data
}

const updateChart = () => {
  if (!chartInstance) return

  chartInstance.setOption({
    xAxis: { data: props.symbols },
    yAxis: { data: props.symbols },
    series: [{
      data: prepareHeatmapData(),
    }],
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

watch(() => props.matrix, () => {
  updateChart()
}, { deep: true })

watch(() => props.symbols, () => {
  updateChart()
})
</script>
