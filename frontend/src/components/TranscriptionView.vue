<template>
  <div class="card mb-6 animate-fadeInUp">
    <div class="flex items-center gap-3 mb-4">
      <span class="text-xl animate-pulse">🎙️</span>
      <div>
        <h3 class="font-bold text-enacom-blue-dark">Transcripción en progreso</h3>
        <p v-if="store.currentFile" class="text-sm text-gray-500">
          Procesando: <span class="font-semibold text-gray-700">{{ store.currentFile }}</span>
          <span class="text-gray-400"> ({{ store.currentFileIndex }}/{{ store.totalFiles }})</span>
        </p>
      </div>
    </div>

    <!-- Live segments -->
    <div
      ref="scrollRef"
      class="bg-gray-950 rounded-lg p-4 border border-gray-800 h-52 overflow-y-auto font-mono text-sm"
    >
      <div v-if="liveSegments.length === 0"
           class="flex flex-col items-center justify-center h-full text-gray-600 gap-2">
        <span class="text-2xl">⏳</span>
        <p class="text-xs">Esperando segmentos...</p>
      </div>

      <div
        v-for="(seg, i) in liveSegments"
        :key="i"
        class="mb-2 leading-relaxed"
        :class="i === liveSegments.length - 1 ? 'text-white' : 'text-gray-400'"
      >
        <span class="text-enacom-blue-mid text-xs mr-2 select-none">{{ seg.ts }}</span>
        <span>{{ seg.text }}</span>
      </div>

      <!-- Cursor parpadeante -->
      <span v-if="liveSegments.length > 0"
            class="inline-block w-2 h-4 bg-enacom-blue-mid opacity-80 animate-pulse ml-1 align-middle" />
    </div>

    <p class="text-xs text-gray-400 mt-2 text-right">
      Los resultados completos y archivos de descarga estarán disponibles al finalizar
    </p>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { useTranscriptionStore } from '@/stores/transcription'

const store = useTranscriptionStore()
const scrollRef = ref(null)
const liveSegments = ref([])

// Escuchar mensajes de progreso del store para simular "live" output
watch(
  () => store.statusMessage,
  (msg) => {
    if (!msg) return
    // El backend emite mensajes como "Segmento 3/12" — los mostramos en la consola
    const now = new Date()
    const ts = `${now.getHours().toString().padStart(2,'0')}:${now.getMinutes().toString().padStart(2,'0')}:${now.getSeconds().toString().padStart(2,'0')}`
    liveSegments.value.push({ ts, text: msg })
    if (liveSegments.value.length > 80) liveSegments.value.shift()

    nextTick(() => {
      if (scrollRef.value) {
        scrollRef.value.scrollTop = scrollRef.value.scrollHeight
      }
    })
  }
)

// Limpiar al cambiar de archivo
watch(
  () => store.currentFile,
  () => {
    liveSegments.value = []
  }
)
</script>