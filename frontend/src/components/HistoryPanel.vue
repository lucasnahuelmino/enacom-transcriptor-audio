<template>
  <div class="card">
    <div class="flex items-center gap-3 mb-4">
      <span class="text-xl">📚</span>
      <h3 class="font-bold text-enacom-blue-dark">Historial de transcripciones</h3>
    </div>
    
    <div v-if="store.history.length === 0" class="text-center py-12 text-gray-500">
      <p class="text-4xl mb-3">📭</p>
      <p class="font-semibold">No hay transcripciones anteriores</p>
      <p class="text-sm">Las transcripciones procesadas aparecerán aquí</p>
    </div>
    
    <div v-else class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b-2 border-enacom-blue-main">
            <th class="text-left py-3 px-2 font-bold text-gray-700">Fecha</th>
            <th class="text-left py-3 px-2 font-bold text-gray-700">Referencia</th>
            <th class="text-left py-3 px-2 font-bold text-gray-700">Archivos</th>
            <th class="text-left py-3 px-2 font-bold text-gray-700">Duración</th>
            <th class="text-left py-3 px-2 font-bold text-gray-700">Infracciones</th>
            <th class="text-left py-3 px-2 font-bold text-gray-700">Estado</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="item in store.history"
            :key="item.id"
            class="border-b border-gray-200 hover:bg-gray-50 transition-colors"
          >
            <td class="py-3 px-2 text-gray-600">
              {{ formatDate(item.created_at) }}
            </td>
            <td class="py-3 px-2 font-semibold">
              {{ item.referencia || '—' }}
            </td>
            <td class="py-3 px-2 text-gray-600">
              {{ item.num_files }}
            </td>
            <td class="py-3 px-2 text-gray-600">
              {{ item.total_duration || '—' }}
            </td>
            <td class="py-3 px-2">
              <span v-if="item.infracciones_count > 0" class="badge badge-red">
                {{ item.infracciones_count }}
              </span>
              <span v-else class="text-gray-400">—</span>
            </td>
            <td class="py-3 px-2">
              <span
                :class="[
                  'badge',
                  item.status === 'completed' ? 'badge-green' : 'badge-blue'
                ]"
              >
                {{ getStatusLabel(item.status) }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { useTranscriptionStore } from '@/stores/transcription'
import { formatDate } from '@/utils/formatters'

const store = useTranscriptionStore()

function getStatusLabel(status) {
  const labels = {
    'completed': '✅ Completado',
    'processing': '⏳ Procesando',
    'failed': '❌ Error',
    'cancelled': '🚫 Cancelado'
  }
  return labels[status] || status
}
</script>
