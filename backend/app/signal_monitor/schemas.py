from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


SignalType = Literal["AM", "FM", "NFM", "WFM", "USB", "LSB"]


class ActivityDetectionConfig(BaseModel):
    threshold_dbm: float = Field(..., ge=-120.0, le=0.0)
    hysteresis_db: float = Field(..., ge=0.1, le=10.0)
    min_duration_seconds: float = Field(..., ge=0.1, le=10.0)


class SignalMonitorConfig(BaseModel):
    frequency_hz: float = Field(..., ge=1_000.0, le=6_000_000_000.0)
    span_hz: float = Field(..., ge=1_000.0, le=100_000_000.0)
    gain_db: float = Field(..., ge=-30.0, le=60.0)
    signal_type: SignalType = "FM"
    mute: bool = False
    live_transcription: bool = False
    activity_detection: ActivityDetectionConfig = Field(
        default_factory=lambda: ActivityDetectionConfig(
            threshold_dbm=-70.0,
            hysteresis_db=3.0,
            min_duration_seconds=0.5
        )
    )


class SignalMonitorStartRequest(SignalMonitorConfig):
    preferred_mode: Optional[Literal["real", "mock", "auto"]] = "auto"


class SignalMonitorUpdateRequest(BaseModel):
    frequency_hz: Optional[float] = Field(None, ge=1_000.0, le=6_000_000_000.0)
    span_hz: Optional[float] = Field(None, ge=1_000.0, le=100_000_000.0)
    gain_db: Optional[float] = Field(None, ge=-30.0, le=60.0)
    signal_type: Optional[SignalType] = None
    mute: Optional[bool] = None


class SignalMonitorRecordingRequest(BaseModel):
    session_name: Optional[str] = Field(None, max_length=120)

    @field_validator("session_name")
    @classmethod
    def normalize_session_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        clean = value.strip()
        return clean or None


class SignalMonitorTranscriptionToggleRequest(BaseModel):
    enabled: bool


class SignalMonitorStatusResponse(BaseModel):
    initialized: bool
    streaming: bool
    recording: bool
    transcription_enabled: bool
    backend_mode: Literal["real", "mock"]
    config: dict
    channel_active: bool
    activity_state_history: list
    last_error: Optional[str] = None
    recording_file: Optional[str] = None