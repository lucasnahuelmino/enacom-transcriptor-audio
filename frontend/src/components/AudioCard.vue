<template>
  <div class="bg-white rounded-enacom border border-gray-200 overflow-hidden shadow-enacom-sm mb-5">
    <!-- ── File header ── -->
    <div class="bg-gradient-to-r from-enacom-blue-dark to-enacom-blue-main px-6 py-4 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <span class="text-2xl">🎵</span>
        <div>
          <h4 class="font-bold text-white leading-tight">{{ result.archivo }}</h4>
          <p class="text-sm text-white/70">Duración: {{ result.duracion_hhmmss }}</p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <span v-if="result.infracciones && result.infracciones.length > 0"
              class="inline-flex items-center gap-1.5 px-3 py-1 bg-red-500 text-white text-xs font-bold rounded-full">
          ⚠ {{ result.infracciones.length }} infraccion{{ result.infracciones.length !== 1 ? 'es' : '' }}
        </span>
        <span v-else class="inline-flex items-center gap-1.5 px-3 py-1 bg-green-500 text-white text-xs font-bold rounded-full">
          ✓ Sin infracciones
        </span>
      </div>
    </div>

    <!-- ── Waveform + Player ── -->
    <div class="px-6 py-5 bg-gray-950 border-b border-gray-800">
      <!-- Waveform container -->
      <div ref="waveformEl" class="mb-4 rounded-lg overflow-hidden" style="min-height: 80px">
        <div v-if="!audioReady && !loadError"
             class="flex items-center justify-center h-20 text-gray-500 text-sm gap-2">
          <span class="animate-spin">⟳</span> Cargando forma de onda...
        </div>
        <div v-if="loadError"
             class="flex items-center justify-center h-20 text-gray-500 text-sm gap-2">
          ⚠ Audio no disponible para previsualización
        </div>
      </div>

      <!-- Player controls -->
      <div class="flex items-center gap-4">
        <button
          @click="playPause"
          :disabled="!audioReady"
          class="flex items-center gap-2 px-5 py-2 bg-enacom-blue-main hover:bg-enacom-blue-mid
                 disabled:opacity-40 disabled:cursor-not-allowed
                 text-white font-bold text-sm rounded-lg transition-colors"
        >
          <span>{{ isPlaying ? '⏸' : '▶' }}</span>
          <span>{{ isPlaying ? 'Pausar' : 'Reproducir' }}</span>
        </button>

        <div class="flex items-center gap-2 flex-1">
          <span class="font-mono text-xs text-gray-400">{{ currentTimeStr }}</span>
          <div class="flex-1 h-1 bg-gray-700 rounded-full cursor-pointer" @click="seekClick">
            <div class="h-1 bg-enacom-blue-mid rounded-full transition-all"
                 :style="{ width: seekPercent + '%' }"></div>
          </div>
          <span class="font-mono text-xs text-gray-400">{{ result.duracion_hhmmss }}</span>
        </div>

        <!-- Volume -->
        <div class="flex items-center gap-2">
          <span class="text-gray-500 text-xs">🔊</span>
          <input
            type="range" min="0" max="1" step="0.05" v-model="volume"
            @input="setVolume"
            class="w-20 accent-enacom-blue-main cursor-pointer"
          />
        </div>
      </div>
    </div>

    <!-- ── Transcription Tabs ── -->
    <div class="px-6 pt-4 pb-2 border-b border-gray-100">
      <div class="flex gap-2">
        <button
          v-for="tab in availableTabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          :class="[
            'px-4 py-1.5 rounded-lg text-sm font-semibold transition-all',
            activeTab === tab.id
              ? 'bg-enacom-blue-main text-white shadow-sm'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          ]"
        >
          {{ tab.label }}
        </button>
      </div>
    </div>

    <!-- Tab: Segmentada -->
    <div v-if="activeTab === 'segmentada'"
         class="px-6 py-4 max-h-72 overflow-y-auto font-mono text-sm bg-gray-50 border-b border-gray-100">
      <template v-if="result.segmentos && result.segmentos.length">
        <div
          v-for="seg in result.segmentos"
          :key="seg.start"
          class="py-1.5 border-b border-gray-200 last:border-0 text-gray-800 leading-relaxed cursor-pointer hover:bg-enacom-blue-soft/50 transition-colors px-2 rounded"
          @click="seekToTime(seg.start)"
        >
          <span class="text-enacom-blue-main font-bold mr-2 text-xs">
            {{ formatTimestamp(seg.start) }}
          </span>
          {{ seg.text }}
        </div>
      </template>
      <p v-else class="text-gray-400 text-center py-8">Sin segmentos disponibles</p>
    </div>

    <!-- Tab: Completa -->
    <div v-if="activeTab === 'completa'"
         class="px-6 py-4 max-h-72 overflow-y-auto text-sm text-gray-800 bg-gray-50 border-b border-gray-100 leading-relaxed">
      <p v-if="result.texto_completo">{{ result.texto_completo }}</p>
      <p v-else class="text-gray-400 text-center py-8">Sin transcripción disponible</p>
    </div>

    <!-- Tab: Infracciones -->
    <div v-if="activeTab === 'infracciones'"
         class="px-6 py-4 max-h-72 overflow-y-auto bg-red-50 border-b border-red-100">
      <div
        v-for="inf in result.infracciones"
        :key="`${inf.inicio}-${inf.termino}-${inf.texto?.slice(0,20)}`"
        class="mb-3 pb-3 border-b border-red-100 last:border-0"
      >
        <div class="flex items-center gap-2 mb-1">
          <span class="px-2 py-0.5 bg-red-100 text-red-700 border border-red-200 rounded text-xs font-bold uppercase">
            {{ inf.termino }}
          </span>
          <span class="text-gray-500 text-xs font-mono">[{{ inf.inicio }} → {{ inf.fin }}]</span>
        </div>
        <p class="text-sm text-gray-700">{{ inf.texto }}</p>
      </div>
    </div>

    <!-- ── Downloads ── -->
    <div class="px-6 py-4 bg-gray-50 flex items-center gap-3 flex-wrap">
      <span class="text-xs font-bold text-gray-500 uppercase tracking-wider mr-1">Descargar:</span>
      <a
        v-if="result.txt_url"
        :href="result.txt_url"
        download
        class="inline-flex items-center gap-1.5 px-4 py-1.5 bg-white border border-gray-300
               hover:border-enacom-blue-main hover:bg-enacom-blue-soft
               text-gray-700 text-sm font-semibold rounded-lg transition-all"
      >
        📝 TXT
      </a>
      <a
        v-if="result.xlsx_url"
        :href="result.xlsx_url"
        download
        class="inline-flex items-center gap-1.5 px-4 py-1.5 bg-white border border-gray-300
               hover:border-enacom-blue-main hover:bg-enacom-blue-soft
               text-gray-700 text-sm font-semibold rounded-lg transition-all"
      >
        📊 XLSX
      </a>
      <a
        v-if="result.docx_url"
        :href="result.docx_url"
        download
        class="inline-flex items-center gap-1.5 px-4 py-1.5 bg-white border border-gray-300
               hover:border-enacom-blue-main hover:bg-enacom-blue-soft
               text-gray-700 text-sm font-semibold rounded-lg transition-all"
      >
        📄 DOCX
      </a>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps({
  result: {
    type: Object,
    required: true
  }
})

