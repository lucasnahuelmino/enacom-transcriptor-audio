# 🎧 ENACOM Transcriptor de audios

Sistema institucional de transcripción automática de audio a texto, desarrollado para la **Dirección Nacional de Control y Fiscalización de ENACOM**.

Basado en [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (backend CTranslate2), con arquitectura desacoplada **Vue 3 + Flask + Celery + Redis**.

---

## ✨ Características

- 🎙️ Transcripción con modelos Whisper **Medium** y **Large v3** seleccionables por el usuario
- 📁 Soporte para múltiples formatos: MP3, WAV, M4A, OGG, FLAC, AAC, Opus, WebM
- 📦 Modo **Individual** e **Informe Combinado (lote)**
- ⚠️ Detección configurable de **infracciones** (términos prohibidos) con coincidencia exacta o parcial
- 📊 Exportación a **TXT**, **XLSX** y **DOCX** por archivo y en lote
- 📦 Generación de **ZIP** con todos los informes
- 📡 Progreso en **tiempo real** vía WebSocket (Socket.IO)
- 🎵 Reproductor de audio con **forma de onda** (WaveSurfer.js) sincronizado con la transcripción segmentada
- 📚 **Historial** de transcripciones anteriores con descarga directa
- 🏛️ Interfaz institucional con identidad visual ENACOM

---

## 🏗️ Arquitectura

```
enacom-transcriptor-vue/
├── backend/                  # Flask + Celery
│   ├── app/
│   │   ├── api/              # REST endpoints + WebSockets
│   │   ├── core/             # Motor de transcripción, exportadores, segmentador
│   │   ├── models/           # Schemas Pydantic
│   │   └── tasks/            # Tareas Celery
│   ├── storage/              # uploads/ y outputs/ (generado en runtime)
│   ├── assets/               # Logo y plantilla Word institucional
│   ├── requirements.txt
│   └── run.py
├── frontend/                 # Vue 3 + Vite + Tailwind
│   └── src/
│       ├── components/       # Header, ConfigPanel, AudioCard, DownloadsPanel, etc.
│       ├── stores/           # Pinia: estado de transcripción
│       ├── services/         # api.js (Axios) + websocket.js (Socket.IO)
│       └── utils/            # Formatters
├── start-dev.sh              # Script de inicio de todos los servicios
└── descargar_modelos.bat     # Descarga de modelos Whisper (Windows)
```

---

## ⚙️ Requisitos previos

| Herramienta | Versión mínima |
|---|---|
| Python | 3.10+ |
| Node.js | 18+ |
| Redis | 6+ |
| ffmpeg | Cualquier versión reciente |

> **Windows:** `ffmpeg` debe estar disponible en el PATH. Recomendado instalar vía [winget](https://github.com/microsoft/winget-cli): `winget install ffmpeg`.

---

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/lucasnahuelmino/enacom-transcriptor-audio.git
cd enacom-transcriptor-audio
```

### 2. Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

> **Windows:** Si `av` (PyAV) falla al instalar, instalá primero las **Visual C++ Build Tools** desde https://visualstudio.microsoft.com/visual-cpp-build-tools/

### 3. Frontend

```bash
cd frontend
npm install
```

### 4. Descargar modelos Whisper

```bash
# Opción A — Windows (interfaz interactiva)
descargar_modelos.bat

# Opción B — Manual
cd backend
python download_models.py           # Descarga Medium (~1.5 GB)
python download_models.py --large   # Descarga Medium + Large v3 (~4.6 GB)
```

Los modelos se almacenan en el cache de HuggingFace (`~/.cache/huggingface/hub`). La descarga solo es necesaria una vez por equipo y es reanudable si se interrumpe.

---

## ▶️ Ejecución (modo desarrollo)

### Opción A — Script unificado (Linux / Git Bash en Windows)

```bash
./start-dev.sh
```

Inicia Redis (si no está corriendo), Celery worker, Flask y Vite en una sola terminal.

### Opción B — Terminales separadas

**Terminal 1 — Redis**
```bash
redis-server
```

**Terminal 2 — Flask backend**
```bash
cd backend
source venv/Scripts/activate   # Windows
python run.py
```

**Terminal 3 — Celery worker**
```bash
cd backend
source venv/Scripts/activate   # Windows
celery -A celery_worker.celery_app worker --loglevel=info --pool=solo
```

**Terminal 4 — Frontend Vite**
```bash
cd frontend
npm run dev
```

| Servicio | URL |
|---|---|
| Frontend | http://localhost:5174 |
| Backend API | http://localhost:5000 |
| Health check | http://localhost:5000/api/v1/health |

---

## 🖥️ Uso

1. Abrí http://localhost:5174 en el navegador.
2. **Seleccioná** uno o más archivos de audio (arrastrar y soltar o clic).
3. Completá la **configuración**: referencia, idioma, modelo Whisper, modo de informe y términos de infracciones.
4. Presioná **▶ Procesar**.
5. Seguí el progreso en tiempo real. Al finalizar, descargá los informes por archivo o el ZIP completo.

---

## 📡 API REST (resumen)

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/api/v1/transcription/upload` | Sube archivos e inicia tarea |
| `GET` | `/api/v1/transcription/status/:id` | Estado de la tarea |
| `GET` | `/api/v1/transcription/result/:id` | Resultado completo |
| `POST` | `/api/v1/transcription/cancel/:id` | Cancela la tarea |
| `GET` | `/api/v1/history` | Historial de transcripciones |
| `GET` | `/api/v1/download/:path` | Descarga de archivos generados |
| `GET` | `/api/v1/audio/:task_id/:filename` | Sirve el audio original |
| `GET` | `/api/v1/health` | Estado del servicio |

---

## 🔧 Configuración

El backend se configura mediante variables de entorno o el archivo `backend/.env`:

```env
WHISPER_MODEL=medium           # medium | large-v3
WHISPER_DEVICE=auto            # auto | cpu | cuda
WHISPER_COMPUTE_TYPE=float16   # float16 | int8
MAX_AUDIO_SIZE_MB=500
SEGMENT_DURATION_SECONDS=20
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
REDIS_URL=redis://localhost:6379/1
```

---

## 🧱 Stack tecnológico

**Backend**
- [Flask](https://flask.palletsprojects.com/) + Flask-CORS + Flask-SocketIO
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (CTranslate2)
- [Celery](https://docs.celeryq.dev/) + Redis
- [Pydantic v2](https://docs.pydantic.dev/)
- python-docx, openpyxl

**Frontend**
- [Vue 3](https://vuejs.org/) (Composition API)
- [Vite 5](https://vitejs.dev/)
- [Pinia](https://pinia.vuejs.org/)
- [Tailwind CSS 3](https://tailwindcss.com/)
- [Socket.IO client](https://socket.io/)
- [WaveSurfer.js 7](https://wavesurfer.xyz/)
- Axios

---

## 📝 Licencia

Uso interno ENACOM. No distribuir sin autorización.

---

*Desarrollado por la Dirección Nacional de Control y Fiscalización — ENACOM*
