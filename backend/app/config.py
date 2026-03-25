from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuración global del backend"""
    
    # Flask
    SECRET_KEY: str = "enacom-transcriptor-secret-key-change-in-production"
    DEBUG: bool = True
    
    # CORS
    CORS_ORIGINS: list[str] = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5174",
    "http://localhost:5174"
]
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    STORAGE_DIR: Path = BASE_DIR / "storage"
    UPLOADS_DIR: Path = STORAGE_DIR / "uploads"
    OUTPUTS_DIR: Path = STORAGE_DIR / "outputs"
    SIGNAL_MONITOR_DIR: Path = STORAGE_DIR / "signal_monitor"
    ASSETS_DIR: Path = BASE_DIR / "assets"
    
    # Whisper
    WHISPER_MODEL: str = "large-v3"
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
    # Sin límite de tiempo — las transcripciones pueden durar horas
    TASK_TIMEOUT_SECONDS: Optional[int] = None

    # Signal Monitor
    SIGNAL_MONITOR_MOCK_MODE: bool = True
    SIGNAL_MONITOR_ALLOW_MOCK_FALLBACK: bool = True
    SIGNAL_MONITOR_DEFAULT_FREQUENCY_HZ: float = 101_700_000.0
    SIGNAL_MONITOR_DEFAULT_SPAN_HZ: float = 2_500_000.0
    SIGNAL_MONITOR_DEFAULT_GAIN_DB: float = 18.0
    SIGNAL_MONITOR_ACTIVITY_THRESHOLD_DBM: float = -70.0
    SIGNAL_MONITOR_ACTIVITY_HYSTERESIS_DB: float = 3.0
    SIGNAL_MONITOR_ACTIVITY_MIN_DURATION_SECONDS: float = 0.5
    SIGNAL_MONITOR_AUDIO_SAMPLE_RATE: int = 16000
    SIGNAL_MONITOR_CHUNK_SECONDS: float = 0.2
    SIGNAL_MONITOR_SPECTRUM_BINS: int = 256
    SIGNAL_MONITOR_TRANSCRIPTION_WINDOW_SECONDS: float = 6.0
    SIGNAL_MONITOR_TRANSCRIPTION_OVERLAP_SECONDS: float = 1.5
    SIGNAL_MONITOR_SDK_DLL: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Crear directorios si no existen
        for dir_path in [self.STORAGE_DIR, self.UPLOADS_DIR, self.OUTPUTS_DIR, self.SIGNAL_MONITOR_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)


settings = Settings()