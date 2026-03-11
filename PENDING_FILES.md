# 📝 Archivos pendientes y próximos pasos

Este documento lista los archivos que faltan crear para completar la migración.

---

## ✅ Archivos ya creados

### Backend
- ✅ `backend/requirements.txt`
- ✅ `backend/app/config.py`
- ✅ `backend/app/__init__.py`
- ✅ `backend/app/models/schemas.py`
- ✅ `backend/app/core/transcription.py` (faster-whisper)
- ✅ `backend/app/api/routes.py`
- ✅ `backend/app/api/websockets.py`
- ✅ `backend/app/tasks/celery_tasks.py`
- ✅ `backend/run.py`
- ✅ `backend/celery_worker.py`
- ✅ `backend/.env.example`

### Frontend
- ✅ `frontend/package.json`
- ✅ `frontend/vite.config.js`
- ✅ `frontend/tailwind.config.js`
- ✅ `frontend/src/stores/transcription.js`
- ✅ `frontend/src/services/api.js`
- ✅ `frontend/src/services/websocket.js`
- ✅ `frontend/src/components/Header.vue`

### Documentación
- ✅ `README.md`
- ✅ `MIGRATION_GUIDE.md`

---

## 📋 Archivos pendientes

### Backend - Core modules

```bash
backend/app/core/
├── audio_processor.py     # ⚠️ ADAPTAR desde audio_ops.py
├── segmenter.py          # ⚠️ COPIAR desde enacom_transcriptor/segmenter.py
├── exporters.py          # ⚠️ ADAPTAR desde enacom_transcriptor/exporters.py
├── infracciones.py       # ⚠️ COPIAR desde enacom_transcriptor/infracciones.py
└── __init__.py
```

**Acción requerida:**
```bash
# Copiar y adaptar
cp enacom_transcriptor/audio_ops.py backend/app/core/audio_processor.py
cp enacom_transcriptor/segmenter.py backend/app/core/segmenter.py
cp enacom_transcriptor/exporters.py backend/app/core/exporters.py
cp enacom_transcriptor/infracciones.py backend/app/core/infracciones.py

# Renombrar funciones para cumplir con nomenclatura del backend:
# - ffprobe_duration_seconds() → get_audio_duration()
# - split_audio_to_wavs() → split_audio()
# - windowed_segments() → build_windowed_segments()
# - etc.
```

### Backend - Otros

```bash
backend/
├── .gitignore
├── pytest.ini            # Config para tests
├── tests/
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_transcription.py
│   └── test_exporters.py
└── assets/               # ⚠️ COPIAR desde raíz
    ├── logo_enacom.png
    ├── enacom_footer.png
    └── plantilla_enacom_limpia.docx
```

### Frontend - Componentes Vue

```bash
frontend/src/components/
├── Header.vue                   # ✅ Creado
├── ConfigPanel.vue              # ⚠️ CREAR
├── AudioUploader.vue            # ⚠️ CREAR
├── TranscriptionView.vue        # ⚠️ CREAR
├── ProgressBar.vue              # ⚠️ CREAR
├── AudioPlayer.vue              # ⚠️ CREAR
├── WaveformVisualizer.vue       # ⚠️ CREAR (con Plotly)
├── InfractionsList.vue          # ⚠️ CREAR
├── SegmentsList.vue             # ⚠️ CREAR
├── DownloadsPanel.vue           # ⚠️ CREAR
├── HistoryPanel.vue             # ⚠️ CREAR
├── FileCard.vue                 # ⚠️ CREAR
└── EmptyState.vue               # ⚠️ CREAR
```

### Frontend - Otros

```bash
frontend/
├── .gitignore
├── .eslintrc.cjs
├── postcss.config.js
├── index.html
├── public/
│   ├── logo_enacom.png          # ⚠️ COPIAR
│   └── enacom_footer.png        # ⚠️ COPIAR
└── src/
    ├── main.js                  # ⚠️ CREAR
    ├── App.vue                  # ⚠️ CREAR
    ├── router/
    │   └── index.js             # ⚠️ CREAR (opcional)
    ├── assets/
    │   └── enacom.css           # ⚠️ ADAPTAR CSS de Streamlit
    └── utils/
        ├── formatters.js        # ⚠️ CREAR (fmt_hhmmss, etc.)
        └── constants.js
```

---

## 🎯 Prioridades de implementación

### Fase 1: Backend funcional (CRÍTICO)
**Tiempo estimado: 2-3 días**

