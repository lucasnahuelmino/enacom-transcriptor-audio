# ENACOM Transcriptor de Audios

Sistema institucional de transcripción automática de audio a texto desarrollado para la Dirección Nacional de Control y Fiscalización de ENACOM.

El proyecto permite procesar archivos de audio de manera individual o en lote, detectar términos configurables de infracciones y generar salidas en TXT, XLSX, DOCX y ZIP. La solución cuenta con dos modalidades de operación:

- modo desarrollo, con frontend Vue 3 y backend Flask + Celery + Redis
- modo distribución standalone para Windows, empaquetado con PyInstaller e instalado mediante Inno Setup

## Objetivo

La aplicación fue diseñada para asistir tareas de fiscalización y análisis de material sonoro mediante una interfaz simple, resultados exportables y operación local dentro del entorno institucional.

## Alcance funcional

- Transcripción automática de audio usando faster-whisper
- Procesamiento de uno o varios archivos por corrida
- Selección de idioma del audio: español, inglés, portugués o detección automática
- Detección configurable de términos de infracciones
- Generación de informes individuales o combinados
- Exportación a TXT, XLSX y DOCX
- Generación opcional de ZIP con la corrida completa
- Historial local de transcripciones generadas
- Reproducción del audio original junto a segmentos transcritos
- Progreso en tiempo real durante el procesamiento

## Modalidades de ejecución

### 1. Desarrollo

Orientado al equipo técnico. Utiliza componentes desacoplados:

- frontend en Vue 3 con Vite
- backend Flask + Flask-SocketIO
- ejecución de tareas con Celery
- Redis como broker y backend de resultados

Puertos por defecto:

- frontend: http://127.0.0.1:5174
- backend API: http://127.0.0.1:5000
- health check: http://127.0.0.1:5000/api/v1/health

### 2. Standalone para Windows

Orientado a distribución interna. En esta modalidad:

- el frontend buildado se sirve desde el mismo ejecutable
- no se requiere Node.js, Redis ni un backend separado en la máquina usuaria
- la aplicación se ejecuta como proceso único local
- el instalador puede instalarse sin privilegios de administrador

Punto de acceso por defecto en standalone:

- aplicación local: http://127.0.0.1:5000

## Arquitectura del repositorio

```text
enacom-transcriptor-audio/
├── assets/                           # Iconografía e imágenes institucionales
├── backend/
│   ├── app/
│   │   ├── api/                      # Endpoints REST y WebSockets
│   │   ├── core/                     # Lógica de transcripción, exportación y audio
│   │   ├── models/                   # Schemas Pydantic
│   │   └── tasks/                    # Tareas Celery y reemplazo standalone
│   ├── run.py                        # Entry point de desarrollo
│   ├── run_standalone.py             # Entry point del ejecutable standalone
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/               # Componentes UI
│   │   ├── services/                 # API y WebSocket client
│   │   ├── stores/                   # Estado de transcripción
│   │   └── utils/
│   └── package.json
├── tools/
│   ├── ffmpeg/                       # Binarios portables requeridos en standalone
│   └── models/                       # Modelos Whisper locales para distribución
├── ENACOM-Transcriptor-standalone.spec
├── ENACOM-Transcriptor.iss
├── INSTALACION.md
└── MANUAL_DE_USO.md
```

## Tecnologías principales

### Backend

- Flask
- Flask-CORS
- Flask-SocketIO
- Celery
- Redis
- faster-whisper
- CTranslate2
- python-docx
- openpyxl

### Frontend

- Vue 3
- Vite 5
- Pinia
- Tailwind CSS
- Axios
- Socket.IO Client
- WaveSurfer.js

## Requisitos para desarrollo

| Componente | Requisito mínimo |
|---|---|
| Python | 3.10 o superior |
| Node.js | 18 o superior |
| Redis | 6 o superior |
| Sistema operativo | Windows 10/11 o entorno compatible para desarrollo |

## Puesta en marcha en desarrollo

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

### Worker Celery

```bash
cd backend
venv\Scripts\activate
celery -A celery_worker.celery_app worker --loglevel=info --pool=solo
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Redis

```bash
redis-server
```

## Flujo de empaquetado standalone

El flujo actual de distribución para Windows es el siguiente.

### 1. Generar build del frontend

```bash
cd frontend
npm install
npm run build
```

Salida esperada:

- frontend/dist/

### 2. Generar ejecutable standalone con PyInstaller

Desde la raíz del repositorio:

```bash
pyinstaller ENACOM-Transcriptor-standalone.spec
```

Salida esperada:

- dist/ENACOM-Transcriptor/ENACOM-Transcriptor.exe

### 3. Generar instalador con Inno Setup

Compilar:

- ENACOM-Transcriptor.iss

El instalador resultante se genera en:

- Output/ENACOM-Transcriptor-standalone-v3.0-Setup.exe

## Comportamiento del instalador actual

El instalador está configurado para:

- instalar por usuario, sin requerir permisos de administrador
- copiar el runtime standalone generado por PyInstaller
- incluir tools/ffmpeg y tools/models
- crear accesos directos en escritorio y menú inicio del usuario
- usar una carpeta de instalación bajo LocalAppData

Ruta por defecto de instalación:

- %LOCALAPPDATA%/Programs/ENACOM/Transcriptor

## Archivos de documentación del repositorio

- README.md: visión institucional, técnica y de despliegue
- INSTALACION.md: guía de instalación del paquete distribuible
- MANUAL_DE_USO.md: manual de uso para personal operador

## Estructura de resultados generados

La aplicación almacena los archivos procesados y exportados en almacenamiento local. En standalone, estos directorios se crean junto al ejecutable instalado.

- storage/uploads/
- storage/outputs/

Archivos exportables:

- TXT: transcripción y texto corrido
- XLSX: segmentos y detección de infracciones
- DOCX: informe institucional formateado
- ZIP: paquete completo de la corrida

## Consideraciones operativas

- La modalidad standalone utiliza el modelo local incluido en tools/models
- El frontend standalone no depende de Vite ni de Node.js en tiempo de ejecución
- El motor standalone sirve la interfaz directamente desde el ejecutable
- La aplicación está orientada a uso local interno ENACOM

## Solución de problemas frecuentes

### La aplicación standalone no abre

Verificar:

- que el instalador haya copiado correctamente la carpeta completa
- que no haya otra aplicación usando el puerto 5000
- que existan tools/ffmpeg y tools/models dentro de la instalación

### La aplicación de desarrollo no conecta con el backend

Verificar:

- frontend en puerto 5174
- backend en puerto 5000
- Redis activo
- worker Celery corriendo

### Error por archivos grandes o formatos no válidos

Validar:

- formato soportado: mp3, wav, m4a, ogg, flac, aac, opus, webm
- tamaño máximo configurado en backend

## Uso interno

Este software es de uso interno ENACOM. No distribuir fuera del ámbito autorizado.

## Autoría

Desarrollado para la Dirección Nacional de Control y Fiscalización de ENACOM.
