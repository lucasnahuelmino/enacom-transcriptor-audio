<template>
  <div class="card mb-6 animate-fadeInUp">
    <div class="flex items-center gap-3 mb-4">
      <span class="text-xl">📝</span>
      <h3 class="font-bold text-enacom-blue-dark">Transcripción en progreso</h3>
    </div>
    
    <div class="bg-gray-50 rounded-lg p-4 border border-gray-200 max-h-96 overflow-y-auto font-mono text-sm">
      <p class="text-gray-600 text-center py-8">
        La transcripción se mostrará aquí en tiempo real...
      </p>
      
      <!-- Aquí se mostrarían los segmentos en vivo cuando lleguen por WebSocket -->
      <!-- Por ahora dejamos esto simplificado -->
    </div>
    
    <p class="text-xs text-gray-500 mt-3 text-center">
      Los resultados completos estarán disponibles al finalizar el procesamiento
    </p>
  </div>
</template>

<script setup>
import { useTranscriptionStore } from '@/stores/transcription'

const store = useTranscriptionStore()

// En una versión completa, aquí escucharías los updates de WebSocket
// y mostrarías los segmentos en tiempo real
</script>
