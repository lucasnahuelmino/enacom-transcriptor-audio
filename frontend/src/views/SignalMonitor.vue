<template>
  <div class="grid grid-cols-1 xl:grid-cols-[320px_minmax(0,1fr)_360px] gap-6">
    <section class="card animate-fadeInUp bg-white/95 backdrop-blur">
      <div class="flex items-center justify-between mb-5 pb-4 border-b border-slate-200">
        <div>
          <p class="text-xs font-black uppercase tracking-[0.22em] text-enacom-blue-main">Live Signal Monitor</p>
          <h2 class="text-xl font-extrabold text-slate-900 mt-2">Configuración</h2>
        </div>
        <span :class="store.backendMode === 'real' ? 'badge badge-green' : 'badge badge-blue'">
          {{ store.backendMode === 'real' ? 'BB60C real' : 'Modo mock' }}
        </span>
      </div>

      <div class="space-y-4">
        <div>
          <label class="label">Frecuencia central</label>
          <input v-model.number="store.config.frequency_hz" type="number" min="1000" step="1000" class="input" />
        </div>

        <div>
          <label class="label">Span</label>
          <input v-model.number="store.config.span_hz" type="number" min="1000" step="1000" class="input" />
        </div>

        <div>
          <label class="label">Tipo de señal</label>
          <select v-model="store.config.signal_type" class="input">
            <option value="AM">AM</option>
            <option value="FM">FM</option>
            <option value="NFM">NFM</option>
            <option value="WFM">WFM</option>
            <option value="USB">USB</option>
            <option value="LSB">LSB</option>
          </select>
        </div>

        <div>
          <label class="label">Ganancia</label>
          <div class="flex items-center gap-3">
            <input v-model.number="store.config.gain_db" type="range" min="-10" max="40" step="1" class="w-full accent-enacom-blue-main" />
            <span class="w-12 text-right text-sm font-semibold text-slate-700">{{ store.config.gain_db }} dB</span>
          </div>
        </div>

        <div>
          <label class="label">Modo de dispositivo</label>
          <select v-model="store.config.preferred_mode" class="input">
            <option value="auto">Auto</option>
            <option value="mock">Mock</option>
            <option value="real">Real</option>
          </select>
        </div>

        <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm font-bold text-slate-700">Nivel instantáneo</span>
            <span class="text-sm font-black text-slate-900">{{ formatDbm(store.peakLevelDbm) }}</span>
          </div>
          <div class="h-3 rounded-full bg-slate-200 overflow-hidden">
            <div class="h-full rounded-full transition-all duration-200" :style="strengthStyle"></div>
          </div>
          <div class="mt-3 flex items-center justify-between text-xs text-slate-500">
            <span>{{ formatFrequency(store.peakFrequencyHz || store.config.frequency_hz) }}</span>
            <span>{{ store.isFrequencyActive ? 'Canal activo' : 'Canal en reposo' }}</span>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3 pt-2">
          <button @click="handleStart" :disabled="store.streaming" class="btn-primary !py-2.5">▶ Play</button>
          <button @click="handleStop" :disabled="!store.streaming" class="btn-secondary !py-2.5">⏸ Stop</button>
          <button @click="handleMute" class="btn-secondary !py-2.5">{{ store.config.mute ? '🔊 Activar' : '🔇 Mute' }}</button>
          <button @click="handleRecord" :class="store.recording ? 'bg-red-600 text-white border-red-600' : ''" class="btn-secondary !py-2.5">🔴 Record</button>
        </div>

        <div class="rounded-2xl border border-slate-200 p-4 space-y-3">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-bold text-slate-800">Transcripción en vivo</p>
              <p class="text-xs text-slate-500">Procesa chunks del stream reutilizando Whisper</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input :checked="store.transcriptionEnabled" type="checkbox" class="sr-only peer" @change="handleToggleTranscription($event.target.checked)" />
              <div class="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:bg-enacom-blue-main after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:after:translate-x-full"></div>
            </label>
          </div>
          <button @click="handleSaveConfig" class="btn-secondary w-full">Aplicar configuración</button>
        </div>

        <div class="rounded-2xl border border-slate-200 p-4">
          <div class="flex items-center justify-between mb-3">
            <div>
              <p class="text-sm font-bold text-slate-800">Bookmarks</p>
              <p class="text-xs text-slate-500">Saltos rápidos entre frecuencias observadas</p>
            </div>
            <button @click="store.addBookmark()" class="text-sm font-semibold text-enacom-blue-main">+ Guardar</button>
          </div>
          <div class="space-y-2 max-h-48 overflow-auto pr-1">
            <div v-for="bookmark in store.bookmarks" :key="bookmark.id" class="flex items-center gap-2 rounded-xl bg-slate-50 px-3 py-2 border border-slate-200">
              <button class="flex-1 text-left" @click="store.applyBookmark(bookmark)">
                <p class="text-sm font-semibold text-slate-800">{{ bookmark.label }}</p>
                <p class="text-xs text-slate-500">{{ bookmark.signal_type }} · {{ formatFrequency(bookmark.span_hz) }} span</p>
              </button>
              <button class="text-xs font-semibold text-red-500" @click="store.removeBookmark(bookmark.id)">Quitar</button>
            </div>
            <p v-if="store.bookmarks.length === 0" class="text-sm text-slate-500">Sin bookmarks todavía.</p>
          </div>
        </div>
      </div>
    </section>

    <section class="space-y-6">
      <div class="card animate-fadeInUp !p-0 overflow-hidden bg-[linear-gradient(180deg,#0f172a_0%,#111827_100%)] text-white">
        <div class="px-6 py-4 border-b border-white/10 flex items-center justify-between">
          <div>
            <p class="text-xs uppercase tracking-[0.26em] text-cyan-300 font-black">Spectrum</p>
            <h2 class="text-lg font-bold mt-1">Visualización en tiempo real</h2>
          </div>
          <div class="text-right text-sm text-white/70">
            <p>{{ formatFrequency(store.config.frequency_hz) }}</p>
            <p>{{ formatFrequency(store.config.span_hz) }} span</p>
          </div>
        </div>
        <div class="p-6">
          <canvas ref="chartCanvas" class="w-full h-[320px]"></canvas>
        </div>
      </div>

      <div class="card animate-fadeInUp !p-0 overflow-hidden bg-slate-950 text-white">
        <div class="px-6 py-4 border-b border-white/10 flex items-center justify-between">
          <div>
            <p class="text-xs uppercase tracking-[0.26em] text-amber-300 font-black">Waterfall</p>
            <h2 class="text-lg font-bold mt-1">Historial espectral</h2>
          </div>
          <span class="text-sm text-white/60">{{ store.waterfall.length }} frames</span>
        </div>
        <div class="p-4">
          <canvas ref="waterfallCanvas" width="960" height="320" class="w-full h-[320px] rounded-xl bg-black"></canvas>
        </div>
      </div>
    </section>

    <section class="space-y-6">
      <div class="card animate-fadeInUp bg-white/95 backdrop-blur">
        <div class="flex items-center justify-between mb-4">
          <div>
            <p class="text-xs uppercase tracking-[0.22em] text-enacom-blue-main font-black">Audio</p>
            <h2 class="text-lg font-bold text-slate-900 mt-1">Reproducción en vivo</h2>
          </div>
          <span :class="store.streaming ? 'badge badge-green' : 'badge badge-red'">{{ store.streaming ? 'Streaming' : 'Detenido' }}</span>
        </div>

        <div class="rounded-2xl bg-slate-50 border border-slate-200 p-4">
          <div class="flex items-center justify-between mb-3">
            <span class="text-sm font-semibold text-slate-700">Volumen</span>
            <span class="text-sm font-black text-slate-900">{{ Math.round(store.volume * 100) }}%</span>
          </div>
          <input :value="store.volume" type="range" min="0" max="1" step="0.01" class="w-full accent-enacom-blue-main" @input="store.updateVolume(Number($event.target.value))" />
        </div>

        <div class="mt-4 grid grid-cols-2 gap-3 text-sm">
          <div class="rounded-2xl border border-slate-200 p-4 bg-slate-50">
            <p class="text-slate-500 uppercase tracking-wide text-xs font-bold">Pico</p>
            <p class="mt-2 text-xl font-extrabold text-slate-900">{{ formatDbm(store.peakLevelDbm) }}</p>
          </div>
          <div class="rounded-2xl border border-slate-200 p-4 bg-slate-50">
            <p class="text-slate-500 uppercase tracking-wide text-xs font-bold">Noise floor</p>
            <p class="mt-2 text-xl font-extrabold text-slate-900">{{ formatDbm(store.noiseFloorDbm) }}</p>
          </div>
        </div>

        <p v-if="store.recordingFile" class="mt-4 text-xs text-slate-500 break-all">Último archivo grabado: {{ store.recordingFile }}</p>
      </div>

      <div class="card animate-fadeInUp bg-white/95 backdrop-blur">
        <div class="flex items-center justify-between mb-4">
          <div>
            <p class="text-xs uppercase tracking-[0.22em] text-enacom-blue-main font-black">Activity</p>
            <h2 class="text-lg font-bold text-slate-900 mt-1">Detección automática</h2>
          </div>
          <span :class="store.channelActive ? 'badge badge-green' : 'badge badge-slate'">
            {{ store.channelActive ? '🟢 Activo' : '⚪ Inactivo' }}
          </span>
        </div>

        <div class="space-y-4">
          <div>
            <div class="flex items-center justify-between mb-2">
              <label class="label">Threshold (dBm)</label>
              <span class="text-sm font-semibold text-slate-900">{{ store.activityConfig.threshold_dbm }}</span>
            </div>
            <input v-model.number="store.activityConfig.threshold_dbm" type="range" min="-120" max="0" step="0.5" class="w-full accent-enacom-blue-main" />
            <p class="mt-1 text-xs text-slate-500">Nivel mínimo para considerar canal activo</p>
          </div>

          <div>
            <div class="flex items-center justify-between mb-2">
              <label class="label">Hysteresis (dB)</label>
              <span class="text-sm font-semibold text-slate-900">{{ store.activityConfig.hysteresis_db }}</span>
            </div>
            <input v-model.number="store.activityConfig.hysteresis_db" type="range" min="0.1" max="10" step="0.1" class="w-full accent-enacom-blue-main" />
            <p class="mt-1 text-xs text-slate-500">Banda de histéresis para evitar flickering</p>
          </div>

          <div>
            <div class="flex items-center justify-between mb-2">
              <label class="label">Min Duration (s)</label>
              <span class="text-sm font-semibold text-slate-900">{{ store.activityConfig.min_duration_seconds }}</span>
            </div>
            <input v-model.number="store.activityConfig.min_duration_seconds" type="range" min="0.1" max="10" step="0.1" class="w-full accent-enacom-blue-main" />
            <p class="mt-1 text-xs text-slate-500">Duración mínima para confirmar cambio de estado</p>
          </div>

          <button @click="handleUpdateActivityConfig" class="btn-secondary w-full">Aplicar detección</button>
        </div>

        <div v-if="store.activityStateHistory.length > 0" class="mt-4 border-t border-slate-200 pt-4">
          <p class="text-xs font-bold text-slate-600 uppercase tracking-wide mb-3">Historial</p>
          <div class="space-y-2 max-h-40 overflow-auto text-xs">
            <div v-for="(entry, index) in store.activityStateHistory.slice().reverse()" :key="`activity-${index}`" class="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2 border border-slate-200">
              <div class="flex-1">
                <span :class="entry.is_active ? 'text-green-600 font-bold' : 'text-slate-600 font-bold'">
                  {{ entry.is_active ? '🟢' : '⚪' }} {{ entry.reason || 'Cambio de estado' }}
                </span>
                <p class="text-slate-500 text-xs">{{ formatTimestamp(entry.timestamp) }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="card animate-fadeInUp bg-white/95 backdrop-blur">
        <div class="flex items-center justify-between mb-4">
          <div>
            <p class="text-xs uppercase tracking-[0.22em] text-enacom-blue-main font-black">Transcript</p>
            <h2 class="text-lg font-bold text-slate-900 mt-1">Caja de transcripción</h2>
          </div>
          <span class="text-xs font-semibold text-slate-500">{{ store.transcriptionEnabled ? 'Whisper activo' : 'Whisper inactivo' }}</span>
        </div>

        <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 min-h-[240px] max-h-[320px] overflow-auto">
          <p v-if="store.transcriptionText" class="text-sm leading-7 text-slate-800 whitespace-pre-wrap">{{ store.transcriptionText }}</p>
          <p v-else class="text-sm text-slate-500">La transcripción parcial aparecerá acá cuando el stream entregue audio suficiente.</p>
        </div>

        <div v-if="store.partialText" class="mt-3 rounded-2xl bg-enacom-blue-soft border border-enacom-blue-main/20 px-4 py-3 text-sm text-enacom-blue-dark">
          Última actualización: {{ store.partialText }}
        </div>
      </div>

      <div class="card animate-fadeInUp bg-white/95 backdrop-blur">
        <div class="flex items-center justify-between mb-4">
          <div>
            <p class="text-xs uppercase tracking-[0.22em] text-enacom-blue-main font-black">Events</p>
            <h2 class="text-lg font-bold text-slate-900 mt-1">Registro reciente</h2>
          </div>
          <span class="text-xs text-slate-500">{{ store.events.length }} eventos</span>
        </div>

        <div class="space-y-2 max-h-[280px] overflow-auto pr-1">
          <div v-for="(event, index) in store.events" :key="`${event.timestamp}-${index}`" class="rounded-2xl border border-slate-200 px-4 py-3 bg-slate-50">
            <div class="flex items-center justify-between text-xs text-slate-500">
              <span>{{ formatTimestamp(event.timestamp) }}</span>
              <span>{{ event.active ? 'Activo' : 'Idle' }}</span>
            </div>
            <div class="mt-2 flex items-center justify-between text-sm font-semibold text-slate-800">
              <span>{{ formatFrequency(event.peak_frequency_hz || store.config.frequency_hz) }}</span>
              <span>{{ formatDbm(event.peak_level_dbm) }}</span>
            </div>
          </div>
          <p v-if="store.events.length === 0" class="text-sm text-slate-500">Todavía no ingresaron eventos del stream.</p>
        </div>
      </div>

      <div v-if="store.lastError" class="card border-l-4 border-red-500 bg-red-50">
        <p class="font-bold text-red-700">Error de monitoreo</p>
        <p class="text-sm text-red-600 mt-1">{{ store.lastError }}</p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'

import { useSignalMonitorStore } from '@/stores/signalMonitor'

const store = useSignalMonitorStore()
const chartCanvas = ref(null)
const waterfallCanvas = ref(null)

const strengthStyle = computed(() => ({
  width: `${store.signalStrengthPercent}%`,
  background: store.isFrequencyActive
    ? 'linear-gradient(90deg, #14b8a6 0%, #10b981 100%)'
    : 'linear-gradient(90deg, #f59e0b 0%, #f97316 100%)'
}))

function formatFrequency(value) {
  if (!value) return '0 Hz'
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(3)} MHz`
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)} kHz`
  return `${Math.round(value)} Hz`
}

