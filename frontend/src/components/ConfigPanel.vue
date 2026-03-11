<template>
  <div class="card mb-6 animate-fadeInUp">
    <!-- Header -->
    <div class="flex items-center gap-3 mb-6 pb-4 border-b-2 border-enacom-blue-main">
      <span class="text-xl">⚙️</span>
      <h2 class="text-lg font-bold text-enacom-blue-dark">
        Configuración del procesamiento
      </h2>
    </div>
    
    <!-- Upload de archivos -->
    <div class="mb-6">
      <label class="label">Archivos de audio</label>
      <div
        @drop.prevent="handleDrop"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        :class="[
          'border-2 border-dashed rounded-enacom p-8 text-center transition-all cursor-pointer',
          isDragging 
            ? 'border-enacom-blue-main bg-enacom-blue-soft' 
            : 'border-gray-300 hover:border-enacom-blue-main hover:bg-gray-50'
        ]"
        @click="$refs.fileInput.click()"
      >
        <input
          ref="fileInput"
          type="file"
          multiple
          accept=".mp3,.wav,.m4a,.ogg,.flac,.aac,.opus,.webm"
          @change="handleFileSelect"
          class="hidden"
        />
        
        <div v-if="selectedFiles.length === 0">
          <div class="text-4xl mb-3">📁</div>
          <p class="text-gray-600 font-semibold mb-1">
            Arrastrá archivos aquí o hacé clic para seleccionar
          </p>
          <p class="text-sm text-gray-500">
            MP3, WAV, M4A, OGG, FLAC, AAC, Opus, WebM (máx 500MB)
          </p>
        </div>
        
        <div v-else class="space-y-2">
          <div v-for="(file, index) in selectedFiles" :key="index" 
               class="flex items-center justify-between bg-white px-4 py-2 rounded-lg border border-gray-200">
            <div class="flex items-center gap-3">
              <span class="text-xl">🎵</span>
              <div class="text-left">
                <p class="font-semibold text-sm">{{ file.name }}</p>
                <p class="text-xs text-gray-500">{{ formatFileSize(file.size) }}</p>
              </div>
            </div>
            <button
              @click.stop="removeFile(index)"
              class="text-red-500 hover:text-red-700 font-bold"
            >
              ✕
            </button>
          </div>
          
          <button
            @click.stop="selectedFiles = []"
            class="text-sm text-red-600 hover:text-red-800 font-semibold mt-2"
          >
            Limpiar todos
          </button>
        </div>
      </div>
      
      <p v-if="selectedFiles.length > 0" class="mt-2 text-sm font-semibold text-enacom-blue-dark">
        📂 {{ selectedFiles.length }} archivo(s) seleccionado(s) — {{ formatTotalSize }}
      </p>
    </div>
    
    <!-- Configuración en 3 columnas -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <!-- Referencia -->
      <div>
        <label class="label">Nombre / Referencia</label>
        <input
          v-model="config.referencia"
          type="text"
          placeholder="Ej.: Acta 1542 - Operativo Centro"
          class="input"
        />
        <p class="text-xs text-gray-500 mt-1">Se usará como identificador en informes</p>
      </div>
      
      <!-- Idioma -->
      <div>
        <label class="label">Idioma del audio</label>
        <select v-model="config.language" class="input">
          <option value="es">🇦🇷 Español</option>
          <option value="en">🇺🇸 Inglés</option>
          <option value="pt">🇧🇷 Portugués</option>
          <option value="auto">🌍 Detección automática</option>
        </select>
      </div>
      
      <!-- Modo lote -->
      <div>
        <label class="label">Informe final</label>
        <div class="flex gap-2">
          <button
            @click="config.modo_lote = 'individual'"
            :class="[
              'flex-1 px-3 py-2 rounded-enacom-sm font-semibold transition-all',
              config.modo_lote === 'individual'
                ? 'bg-enacom-blue-soft border-2 border-enacom-blue-main text-enacom-blue-dark'
                : 'bg-gray-100 border-2 border-gray-300 text-gray-600 hover:border-gray-400'
            ]"
          >
            Individual
          </button>
          <button
            @click="config.modo_lote = 'combinado'"
            :class="[
              'flex-1 px-3 py-2 rounded-enacom-sm font-semibold transition-all',
              config.modo_lote === 'combinado'
                ? 'bg-enacom-blue-soft border-2 border-enacom-blue-main text-enacom-blue-dark'
                : 'bg-gray-100 border-2 border-gray-300 text-gray-600 hover:border-gray-400'
            ]"
          >
            Combinado
          </button>
        </div>
        
        <!-- Toggle ZIP -->
        <div class="flex items-center gap-2 mt-3 pt-3 border-t border-gray-200">
          <span class="text-lg">📦</span>
          <label class="text-sm font-semibold text-gray-600 flex-1">Incluir ZIP</label>
          <input
            v-model="config.export_zip"
            type="checkbox"
            class="w-5 h-5 text-enacom-blue-main rounded focus:ring-2 focus:ring-enacom-blue-main"
          />
        </div>
      </div>
    </div>
    
    <!-- Infracciones -->
    <div class="mb-6">
      <label class="label">Detección de infracciones</label>
      <textarea
        v-model="config.infracciones_raw"
        placeholder="Separar términos por comas..."
        rows="3"
        class="input font-mono text-sm"
      ></textarea>
      <p class="text-xs text-gray-500 mt-1">
        Ejemplo: put, pelotud, bolud, forr, conch, etc.
      </p>
    </div>
    
    <!-- Botón procesar -->
    <button
      @click="handleStart"
      :disabled="!canStart || disabled"
      class="btn-primary w-full text-lg"
    >
      <span v-if="!disabled">▶ Procesar {{ selectedFiles.length }} archivo(s)</span>
      <span v-else>⏳ Procesando...</span>
    </button>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { formatFileSize } from '@/utils/formatters'

