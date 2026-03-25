<template>
  <div>
    <ConfigPanel
      @start="handleStartTranscription"
      :disabled="store.isProcessing"
    />

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
        class="absolute top-30 right-1 inline-flex items-center gap-1.5 px-3 py-1.5
               bg-red-50 border border-red-300 hover:bg-red-100
               text-red-600 text-sm font-semibold rounded-lg transition-all"
        title="Cancelar transcripción"
      >
        ✕ Cancelar
      </button>
    </div>

    <TranscriptionView v-if="store.isProcessing" />

    <DownloadsPanel
      v-if="store.hasResults"
      @clear="handleClear"
    />

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

    <HistoryPanel class="mt-6" />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'

import ConfigPanel from '@/components/ConfigPanel.vue'
import DownloadsPanel from '@/components/DownloadsPanel.vue'
import HistoryPanel from '@/components/HistoryPanel.vue'
import ProgressBar from '@/components/ProgressBar.vue'
import TranscriptionView from '@/components/TranscriptionView.vue'
import { useTranscriptionStore } from '@/stores/transcription'

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
  if (!window.confirm('¿Cancelar la transcripción en curso?')) return
  await store.cancelTask()
}

function handleClear() {
  if (window.confirm('¿Limpiar los resultados actuales?')) {
    store.reset()
  }
}

onMounted(() => {
  store.loadHistory()
})
</script>