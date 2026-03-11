/**
 * Store de Pinia para gestión del estado de transcripción
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'
import websocket from '@/services/websocket'

export const useTranscriptionStore = defineStore('transcription', () => {
  // State
  const currentTask = ref(null)
  const taskStatus = ref('idle') // idle, pending, processing, completed, failed
  const progress = ref(0)
  const currentFile = ref(null)
  const currentFileIndex = ref(0)
  const totalFiles = ref(0)
  const statusMessage = ref('')
  
  const resultados = ref([])
  const loteResult = ref(null)
  const runMeta = ref(null)
  const runZipUrl = ref(null)
  
  const history = ref([])
  
  // Computed
  const isProcessing = computed(() => 
    taskStatus.value === 'processing' || taskStatus.value === 'pending'
  )
  
  const hasResults = computed(() => 
    resultados.value.length > 0 || loteResult.value !== null
  )
  
  // Actions
  async function uploadAndStart(files, config) {
    const formData = new FormData()
    
    files.forEach(file => {
      formData.append('files', file)
    })
    
    formData.append('config', JSON.stringify(config))
    
    try {
      const response = await api.uploadFiles(formData)
      
      currentTask.value = response.task_id
      taskStatus.value = 'pending'
      totalFiles.value = response.files_count
      
      // Suscribirse a updates vía WebSocket
      websocket.subscribeToTask(response.task_id)
      
      return response.task_id
    } catch (error) {
      taskStatus.value = 'failed'
      throw error
    }
  }
  
  function updateProgress(data) {
    progress.value = data.progress || 0
    statusMessage.value = data.message || ''
    currentFile.value = data.current_file || null
    currentFileIndex.value = data.current_file_index || 0
    
    if (data.status) {
      taskStatus.value = data.status
    }
  }
  
  function setCompleted(result) {
    taskStatus.value = 'completed'
    progress.value = 100
    resultados.value = result.resultados || []
    
    if (result.lote_txt_url) {
      loteResult.value = {
        txt: result.lote_txt_url,
        xlsx: result.lote_xlsx_url,
        docx: result.lote_docx_url
      }
    }
    
    runMeta.value = {
      referencia: result.referencia,
      modo: result.modo,
      model_size: result.model_size,
      language: result.language,
      total_files: result.total_files,
      total_duration_hhmmss: result.total_duration_hhmmss,
      infracciones_total: result.infracciones_total,
      archivos_con_infracciones: result.archivos_con_infracciones
    }
    
    runZipUrl.value = result.zip_url || null
  }
  
  function setError(error) {
    taskStatus.value = 'failed'
    statusMessage.value = error
  }
  
  async function cancelTask() {
    if (!currentTask.value) return
    
    try {
      await api.cancelTask(currentTask.value)
      websocket.unsubscribeFromTask(currentTask.value)
      reset()
    } catch (error) {
      console.error('Error cancelando tarea:', error)
    }
  }
  
  async function loadHistory() {
    try {
      history.value = await api.getHistory()
    } catch (error) {
      console.error('Error cargando historial:', error)
    }
  }
  
  function reset() {
    currentTask.value = null
    taskStatus.value = 'idle'
    progress.value = 0
    currentFile.value = null
    currentFileIndex.value = 0
    totalFiles.value = 0
    statusMessage.value = ''
    resultados.value = []
    loteResult.value = null
    runMeta.value = null
    runZipUrl.value = null
  }
  
  return {
    // State
    currentTask,
    taskStatus,
    progress,
    currentFile,
    currentFileIndex,
    totalFiles,
    statusMessage,
    resultados,
    loteResult,
    runMeta,
    runZipUrl,
    history,
    
    // Computed
    isProcessing,
    hasResults,
    
    // Actions
    uploadAndStart,
    updateProgress,
    setCompleted,
    setError,
    cancelTask,
    loadHistory,
    reset
  }
})
