<template>
  <div class="animate-fadeInUp">

    <!-- ── Top bar ── -->
    <div class="flex items-center justify-between mb-5">
      <div class="flex items-center gap-3">
        <span class="text-2xl">📥</span>
        <div>
          <h2 class="text-lg font-bold text-enacom-blue-dark">Resultados</h2>
          <p class="text-sm text-gray-500">{{ store.resultados.length }} archivo(s) procesado(s)</p>
        </div>
      </div>
      <button
        @click="$emit('clear')"
        class="inline-flex items-center gap-2 px-4 py-2 bg-white border border-red-300
               hover:bg-red-50 text-red-600 text-sm font-semibold rounded-lg transition-all"
      >
        🧹 Limpiar resultados
      </button>
    </div>

    <!-- ── Run meta ── -->
    <div v-if="store.runMeta" class="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-6">
      <div v-for="m in metaItems" :key="m.label"
           class="bg-white rounded-lg border border-gray-200 px-4 py-3 border-t-2 border-t-enacom-blue-main">
        <p class="text-xs text-gray-500 font-bold uppercase tracking-wide mb-1">{{ m.label }}</p>
        <p class="text-base font-black text-enacom-blue-dark truncate">{{ m.value }}</p>
      </div>
    </div>

    <!-- ── Per-file AudioCards ── -->
    <AudioCard
      v-for="(result, i) in store.resultados"
      :key="result.archivo + i"
      :result="result"
    />

    <!-- ── Lote (combined) downloads ── -->
    <div v-if="store.loteResult"
         class="mt-6 bg-white rounded-enacom border-2 border-enacom-blue-main overflow-hidden">
      <div class="bg-gradient-to-r from-enacom-blue-dark to-enacom-blue-main px-6 py-4">
        <div class="flex items-center gap-3">
          <span class="text-2xl">📦</span>
          <div>
            <h3 class="font-bold text-white">Informe combinado (lote)</h3>
            <p class="text-sm text-white/70">Todos los archivos en un único informe</p>
          </div>
        </div>
      </div>
      <div class="px-6 py-5 flex items-center gap-3 flex-wrap">
        <a
          v-if="store.loteResult.txt"
          :href="store.loteResult.txt"
          download
          class="inline-flex items-center gap-2 px-5 py-2.5 bg-white border border-gray-300
                 hover:border-enacom-blue-main hover:bg-enacom-blue-soft
                 text-gray-700 font-semibold rounded-lg transition-all"
        >
          📝 TXT combinado
        </a>
        <a
          v-if="store.loteResult.xlsx"
          :href="store.loteResult.xlsx"
          download
          class="inline-flex items-center gap-2 px-5 py-2.5 bg-white border border-gray-300
                 hover:border-enacom-blue-main hover:bg-enacom-blue-soft
                 text-gray-700 font-semibold rounded-lg transition-all"
        >
          📊 XLSX combinado
        </a>
        <a
          v-if="store.loteResult.docx"
          :href="store.loteResult.docx"
          download
          class="inline-flex items-center gap-2 px-5 py-2.5 bg-white border border-gray-300
                 hover:border-enacom-blue-main hover:bg-enacom-blue-soft
                 text-gray-700 font-semibold rounded-lg transition-all"
        >
          📄 DOCX combinado
        </a>
      </div>
    </div>

    <!-- ── ZIP completo ── -->
    <div v-if="store.runZipUrl" class="mt-4">
      <a
        :href="store.runZipUrl"
        download
        class="flex items-center justify-center gap-3 w-full py-3.5
               bg-gradient-to-r from-enacom-blue-dark to-enacom-blue-main
               hover:from-enacom-blue-main hover:to-enacom-blue-mid
               text-white font-bold rounded-enacom shadow-enacom-blue
               transition-all hover:-translate-y-0.5 hover:shadow-lg"
      >
        📦 Descargar transcripción completa (ZIP)
      </a>
    </div>

  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useTranscriptionStore } from '@/stores/transcription'
import AudioCard from '@/components/AudioCard.vue'

defineEmits(['clear'])

const store = useTranscriptionStore()

const metaItems = computed(() => {
  if (!store.runMeta) return []
  return [
    { label: 'Modo',        value: store.runMeta.modo },
    { label: 'Modelo',      value: store.runMeta.model_size },
    { label: 'Referencia',  value: store.runMeta.referencia || '—' },
    { label: 'Duración',    value: store.runMeta.total_duration_hhmmss },
    { label: 'Infracciones',value: `${store.runMeta.infracciones_total} (${store.runMeta.archivos_con_infracciones} arch.)` },
  ]
})
</script>