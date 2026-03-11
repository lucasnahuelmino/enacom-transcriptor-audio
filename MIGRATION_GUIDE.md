# 📖 Guía de Migración: v2.0 (Streamlit) → v3.0 (Vue + Flask)

Esta guía detalla el proceso de migración paso a paso desde la versión monolítica Streamlit a la nueva arquitectura separada.

---

## 🎯 Objetivo

Migrar de:
- **Monolito Streamlit** → **Arquitectura cliente-servidor**
- **openai-whisper** → **faster-whisper** (4x más rápido)
- **Procesamiento síncrono** → **Tareas asíncronas con Celery**
- **Estado en session_state** → **Estado centralizado con Pinia**

---

## 📋 Checklist de migración

### Fase 1: Preparación (1 día)

- [ ] **1.1** Hacer backup de la versión actual
  ```bash
  git checkout -b backup/v2-streamlit
  git push origin backup/v2-streamlit
  ```

- [ ] **1.2** Crear rama de desarrollo para v3
  ```bash
  git checkout main
  git checkout -b feat/v3-vue-flask-migration
  ```

- [ ] **1.3** Instalar dependencias del sistema
  - Redis: `sudo apt install redis-server` (Linux) / `brew install redis` (Mac)
  - Node.js 18+: desde [nodejs.org](https://nodejs.org)
  - Verificar FFmpeg: `ffmpeg -version`

### Fase 2: Setup del Backend (2-3 días)

- [ ] **2.1** Copiar estructura de backend
  ```bash
  mkdir -p backend/app/{api,core,tasks,models,storage}
  cp /tmp/migration/backend/* backend/ -r
  ```

- [ ] **2.2** Migrar lógica de negocio
  
  | Archivo v2.0 | Nuevo archivo v3.0 | Notas |
  |---|---|---|
  | `enacom_transcriptor/audio_ops.py` | `backend/app/core/audio_processor.py` | Renombrar funciones |
  | `enacom_transcriptor/segmenter.py` | `backend/app/core/segmenter.py` | Sin cambios |
  | `enacom_transcriptor/exporters.py` | `backend/app/core/exporters.py` | Sin cambios |
  | `enacom_transcriptor/infracciones.py` | `backend/app/core/infracciones.py` | Sin cambios |
  | `enacom_transcriptor/model.py` | `backend/app/core/transcription.py` | **Reemplazar con faster-whisper** |
  | `enacom_transcriptor/processing.py` | `backend/app/tasks/celery_tasks.py` | Adaptar a Celery task |

- [ ] **2.3** Instalar dependencias del backend
  ```bash
  cd backend
  python -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  ```

- [ ] **2.4** Configurar `.env`
  ```bash
  cp .env.example .env
  # Editar valores según tu entorno
  ```

- [ ] **2.5** Probar el backend aislado
  ```bash
  # Terminal 1: Redis
  redis-server
  
  # Terminal 2: Backend
  python run.py
  
  # Terminal 3: Celery worker
  celery -A celery_worker.celery_app worker --loglevel=info
  
  # Terminal 4: Test con curl
  curl http://localhost:5000/health
  ```

### Fase 3: Setup del Frontend (2-3 días)

- [ ] **3.1** Copiar estructura de frontend
  ```bash
  cp /tmp/migration/frontend/* frontend/ -r
  ```

- [ ] **3.2** Instalar dependencias
  ```bash
  cd frontend
  npm install
  ```

- [ ] **3.3** Migrar componentes de UI

  | Concepto v2.0 | Concepto v3.0 | Implementación |
  |---|---|---|
  | `ui.py::render_header()` | `Header.vue` | Componente Vue |
  | `ui.py::render_config()` | `ConfigPanel.vue` | Componente Vue + Pinia |
  | `ui.py::render_sidebar()` | `AudioUploader.vue` | Componente Vue |
  | `proc_ui.py::render_progress_block()` | `ProgressBar.vue` | Componente Vue + WebSocket |
  | `proc_ui.py::render_audio_panel()` | `AudioPlayer.vue` | Componente Vue |
  | `ui.py::render_downloads()` | `DownloadsPanel.vue` | Componente Vue |
  | `ui.py::render_history()` | `HistoryPanel.vue` | Componente Vue |

- [ ] **3.4** Migrar estilos CSS
  - Adaptar `assets/styles/enacom.css` a clases de Tailwind
  - Configurar `tailwind.config.js` con colores institucionales
  - Usar componentes de Headless UI para dropdowns, modales, etc.

- [ ] **3.5** Probar frontend aislado
  ```bash
  npm run dev
  # Abrir http://localhost:5173
  ```

### Fase 4: Integración (2-3 días)

- [ ] **4.1** Conectar frontend con backend
  - Verificar que las URLs de la API sean correctas en `services/api.js`
  - Verificar WebSocket URL en `services/websocket.js`

- [ ] **4.2** Probar flujo completo
  1. Cargar archivos
  2. Configurar parámetros
  3. Iniciar transcripción
  4. Ver progreso en tiempo real vía WebSocket
  5. Descargar resultados

- [ ] **4.3** Verificar funcionalidades críticas
  - [ ] Upload de múltiples archivos
  - [ ] Transcripción con faster-whisper
  - [ ] Detección de infracciones
  - [ ] Exportación TXT/XLSX/DOCX
  - [ ] Generación de ZIP
  - [ ] Modo lote combinado
  - [ ] Historial de transcripciones

### Fase 5: Testing y Deploy (2-3 días)

- [ ] **5.1** Testing exhaustivo
  - [ ] Casos edge: archivos grandes (500MB), formatos raros
  - [ ] Cancelación de tareas
  - [ ] Reconexión de WebSocket
  - [ ] Manejo de errores (sin FFmpeg, sin Redis, etc.)

- [ ] **5.2** Optimizaciones
  - [ ] Configurar Nginx como reverse proxy (producción)
  - [ ] Configurar supervisord para Celery workers
  - [ ] Configurar systemd para backend
  - [ ] Build optimizado del frontend: `npm run build`

- [ ] **5.3** Documentación
  - [ ] Actualizar README.md
  - [ ] Documentar API endpoints
  - [ ] Crear guía de troubleshooting
  - [ ] Documentar proceso de deploy

- [ ] **5.4** Deploy en servidor ENACOM
  ```bash
  # Backend
  sudo systemctl start enacom-backend
  sudo systemctl start enacom-celery
  
  # Frontend (build estático servido por Nginx)
  npm run build
  sudo cp -r dist/* /var/www/enacom-transcriptor/
  sudo systemctl reload nginx
  ```

---

## ⚙️ Mapeo de funcionalidades

### Estado y configuración

| v2.0 (Streamlit) | v3.0 (Vue + Flask) |
|---|---|
| `st.session_state["busy"]` | `useTranscriptionStore().isProcessing` |
| `st.session_state["resultados"]` | `useTranscriptionStore().resultados` |
| `cfg = render_config()` | `ConfigPanel.vue` emite evento con config |
| `sidebar = render_sidebar()` | `AudioUploader.vue` maneja uploads |

### Procesamiento

| v2.0 (Streamlit) | v3.0 (Vue + Flask) |
|---|---|
| `run_processing(cfg, sidebar)` | `POST /api/v1/transcription/upload` |
| `processing.py` (síncrono) | `celery_tasks.py::process_transcription_task` |
| `model.load_model_cached()` | `TranscriptionEngine().transcribe()` |
| Progreso via `st.rerun()` | Progreso vía WebSocket (`task_progress`) |

### UI y visualización

| v2.0 (Streamlit) | v3.0 (Vue + Flask) |
|---|---|
| `st.file_uploader()` | `<input type="file" multiple>` en AudioUploader |
| `st.progress()` | `<ProgressBar>` con animaciones CSS |
| `st.markdown()` con HTML | Templates de Vue con clases Tailwind |
| `st.download_button()` | `<a :href="downloadUrl">` |
| `st.tabs()` | `<Tabs>` de Headless UI |

---

## 🔄 Migración de datos

Si ya tenés transcripciones en `transcripciones/`:

```bash
# Copiar transcripciones existentes al nuevo storage
cp -r transcripciones/* backend/storage/outputs/
```

Los archivos antiguos serán compatibles con el nuevo historial.

---

## 🐛 Troubleshooting común

### Problema: "Celery worker no conecta a Redis"

**Solución:**
```bash
# Verificar que Redis esté corriendo
redis-cli ping
# Debería responder "PONG"

# Verificar URL en .env
CELERY_BROKER_URL=redis://localhost:6379/0
```

### Problema: "WebSocket no conecta"

**Solución:**
- Verificar que Flask-SocketIO esté corriendo: `python run.py`
- Verificar la URL en `frontend/src/services/websocket.js`
- Abrir consola del navegador para ver errores de conexión

### Problema: "faster-whisper no encuentra CUDA"

**Solución:**
```bash
# Verificar CUDA
nvidia-smi

# Si no hay GPU, usar CPU (más lento pero funciona)
# En .env:
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
```

### Problema: "Frontend no carga assets"

**Solución:**
```bash
# Limpiar caché de Vite
rm -rf node_modules/.vite

# Reinstalar
npm install
npm run dev
```

---

## 📊 Comparativa de rendimiento

| Métrica | v2.0 (Streamlit + openai-whisper) | v3.0 (Vue + faster-whisper) |
|---|---|---|
| **Velocidad de transcripción (CPU)** | Baseline | **4x más rápido** |
| **Velocidad de transcripción (GPU)** | Baseline | **2x más rápido** |
| **Uso de memoria** | Alto | **-50%** |
| **Concurrencia** | 1 usuario a la vez | **Múltiples usuarios simultáneos** |
| **Progreso en tiempo real** | Polling cada 200ms | **WebSocket instantáneo** |
| **Tiempo de respuesta UI** | ~200-500ms (rerun) | **<50ms (reactivo)** |
| **Escalabilidad** | Limitada | **Alta (Celery workers)** |

---

## ✅ Validación final

Antes de considerar la migración completa:

- [ ] Todas las funcionalidades de v2.0 están implementadas
- [ ] Faster-whisper transcribe correctamente en español
- [ ] WebSockets muestran progreso en tiempo real
- [ ] Exportación TXT/XLSX/DOCX genera archivos idénticos a v2.0
- [ ] Diseño visual respeta los colores institucionales ENACOM
- [ ] Performance es al menos 2x mejor que v2.0
- [ ] Sistema es estable con 5+ archivos simultáneos

---

## 📝 Commits sugeridos

```bash
# Fase 1
git commit -m "chore: setup backend structure with Flask and Celery"
git commit -m "feat(backend): implement faster-whisper transcription engine"
git commit -m "feat(backend): add REST API endpoints for transcription"
git commit -m "feat(backend): add WebSocket support for real-time progress"

# Fase 2
git commit -m "chore: setup frontend structure with Vue 3 and Vite"
git commit -m "feat(frontend): implement Header component with ENACOM branding"
git commit -m "feat(frontend): implement ConfigPanel with validation"
git commit -m "feat(frontend): add WebSocket integration for live updates"

# Fase 3
git commit -m "feat: integrate frontend with backend API"
git commit -m "feat: implement full transcription workflow end-to-end"
git commit -m "docs: update README for v3.0 architecture"
git commit -m "chore: add Docker support for containerized deployment"
```

---

## 🎉 ¡Migración completada!

Una vez validado todo, mergear a `main`:

```bash
git checkout main
git merge feat/v3-vue-flask-migration
git tag -a v3.0.0 -m "Release v3.0.0: Vue + Flask architecture"
git push origin main --tags
```

---

**¿Dudas durante la migración?** Consultá la documentación o abrí un issue en GitLab.