1. **Crear módulos core faltantes**
   ```bash
   # Prioridad ALTA
   backend/app/core/audio_processor.py
   backend/app/core/segmenter.py
   backend/app/core/exporters.py
   backend/app/core/infracciones.py
   ```

2. **Verificar que Celery task funcione end-to-end**
   - Probar con un audio de prueba
   - Verificar que genera TXT/XLSX/DOCX/ZIP correctamente

3. **Copiar assets**
   ```bash
   mkdir -p backend/assets
   cp assets/*.png backend/assets/
   cp assets/plantilla_enacom_limpia.docx backend/assets/
   ```

### Fase 2: Frontend básico (CRÍTICO)
**Tiempo estimado: 3-4 días**

1. **Crear App.vue y main.js**
   ```vue
   <!-- App.vue -->
   <template>
     <div class="min-h-screen bg-gray-50">
       <Header />
       <main class="max-w-7xl mx-auto px-4 py-6">
         <ConfigPanel @start="handleStart" />
         <ProgressBar v-if="store.isProcessing" />
         <TranscriptionView v-if="store.hasResults" />
         <DownloadsPanel v-if="store.hasResults" />
       </main>
     </div>
   </template>
   
   <script setup>
   import { useTranscriptionStore } from '@/stores/transcription'
   const store = useTranscriptionStore()
   </script>
   ```

2. **Crear componentes críticos uno por uno**
   - ConfigPanel.vue (formulario de configuración)
   - AudioUploader.vue (drag & drop de archivos)
   - ProgressBar.vue (barra de progreso animada)
   - TranscriptionView.vue (mostrar transcripción)
   - DownloadsPanel.vue (botones de descarga)

3. **Adaptar estilos CSS**
   - Convertir clases custom de `enacom.css` a Tailwind
   - Mantener colores institucionales

### Fase 3: Features avanzadas (MEDIO)
**Tiempo estimado: 2-3 días**

1. **AudioPlayer con waveform**
   - Integrar Plotly para visualización
   - Player HTML5 con controles

2. **InfractionsList**
   - Chips de infracciones
   - Lista detallada con timestamps

3. **HistoryPanel**
   - Lista de transcripciones anteriores
   - Filtros y búsqueda

### Fase 4: Polish y testing (BAJO)
**Tiempo estimado: 2-3 días**

1. Tests automatizados (pytest + Jest)
2. Manejo de errores robusto
3. Loading states y skeletons
4. Animaciones y transiciones
5. Responsive design
6. Accessibility (ARIA labels)

---

## 🔧 Componentes Vue - Ejemplos

### ConfigPanel.vue (ejemplo rápido)

```vue
<template>
  <div class="bg-white rounded-enacom shadow-enacom-sm p-6 mb-6">
    <h2 class="text-lg font-bold text-enacom-blue-dark mb-4">
      ⚙️ Configuración del procesamiento
    </h2>
    
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <!-- Referencia -->
      <div>
        <label class="block text-xs font-bold text-gray-600 uppercase mb-2">
          Nombre / Referencia
        </label>
        <input
          v-model="config.referencia"
          type="text"
          placeholder="Ej.: Acta 1542"
          class="w-full px-3 py-2 border border-gray-300 rounded-enacom-sm focus:ring-2 focus:ring-enacom-blue-main"
        />
      </div>
      
      <!-- Idioma -->
      <div>
        <label class="block text-xs font-bold text-gray-600 uppercase mb-2">
          Idioma del audio
        </label>
        <select
          v-model="config.language"
          class="w-full px-3 py-2 border border-gray-300 rounded-enacom-sm"
        >
          <option value="es">Español</option>
          <option value="en">Inglés</option>
          <option value="pt">Portugués</option>
          <option value="auto">Detección automática</option>
        </select>
      </div>
      
      <!-- Modo lote -->
      <div>
        <label class="block text-xs font-bold text-gray-600 uppercase mb-2">
          Informe final
        </label>
        <div class="flex gap-2">
          <button
            @click="config.modo_lote = 'individual'"
            :class="[
              'flex-1 px-3 py-2 rounded-enacom-sm font-semibold transition',
              config.modo_lote === 'individual'
                ? 'bg-enacom-blue-soft border-2 border-enacom-blue-main text-enacom-blue-dark'
                : 'bg-gray-100 border-2 border-gray-300 text-gray-600'
            ]"
          >
            Individual
          </button>
          <button
            @click="config.modo_lote = 'combinado'"
            :class="[
              'flex-1 px-3 py-2 rounded-enacom-sm font-semibold transition',
              config.modo_lote === 'combinado'
                ? 'bg-enacom-blue-soft border-2 border-enacom-blue-main text-enacom-blue-dark'
                : 'bg-gray-100 border-2 border-gray-300 text-gray-600'
            ]"
          >
            Combinado
          </button>
        </div>
      </div>
    </div>
    
    <!-- Infracciones -->
    <div class="mt-4">
      <label class="block text-xs font-bold text-gray-600 uppercase mb-2">
        Detección de infracciones
      </label>
      <textarea
        v-model="config.infracciones_raw"
        placeholder="Separar términos por comas..."
        rows="3"
        class="w-full px-3 py-2 border border-gray-300 rounded-enacom-sm font-mono text-sm"
      ></textarea>
    </div>
    
    <!-- Botón procesar -->
    <button
      @click="emitStart"
      :disabled="!canStart"
      class="mt-4 w-full bg-gradient-to-r from-enacom-blue-dark to-enacom-blue-main text-white font-bold py-3 px-6 rounded-enacom shadow-enacom-blue hover:shadow-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
    >
      ▶ Procesar archivos
    </button>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const emit = defineEmits(['start'])

const config = ref({
  referencia: '',
  language: 'es',
  modo_lote: 'individual',
  export_zip: true,
  infracciones_raw: 'put, pelotud, bolud, forr',
  coincidencia_parcial: true
})

const canStart = computed(() => {
  // Validar que haya archivos cargados (desde store)
  return true // Simplificado
})

function emitStart() {
  const configToSend = {
    ...config.value,
    infracciones: config.value.infracciones_raw
      .split(',')
      .map(t => t.trim())
      .filter(Boolean)
  }
  emit('start', configToSend)
}
</script>
```

