<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <Header />
      
      <!-- Panel de configuración -->
      <ConfigPanel 
        @start="handleStartTranscription"
        :disabled="store.isProcessing"
      />
      
      <!-- Barra de progreso -->
      <ProgressBar 
        v-if="store.isProcessing"
        :progress="store.progress"
        :current-file="store.currentFile"
        :current-index="store.currentFileIndex"
        :total-files="store.totalFiles"
        :message="store.statusMessage"
      />
      
      <!-- Vista de transcripción en vivo -->
      <TranscriptionView 
        v-if="store.isProcessing && store.currentFileIndex > 0"
      />
      
      <!-- Panel de descargas (solo cuando hay resultados) -->
      <DownloadsPanel 
        v-if="store.hasResults"
        @clear="handleClear"
      />
      
      <!-- Panel de historial -->
      <HistoryPanel class="mt-6" />
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import { useTranscriptionStore } from '@/stores/transcription'
import websocket from '@/services/websocket'

// Componentes
import Header from '@/components/Header.vue'
import ConfigPanel from '@/components/ConfigPanel.vue'
import ProgressBar from '@/components/ProgressBar.vue'
import TranscriptionView from '@/components/TranscriptionView.vue'
import DownloadsPanel from '@/components/DownloadsPanel.vue'
import HistoryPanel from '@/components/HistoryPanel.vue'

// Store
const store = useTranscriptionStore()

// Handlers
async function handleStartTranscription({ files, config }) {
  try {
    console.log('Iniciando transcripción con', files.length, 'archivos')
    await store.uploadAndStart(files, config)
  } catch (error) {
    console.error('Error iniciando transcripción:', error)
    alert('Error al iniciar transcripción: ' + error.message)
  }
}

function handleClear() {
  if (confirm('¿Estás seguro de limpiar los resultados actuales?')) {
    store.reset()
  }
}

// Lifecycle
onMounted(() => {
  console.log('App montada')
  websocket.connect()
  store.loadHistory()
})

onUnmounted(() => {
  websocket.disconnect()
})
</script>
