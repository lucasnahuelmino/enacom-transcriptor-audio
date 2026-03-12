<template>
  <div class="card">
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-3">
        <span class="text-xl">📚</span>
        <h3 class="font-bold text-enacom-blue-dark">Historial de transcripciones</h3>
      </div>
      <button
        @click="reload"
        class="text-sm text-enacom-blue-main hover:text-enacom-blue-dark font-semibold transition-colors"
        title="Recargar historial"
      >
        ↺ Actualizar
      </button>
    </div>

    <div v-if="loading" class="text-center py-10 text-gray-500">
      <p class="text-2xl mb-2 animate-spin inline-block">⟳</p>
      <p class="text-sm">Cargando historial...</p>
    </div>

    <div v-else-if="store.history.length === 0" class="text-center py-12 text-gray-500">
      <p class="text-4xl mb-3">📭</p>
      <p class="font-semibold">No hay transcripciones anteriores</p>
      <p class="text-sm mt-1">Las transcripciones procesadas aparecerán aquí</p>
    </div>

    <div v-else class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b-2 border-enacom-blue-main text-xs uppercase tracking-wider text-gray-500">
            <th class="text-left py-3 px-2 font-bold">Fecha</th>
            <th class="text-left py-3 px-2 font-bold">Referencia / ID</th>
            <th class="text-left py-3 px-2 font-bold">Tipo</th>
            <th class="text-left py-3 px-2 font-bold">Archivos</th>
            <th class="text-left py-3 px-2 font-bold">Tamaño</th>
            <th class="text-left py-3 px-2 font-bold">Descargas</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="item in store.history"
            :key="item.task_id"
            class="border-b border-gray-100 hover:bg-gray-50 transition-colors"
          >
            <!-- Fecha -->
            <td class="py-3 px-2 text-gray-600 whitespace-nowrap text-xs">
              {{ formatDate(item.fecha) }}
            </td>

            <!-- Referencia -->
            <td class="py-3 px-2">
              <span class="font-semibold text-gray-800 block leading-tight">
                {{ item.referencia || '—' }}
              </span>
              <span class="text-xs text-gray-400 font-mono">{{ item.task_id?.slice(0, 8) }}…</span>
            </td>

            <!-- Tipo -->
            <td class="py-3 px-2">
              <span
                :class="[
                  'inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold',
                  item.tipo === 'LOTE'
                    ? 'bg-blue-100 text-blue-700'
                    : 'bg-gray-100 text-gray-600'
                ]"
              >
                {{ item.tipo }}
              </span>
            </td>

            <!-- Nº archivos -->
            <td class="py-3 px-2 text-gray-600 text-center">
              {{ item.num_files || '—' }}
            </td>

            <!-- Tamaño -->
            <td class="py-3 px-2 text-gray-500 text-xs whitespace-nowrap">
              {{ formatFileSize(item.tamaño_bytes) }}
            </td>

            <!-- Descargas -->
            <td class="py-3 px-2">
              <div class="flex items-center gap-1 flex-wrap">
                <a
                  v-if="item.txt_url"
                  :href="item.txt_url"
                  download
                  class="inline-flex items-center px-2 py-1 bg-white border border-gray-300
                         hover:border-enacom-blue-main hover:bg-enacom-blue-soft
                         text-gray-600 text-xs font-semibold rounded transition-all"
                  title="Descargar TXT"
                >
                  📝 TXT
                </a>
                <a
                  v-if="item.xlsx_url"
                  :href="item.xlsx_url"
                  download
                  class="inline-flex items-center px-2 py-1 bg-white border border-gray-300
                         hover:border-enacom-blue-main hover:bg-enacom-blue-soft
                         text-gray-600 text-xs font-semibold rounded transition-all"
                  title="Descargar XLSX"
                >
                  📊 XLSX
                </a>
                <a
                  v-if="item.docx_url"
                  :href="item.docx_url"
                  download
                  class="inline-flex items-center px-2 py-1 bg-white border border-gray-300
                         hover:border-enacom-blue-main hover:bg-enacom-blue-soft
                         text-gray-600 text-xs font-semibold rounded transition-all"
                  title="Descargar DOCX"
                >
                  📄 DOCX
                </a>
                <a
                  v-if="item.zip_url"
                  :href="item.zip_url"
                  download
                  class="inline-flex items-center px-2 py-1 bg-enacom-blue-soft border border-enacom-blue-main/30
                         hover:bg-enacom-blue-main hover:text-white
                         text-enacom-blue-dark text-xs font-bold rounded transition-all"
                  title="Descargar ZIP completo"
                >
                  📦 ZIP
                </a>
                <span
                  v-if="!item.txt_url && !item.xlsx_url && !item.docx_url && !item.zip_url"
                  class="text-gray-400 text-xs"
                >
                  Sin archivos
                </span>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useTranscriptionStore } from '@/stores/transcription'
import { formatDate, formatFileSize } from '@/utils/formatters'

const store = useTranscriptionStore()
const loading = ref(false)

async function reload() {
  loading.value = true
  try {
    await store.loadHistory()
  } finally {
    loading.value = false
  }
}

onMounted(reload)
</script>