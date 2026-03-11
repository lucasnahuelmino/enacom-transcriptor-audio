# ENACOM Transcriptor - Frontend v3.0

Frontend Vue.js para el sistema de transcripción de ENACOM.

## 🚀 Stack Tecnológico

- **Vue 3.4** (Composition API)
- **Vite 5.0** (Build tool)
- **Pinia** (State management)
- **Tailwind CSS** (Styling)
- **Socket.io-client** (WebSockets en tiempo real)
- **Axios** (HTTP client)

## 📦 Instalación

```bash
# Instalar dependencias
npm install

# Desarrollo (puerto 5173)
npm run dev

# Build para producción
npm run build

# Preview del build
npm run preview
```

## 🎨 Estructura del Proyecto

```
src/
├── main.js                    # Entry point
├── App.vue                    # Componente raíz
├── stores/
│   └── transcription.js       # Pinia store
├── services/
│   ├── api.js                 # Cliente HTTP
│   └── websocket.js           # Cliente WebSocket
├── components/
│   ├── Header.vue             # Header institucional
│   ├── ConfigPanel.vue        # Panel de configuración
│   ├── ProgressBar.vue        # Barra de progreso
│   ├── TranscriptionView.vue  # Vista de transcripción
│   ├── DownloadsPanel.vue     # Panel de descargas
│   └── HistoryPanel.vue       # Historial
├── utils/
│   └── formatters.js          # Utilidades de formateo
└── assets/
    └── main.css               # Estilos globales
```

## 🔌 Conexión con Backend

El frontend se conecta al backend Flask en `http://localhost:5000`:

- **REST API**: `/api/v1/*`
- **WebSocket**: `/socket.io`

Configurado en `vite.config.js` con proxy.

## 🎨 Design System

### Colores ENACOM

```css
enacom-blue-dark: #002f6c
enacom-blue-main: #0050b3
enacom-blue-mid: #0066cc
enacom-blue-soft: #e6f0ff
enacom-green: #15803d
enacom-red: #dc2626
enacom-amber: #d97706
```

### Componentes UI

- `.btn-primary` - Botón principal con gradiente
- `.btn-secondary` - Botón secundario
- `.card` - Tarjeta con sombra
- `.input` - Campo de entrada
- `.badge` - Badge de estado

## 📡 Flujo de Datos

```
Usuario → ConfigPanel → emit('start')
       ↓
    App.vue → store.uploadAndStart()
       ↓
   api.uploadFiles() → Flask API
       ↓
   WebSocket ← task_progress
       ↓
   store.updateProgress()
       ↓
   ProgressBar (reactivo)
```

## 🔧 Scripts Disponibles

```bash
npm run dev         # Servidor de desarrollo
npm run build       # Build para producción
npm run preview     # Preview del build
npm run lint        # Linter (si está configurado)
```

## 📝 Notas

- El puerto por defecto es **5173**
- El backend debe estar corriendo en **5000**
- Redis debe estar activo para WebSockets
- Las rutas usan alias `@/` para `src/`

---

**Desarrollado por ENACOM - Dirección Nacional de Control y Fiscalización**
