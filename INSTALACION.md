# ENACOM Transcriptor v3.0 — Guía de Instalación

**Sistema de transcripción automática de audio a texto**  
Dirección Nacional de Control y Fiscalización — ENACOM

---

## Requisitos del equipo

| Componente | Mínimo requerido |
|---|---|
| Sistema operativo | Windows 10 / 11 (64 bits) |
| RAM | 8 GB (recomendado 16 GB) |
| Almacenamiento libre | 10 GB |
| Python | 3.10 o superior |
| Node.js | 18 o superior |
| Conexión a internet | No requerida después de instalar |

> **Nota sobre Python y Node.js:** si no están instalados, ver la sección [Instalación de requisitos previos](#instalación-de-requisitos-previos) al final de este documento.

---

## Estructura del paquete

Al descomprimir el ZIP, la carpeta tiene la siguiente estructura:

```
enacom-transcriptor-audio/
│
├── INSTALAR.bat          ← Ejecutar UNA SOLA VEZ
├── INICIAR.bat           ← Uso diario (doble clic para arrancar)
├── EMPAQUETAR.bat        ← Solo para el área técnica
├── INSTALACION.md        ← Este archivo
│
├── tools/
│   ├── ffmpeg/bin/       ← ffmpeg portable (incluido)
│   ├── redis/            ← Redis portable (incluido)
│   └── models/
│       └── faster-whisper-large/  ← Modelo Whisper large-v3 (incluido)
│
├── backend/              ← Servidor Flask + Celery
└── frontend/             ← Interfaz Vue.js
```

> Los modelos, ffmpeg y Redis ya están incluidos en el paquete. **No se necesita descargar nada adicional ni tener conexión a internet.**

---

## Instalación (primera vez)

### Paso 1 — Descomprimir el paquete

Descomprimir el ZIP en una ubicación accesible, por ejemplo:

```
C:\ENACOM\enacom-transcriptor-audio\
```

> **Importante:** evitar rutas con espacios o caracteres especiales (acentos, ñ, etc.) como `C:\Mis Documentos\`.

---

### Paso 2 — Ejecutar INSTALAR.bat

Hacer doble clic en **`INSTALAR.bat`** y seguir las instrucciones en pantalla.

Este script realiza automáticamente:
1. Verifica que Python y Node.js estén instalados
2. Crea el entorno virtual Python en `backend\venv\`
3. Instala todas las dependencias Python
4. Instala las dependencias Node.js en `frontend\node_modules\`

⏱ **Tiempo estimado:** 5 a 10 minutos (depende del equipo).

> Ejecutar **una sola vez por equipo**. No es necesario repetirlo en usos posteriores.

---

## Uso diario

### Iniciar la aplicación

Hacer doble clic en **`INICIAR.bat`**.

El script abre automáticamente 3 ventanas de terminal (Celery, Backend y Frontend), inicia Redis en segundo plano, y abre el navegador en:

```
http://localhost:5174
```

> Si el navegador no se abre solo, escribir esa dirección manualmente.

---

### Detener la aplicación

Cerrar las **3 ventanas de terminal** que se abrieron (identificadas como "Celery - ENACOM", "Backend - ENACOM" y "Frontend - ENACOM") y la ventana minimizada de Redis en la barra de tareas.

---

## Flujo de trabajo

1. **Seleccionar archivos** de audio (arrastrar y soltar, o clic para explorar)  
   — Formatos soportados: MP3, WAV, M4A, OGG, FLAC, AAC, Opus, WebM  
   — Tamaño máximo por archivo: 500 MB

2. **Completar la configuración:**
   - Nombre / Referencia del expediente
   - Idioma del audio (Español por defecto)
   - Modo de informe: Individual o Combinado (lote)
   - Términos de infracciones a detectar (separados por coma)

3. Hacer clic en **▶ Procesar**

4. **Seguir el progreso** en tiempo real. Al finalizar, descargar los informes individuales (TXT, XLSX, DOCX) o el ZIP completo.

---

## Descripción de los archivos generados

| Formato | Contenido |
|---|---|
| **TXT** | Transcripción con timestamps + texto completo + resumen de infracciones |
| **XLSX** | Tabla de segmentos (Inicio / Fin / Texto) + hoja de infracciones |
| **DOCX** | Informe institucional ENACOM con formato Word |
| **ZIP** | Todos los archivos anteriores comprimidos en un solo paquete |

---

## Solución de problemas frecuentes

### La aplicación no abre en el navegador

Verificar que las 3 ventanas de terminal no muestren errores en rojo. Esperar 10 segundos adicionales y navegar manualmente a `http://localhost:5174`.

### Error "Puerto 5000 en uso"

Otro proceso está usando el puerto 5000. Abrir el Administrador de tareas, buscar procesos Python o Flask y cerrarlos antes de volver a ejecutar `INICIAR.bat`.

### Error "Puerto 6379 en uso"

Redis ya está corriendo (de una sesión anterior). No es un error; la aplicación funcionará igualmente.

### La transcripción tarda mucho

El modelo Whisper large-v3 es de alta precisión pero requiere tiempo. Para archivos largos (más de 30 minutos de audio), la transcripción puede demorar tanto o más que la duración del audio en equipos sin GPU dedicada.

### Error en INSTALAR.bat: "Python no encontrado"

Python no está en el PATH del sistema. Ver la sección siguiente.

---

## Instalación de requisitos previos

### Python 3.10+

1. Descargar desde [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Durante la instalación, **marcar la casilla "Add Python to PATH"**
3. Completar la instalación y reiniciar el equipo
4. Volver a ejecutar `INSTALAR.bat`

### Node.js 18+

1. Descargar desde [https://nodejs.org/](https://nodejs.org/) (versión LTS recomendada)
2. Instalar con las opciones por defecto
3. Reiniciar el equipo
4. Volver a ejecutar `INSTALAR.bat`

---

## Información técnica

| Componente | Tecnología |
|---|---|
| Motor de transcripción | faster-whisper (CTranslate2) — modelo large-v3 |
| Backend | Flask 3.0 + Celery 5.3 + Redis 6 |
| Frontend | Vue 3.4 + Vite 5 + Tailwind CSS |
| Comunicación en tiempo real | Socket.IO |
| Reproductor de audio | WaveSurfer.js 7 |
| Exportación | python-docx + openpyxl |

---

*Desarrollado por la Dirección Nacional de Control y Fiscalización — ENACOM*  
*Versión 3.0 — Marzo 2026*
