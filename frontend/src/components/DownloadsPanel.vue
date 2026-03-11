<template>
  <div class="card animate-fadeInUp">
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center gap-3">
        <span class="text-2xl">📥</span>
        <h2 class="text-lg font-bold text-enacom-blue-dark">
          Descargas disponibles
        </h2>
      </div>
      
      <button
        @click="$emit('clear')"
        class="btn-secondary text-red-600 hover:bg-red-50"
      >
        🧹 Limpiar resultados
      </button>
    </div>
    
    <!-- Métricas -->
    <div v-if="store.runMeta" class="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
      <div class="bg-gray-50 rounded-lg p-4 border-t-2 border-enacom-blue-main">
        <p class="text-xs text-gray-600 font-bold uppercase mb-1">Modo</p>
        <p class="text-lg font-black text-enacom-blue-dark">
          {{ store.runMeta.modo }}
        </p>
      </div>
      
      <div class="bg-gray-50 rounded-lg p-4 border-t-2 border-enacom-blue-main">
        <p class="text-xs text-gray-600 font-bold uppercase mb-1">Modelo</p>
        <p class="text-lg font-black text-enacom-blue-dark">
          {{ store.runMeta.model_size }}
        </p>
      </div>
      
      <div class="bg-gray-50 rounded-lg p-4 border-t-2 border-enacom-blue-main">
        <p class="text-xs text-gray-600 font-bold uppercase mb-1">Referencia</p>
        <p class="text-lg font-black text-enacom-blue-dark truncate">
          {{ store.runMeta.referencia || '—' }}
        </p>
      </div>
      
      <div class="bg-gray-50 rounded-lg p-4 border-t-2 border-enacom-blue-main">
        <p class="text-xs text-gray-600 font-bold uppercase mb-1">Duración</p>
        <p class="text-lg font-black text-enacom-blue-dark">
          {{ store.runMeta.total_duration_hhmmss }}
        </p>
      </div>
      
      <div class="bg-gray-50 rounded-lg p-4 border-t-2 border-enacom-blue-main">
        <p class="text-xs text-gray-600 font-bold uppercase mb-1">Infracciones</p>
        <p class="text-lg font-black text-enacom-blue-dark">
          {{ store.runMeta.infracciones_total }}
          <span class="text-sm text-gray-500">
            ({{ store.runMeta.archivos_con_infracciones }} arch.)
          </span>
        </p>
      </div>
    </div>
    
    <!-- Lote (si existe) -->
    <div v-if="store.loteResult" class="mb-6">
      <h3 class="font-bold text-gray-700 mb-3">📦 Lote consolidado</h3>
      <div class="grid grid-cols-3 gap-3">
        <a
          v-if="store.loteResult.txt"
          :href="getDownloadUrl(store.loteResult.txt)"
          download
          class="btn-secondary text-center"
        >
          📝 TXT (Lote)
        </a>
        <a
          v-if="store.loteResult.xlsx"
          :href="getDownloadUrl(store.loteResult.xlsx)"
          download
          class="btn-secondary text-center"
        >
          📊 XLSX (Lote)
        </a>
        <a
          v-if="store.loteResult.docx"
          :href="getDownloadUrl(store.loteResult.docx)"
          download
          class="btn-secondary text-center"
        >
          📄 DOCX (Lote)
        </a>
      </div>
    </div>
    
    <!-- Archivos individuales -->
    <div v-if="store.resultados.length > 0">
      <h3 class="font-bold text-gray-700 mb-3">
        🎧 Archivos individuales ({{ store.resultados.length }})
      </h3>
      
      <!-- Filtro -->
      <input
        v-model="filter"
        type="text"
        placeholder="Filtrar por nombre..."
        class="input mb-4"
      />
      
      <!-- Lista -->
      <div class="space-y-3">
        <div
          v-for="(item, index) in filteredResults"
          :key="index"
          class="bg-gray-50 rounded-lg p-4 border border-gray-200"
        >
          <p class="font-bold text-gray-800 mb-3">{{ item.archivo }}</p>
          
          <div class="grid grid-cols-4 gap-2">
            <a
              v-if="item.txt_url"
              :href="getDownloadUrl(item.txt_url)"
              download
              class="btn-secondary text-sm text-center"
            >
              📝 TXT
            </a>
            <a
              v-if="item.xlsx_url"
              :href="getDownloadUrl(item.xlsx_url)"
              download
              class="btn-secondary text-sm text-center"
            >
              📊 XLSX
            </a>
            <a
              v-if="item.docx_url"
              :href="getDownloadUrl(item.docx_url)"
              download
              class="btn-secondary text-sm text-center"
            >
              📄 DOCX
            </a>
            <button class="btn-secondary text-sm">
              📦 ZIP
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- ZIP completo -->
    <div v-if="store.runZipUrl" class="mt-6 pt-6 border-t-2 border-gray-200">
      <a
        :href="getDownloadUrl(store.runZipUrl)"
        download
        class="btn-primary w-full text-center block"
      >
        📦 Descargar transcripción completa (ZIP)
      </a>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useTranscriptionStore } from '@/stores/transcription'

defineEmits(['clear'])

const store = useTranscriptionStore()
const filter = ref('')

const filteredResults = computed(() => {
  if (!filter.value) return store.resultados
  
  const q = filter.value.toLowerCase()
  return store.resultados.filter(r => 
    r.archivo.toLowerCase().includes(q)
  )
})

function getDownloadUrl(url) {
  // Si la URL ya es absoluta, usarla directamente
  if (url.startsWith('http')) return url
  
  // Si es relativa, agregar el base URL del backend
  return `http://localhost:5000${url}`
}
</script>
