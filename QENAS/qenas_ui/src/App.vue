<template>
  <div id="app" class="min-h-screen">
    <nav class="bg-slate-800 border-b border-slate-700">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <router-link to="/" class="text-xl font-bold text-blue-400">
                QENAS
              </router-link>
            </div>
            <div class="hidden md:block">
              <div class="ml-10 flex items-baseline space-x-4">
                <router-link
                  v-for="item in navItems"
                  :key="item.path"
                  :to="item.path"
                  class="px-3 py-2 rounded-md text-sm font-medium hover:bg-slate-700 transition-colors"
                  :class="$route.path === item.path ? 'bg-slate-700 text-blue-400' : 'text-slate-300'"
                >
                  {{ item.name }}
                </router-link>
              </div>
            </div>
          </div>
          <div class="text-sm text-slate-400">
            量子纠缠生态位自适应网络
          </div>
        </div>
      </div>
    </nav>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
const navItems = [
  { name: '仪表板', path: '/' },
  { name: '回测', path: '/backtest' },
  { name: '监控', path: '/monitoring' },
  { name: '设置', path: '/settings' },
]
</script>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
