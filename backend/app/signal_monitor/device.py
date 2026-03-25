from __future__ import annotations

import ctypes
import logging
import math
import os
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)


class DeviceUnavailableError(RuntimeError):
    pass


class BaseSignalDevice(ABC):
    mode = "mock"

    def __init__(self):
        self.frequency_hz = settings.SIGNAL_MONITOR_DEFAULT_FREQUENCY_HZ
        self.span_hz = settings.SIGNAL_MONITOR_DEFAULT_SPAN_HZ
        self.gain_db = settings.SIGNAL_MONITOR_DEFAULT_GAIN_DB
        self.signal_type = "FM"
        self.initialized = False
        self.streaming = False

    @abstractmethod
    def initialize_device(self):
        raise NotImplementedError

    def set_frequency(self, freq: float):
        self.frequency_hz = freq

    def set_span(self, span: float):
        self.span_hz = span

    def set_gain(self, gain: float):
        self.gain_db = gain

    def set_signal_type(self, signal_type: str):
        self.signal_type = signal_type

    @abstractmethod
    def start_stream(self):
        raise NotImplementedError

    @abstractmethod
    def stop_stream(self):
        raise NotImplementedError

    @abstractmethod
    def get_signal_data(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_audio_stream(self) -> dict:
        raise NotImplementedError


class MockSignalHoundDevice(BaseSignalDevice):
    mode = "mock"

    def __init__(self):
        super().__init__()
        self._rng = np.random.default_rng()
        self._phase = 0.0
        self._tone_phase = 0.0
        self._last_timestamp = time.time()

    def initialize_device(self):
        self.initialized = True
        logger.info("Signal Monitor iniciado en modo mock")

    def start_stream(self):
        self.streaming = True
        self._last_timestamp = time.time()

    def stop_stream(self):
        self.streaming = False

    def get_signal_data(self) -> dict:
        if not self.streaming:
            raise DeviceUnavailableError("El stream no está activo")

        bins = settings.SIGNAL_MONITOR_SPECTRUM_BINS
        now = time.time()
        elapsed = now - self._last_timestamp
        self._last_timestamp = now
        self._phase += elapsed * 0.85

        frequencies = np.linspace(
            self.frequency_hz - self.span_hz / 2,
            self.frequency_hz + self.span_hz / 2,
            bins,
            dtype=np.float64,
        )

        drift = math.sin(self._phase * 0.55) * min(self.span_hz * 0.18, 180_000.0)
        secondary_drift = math.cos(self._phase * 0.23) * min(self.span_hz * 0.07, 42_000.0)
        peak_frequency = self.frequency_hz + drift + secondary_drift
        width_hz = max(self.span_hz / 18.0, 12_000.0)

        baseline = -94.0 + self._rng.normal(0.0, 1.6, bins)
        signal_envelope = np.exp(-0.5 * ((frequencies - peak_frequency) / width_hz) ** 2)
        peak_boost = 34.0 + 6.0 * math.sin(self._phase * 0.37)
        levels = baseline + (signal_envelope * peak_boost)

        active = float(levels.max()) > -67.0
        peak_level = float(levels.max())

        return {
            "timestamp": now,
            "center_frequency_hz": self.frequency_hz,
            "span_hz": self.span_hz,
            "frequencies_hz": [round(float(value), 2) for value in frequencies.tolist()],
            "levels_dbm": [round(float(value), 2) for value in levels.tolist()],
            "peak_frequency_hz": round(float(peak_frequency), 2),
            "peak_level_dbm": round(peak_level, 2),
            "noise_floor_dbm": round(float(np.percentile(levels, 15)), 2),
            "active": active,
        }

    def get_audio_stream(self) -> dict:
        if not self.streaming:
            raise DeviceUnavailableError("El stream no está activo")

        sample_rate = settings.SIGNAL_MONITOR_AUDIO_SAMPLE_RATE
        chunk_seconds = settings.SIGNAL_MONITOR_CHUNK_SECONDS
        sample_count = max(1, int(sample_rate * chunk_seconds))
        timeline = np.arange(sample_count, dtype=np.float64) / sample_rate

        carrier = 900.0 + 200.0 * math.sin(self._phase * 0.41)
        modulation = 55.0 + 15.0 * math.cos(self._phase * 0.32)

        if self.signal_type in {"AM", "USB", "LSB"}:
            envelope = 0.55 + 0.35 * np.sin(2 * np.pi * modulation * timeline + self._tone_phase)
            signal = envelope * np.sin(2 * np.pi * carrier * timeline + self._tone_phase)
        else:
            deviation = 65.0 if self.signal_type == "FM" else 35.0
            phase = 2 * np.pi * carrier * timeline + deviation * np.sin(2 * np.pi * modulation * timeline)
            signal = np.sin(phase + self._tone_phase)

        self._tone_phase += 2 * np.pi * carrier * chunk_seconds
        noise = self._rng.normal(0.0, 0.035, sample_count)
        pcm = np.clip((signal + noise) * 0.55, -1.0, 1.0)
        pcm_int16 = (pcm * 32767.0).astype(np.int16)

        return {
            "sample_rate": sample_rate,
            "channels": 1,
            "pcm_bytes": pcm_int16.tobytes(),
        }


class RealSignalHoundDevice(BaseSignalDevice):
    mode = "real"

    def __init__(self):
        super().__init__()
        self._api = None
        self._device_handle = ctypes.c_int()

    def initialize_device(self):
        dll_path = self._resolve_dll_path()
        if dll_path is None:
            raise DeviceUnavailableError("No se encontró la DLL del SDK de Signal Hound")

        self._api = ctypes.WinDLL(str(dll_path))
        if not hasattr(self._api, "bbOpenDevice"):
            raise DeviceUnavailableError("La DLL encontrada no expone bbOpenDevice")

        result = self._api.bbOpenDevice(ctypes.byref(self._device_handle))
        if result != 0:
            raise DeviceUnavailableError(f"bbOpenDevice devolvió código {result}")

        self.initialized = True
        logger.info("Signal Hound BB60C inicializado con handle %s", self._device_handle.value)

    def set_frequency(self, freq: float):
        super().set_frequency(freq)
        self._configure_center_span()

    def set_span(self, span: float):
        super().set_span(span)
        self._configure_center_span()

    def set_gain(self, gain: float):
        super().set_gain(gain)
        self._configure_gain()

    def start_stream(self):
        if self._api is None:
            raise DeviceUnavailableError("El dispositivo BB60C no está inicializado")
        self.streaming = True
        self._configure_center_span()
        self._configure_gain()

    def stop_stream(self):
        self.streaming = False

    def get_signal_data(self) -> dict:
        raise DeviceUnavailableError(
            "La captura en tiempo real del SDK BB60C requiere mapear las funciones de sweep/IQ del SDK instalado. "
            "Active el modo mock o complete la vinculación del SDK en app/signal_monitor/device.py."
        )

    def get_audio_stream(self) -> dict:
        raise DeviceUnavailableError(
            "La demodulación de audio sobre BB60C depende de disponibilidad de IQ/raw stream en el SDK instalado."
        )

    def close(self):
        if self._api is not None and hasattr(self._api, "bbCloseDevice"):
            self._api.bbCloseDevice(self._device_handle)

    def _configure_center_span(self):
        if not self.initialized or self._api is None or not hasattr(self._api, "bbConfigureCenterSpan"):
            return
        self._api.bbConfigureCenterSpan(self._device_handle, ctypes.c_double(self.frequency_hz), ctypes.c_double(self.span_hz))

    def _configure_gain(self):
        if not self.initialized or self._api is None or not hasattr(self._api, "bbConfigureGainAtten"):
            return
        self._api.bbConfigureGainAtten(self._device_handle, ctypes.c_double(self.gain_db), ctypes.c_int(0), ctypes.c_bool(True))

    def _resolve_dll_path(self) -> Optional[Path]:
        candidates = []
        if settings.SIGNAL_MONITOR_SDK_DLL:
            candidates.append(Path(settings.SIGNAL_MONITOR_SDK_DLL))

        env_value = os.getenv("SIGNAL_HOUND_SDK_DLL")
        if env_value:
            candidates.append(Path(env_value))

        candidates.extend([
            settings.ASSETS_DIR / "signal_hound" / "bb_api.dll",
            settings.ASSETS_DIR / "signal_hound" / "bb_api64.dll",
            Path("C:/Program Files/Signal Hound/Spike/software/bb_api.dll"),
            Path("C:/Program Files/Signal Hound/Spike/software/bb_api64.dll"),
        ])

        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None


def build_signal_device(preferred_mode: str = "auto") -> BaseSignalDevice:
    force_mock = settings.SIGNAL_MONITOR_MOCK_MODE or preferred_mode == "mock"
    force_real = preferred_mode == "real"

    if force_mock and not force_real:
        return MockSignalHoundDevice()

    try:
        device = RealSignalHoundDevice()
        device.initialize_device()
        return device
    except Exception as exc:
        if not settings.SIGNAL_MONITOR_ALLOW_MOCK_FALLBACK and force_real:
            raise
        logger.warning("No fue posible iniciar BB60C real, se usa modo mock: %s", exc)
        mock = MockSignalHoundDevice()
        mock.initialize_device()
        return mock