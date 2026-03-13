"""
Pydantic models para validación de requests y responses
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class LanguageEnum(str, Enum):
    SPANISH = "es"
    ENGLISH = "en"
    PORTUGUESE = "pt"
    AUTO = "auto"


class ModoLoteEnum(str, Enum):
    INDIVIDUAL = "individual"
    COMBINADO = "combinado"


class WhisperModelEnum(str, Enum):
    LARGE_V3 = "large-v3"


class TranscriptionRequest(BaseModel):
    referencia: Optional[str] = Field(None, max_length=200)
    language: LanguageEnum = Field(LanguageEnum.SPANISH)
    modo_lote: ModoLoteEnum = Field(ModoLoteEnum.INDIVIDUAL)
    export_zip: bool = Field(True)
    infracciones: List[str] = Field(default_factory=list)
    coincidencia_parcial: bool = Field(True)
    whisper_model: WhisperModelEnum = Field(WhisperModelEnum.LARGE_V3, description="Modelo Whisper a usar")

    @field_validator('infracciones')
    @classmethod
    def validate_infracciones(cls, v):
        return list(set([term.strip().lower() for term in v if term.strip()]))


class TaskStatusEnum(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskProgressUpdate(BaseModel):
    task_id: str
    status: TaskStatusEnum
    progress: int = Field(0, ge=0, le=100)
    current_file: Optional[str] = None
    current_file_index: Optional[int] = None
    total_files: Optional[int] = None
    message: Optional[str] = None
    error: Optional[str] = None


class SegmentResponse(BaseModel):
    start: float
    end: float
    text: str
    line: str


class InfractionResponse(BaseModel):
    archivo: str
    termino: str
    inicio: str
    fin: str
    texto: str


class FileResultResponse(BaseModel):
    archivo: str
    duracion_hhmmss: str
    audio_url: Optional[str] = None
    txt_url: Optional[str] = None
    xlsx_url: Optional[str] = None
    docx_url: Optional[str] = None
    infracciones: List[InfractionResponse] = []
    segmentos: List[SegmentResponse] = []
    texto_completo: str


class TranscriptionResultResponse(BaseModel):
    model_config = {'protected_namespaces': ()}

    task_id: str
    status: TaskStatusEnum
    created_at: datetime
    completed_at: Optional[datetime] = None
    referencia: Optional[str] = None
    modo: ModoLoteEnum
    model_size: str
    language: str
    total_files: int
    total_duration_hhmmss: str
    infracciones_total: int
    archivos_con_infracciones: int
    resultados: List[FileResultResponse] = []
    lote_txt_url: Optional[str] = None
    lote_xlsx_url: Optional[str] = None
    lote_docx_url: Optional[str] = None
    zip_url: Optional[str] = None
    error_message: Optional[str] = None


class HistoryItemResponse(BaseModel):
    base_name: str
    tipo: str
    fecha: datetime
    tamaño_bytes: int
    archivos_disponibles: List[str]


class HealthResponse(BaseModel):
    model_config = {'protected_namespaces': ()}

    status: str
    service: str
    whisper_model_loaded: bool
    celery_workers: int
    redis_connected: bool