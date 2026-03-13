"""
Core de transcripción usando faster-whisper.
Soporta múltiples instancias en paralelo (medium + large-v3).
"""
from faster_whisper import WhisperModel
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

from app.config import settings

logger = logging.getLogger(__name__)


_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_MODELS_DIR   = _PROJECT_ROOT / "tools" / "models"

_LOCAL_MODEL_DIRS: Dict[str, Path] = {
    "large":    _MODELS_DIR / "faster-whisper-large",
    "large-v3": _MODELS_DIR / "faster-whisper-large",
    "medium":   _MODELS_DIR / "faster-whisper-medium",
}


def _resolve_model_path(model_size: str) -> str:
    """
    Devuelve la ruta local al modelo si existe en tools/models/,
    o el nombre original para que faster-whisper lo descargue.
    """
    local_path = _LOCAL_MODEL_DIRS.get(model_size.lower())
    if local_path and local_path.is_dir():
        logger.info(f"Modelo encontrado localmente: {local_path}")
        return str(local_path)

    logger.warning(
        f"Modelo '{model_size}' no encontrado en {_MODELS_DIR}. "
        f"Se descargará desde HuggingFace."
    )
    return model_size


class TranscriptionEngine:
    """
    Wrapper para faster-whisper.
    Cada instancia carga y mantiene en memoria UN modelo específico.
    El engine cache en celery_tasks.py evita recargas innecesarias.
    """

    def __init__(self, model_size: Optional[str] = None):
        self._model_size = model_size or settings.WHISPER_MODEL
        self._model: Optional[WhisperModel] = None
        self._load_model()

    def _load_model(self):
        logger.info(f"Cargando modelo faster-whisper: {self._model_size}")

        device = settings.WHISPER_DEVICE
        if device == "auto":
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                device = "cpu"

        compute_type = settings.WHISPER_COMPUTE_TYPE if device == "cuda" else "int8"
        logger.info(f"Dispositivo: {device} | compute_type: {compute_type}")

        # Resuelve ruta local; si no existe, usa el nombre para descarga remota
        model_path_or_name = _resolve_model_path(self._model_size)

        self._model = WhisperModel(
            model_path_or_name,
            device=device,
            compute_type=compute_type,
            download_root=None,
            local_files_only=Path(model_path_or_name).is_dir()  # True solo si es ruta local
        )
        logger.info(f"Modelo '{self._model_size}' cargado exitosamente")

    def transcribe(
        self,
        audio_path: Path,
        language: Optional[str] = None,
        **kwargs
    ) -> Tuple[str, List[Dict]]:
        if self._model is None:
            self._load_model()

        logger.info(f"Transcribiendo [{self._model_size}]: {audio_path.name}")

        transcribe_params = {
            "beam_size": 5,
            "best_of": 5,
            "temperature": 0.0,
            "condition_on_previous_text": False,
            "vad_filter": True,
            "vad_parameters": {
                "threshold": 0.5,
                "min_speech_duration_ms": 250,
                "min_silence_duration_ms": 500
            }
        }

        if language and language != "auto":
            transcribe_params["language"] = language

        transcribe_params.update(kwargs)

        segments_iterator, info = self._model.transcribe(str(audio_path), **transcribe_params)

        segments = []
        text_parts = []

        for segment in segments_iterator:
            seg_dict = {
                "start":          segment.start,
                "end":            segment.end,
                "text":           segment.text.strip(),
                "avg_logprob":    segment.avg_logprob,
                "no_speech_prob": segment.no_speech_prob
            }
            segments.append(seg_dict)
            text_parts.append(segment.text.strip())

        full_text = " ".join(text_parts)
        logger.info(
            f"Completado [{self._model_size}]: {len(segments)} segmentos, "
            f"idioma: {info.language if not language or language == 'auto' else language}"
        )
        return full_text, segments

    def is_loaded(self) -> bool:
        return self._model is not None

    def unload(self):
        if self._model is not None:
            del self._model
            self._model = None
            logger.info(f"Modelo '{self._model_size}' descargado de memoria")


# Instancia singleton por defecto (retrocompatibilidad con health check en routes.py)
transcription_engine = TranscriptionEngine(model_size=settings.WHISPER_MODEL)