// ── Waveform / WaveSurfer ──────────────────────────────────────────
const waveformEl = ref(null)
const wavesurfer = ref(null)
const audioReady = ref(false)
const loadError = ref(false)
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const volume = ref(0.8)

const currentTimeStr = computed(() => secToHms(currentTime.value))
const seekPercent = computed(() => duration.value > 0 ? (currentTime.value / duration.value) * 100 : 0)

function secToHms(sec) {
  const s = Math.floor(sec)
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const ss = s % 60
  return `${h.toString().padStart(2,'0')}:${m.toString().padStart(2,'0')}:${ss.toString().padStart(2,'0')}`
}

function formatTimestamp(sec) {
  return secToHms(sec)
}

onMounted(async () => {
  if (!props.result.audio_url) { loadError.value = true; return }

  try {
    const WaveSurfer = (await import('wavesurfer.js')).default

    wavesurfer.value = WaveSurfer.create({
      container: waveformEl.value,
      waveColor: '#1e40af',
      progressColor: '#002f6c',
      cursorColor: '#d97706',
      height: 80,
      normalize: true,
      barWidth: 2,
      barGap: 1,
      barRadius: 2,
      backend: 'WebAudio',
    })

    wavesurfer.value.on('ready', () => {
      audioReady.value = true
      duration.value = wavesurfer.value.getDuration()
      wavesurfer.value.setVolume(volume.value)
    })
    wavesurfer.value.on('play',  () => isPlaying.value = true)
    wavesurfer.value.on('pause', () => isPlaying.value = false)
    wavesurfer.value.on('finish', () => { isPlaying.value = false; currentTime.value = 0 })
    wavesurfer.value.on('audioprocess', t => currentTime.value = t)
    wavesurfer.value.on('error', () => { loadError.value = true })

    await wavesurfer.value.load(props.result.audio_url)
  } catch (e) {
    console.error('WaveSurfer error:', e)
    loadError.value = true
  }
})

onUnmounted(() => {
  wavesurfer.value?.destroy()
})

function playPause() {
  wavesurfer.value?.playPause()
}

function setVolume() {
  wavesurfer.value?.setVolume(Number(volume.value))
}

function seekClick(e) {
  if (!wavesurfer.value || !audioReady.value) return
  const rect = e.currentTarget.getBoundingClientRect()
  const pct = (e.clientX - rect.left) / rect.width
  wavesurfer.value.seekTo(pct)
}

function seekToTime(sec) {
  if (!wavesurfer.value || !audioReady.value || !duration.value) return
  wavesurfer.value.seekTo(Math.min(sec / duration.value, 1))
}

// ── Tabs ──────────────────────────────────────────────────────────
const activeTab = ref('segmentada')

const availableTabs = computed(() => {
  const tabs = [
    { id: 'segmentada', label: '🕐 Segmentada' },
    { id: 'completa',   label: '📄 Completa' },
  ]
  if (props.result.infracciones?.length) {
    tabs.push({ id: 'infracciones', label: `⚠ Infracciones (${props.result.infracciones.length})` })
  }
  return tabs
})
</script>