"""
Core de transcripción usando faster-whisper
Mucho más rápido que openai-whisper (~4x en CPU, ~2x en GPU)
"""
from faster_whisper import WhisperModel
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class TranscriptionEngine:
    """
    Wrapper para faster-whisper con carga lazy del modelo
    """
    
    _instance: Optional['TranscriptionEngine'] = None
    _model: Optional[WhisperModel] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._model is None:
            self._load_model()
    
    def _load_model(self):
        """Carga el modelo faster-whisper"""
        logger.info(f"Cargando modelo faster-whisper: {settings.WHISPER_MODEL}")
        
        device = settings.WHISPER_DEVICE
        if device == "auto":
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                device = "cpu"
        
        logger.info(f"Dispositivo seleccionado: {device}")
        
        # Cargar modelo
        self._model = WhisperModel(
            settings.WHISPER_MODEL,
            device=device,
            compute_type=settings.WHISPER_COMPUTE_TYPE if device == "cuda" else "int8",
            download_root=None,  # Usa cache por defecto en ~/.cache/huggingface
            local_files_only=False
        )
        
        logger.info("Modelo cargado exitosamente")
    
    def transcribe(
        self,
        audio_path: Path,
        language: Optional[str] = None,
        **kwargs
    ) -> Tuple[str, List[Dict]]:
        """
        Transcribe un archivo de audio
        
        Returns:
            Tuple[str, List[Dict]]: (texto_completo, segmentos)
            
        Formato de segmentos:
            [
                {
                    "start": float,
                    "end": float,
                    "text": str,
                    "avg_logprob": float,
                    "no_speech_prob": float
                },
                ...
            ]
        """
        if self._model is None:
            self._load_model()
        
        logger.info(f"Transcribiendo: {audio_path.name}")
        
        # Parámetros de transcripción
        transcribe_params = {
            "beam_size": 5,
            "best_of": 5,
            "temperature": 0.0,
            "condition_on_previous_text": False,
            "vad_filter": True,  # Voice Activity Detection
            "vad_parameters": {
                "threshold": 0.5,
                "min_speech_duration_ms": 250,
                "min_silence_duration_ms": 500
            }
        }
        
        if language and language != "auto":
            transcribe_params["language"] = language
        
        # Actualizar con kwargs adicionales
        transcribe_params.update(kwargs)
        
        # Transcribir
        segments_iterator, info = self._model.transcribe(
            str(audio_path),
            **transcribe_params
        )
        
        # Convertir iterator a lista y extraer texto
        segments = []
        text_parts = []
        
        for segment in segments_iterator:
            seg_dict = {
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip(),
                "avg_logprob": segment.avg_logprob,
                "no_speech_prob": segment.no_speech_prob
            }
            segments.append(seg_dict)
            text_parts.append(segment.text.strip())
        
        full_text = " ".join(text_parts)
        
        logger.info(
            f"Transcripción completada: {len(segments)} segmentos, "
            f"idioma detectado: {info.language if language == 'auto' else language}"
        )
        
        return full_text, segments
    
    def is_loaded(self) -> bool:
        """Verifica si el modelo está cargado"""
        return self._model is not None
    
    def unload(self):
        """Descarga el modelo de memoria"""
        if self._model is not None:
            del self._model
            self._model = None
            logger.info("Modelo descargado de memoria")


# Instancia singleton
transcription_engine = TranscriptionEngine()
