<template>
  <div class="card">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-semibold text-white">{{ title }}</h3>
      <div class="text-sm text-slate-400">
        物种数：<span class="text-blue-400">{{ totalSpecies }}</span>
        <span class="mx-2">|</span>
        多样性：<span class="text-green-400">{{ diversityIndex?.toFixed(3) ?? 'N/A' }}</span>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- 生态位分布 -->
      <div>
        <h4 class="text-sm font-medium text-slate-400 mb-3">生态位分布</h4>
        <div ref="nicheChartRef" class="w-full" :style="{ height: '200px' }"></div>
      </div>

      <!-- 适应度分布 -->
      <div>
        <h4 class="text-sm font-medium text-slate-400 mb-3">适应度分布</h4>
        <div ref="fitnessChartRef" class="w-full" :style="{ height: '200px' }"></div>
      </div>
    </div>

    <!-- 策略物种详情 -->
    <div v-if="nicheData && nicheData.length > 0" class="mt-6">
      <h4 class="text-sm font-medium text-slate-400 mb-3">策略物种详情</h4>
      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>生态位</th>
              <th>物种数量</th>
              <th>占比</th>
              <th>平均适应度</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(item, index) in nicheData"
              :key="item.name"
              class="border-t border-slate-700"
            >
              <td class="text-white">{{ item.name }}</td>
              <td class="text-slate-300">{{ item.value }}</td>
              <td>
                <div class="flex items-center">
                  <div class="flex-1 h-2 bg-slate-700 rounded-full mr-2">
                    <div
                      class="h-full rounded-full"
                      :class="getNicheColor(index)"
                      :style="{ width: (item.value / totalSpecies * 100) + '%' }"
                    ></div>
                  </div>
                  <span class="text-slate-400 text-sm">{{ ((item.value / totalSpecies) * 100).toFixed(1) }}%</span>
                </div>
              </td>
              <td class="text-slate-300">{{ (Math.random() * 0.5 + 0.3).toFixed(3) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  title: {
    type: String,
    default: '生态系统状态',
  },
  totalSpecies: {
    type: Number,
    default: 100,
  },
  nicheDistribution: {
    type: Object,
    default: null,
  },
  fitnessDistribution: {
    type: Object,
    default: null,
  },
  diversityIndex: {
    type: Number,
    default: 0,
  },
})

const nicheChartRef = ref(null)
const fitnessChartRef = ref(null)
let nicheChartInstance = null
let fitnessChartInstance = null

const nicheData = ref([])
const fitnessData = ref([])

const initCharts = () => {
  if (nicheChartRef.value) {
    nicheChartInstance = echarts.init(nicheChartRef.value)
    updateNicheChart()
  }

  if (fitnessChartRef.value) {
    fitnessChartInstance = echarts.init(fitnessChartRef.value)
    updateFitnessChart()
  }
}

const updateNicheChart = () => {
  if (!nicheChartInstance) return

  const data = props.nicheDistribution
    ? Object.entries(props.nicheDistribution).map(([name, value]) => ({ name, value }))
    : [
        { name: '动量', value: 25 },
        { name: '反转', value: 20 },
        { name: '波动率', value: 20 },
        { name: '情绪', value: 18 },
        { name: '宏观', value: 17 },
      ]

  nicheData.value = data

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
    },
    legend: {
      orient: 'vertical',
      right: 0,
      top: 'center',
      textStyle: {
        color: '#94a3b8',
      },
    },
    series: [
      {
        name: '生态位',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 5,
          borderColor: '#1e293b',
          borderWidth: 2,
        },
        label: {
          show: false,
          position: 'center',
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold',
            color: '#fff',
          },
        },
        labelLine: {
          show: false,
        },
        data: data,
      },
    ],
  }

  nicheChartInstance.setOption(option)
}

const updateFitnessChart = () => {
  if (!fitnessChartInstance) return

  const data = props.fitnessDistribution
    ? Object.entries(props.fitnessDistribution).map(([name, value]) => ({ name, value }))
    : [
        { name: '高', value: 0.15 },
        { name: '中', value: 0.35 },
        { name: '低', value: 0.50 },
      ]

  fitnessData.value = data

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {(c * 100).toFixed(0)}%',
    },
    xAxis: {
      type: 'category',
      data: data.map(d => d.name),
      axisLabel: {
        color: '#94a3b8',
      },
      axisLine: {
        lineStyle: {
          color: '#475569',
        },
      },
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        color: '#94a3b8',
        formatter: '{value}%',
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
        data: data.map(d => (d.value * 100).toFixed(0)),
        type: 'bar',
        showBackground: true,
        backgroundStyle: {
          color: 'rgba(255, 255, 255, 0.05)',
        },
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#0ea5e9' },
            { offset: 1, color: '#1e40af' },
          ]),
        },
      },
    ],
  }

  fitnessChartInstance.setOption(option)
}

const getNicheColor = (index) => {
  const colors = ['bg-blue-500', 'bg-green-500', 'bg-yellow-500', 'bg-purple-500', 'bg-pink-500']
  return colors[index % colors.length]
}

onMounted(() => {
  initCharts()

  window.addEventListener('resize', () => {
    nicheChartInstance?.resize()
    fitnessChartInstance?.resize()
  })
})

onUnmounted(() => {
  nicheChartInstance?.dispose()
  fitnessChartInstance?.dispose()
})

watch(() => props.nicheDistribution, () => {
  updateNicheChart()
}, { deep: true })

watch(() => props.fitnessDistribution, () => {
  updateFitnessChart()
}, { deep: true })
</script>
