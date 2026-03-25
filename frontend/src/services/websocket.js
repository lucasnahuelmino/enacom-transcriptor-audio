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
    this.listeners = new Map()
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

    ;[
      'signal_monitor_state',
      'signal_monitor_spectrum',
      'signal_monitor_audio',
      'signal_monitor_transcription',
      'signal_monitor_event',
      'signal_monitor_activity_change',
      'signal_monitor_error',
      'signal_monitor_subscribed',
      'signal_monitor_unsubscribed'
    ].forEach(eventName => {
      this.socket.on(eventName, payload => {
        this.notify(eventName, payload)
      })
    })
  }

  on(eventName, handler) {
    if (!this.listeners.has(eventName)) {
      this.listeners.set(eventName, new Set())
    }
    this.listeners.get(eventName).add(handler)
  }

  off(eventName, handler) {
    const handlers = this.listeners.get(eventName)
    if (!handlers) return
    handlers.delete(handler)
    if (handlers.size === 0) {
      this.listeners.delete(eventName)
    }
  }

  notify(eventName, payload) {
    const handlers = this.listeners.get(eventName)
    if (!handlers) return
    handlers.forEach(handler => handler(payload))
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

  subscribeToSignalMonitor() {
    if (!this.socket || !this.connected) {
      this.connect()
      setTimeout(() => this.subscribeToSignalMonitor(), 500)
      return
    }
    this.socket.emit('subscribe_signal_monitor')
  }

  unsubscribeFromSignalMonitor() {
    if (!this.socket || !this.connected) return
    this.socket.emit('unsubscribe_signal_monitor')
  }
  
  disconnect() {
    if (this.socket) {
      if (this.currentTaskId) {
        this.unsubscribeFromTask(this.currentTaskId)
      }
      this.unsubscribeFromSignalMonitor()
      this.socket.disconnect()
      this.socket = null
      this.connected = false
    }
  }
}

export default new WebSocketService()