const props = defineProps({
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['start'])

// State
const selectedFiles = ref([])
const isDragging = ref(false)
const fileInput = ref(null)

const config = ref({
  referencia: '',
  language: 'es',
  modo_lote: 'individual',
  export_zip: true,
  infracciones_raw: 'put, pelotud, bolud, forr, conch, cornud, cag, mierd, cul, soret, gil, garc, tarad, imbécil, imbecil, idiota, estupid, inutil, pija, pijoter, mogolic, retrasad, animal, besti, ostia, caraj, chup, jodet, cretin, maric, trol, pajer, salam, otari, panch, zarpad',
  coincidencia_parcial: true
})

// Computed
const canStart = computed(() => selectedFiles.value.length > 0)

const formatTotalSize = computed(() => {
  const total = selectedFiles.value.reduce((sum, file) => sum + file.size, 0)
  return formatFileSize(total)
})

// Methods
function handleFileSelect(event) {
  const files = Array.from(event.target.files)
  selectedFiles.value.push(...files)
}

function handleDrop(event) {
  isDragging.value = false
  const files = Array.from(event.dataTransfer.files)
  
  // Filtrar solo formatos soportados
  const supportedFormats = ['.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac', '.opus', '.webm']
  const validFiles = files.filter(file => {
    const ext = '.' + file.name.split('.').pop().toLowerCase()
    return supportedFormats.includes(ext)
  })
  
  if (validFiles.length < files.length) {
    alert(`Se ignoraron ${files.length - validFiles.length} archivo(s) con formato no soportado`)
  }
  
  selectedFiles.value.push(...validFiles)
}

function removeFile(index) {
  selectedFiles.value.splice(index, 1)
}

function handleStart() {
  if (!canStart.value) return
  
  // Preparar configuración
  const configToSend = {
    ...config.value,
    infracciones: config.value.infracciones_raw
      .split(',')
      .map(t => t.trim())
      .filter(Boolean)
  }
  
  emit('start', {
    files: selectedFiles.value,
    config: configToSend
  })
}
</script>
