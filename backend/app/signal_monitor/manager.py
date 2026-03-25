from __future__ import annotations

import base64
import logging
import threading
import time
from collections import deque
from copy import deepcopy
from typing import Optional

from app.config import settings
from app.signal_monitor.activity import ActivityDetector
from app.signal_monitor.device import BaseSignalDevice, DeviceUnavailableError, build_signal_device
from app.signal_monitor.recorder import SignalRecorder
from app.signal_monitor.schemas import SignalMonitorConfig
from app.signal_monitor.transcription import LiveTranscriptionProcessor

logger = logging.getLogger(__name__)


class SignalMonitorService:
    def __init__(self):
        self._lock = threading.RLock()
        self._device: Optional[BaseSignalDevice] = None
        self._stream_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._config = SignalMonitorConfig(
            frequency_hz=settings.SIGNAL_MONITOR_DEFAULT_FREQUENCY_HZ,
            span_hz=settings.SIGNAL_MONITOR_DEFAULT_SPAN_HZ,
            gain_db=settings.SIGNAL_MONITOR_DEFAULT_GAIN_DB,
            signal_type="FM",
            mute=False,
            live_transcription=False,
            activity_detection={
                "threshold_dbm": settings.SIGNAL_MONITOR_ACTIVITY_THRESHOLD_DBM,
                "hysteresis_db": settings.SIGNAL_MONITOR_ACTIVITY_HYSTERESIS_DB,
                "min_duration_seconds": settings.SIGNAL_MONITOR_ACTIVITY_MIN_DURATION_SECONDS,
            },
        )
        self._backend_mode = "mock"
        self._last_error: Optional[str] = None
        self._recent_events: deque[dict] = deque(maxlen=200)
        self._recorder = SignalRecorder(settings.SIGNAL_MONITOR_DIR, settings.SIGNAL_MONITOR_AUDIO_SAMPLE_RATE)
        self._transcription = LiveTranscriptionProcessor(self._emit_transcription, settings.SIGNAL_MONITOR_AUDIO_SAMPLE_RATE)
        self._activity_detector = ActivityDetector(
            threshold_dbm=settings.SIGNAL_MONITOR_ACTIVITY_THRESHOLD_DBM,
            hysteresis_db=settings.SIGNAL_MONITOR_ACTIVITY_HYSTERESIS_DB,
            min_duration_seconds=settings.SIGNAL_MONITOR_ACTIVITY_MIN_DURATION_SECONDS,
            emit_callback=self._emit_activity_change,
        )
        self._emit_state = None
        self._emit_spectrum = None
        self._emit_audio = None
        self._emit_transcription_event = None
        self._emit_event = None
        self._emit_activity_change_event = None
        self._emit_error = None

    def bind_emitters(self, emit_state, emit_spectrum, emit_audio, emit_transcription, emit_event, emit_activity_change, emit_error):
        self._emit_state = emit_state
        self._emit_spectrum = emit_spectrum
        self._emit_audio = emit_audio
        self._emit_transcription_event = emit_transcription
        self._emit_event = emit_event
        self._emit_activity_change_event = emit_activity_change
        self._emit_error = emit_error

    def start(self, config: dict, preferred_mode: str = "auto") -> dict:
        with self._lock:
            merged = self._config.model_dump()
            merged.update(config)
            self._config = SignalMonitorConfig(**merged)

            if self._device is None:
                self._device = build_signal_device(preferred_mode)
                self._backend_mode = self._device.mode
                if not self._device.initialized:
                    self._device.initialize_device()

            self._apply_config_locked(self._config.model_dump())
            self._stop_event.clear()
            self._device.start_stream()
            self._transcription.reset()
            self._transcription.set_enabled(self._config.live_transcription)
            self._activity_detector.reset()

            if self._stream_thread is None or not self._stream_thread.is_alive():
                self._stream_thread = threading.Thread(target=self._run_stream_loop, name="signal-monitor-stream", daemon=True)
                self._stream_thread.start()

            self._publish_state_locked(message="Monitoreo iniciado")
            return self.status()

    def stop(self) -> dict:
        with self._lock:
            self._stop_event.set()
            if self._device is not None:
                self._device.stop_stream()
            if self._stream_thread and self._stream_thread.is_alive():
                self._stream_thread.join(timeout=2.0)
            self._stream_thread = None
            self._transcription.set_enabled(False)
            self._transcription.stop()
            self._activity_detector.reset()
            self.stop_recording()
            self._publish_state_locked(message="Monitoreo detenido")
            return self.status()

    def update_config(self, config: dict) -> dict:
        with self._lock:
            merged = self._config.model_dump()
            merged.update({key: value for key, value in config.items() if value is not None})
            self._config = SignalMonitorConfig(**merged)
            self._apply_config_locked(config)
            if "activity_detection" in config and config["activity_detection"]:
                ad_cfg = config["activity_detection"]
                if "threshold_dbm" in ad_cfg:
                    self._activity_detector.update_threshold(ad_cfg["threshold_dbm"])
                if "hysteresis_db" in ad_cfg:
                    self._activity_detector.update_hysteresis(ad_cfg["hysteresis_db"])
            self._publish_state_locked(message="Configuración actualizada")
            return self.status()

    def start_recording(self, session_name: Optional[str] = None) -> dict:
        with self._lock:
            artifact = self._recorder.start(session_name, self._config.model_dump())
            self._publish_state_locked(message="Grabación iniciada")
            return {
                "recording": True,
                "session_id": artifact.session_id,
                "audio_file": str(artifact.audio_path),
            }

    def stop_recording(self) -> dict:
        artifact = self._recorder.stop()
        if artifact is None:
            return {"recording": False}

        with self._lock:
            self._publish_state_locked(message="Grabación detenida")
            return {
                "recording": False,
                "session_id": artifact.session_id,
                "audio_file": str(artifact.audio_path),
            }

    def toggle_transcription(self, enabled: bool) -> dict:
        with self._lock:
            merged = self._config.model_dump()
            merged["live_transcription"] = enabled
            self._config = SignalMonitorConfig(**merged)
            self._transcription.set_enabled(enabled)
            self._publish_state_locked(message="Transcripción en vivo actualizada")
            return self.status()

    def status(self) -> dict:
        with self._lock:
            return {
                "initialized": bool(self._device and self._device.initialized),
                "streaming": bool(self._device and self._device.streaming and not self._stop_event.is_set()),
                "recording": self._recorder.active_artifact is not None,
                "transcription_enabled": self._config.live_transcription,
                "channel_active": self._activity_detector.is_active,
                "activity_state_history": self._activity_detector.state_history,
                "backend_mode": self._backend_mode,
                "config": self._config.model_dump(),
                "last_error": self._last_error,
                "recording_file": str(self._recorder.active_artifact.audio_path) if self._recorder.active_artifact else None,
                "events": list(self._recent_events)[-20:],
                "transcription_text": self._transcription.current_text(),
            }

    def _apply_config_locked(self, config: dict):
        if self._device is None:
            return
        if config.get("frequency_hz") is not None:
            self._device.set_frequency(float(config["frequency_hz"]))
        if config.get("span_hz") is not None:
            self._device.set_span(float(config["span_hz"]))
        if config.get("gain_db") is not None:
            self._device.set_gain(float(config["gain_db"]))
        if config.get("signal_type") is not None:
            self._device.set_signal_type(config["signal_type"])

    def _run_stream_loop(self):
        while not self._stop_event.is_set():
            try:
                if self._device is None or not self._device.streaming:
                    time.sleep(0.2)
                    continue

                spectrum = self._device.get_signal_data()
                self._register_event(spectrum)
                self._activity_detector.update(spectrum.get("peak_level_dbm", -120))
                if self._emit_spectrum:
                    self._emit_spectrum(spectrum)

                audio = self._device.get_audio_stream()
                pcm_bytes = audio.get("pcm_bytes", b"")
                if pcm_bytes:
                    if self._recorder.active_artifact is not None:
                        self._recorder.write_audio(pcm_bytes)
                    if self._config.live_transcription:
                        self._transcription.push_audio(pcm_bytes)
                    if not self._config.mute and self._emit_audio:
                        self._emit_audio({
                            "sample_rate": audio["sample_rate"],
                            "channels": audio.get("channels", 1),
                            "pcm_base64": base64.b64encode(pcm_bytes).decode("ascii"),
                            "timestamp": time.time(),
                        })

                time.sleep(max(0.05, settings.SIGNAL_MONITOR_CHUNK_SECONDS * 0.5))
            except DeviceUnavailableError as exc:
                logger.error("Error de dispositivo en Signal Monitor: %s", exc)
                self._last_error = str(exc)
                if self._emit_error:
                    self._emit_error({"message": str(exc)})
                self._publish_state_locked(message="Error de dispositivo")
                self._stop_event.set()
            except Exception as exc:
                logger.error("Error en loop de Signal Monitor: %s", exc, exc_info=True)
                self._last_error = str(exc)
                if self._emit_error:
                    self._emit_error({"message": str(exc)})
                time.sleep(0.5)

    def _register_event(self, spectrum: dict):
        event = {
            "timestamp": spectrum.get("timestamp", time.time()),
            "peak_frequency_hz": spectrum.get("peak_frequency_hz"),
            "peak_level_dbm": spectrum.get("peak_level_dbm"),
            "active": spectrum.get("active"),
        }
        self._recent_events.append(event)
        if self._emit_event:
            self._emit_event(event)
        if self._recorder.active_artifact is not None:
            self._recorder.write_event(event)

    def _emit_transcription(self, payload: dict):
        if self._emit_transcription_event:
            self._emit_transcription_event(payload)

    def _emit_activity_change(self, payload: dict):
        if self._emit_activity_change_event:
            self._emit_activity_change_event(payload)

    def _publish_state_locked(self, message: Optional[str] = None):
        if self._emit_state:
            payload = self.status()
            if message:
                payload["message"] = message
            self._emit_state(payload)


signal_monitor_service = SignalMonitorService()