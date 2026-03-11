
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuración global del backend"""
    
    # Flask
    SECRET_KEY: str = "enacom-transcriptor-secret-key-change-in-production"
    DEBUG: bool = True
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    STORAGE_DIR: Path = BASE_DIR / "storage"
    UPLOADS_DIR: Path = STORAGE_DIR / "uploads"
    OUTPUTS_DIR: Path = STORAGE_DIR / "outputs"
    ASSETS_DIR: Path = BASE_DIR / "assets"
    
    # Whisper
    WHISPER_MODEL: str = "medium"  # tiny, base, small, medium, large-v2, large-v3
    WHISPER_DEVICE: str = "auto"  # auto, cpu, cuda
    WHISPER_COMPUTE_TYPE: str = "float16"  # float16, int8, int8_float16
    
    # Audio processing
    MAX_AUDIO_SIZE_MB: int = 500
    SEGMENT_DURATION_SECONDS: int = 20
    SUPPORTED_FORMATS: list[str] = ["mp3", "wav", "m4a", "ogg", "flac", "aac", "opus", "webm"]
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # Redis (para WebSockets y cache)
    REDIS_URL: str = "redis://localhost:6379/1"
    
    # Limits
    MAX_CONCURRENT_TASKS: int = 2
    TASK_TIMEOUT_SECONDS: int = 3600  # 1 hora
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Crear directorios si no existen
        for dir_path in [self.STORAGE_DIR, self.UPLOADS_DIR, self.OUTPUTS_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)


settings = Settings()