---

## 📦 Archivos de utilidad

### frontend/src/utils/formatters.js

```javascript
export function formatDuration(seconds) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

export function formatFileSize(bytes) {
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unitIndex = 0
  
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  
  return `${size.toFixed(unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`
}
```

---

## ✅ Checklist de archivos

Copiar esta lista para trackear progreso:

### Backend
- [ ] `app/core/audio_processor.py`
- [ ] `app/core/segmenter.py`
- [ ] `app/core/exporters.py`
- [ ] `app/core/infracciones.py`
- [ ] `app/core/__init__.py`
- [ ] `app/storage/file_manager.py`
- [ ] `assets/` (copiar logos y plantilla)
- [ ] `.gitignore`
- [ ] `tests/` (opcional pero recomendado)

### Frontend
- [ ] `src/main.js`
- [ ] `src/App.vue`
- [ ] `index.html`
- [ ] `postcss.config.js`
- [ ] `.eslintrc.cjs`
- [ ] `src/components/ConfigPanel.vue`
- [ ] `src/components/AudioUploader.vue`
- [ ] `src/components/TranscriptionView.vue`
- [ ] `src/components/ProgressBar.vue`
- [ ] `src/components/AudioPlayer.vue`
- [ ] `src/components/InfractionsList.vue`
- [ ] `src/components/DownloadsPanel.vue`
- [ ] `src/components/HistoryPanel.vue`
- [ ] `src/utils/formatters.js`
- [ ] `src/assets/enacom.css` (adaptar)
- [ ] `public/` (copiar logos)

### Docker
- [ ] `docker/backend.Dockerfile`
- [ ] `docker/frontend.Dockerfile`
- [ ] `docker/docker-compose.yml`
- [ ] `docker/.dockerignore`

---

## 🚀 Comandos para iniciar rápido

```bash
# 1. Copiar archivos faltantes del backend
cd backend/app/core
cp ../../../enacom_transcriptor/audio_ops.py audio_processor.py
cp ../../../enacom_transcriptor/segmenter.py .
cp ../../../enacom_transcriptor/exporters.py .
cp ../../../enacom_transcriptor/infracciones.py .

# 2. Copiar assets
cd ../..
mkdir -p assets
cp ../assets/*.png assets/
cp ../assets/plantilla_enacom_limpia.docx assets/

# 3. Crear estructura frontend
cd ../frontend/src
mkdir -p components utils assets router public

# 4. Empezar a crear componentes
# (Usar los ejemplos de arriba como base)
```

---

**Próximos pasos inmediatos:**
1. Completar módulos `backend/app/core/`
2. Crear `main.js` y `App.vue`
3. Crear componentes críticos: ConfigPanel, AudioUploader, ProgressBar
4. Probar flujo end-to-end con un audio de prueba

Una vez que estos estén listos, el resto es cosmética y polish 🎨