function formatDbm(value) {
  if (value === null || value === undefined) return '-- dBm'
  return `${Number(value).toFixed(1)} dBm`
}

function formatTimestamp(timestamp) {
  if (!timestamp) return '--:--:--'
  return new Date(timestamp * 1000).toLocaleTimeString('es-AR')
}

async function handleStart() {
  try {
    await store.startMonitoring()
  } catch (error) {
    alert(error.response?.data?.error || error.message)
  }
}

async function handleStop() {
  try {
    await store.stopMonitoring()
  } catch (error) {
    alert(error.response?.data?.error || error.message)
  }
}

async function handleSaveConfig() {
  try {
    await store.saveConfig()
  } catch (error) {
    alert(error.response?.data?.error || error.message)
  }
}

async function handleToggleTranscription(enabled) {
  try {
    await store.toggleTranscription(enabled)
  } catch (error) {
    alert(error.response?.data?.error || error.message)
  }
}

function handleMute() {
  store.setMute(!store.config.mute)
  store.saveConfig().catch(error => {
    alert(error.response?.data?.error || error.message)
  })
}

async function handleRecord() {
  try {
    await store.toggleRecording()
  } catch (error) {
    alert(error.response?.data?.error || error.message)
  }
}

async function handleUpdateActivityConfig() {
  try {
    await store.updateActivityConfig({
      threshold_dbm: store.activityConfig.threshold_dbm,
      hysteresis_db: store.activityConfig.hysteresis_db,
      min_duration_seconds: store.activityConfig.min_duration_seconds
    })
  } catch (error) {
    alert(error.response?.data?.error || error.message)
  }
}

