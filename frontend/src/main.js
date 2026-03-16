/**
 * Entry point de la aplicación Vue
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'

// Estilos
import './assets/main.css'

// Crear app
const app = createApp(App)

// Pinia para state management
app.use(createPinia())

// Montar app
app.mount('#app')

console.log('🎧 ENACOM Transcriptor de audios iniciado')
