<template>
  <div class="min-h-screen bg-gray-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <Header />

      <!-- Panel de configuración -->
      <ConfigPanel
        @start="handleStartTranscription"
        :disabled="store.isProcessing"
      />

      <!-- Barra de progreso + Cancelar -->
      <div v-if="store.isProcessing" class="relative">
        <ProgressBar
          :progress="store.progress"
          :current-file="store.currentFile"
          :current-index="store.currentFileIndex"
          :total-files="store.totalFiles"
          :message="store.statusMessage"
        />
        <button
          @click="handleCancel"
          class="absolute top-4 right-4 inline-flex items-center gap-1.5 px-3 py-1.5
                 bg-red-50 border border-red-300 hover:bg-red-100
                 text-red-600 text-sm font-semibold rounded-lg transition-all"
          title="Cancelar transcripción"
        >
          ✕ Cancelar
        </button>
      </div>

      <!-- Vista de transcripción en vivo -->
      <TranscriptionView v-if="store.isProcessing" />

      <!-- Panel de descargas -->
      <DownloadsPanel
        v-if="store.hasResults"
        @clear="handleClear"
      />

      <!-- Error -->
      <div
        v-if="store.taskStatus === 'failed'"
        class="card mb-6 border-l-4 border-red-500 bg-red-50"
      >
        <div class="flex items-center gap-3">
          <span class="text-2xl">❌</span>
          <div>
            <p class="font-bold text-red-700">Error en la transcripción</p>
            <p class="text-sm text-red-600 mt-1">{{ store.statusMessage || 'Ocurrió un error inesperado. Revisá los logs del backend.' }}</p>
          </div>
          <button
            @click="store.reset()"
            class="ml-auto text-sm text-red-600 hover:text-red-800 font-semibold underline"
          >
            Reiniciar
          </button>
        </div>
      </div>

      <!-- Panel de historial -->
      <HistoryPanel class="mt-6" />
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import { useTranscriptionStore } from '@/stores/transcription'
import websocket from '@/services/websocket'

import Header from '@/components/Header.vue'
import ConfigPanel from '@/components/ConfigPanel.vue'
import ProgressBar from '@/components/ProgressBar.vue'
import TranscriptionView from '@/components/TranscriptionView.vue'
import DownloadsPanel from '@/components/DownloadsPanel.vue'
import HistoryPanel from '@/components/HistoryPanel.vue'

const store = useTranscriptionStore()

async function handleStartTranscription({ files, config }) {
  try {
    await store.uploadAndStart(files, config)
  } catch (error) {
    console.error('Error iniciando transcripción:', error)
    alert('Error al iniciar transcripción: ' + (error.response?.data?.error || error.message))
  }
}

async function handleCancel() {
  if (!confirm('¿Cancelar la transcripción en curso?')) return
  await store.cancelTask()
}

function handleClear() {
  if (confirm('¿Limpiar los resultados actuales?')) {
    store.reset()
  }
}

onMounted(() => {
  websocket.connect()
  store.loadHistory()
})

onUnmounted(() => {
  websocket.disconnect()
})
</script>