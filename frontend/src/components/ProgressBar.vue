<template>
  <div class="card mb-6 animate-fadeInUp">
    <!-- Header con estado -->
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-3">
        <div class="animate-spin text-2xl">⚙️</div>
        <div>
          <h3 class="font-bold text-enacom-blue-dark">
            {{ statusText }}
          </h3>
          <p class="text-sm text-gray-600" v-if="currentFile">
            {{ currentFile }} 
            <span class="text-gray-400">
              ({{ currentIndex }} / {{ totalFiles }})
            </span>
          </p>
        </div>
      </div>
      
      <div class="text-right">
        <span class="text-3xl font-black text-enacom-blue-dark">
          {{ progress }}%
        </span>
      </div>
    </div>
    
    <!-- Barra de progreso -->
    <div class="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
      <div
        :style="{ width: progress + '%' }"
        class="h-full rounded-full bg-gradient-to-r from-enacom-blue-main via-enacom-blue-mid to-blue-400 transition-all duration-500 ease-out animate-shimmer"
        style="background-size: 200% 100%"
      ></div>
    </div>
    
    <!-- Mensaje adicional -->
    <p v-if="message" class="text-sm text-gray-600 mt-3 text-center">
      {{ message }}
    </p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  progress: {
    type: Number,
    default: 0
  },
  currentFile: {
    type: String,
    default: null
  },
  currentIndex: {
    type: Number,
    default: 0
  },
  totalFiles: {
    type: Number,
    default: 0
  },
  message: {
    type: String,
    default: ''
  }
})

const statusText = computed(() => {
  if (props.progress === 0) return 'Iniciando...'
  if (props.progress === 100) return '✅ Completado'
  if (props.progress >= 95) return 'Finalizando...'
  return '🎙️ Transcribiendo...'
})
</script>

<style scoped>
@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

.animate-shimmer {
  animation: shimmer 2s linear infinite;
}
</style>
