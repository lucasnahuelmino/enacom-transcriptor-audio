<template>
  <div class="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(0,102,204,0.12),_transparent_34%),linear-gradient(180deg,#f8fbff_0%,#eef4fb_100%)]">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <Header />

      <nav class="mb-6 rounded-enacom border border-white/70 bg-white/80 backdrop-blur shadow-enacom-sm p-2 flex flex-wrap gap-2">
        <button class="module-link" :class="currentView === 'transcription' ? 'module-link-active' : ''" @click="setView('transcription')">Transcriptor</button>
        <button class="module-link" :class="currentView === 'signal-monitor' ? 'module-link-active' : ''" @click="setView('signal-monitor')">Live Signal Monitor</button>
      </nav>

      <component :is="activeComponent" />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'

import Header from '@/components/Header.vue'
import websocket from '@/services/websocket'
import SignalMonitor from '@/views/SignalMonitor.vue'
import TranscriptionWorkspace from '@/views/TranscriptionWorkspace.vue'

const currentView = ref(window.location.pathname.includes('signal-monitor') ? 'signal-monitor' : 'transcription')

const activeComponent = computed(() => {
  return currentView.value === 'signal-monitor' ? SignalMonitor : TranscriptionWorkspace
})

function setView(viewName) {
  currentView.value = viewName
  const nextPath = viewName === 'signal-monitor' ? '/signal-monitor' : '/'
  window.history.replaceState({}, '', nextPath)
}

onMounted(() => {
  websocket.connect()
})

onUnmounted(() => {
  websocket.disconnect()
})
</script>

<style scoped>
.module-link {
  @apply px-4 py-2.5 rounded-enacom-sm text-sm font-bold text-slate-600 transition-all;
}

.module-link:hover {
  @apply bg-slate-100 text-slate-900;
}

.module-link-active {
  @apply bg-gradient-to-r from-enacom-blue-dark to-enacom-blue-main text-white shadow-enacom-blue;
}
</style>