function renderSpectrum() {
  const canvas = chartCanvas.value
  if (!canvas) return

  const context = canvas.getContext('2d')
  const rect = canvas.getBoundingClientRect()
  if (rect.width > 0) {
    canvas.width = rect.width * window.devicePixelRatio
    canvas.height = rect.height * window.devicePixelRatio
    context.scale(window.devicePixelRatio, window.devicePixelRatio)
  }

  const width = rect.width || canvas.width
  const height = rect.height || canvas.height
  context.clearRect(0, 0, width, height)
  context.fillStyle = '#0f172a'
  context.fillRect(0, 0, width, height)

  if (!store.levels.length) {
    return
  }

  const minLevel = Math.min(...store.levels) - 3
  const maxLevel = Math.max(...store.levels) + 3
  const stepX = width / Math.max(store.levels.length - 1, 1)

  context.strokeStyle = 'rgba(255,255,255,0.08)'
  context.lineWidth = 1
  for (let row = 1; row < 5; row += 1) {
    const y = (height / 5) * row
    context.beginPath()
    context.moveTo(0, y)
    context.lineTo(width, y)
    context.stroke()
  }

  context.beginPath()
  store.levels.forEach((value, index) => {
    const normalized = (value - minLevel) / Math.max(maxLevel - minLevel, 1)
    const x = index * stepX
    const y = height - (normalized * (height - 24)) - 12
    if (index === 0) {
      context.moveTo(x, y)
    } else {
      context.lineTo(x, y)
    }
  })

  context.strokeStyle = '#38bdf8'
  context.lineWidth = 2
  context.stroke()

  context.lineTo(width, height - 8)
  context.lineTo(0, height - 8)
  context.closePath()
  context.fillStyle = 'rgba(56, 189, 248, 0.16)'
  context.fill()

  context.fillStyle = 'rgba(255,255,255,0.72)'
  context.font = '12px sans-serif'
  context.fillText(formatFrequency(store.config.frequency_hz - (store.config.span_hz / 2)), 8, height - 8)
  context.fillText(formatFrequency(store.config.frequency_hz + (store.config.span_hz / 2)), width - 110, height - 8)
}

