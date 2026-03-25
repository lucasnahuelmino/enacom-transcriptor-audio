from __future__ import annotations

import logging
import tempfile
import threading
import time
import wave
from pathlib import Path
from typing import Callable, Optional

from app.config import settings
from app.core.transcription import TranscriptionEngine

logger = logging.getLogger(__name__)


def _merge_transcripts(existing_text: str, incoming_text: str) -> str:
    if not existing_text:
        return incoming_text.strip()
    if not incoming_text:
        return existing_text.strip()

    existing_words = existing_text.split()
    incoming_words = incoming_text.split()
    overlap_limit = min(18, len(existing_words), len(incoming_words))

    for overlap in range(overlap_limit, 0, -1):
        if existing_words[-overlap:] == incoming_words[:overlap]:
            merged = existing_words + incoming_words[overlap:]
            return " ".join(merged).strip()

    return f"{existing_text.strip()} {incoming_text.strip()}".strip()


class LiveTranscriptionProcessor:
    def __init__(self, emit_callback: Callable[[dict], None], sample_rate: int):
        self._emit_callback = emit_callback
        self._sample_rate = sample_rate
        self._bytes_per_second = sample_rate * 2
        self._window_seconds = settings.SIGNAL_MONITOR_TRANSCRIPTION_WINDOW_SECONDS
        self._overlap_seconds = settings.SIGNAL_MONITOR_TRANSCRIPTION_OVERLAP_SECONDS
        self._buffer = bytearray()
        self._buffer_start_seconds = 0.0
        self._processed_seconds = 0.0
        self._transcript_text = ""
        self._enabled = False
        self._worker: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._engine: Optional[TranscriptionEngine] = None

    def start(self):
        if self._worker and self._worker.is_alive():
            return
        self._stop_event.clear()
        self._worker = threading.Thread(target=self._run_loop, name="signal-live-transcription", daemon=True)
        self._worker.start()

    def stop(self):
        if self._enabled:
            self._flush_pending_window()
        self._stop_event.set()
        if self._worker and self._worker.is_alive():
            self._worker.join(timeout=2.0)
        self._worker = None

    def set_enabled(self, enabled: bool):
        self._enabled = enabled
        if enabled:
            self.start()

    def push_audio(self, pcm_bytes: bytes):
        if not self._enabled:
            return
        with self._lock:
            self._buffer.extend(pcm_bytes)

    def reset(self):
        with self._lock:
            self._buffer.clear()
            self._buffer_start_seconds = 0.0
            self._processed_seconds = 0.0
            self._transcript_text = ""

    def current_text(self) -> str:
        with self._lock:
            return self._transcript_text

    def _run_loop(self):
        while not self._stop_event.is_set():
            try:
                if not self._enabled:
                    time.sleep(0.2)
                    continue

                window = self._consume_window()
                if window is None:
                    time.sleep(0.2)
                    continue

                text = self._transcribe_window(window)
                if not text:
                    continue

                with self._lock:
                    self._transcript_text = _merge_transcripts(self._transcript_text, text)
                    payload = {
                        "text": self._transcript_text,
                        "partial_text": text,
                        "updated_at": time.time(),
                    }
                self._emit_callback(payload)
            except Exception as exc:
                logger.error("Error en transcripción en vivo: %s", exc, exc_info=True)
                time.sleep(0.5)

    def _consume_window(self) -> Optional[bytes]:
        with self._lock:
            buffered_seconds = self._buffer_start_seconds + (len(self._buffer) / self._bytes_per_second)
            if buffered_seconds - self._processed_seconds < self._window_seconds:
                return None

            start_seconds = max(self._buffer_start_seconds, self._processed_seconds - self._overlap_seconds)
            end_seconds = min(buffered_seconds, self._processed_seconds + self._window_seconds)

            start_offset = int((start_seconds - self._buffer_start_seconds) * self._bytes_per_second)
            end_offset = int((end_seconds - self._buffer_start_seconds) * self._bytes_per_second)
            window = bytes(self._buffer[start_offset:end_offset])

            self._processed_seconds = end_seconds
            self._trim_buffer_locked()
            return window

    def _flush_pending_window(self):
        with self._lock:
            buffered_seconds = self._buffer_start_seconds + (len(self._buffer) / self._bytes_per_second)
            remaining_seconds = buffered_seconds - self._processed_seconds
            if remaining_seconds < 2.0:
                return

            start_seconds = max(self._buffer_start_seconds, self._processed_seconds - self._overlap_seconds)
            start_offset = int((start_seconds - self._buffer_start_seconds) * self._bytes_per_second)
            window = bytes(self._buffer[start_offset:])
            self._processed_seconds = buffered_seconds

        text = self._transcribe_window(window)
        if not text:
            return

        with self._lock:
            self._transcript_text = _merge_transcripts(self._transcript_text, text)
            payload = {
                "text": self._transcript_text,
                "partial_text": text,
                "updated_at": time.time(),
            }

        self._emit_callback(payload)

    def _trim_buffer_locked(self):
        keep_seconds = 12.0
        trim_to_seconds = max(self._buffer_start_seconds, self._processed_seconds - keep_seconds)
        trim_bytes = int((trim_to_seconds - self._buffer_start_seconds) * self._bytes_per_second)
        if trim_bytes <= 0:
            return
        del self._buffer[:trim_bytes]
        self._buffer_start_seconds = trim_to_seconds

    def _transcribe_window(self, pcm_bytes: bytes) -> str:
        if not pcm_bytes:
            return ""
        if self._engine is None:
            self._engine = TranscriptionEngine(model_size=settings.WHISPER_MODEL)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

        try:
            with wave.open(str(tmp_path), "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(self._sample_rate)
                wav_file.writeframes(pcm_bytes)

            text, _segments = self._engine.transcribe(tmp_path, language="es")
            return text.strip()
        finally:
            tmp_path.unlink(missing_ok=True)