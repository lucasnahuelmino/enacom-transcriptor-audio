/**
 * Cliente WebSocket para progreso en tiempo real
 */
import { io } from 'socket.io-client'
import { useTranscriptionStore } from '@/stores/transcription'

class WebSocketService {
  constructor() {
    this.socket = null
    this.connected = false
    this.currentTaskId = null
  }
  
  connect() {
    if (this.socket && this.connected) {
      return
    }
    
    const wsUrl = import.meta.env.VITE_WS_URL || 'http://localhost:5000'
    
    this.socket = io(wsUrl, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5
    })
    
    this.setupListeners()
  }
  
  setupListeners() {
    this.socket.on('connect', () => {
      console.log('[WebSocket] Conectado')
      this.connected = true
    })
    
    this.socket.on('disconnect', () => {
      console.log('[WebSocket] Desconectado')
      this.connected = false
    })
    
    this.socket.on('connected', (data) => {
      console.log('[WebSocket] Mensaje del servidor:', data.message)
    })
    
    this.socket.on('subscribed', (data) => {
      console.log('[WebSocket] Suscrito a tarea:', data.task_id)
    })
    
    this.socket.on('task_progress', (data) => {
      console.log('[WebSocket] Progreso:', data.progress + '%')
      const store = useTranscriptionStore()
      store.updateProgress(data)
    })
    
    this.socket.on('task_completed', (data) => {
      console.log('[WebSocket] Tarea completada:', data.task_id)
      const store = useTranscriptionStore()
      store.setCompleted(data)
      this.unsubscribeFromTask(data.task_id)
    })
    
    this.socket.on('task_error', (data) => {
      console.error('[WebSocket] Error en tarea:', data.error)
      const store = useTranscriptionStore()
      store.setError(data.error)
      this.unsubscribeFromTask(data.task_id)
    })
    
    this.socket.on('error', (error) => {
      console.error('[WebSocket] Error:', error)
    })
  }
  
  subscribeToTask(taskId) {
    if (!this.socket || !this.connected) {
      this.connect()
      // Esperar a que conecte antes de suscribir
      setTimeout(() => this.subscribeToTask(taskId), 500)
      return
    }
    
    this.currentTaskId = taskId
    this.socket.emit('subscribe_task', { task_id: taskId })
    console.log('[WebSocket] Suscribiéndose a tarea:', taskId)
  }
  
  unsubscribeFromTask(taskId) {
    if (!this.socket || !this.connected) return
    
    this.socket.emit('unsubscribe_task', { task_id: taskId })
    console.log('[WebSocket] Desuscribiéndose de tarea:', taskId)
    
    if (this.currentTaskId === taskId) {
      this.currentTaskId = null
    }
  }
  
  disconnect() {
    if (this.socket) {
      if (this.currentTaskId) {
        this.unsubscribeFromTask(this.currentTaskId)
      }
      this.socket.disconnect()
      this.socket = null
      this.connected = false
    }
  }
}

export default new WebSocketService()
