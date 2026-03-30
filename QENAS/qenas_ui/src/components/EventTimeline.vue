<template>
  <div class="card">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-semibold text-white">{{ title }}</h3>
      <div class="flex items-center space-x-2">
        <span class="text-sm text-slate-400">事件数：<span class="text-blue-400">{{ events?.length ?? 0 }}</span></span>
      </div>
    </div>

    <div v-if="!events || events.length === 0" class="text-center py-8 text-slate-400">
      暂无事件数据
    </div>

    <div v-else class="relative">
      <!-- 时间线 -->
      <div class="absolute left-4 top-0 bottom-0 w-0.5 bg-slate-700"></div>

      <div class="space-y-4">
        <div
          v-for="(event, index) in displayEvents"
          :key="event.id || index"
          class="relative pl-10"
        >
          <!-- 时间点标记 -->
          <div
            class="absolute left-0 w-8 h-8 rounded-full flex items-center justify-center border-2"
            :class="getImpactLevelClass(event.impact_level)"
          >
            <div class="w-2 h-2 rounded-full bg-white"></div>
          </div>

          <!-- 事件内容 -->
          <div class="bg-slate-700 rounded-lg p-3 hover:bg-slate-650 transition-colors">
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <h4 class="font-medium text-white">{{ event.title }}</h4>
                <p class="text-sm text-slate-400 mt-1">{{ event.description }}</p>

                <div class="flex items-center space-x-2 mt-2">
                  <span
                    v-if="event.event_type"
                    class="badge badge-info"
                  >
                    {{ getEventTypeLabel(event.event_type) }}
                  </span>
                  <span
                    v-if="event.impact_level"
                    class="badge"
                    :class="getImpactLevelBadgeClass(event.impact_level)"
                  >
                    {{ event.impact_level }}
                  </span>
                  <span class="text-xs text-slate-500">
                    {{ formatTime(event.timestamp) }}
                  </span>
                </div>

                <div v-if="event.symbols" class="flex flex-wrap gap-1 mt-2">
                  <span
                    v-for="symbol in event.symbols"
                    :key="symbol"
                    class="text-xs bg-slate-600 text-slate-300 px-2 py-0.5 rounded"
                  >
                    {{ symbol }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="events.length > maxDisplay" class="text-center mt-4">
        <button
          @click="showAll = !showAll"
          class="text-sm text-blue-400 hover:text-blue-300"
        >
          {{ showAll ? '收起' : `展开全部 ${events.length - maxDisplay} 个事件` }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  title: {
    type: String,
    default: '事件时间线',
  },
  events: {
    type: Array,
    default: () => [],
  },
  maxDisplay: {
    type: Number,
    default: 10,
  },
})

const showAll = ref(false)

const displayEvents = computed(() => {
  if (showAll.value) return props.events
  return props.events.slice(0, props.maxDisplay)
})

const getEventTypeLabel = (type) => {
  const labels = {
    earnings: '财报',
    announcement: '公告',
    regulatory: '监管',
    market_moving: '市场影响',
  }
  return labels[type] || type
}

const getImpactLevelClass = (level) => {
  const classes = {
    LOW: 'border-slate-500 bg-slate-600',
    MEDIUM: 'border-yellow-500 bg-yellow-600',
    HIGH: 'border-orange-500 bg-orange-600',
    CRITICAL: 'border-red-500 bg-red-600',
  }
  return classes[level] || classes.LOW
}

const getImpactLevelBadgeClass = (level) => {
  const classes = {
    LOW: 'badge-info',
    MEDIUM: 'badge-warning',
    HIGH: 'bg-orange-900 text-orange-200',
    CRITICAL: 'badge-error',
  }
  return classes[level] || classes.LOW
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN')
}
</script>
