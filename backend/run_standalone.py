"""
run_standalone.py — Entry point para el exe generado por PyInstaller.

Diferencias respecto a run.py (desarrollo):
  - Sin Celery, sin Redis
  - Usa thread_tasks en lugar de celery_tasks (monkey-patch via sys.modules)
  - Flask sirve frontend/dist/ directamente (sin Vite)
  - SocketIO en modo threading sin message_queue
  - Abre el navegador automáticamente
  - Parchea rutas de tools/ y storage/ para que apunten junto al exe

El código de backend/app/ NO fue modificado.
"""
import logging
import engineio.async_drivers.threading  # noqa: F401
import os
import sys
import threading
import webbrowser
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s — %(message)s',
)
logger = logging.getLogger(__name__)

# ── Detectar si corremos como exe (PyInstaller) o como script ─────
if getattr(sys, 'frozen', False):
    # Exe: sys._MEIPASS es el dir temporal donde PyInstaller extrae los archivos
    BUNDLE_DIR = Path(sys._MEIPASS)
    # EXE_DIR es la carpeta donde está el .exe (junto a tools/, storage/)
    EXE_DIR = Path(sys.executable).parent
else:
    # Script: el repo raíz es dos niveles arriba de este archivo
    BUNDLE_DIR = Path(__file__).resolve().parent.parent
    EXE_DIR = BUNDLE_DIR

# Agregar backend/ al path para que los imports de app.* funcionen
sys.path.insert(0, str(BUNDLE_DIR / 'backend'))

# ── PASO 1: Parchear sys.modules ANTES de importar routes.py ─────
# routes.py hace `from app.tasks.celery_tasks import process_transcription_task`
# en el top-level. Si reemplazamos el módulo antes de que routes.py sea
# importado, recibirá thread_tasks transparentemente.
from app.tasks import thread_tasks as _thread_tasks
sys.modules['app.tasks.celery_tasks'] = _thread_tasks

# ── PASO 2: Parchear paths de tools/ y storage/ ───────────────────
# audio_processor y transcription.py calculan sus rutas via __file__,
# lo que no funciona correctamente en el exe. Los parcharmos aquí.
import app.config as _config_module
_settings = _config_module.settings

# Storage junto al exe (persistente entre ejecuciones)
_storage = EXE_DIR / 'storage'
_settings.STORAGE_DIR  = _storage
_settings.UPLOADS_DIR  = _storage / 'uploads'
_settings.OUTPUTS_DIR  = _storage / 'outputs'
_settings.ASSETS_DIR   = BUNDLE_DIR / 'backend' / 'assets'
_storage.mkdir(parents=True, exist_ok=True)
(_storage / 'uploads').mkdir(exist_ok=True)
(_storage / 'outputs').mkdir(exist_ok=True)

# ffmpeg y ffprobe — apuntar a tools/ffmpeg/ junto al exe
import app.core.audio_processor as _ap
_FFMPEG  = EXE_DIR / 'tools' / 'ffmpeg' / 'bin' / 'ffmpeg.exe'
_FFPROBE = EXE_DIR / 'tools' / 'ffmpeg' / 'bin' / 'ffprobe.exe'
_ap.get_ffmpeg_path  = lambda: str(_FFMPEG)  if _FFMPEG.exists()  else 'ffmpeg'
_ap.get_ffprobe_path = lambda: str(_FFPROBE) if _FFPROBE.exists() else 'ffprobe'

# Modelo Whisper — apuntar a tools/models/ junto al exe
import app.core.transcription as _tr
_MODELS_DIR = EXE_DIR / 'tools' / 'models'
_tr._MODELS_DIR = _MODELS_DIR
_tr._LOCAL_MODEL_DIRS = {
    'large':    _MODELS_DIR / 'faster-whisper-large',
    'large-v3': _MODELS_DIR / 'faster-whisper-large',
    'medium':   _MODELS_DIR / 'faster-whisper-medium',
}

# ── PASO 3: Crear Flask + SocketIO ────────────────────────────────
from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO

app = Flask(__name__, static_folder=None)
app.config['SECRET_KEY'] = _settings.SECRET_KEY

CORS(app, resources={r"/api/*": {"origins": "*"}})

# Sin message_queue — el SocketIO emite directo en el mismo proceso
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='threading',
    logger=False,
    engineio_logger=False,
)

# ── PASO 4: Inyectar socketio y flask app en thread_tasks ────────
# thread_tasks necesita el app context para emitir desde threads secundarios.
import app as _app_pkg
_app_pkg.socketio = socketio

from app.tasks import thread_tasks as _tt
_tt._SOCKETIO  = socketio
_tt._FLASK_APP = app

# También parchear broadcast functions de websockets.py
from app.api import websockets as _ws
_ws.broadcast_progress   = lambda tid, data: socketio.emit('task_progress',  {'task_id': tid, **data},   room=tid, namespace='/')
_ws.broadcast_completion = lambda tid, data: socketio.emit('task_completed', {'task_id': tid, **data},   room=tid, namespace='/')
_ws.broadcast_error      = lambda tid, err:  socketio.emit('task_error',     {'task_id': tid, 'error': err}, room=tid, namespace='/')

# ── PASO 5: Registrar blueprints y WebSocket handlers ────────────
from app.api.routes import api_bp
app.register_blueprint(api_bp, url_prefix='/api/v1')

from app.api import websockets  # registra los handlers @socketio.on(...)

# ── PASO 6: Servir frontend/dist/ ────────────────────────────────
DIST_DIR = BUNDLE_DIR / 'frontend' / 'dist'
if not DIST_DIR.exists():
    logger.warning(f"frontend/dist no encontrado en {DIST_DIR}")

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    if path:
        target = DIST_DIR / path
        if target.exists() and target.is_file():
            return send_from_directory(str(DIST_DIR), path)
    return send_from_directory(str(DIST_DIR), 'index.html')

# ── Abrir navegador automáticamente ──────────────────────────────
def _open_browser():
    import time
    time.sleep(2.5)  # Esperar a que Flask levante
    webbrowser.open('http://localhost:5000')

# ── Entry point ───────────────────────────────────────────────────
if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("  ENACOM Transcriptor v3.0 — Modo standalone")
    logger.info(f"  Bundle dir : {BUNDLE_DIR}")
    logger.info(f"  Exe dir    : {EXE_DIR}")
    logger.info(f"  Frontend   : {DIST_DIR}")
    logger.info(f"  Storage    : {_storage}")
    logger.info(f"  Modelos    : {_MODELS_DIR}")
    logger.info("  URL        : http://localhost:5000")
    logger.info("=" * 60)

    threading.Thread(target=_open_browser, daemon=True).start()

    socketio.run(
        app,
        host='127.0.0.1',
        port=5000,
        debug=False,
        use_reloader=False,
        log_output=False,
    )