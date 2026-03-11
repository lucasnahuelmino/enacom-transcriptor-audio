
from app.config import settings

BACKUP_DIR = settings.OUTPUTS_DIR
LOGO_PATH = settings.ASSETS_DIR / "logo_enacom.png"
TEMPLATE_PATH = settings.ASSETS_DIR / "plantilla_enacom_limpia.docx"
ASSETS_DIR = settings.ASSETS_DIR

def ensure_dirs():
    """Crear directorios si no existen"""
    settings.OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    settings.ASSETS_DIR.mkdir(parents=True, exist_ok=True)