function renderWaterfall() {
  const canvas = waterfallCanvas.value
  if (!canvas) return
  const context = canvas.getContext('2d')
  const rows = store.waterfall
  const width = canvas.width
  const height = canvas.height
  context.clearRect(0, 0, width, height)

  if (!rows.length) {
    context.fillStyle = '#020617'
    context.fillRect(0, 0, width, height)
    return
  }

  const rowHeight = height / rows.length
  rows.forEach((row, rowIndex) => {
    const cellWidth = width / row.length
    row.forEach((value, columnIndex) => {
      const intensity = Math.max(0, Math.min(1, (value + 110) / 60))
      const hue = 220 - (intensity * 190)
      const lightness = 14 + (intensity * 55)
      context.fillStyle = `hsl(${hue} 95% ${lightness}%)`
      context.fillRect(columnIndex * cellWidth, rowIndex * rowHeight, Math.ceil(cellWidth + 1), Math.ceil(rowHeight + 1))
    })
  })
}

watch(
  () => [store.frequencies, store.levels],
  () => {
    renderSpectrum()
  },
  { deep: true }
)

watch(
  () => store.waterfall,
  () => {
    renderWaterfall()
  },
  { deep: true }
)

onMounted(async () => {
  store.subscribe()
  await store.loadStatus()
  await nextTick()
  renderSpectrum()
  renderWaterfall()
})

onUnmounted(() => {
  store.unsubscribe()
})
</script>