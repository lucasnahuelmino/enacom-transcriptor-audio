/**
 * Cliente HTTP para comunicación con el backend
 */
import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Interceptor para logging
apiClient.interceptors.request.use(
  config => {
    console.log(`[API] ${config.method.toUpperCase()} ${config.url}`)
    return config
  },
  error => {
    console.error('[API] Request error:', error)
    return Promise.reject(error)
  }
)

apiClient.interceptors.response.use(
  response => {
    console.log(`[API] Response ${response.status} from ${response.config.url}`)
    return response
  },
  error => {
    console.error('[API] Response error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export default {
  /**
   * Sube archivos y inicia transcripción
   */
  async uploadFiles(formData) {
    const response = await apiClient.post('/transcription/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  },
  
  /**
   * Obtiene el estado de una tarea
   */
  async getTaskStatus(taskId) {
    const response = await apiClient.get(`/transcription/status/${taskId}`)
    return response.data
  },
  
  /**
   * Obtiene el resultado completo de una tarea
   */
  async getTaskResult(taskId) {
    const response = await apiClient.get(`/transcription/result/${taskId}`)
    return response.data
  },
  
  /**
   * Cancela una tarea en progreso
   */
  async cancelTask(taskId) {
    const response = await apiClient.post(`/transcription/cancel/${taskId}`)
    return response.data
  },
  
  /**
   * Obtiene el historial de transcripciones
   */
  async getHistory() {
    const response = await apiClient.get('/history')
    return response.data
  },
  
  /**
   * Descarga un archivo
   */
  getDownloadUrl(filename) {
    return `${apiClient.defaults.baseURL}/download/${filename}`
  },
  
  /**
   * Health check
   */
  async healthCheck() {
    const response = await apiClient.get('/health')
    return response.data
  },

  async getSignalStatus() {
    const response = await apiClient.get('/signal/status')
    return response.data
  },

  async startSignalMonitor(payload) {
    const response = await apiClient.post('/signal/start', payload)
    return response.data
  },

  async stopSignalMonitor() {
    const response = await apiClient.post('/signal/stop')
    return response.data
  },

  async updateSignalConfig(payload) {
    const response = await apiClient.post('/signal/config', payload)
    return response.data
  },

  async startSignalRecording(payload = {}) {
    const response = await apiClient.post('/signal/record/start', payload)
    return response.data
  },

  async stopSignalRecording() {
    const response = await apiClient.post('/signal/record/stop')
    return response.data
  },

  async toggleSignalTranscription(enabled) {
    const response = await apiClient.post('/signal/transcription/toggle', { enabled })
    return response.data
  },

  async updateSignalActivityConfig(payload) {
    const response = await apiClient.post('/signal/activity/config', payload)
    return response.data
  }
}
