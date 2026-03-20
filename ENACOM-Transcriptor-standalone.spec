# =============================================================================
# ENACOM-Transcriptor-standalone.spec
# Archivo de configuración para PyInstaller.
#
# Cómo compilar (desde la RAÍZ del repo, con el venv activado):
#   pip install pyinstaller
#   pyinstaller ENACOM-Transcriptor-standalone.spec
#
# El exe queda en:  dist/ENACOM-Transcriptor/ENACOM-Transcriptor.exe
#
# IMPORTANTE: el modelo Whisper y tools/ NO se incluyen en el exe.
# Deben estar junto a la carpeta dist/ENACOM-Transcriptor/ en la distribución final.
# =============================================================================

import sys
from pathlib import Path

ROOT = Path(SPECPATH)          # raíz del repo (donde está este .spec)
BACKEND = ROOT / 'backend'
FRONTEND_DIST = ROOT / 'frontend' / 'dist'

block_cipher = None

a = Analysis(
    [str(BACKEND / 'run_standalone.py')],
    pathex=[str(BACKEND)],
    binaries=[],
    datas=[
        # Frontend buildado
        (str(FRONTEND_DIST), 'frontend/dist'),
        # Assets institucionales (logo, plantilla Word)
        (str(BACKEND / 'assets'), 'backend/assets'),
        # Codigo fuente de app/
        # faster-whisper assets (silero_vad.onnx necesario para vad_filter=True)
        (str(ROOT / 'backend/venv/Lib/site-packages/faster_whisper/assets'), 'faster_whisper/assets'),
    ],
    hiddenimports=[
        # Flask ecosystem
        'flask',
        'flask_cors',
        'flask_socketio',
        'engineio',
        'socketio',
        # Celery no se usa pero puede estar importado transitivamente
        # Pydantic
        'pydantic',
        'pydantic_settings',
        'pydantic.v1',
        # faster-whisper / ctranslate2
        'faster_whisper',
        'ctranslate2',
        'tokenizers',
        'huggingface_hub',
        # Audio
        'av',
        'soundfile',
        'numpy',
        # Exportadores
        'docx',
        'openpyxl',
        'lxml',
        'lxml.etree',
        'lxml._elementpath',
        # Utilidades
        'dotenv',
        'python_dotenv',
        'redis',           # puede estar importado en health check
        'celery',          # importado transitivamente en algunos lugares
        # Threading
        'concurrent.futures',
        'engineio.async_drivers.threading',
        'engineio.async_drivers',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
        'unittest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ENACOM-Transcriptor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,              # UPX puede romper DLLs de ctranslate2
    console=True,           # True para ver logs si algo falla; cambiar a False en producción
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / 'assets' / 'enacom.ico') if (ROOT / 'assets' / 'enacom.ico').exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='ENACOM-Transcriptor',
)
