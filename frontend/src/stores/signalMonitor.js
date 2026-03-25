import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import api from '@/services/api'
import websocket from '@/services/websocket'

function decodeBase64ToArrayBuffer(base64) {
  const binary = window.atob(base64)
  const length = binary.length
  const bytes = new Uint8Array(length)
  for (let index = 0; index < length; index += 1) {
    bytes[index] = binary.charCodeAt(index)
  }
  return bytes.buffer
}

function formatBookmarkName(frequencyHz) {
  return `${(frequencyHz / 1_000_000).toFixed(3)} MHz`
}

export const useSignalMonitorStore = defineStore('signalMonitor', () => {
  const config = ref({
    frequency_hz: 101_700_000,
    span_hz: 2_500_000,
    gain_db: 18,
    signal_type: 'FM',
    mute: false,
    live_transcription: false,
    preferred_mode: 'auto'
  })

  const initialized = ref(false)
  const streaming = ref(false)
  const recording = ref(false)
  const transcriptionEnabled = ref(false)
  const backendMode = ref('mock')
  const lastError = ref('')
  const message = ref('')
  const recordingFile = ref(null)
  const transcriptionText = ref('')
  const partialText = ref('')
  const frequencies = ref([])
  const levels = ref([])
  const peakFrequencyHz = ref(null)
  const peakLevelDbm = ref(-120)
  const noiseFloorDbm = ref(-120)
  const isFrequencyActive = ref(false)
  const events = ref([])
  const waterfall = ref([])
  const volume = ref(0.85)
  const bookmarks = ref(loadBookmarks())
  const channelActive = ref(false)
  const activityStateHistory = ref([])
  const activityConfig = ref({
    threshold_dbm: -70.0,
    hysteresis_db: 3.0,
    min_duration_seconds: 0.5
  })

  let audioContext = null
  let gainNode = null
  let nextPlaybackTime = 0

  const signalStrengthPercent = computed(() => {
    const normalized = ((peakLevelDbm.value + 120) / 90) * 100
    return Math.max(0, Math.min(100, normalized))
  })

  const currentBookmarkLabel = computed(() => formatBookmarkName(config.value.frequency_hz))

  function loadBookmarks() {
    try {
      const raw = window.localStorage.getItem('enacom.signal-monitor.bookmarks')
      return raw ? JSON.parse(raw) : []
    } catch {
      return []
    }
  }

  function persistBookmarks() {
    window.localStorage.setItem('enacom.signal-monitor.bookmarks', JSON.stringify(bookmarks.value))
  }

  async function ensureAudioEngine() {
    if (!audioContext) {
      audioContext = new window.AudioContext()
      gainNode = audioContext.createGain()
      gainNode.gain.value = volume.value
      gainNode.connect(audioContext.destination)
      nextPlaybackTime = audioContext.currentTime
    }

    if (audioContext.state === 'suspended') {
      await audioContext.resume()
    }
  }

  async function enqueueAudioChunk(payload) {
    if (!payload?.pcm_base64 || config.value.mute) {
      return
    }

    await ensureAudioEngine()

    const arrayBuffer = decodeBase64ToArrayBuffer(payload.pcm_base64)
    const int16Data = new Int16Array(arrayBuffer)
    const float32Data = new Float32Array(int16Data.length)
    for (let index = 0; index < int16Data.length; index += 1) {
      float32Data[index] = int16Data[index] / 32768
    }

    const sampleRate = payload.sample_rate || 16000
    const audioBuffer = audioContext.createBuffer(1, float32Data.length, sampleRate)
    audioBuffer.copyToChannel(float32Data, 0)

    const source = audioContext.createBufferSource()
    source.buffer = audioBuffer
    source.connect(gainNode)

    const startAt = Math.max(audioContext.currentTime + 0.02, nextPlaybackTime)
    source.start(startAt)
    nextPlaybackTime = startAt + audioBuffer.duration
  }

  function attachSocketListeners() {
    websocket.on('signal_monitor_state', handleState)
    websocket.on('signal_monitor_subscribed', handleState)
    websocket.on('signal_monitor_spectrum', handleSpectrum)
    websocket.on('signal_monitor_audio', enqueueAudioChunk)
    websocket.on('signal_monitor_transcription', handleTranscription)
    websocket.on('signal_monitor_event', handleEvent)
    websocket.on('signal_monitor_activity_change', handleActivityChange)
    websocket.on('signal_monitor_error', handleError)
  }

  function detachSocketListeners() {
    websocket.off('signal_monitor_state', handleState)
    websocket.off('signal_monitor_subscribed', handleState)
    websocket.off('signal_monitor_spectrum', handleSpectrum)
    websocket.off('signal_monitor_audio', enqueueAudioChunk)
    websocket.off('signal_monitor_transcription', handleTranscription)
    websocket.off('signal_monitor_event', handleEvent)
    websocket.off('signal_monitor_activity_change', handleActivityChange)
    websocket.off('signal_monitor_error', handleError)
  }

  function subscribe() {
    attachSocketListeners()
    websocket.connect()
    websocket.subscribeToSignalMonitor()
  }

  function unsubscribe() {
    websocket.unsubscribeFromSignalMonitor()
    detachSocketListeners()
  }

  async function loadStatus() {
    const status = await api.getSignalStatus()
    handleState(status)
    return status
  }

  async function startMonitoring() {
    lastError.value = ''
    const response = await api.startSignalMonitor(config.value)
    handleState(response)
    return response
  }

  async function stopMonitoring() {
    const response = await api.stopSignalMonitor()
    handleState(response)
    return response
  }

  async function saveConfig() {
    const response = await api.updateSignalConfig({
      frequency_hz: config.value.frequency_hz,
      span_hz: config.value.span_hz,
      gain_db: config.value.gain_db,
      signal_type: config.value.signal_type,
      mute: config.value.mute
    })
    handleState(response)
    return response
  }

  async function toggleRecording() {
    if (recording.value) {
      const response = await api.stopSignalRecording()
      if (response.audio_file) {
        recordingFile.value = response.audio_file
      }
      recording.value = false
      return response
    }

    const response = await api.startSignalRecording({
      session_name: `freq_${Math.round(config.value.frequency_hz)}`
    })
    recording.value = true
    recordingFile.value = response.audio_file || null
    return response
  }

  async function toggleTranscription(enabled) {
    config.value.live_transcription = enabled
    const response = await api.toggleSignalTranscription(enabled)
    handleState(response)
    return response
  }

  async function updateActivityConfig(updates) {
    activityConfig.value = { ...activityConfig.value, ...updates }
    try {
      const response = await api.updateSignalActivityConfig({
        threshold_dbm: activityConfig.value.threshold_dbm,
        hysteresis_db: activityConfig.value.hysteresis_db,
        min_duration_seconds: activityConfig.value.min_duration_seconds
      })
      if (response.activity_state_history) {
        activityStateHistory.value = response.activity_state_history.slice(-20)
      }
      return response
    } catch (error) {
      lastError.value = `Error al actualizar actividad: ${error.message}`
      throw error
    }
  }

  function handleState(payload) {
    initialized.value = Boolean(payload.initialized)
    streaming.value = Boolean(payload.streaming)
    recording.value = Boolean(payload.recording)
    transcriptionEnabled.value = Boolean(payload.transcription_enabled)
    backendMode.value = payload.backend_mode || 'mock'
    lastError.value = payload.last_error || ''
    recordingFile.value = payload.recording_file || null
    message.value = payload.message || message.value
    if (payload.config) {
      config.value = {
        ...config.value,
        ...payload.config,
        preferred_mode: config.value.preferred_mode
      }
    }
    if (payload.events) {
      events.value = payload.events.slice(-30).reverse()
    }
    if (payload.transcription_text) {
      transcriptionText.value = payload.transcription_text
    }
  }

  function handleSpectrum(payload) {
    frequencies.value = payload.frequencies_hz || []
    levels.value = payload.levels_dbm || []
    peakFrequencyHz.value = payload.peak_frequency_hz
    peakLevelDbm.value = payload.peak_level_dbm ?? peakLevelDbm.value
    noiseFloorDbm.value = payload.noise_floor_dbm ?? noiseFloorDbm.value
    isFrequencyActive.value = Boolean(payload.active)

    waterfall.value = [
      (payload.levels_dbm || []).slice(),
      ...waterfall.value
    ].slice(0, 64)
  }

  function handleTranscription(payload) {
    transcriptionText.value = payload.text || transcriptionText.value
    partialText.value = payload.partial_text || ''
  }

  function handleEvent(payload) {
    events.value = [payload, ...events.value].slice(0, 30)
  }

  function handleActivityChange(payload) {
    channelActive.value = Boolean(payload.is_active)
    if (payload.state_history) {
      activityStateHistory.value = payload.state_history.slice(-20)
    }
  }

  function handleError(payload) {
    lastError.value = payload.message || 'Error desconocido en monitor de señal'
  }

  function updateVolume(value) {
    volume.value = value
    if (gainNode) {
      gainNode.gain.value = value
    }
  }

  function setMute(value) {
    config.value.mute = value
    if (gainNode) {
      gainNode.gain.value = value ? 0 : volume.value
    }
  }

  async function applyBookmark(bookmark) {
    config.value.frequency_hz = bookmark.frequency_hz
    config.value.span_hz = bookmark.span_hz
    config.value.signal_type = bookmark.signal_type
    await saveConfig()
  }

  function addBookmark() {
    const candidate = {
      id: `${Date.now()}`,
      label: formatBookmarkName(config.value.frequency_hz),
      frequency_hz: config.value.frequency_hz,
      span_hz: config.value.span_hz,
      signal_type: config.value.signal_type
    }
    const alreadyExists = bookmarks.value.some(item => item.frequency_hz === candidate.frequency_hz)
    if (!alreadyExists) {
      bookmarks.value = [candidate, ...bookmarks.value].slice(0, 12)
      persistBookmarks()
    }
  }

  function removeBookmark(id) {
    bookmarks.value = bookmarks.value.filter(item => item.id !== id)
    persistBookmarks()
  }

  return {
    config,
    initialized,
    streaming,
    recording,
    transcriptionEnabled,
    backendMode,
    lastError,
    message,
    recordingFile,
    transcriptionText,
    partialText,
    frequencies,
    levels,
    peakFrequencyHz,
    peakLevelDbm,
    noiseFloorDbm,
    isFrequencyActive,
    events,
    waterfall,
    volume,
    bookmarks,
    channelActive,
    activityStateHistory,
    activityConfig,
    signalStrengthPercent,
    currentBookmarkLabel,
    subscribe,
    unsubscribe,
    loadStatus,
    startMonitoring,
    stopMonitoring,
    saveConfig,
    toggleRecording,
    toggleTranscription,
    updateActivityConfig,
    updateVolume,
    setMute,
    applyBookmark,
    addBookmark,
    removeBookmark
  }
})