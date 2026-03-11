"""
Pydantic models para validación de requests y responses
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class LanguageEnum(str, Enum):
    """Idiomas soportados"""
    SPANISH = "es"
    ENGLISH = "en"
    PORTUGUESE = "pt"
    AUTO = "auto"


class ModoLoteEnum(str, Enum):
    """Modo de generación de informe"""
    INDIVIDUAL = "individual"
    COMBINADO = "combinado"


class TranscriptionRequest(BaseModel):
    """Request para iniciar transcripción"""
    referencia: Optional[str] = Field(None, max_length=200, description="Nombre o referencia del expediente")
    language: LanguageEnum = Field(LanguageEnum.SPANISH, description="Idioma del audio")
    modo_lote: ModoLoteEnum = Field(ModoLoteEnum.INDIVIDUAL, description="Modo de informe")
    export_zip: bool = Field(True, description="Generar ZIP con todos los archivos")
    infracciones: List[str] = Field(default_factory=list, description="Términos de infracción")
    coincidencia_parcial: bool = Field(True, description="Buscar coincidencias parciales")
    
    @field_validator('infracciones')
    @classmethod
    def validate_infracciones(cls, v):
        # Limpiar y deduplicar
        return list(set([term.strip().lower() for term in v if term.strip()]))


class TaskStatusEnum(str, Enum):
    """Estados de una tarea"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskProgressUpdate(BaseModel):
    """Actualización de progreso vía WebSocket"""
    task_id: str
    status: TaskStatusEnum
    progress: int = Field(0, ge=0, le=100)
    current_file: Optional[str] = None
    current_file_index: Optional[int] = None
    total_files: Optional[int] = None
    message: Optional[str] = None
    error: Optional[str] = None


class SegmentResponse(BaseModel):
    """Segmento de transcripción"""
    start: float
    end: float
    text: str
    line: str  # Formato: "[HH:MM:SS - HH:MM:SS] texto"


class InfractionResponse(BaseModel):
    """Infracción detectada"""
    archivo: str
    termino: str
    inicio: str  # HH:MM:SS
    fin: str     # HH:MM:SS
    texto: str


class FileResultResponse(BaseModel):
    """Resultado de transcripción de un archivo"""
    archivo: str
    duracion_hhmmss: str
    txt_url: Optional[str] = None
    xlsx_url: Optional[str] = None
    docx_url: Optional[str] = None
    infracciones: List[InfractionResponse] = []
    segmentos: List[SegmentResponse] = []
    texto_completo: str


class TranscriptionResultResponse(BaseModel):
    """Respuesta completa de una tarea de transcripción"""
    task_id: str
    status: TaskStatusEnum
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    # Metadatos
    referencia: Optional[str] = None
    modo: ModoLoteEnum
    model_size: str
    language: str
    total_files: int
    total_duration_hhmmss: str
    infracciones_total: int
    archivos_con_infracciones: int
    
    # Resultados individuales
    resultados: List[FileResultResponse] = []
    
    # Lote (si modo_lote == combinado)
    lote_txt_url: Optional[str] = None
    lote_xlsx_url: Optional[str] = None
    lote_docx_url: Optional[str] = None
    
    # ZIP completo
    zip_url: Optional[str] = None
    
    # Error (si falló)
    error_message: Optional[str] = None


class HistoryItemResponse(BaseModel):
    """Item del historial"""
    base_name: str
    tipo: str  # "LOTE", "INDIVIDUAL", "ZIP"
    fecha: datetime
    tamaño_bytes: int
    archivos_disponibles: List[str]  # ["txt", "xlsx", "docx", "zip"]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    whisper_model_loaded: bool
    celery_workers: int
    redis_connected: bool
