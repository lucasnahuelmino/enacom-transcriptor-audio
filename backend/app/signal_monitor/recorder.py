from __future__ import annotations

import json
import threading
import wave
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class RecordingArtifact:
    session_id: str
    audio_path: Path
    events_path: Path
    metadata_path: Path


class SignalRecorder:
    def __init__(self, base_dir: Path, sample_rate: int):
        self._base_dir = base_dir
        self._sample_rate = sample_rate
        self._lock = threading.Lock()
        self._wave_writer: Optional[wave.Wave_write] = None
        self._events_file = None
        self._artifact: Optional[RecordingArtifact] = None
        self._metadata: Optional[dict] = None

    def start(self, session_name: Optional[str], config: dict) -> RecordingArtifact:
        with self._lock:
            if self._artifact is not None:
                return self._artifact

            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            safe_name = (session_name or "live_monitor").replace(" ", "_")
            session_id = f"{timestamp}_{safe_name}"
            session_dir = self._base_dir / session_id
            session_dir.mkdir(parents=True, exist_ok=True)

            audio_path = session_dir / "demodulated_audio.wav"
            events_path = session_dir / "events.jsonl"
            metadata_path = session_dir / "metadata.json"

            writer = wave.open(str(audio_path), "wb")
            writer.setnchannels(1)
            writer.setsampwidth(2)
            writer.setframerate(self._sample_rate)

            self._events_file = events_path.open("a", encoding="utf-8")
            self._wave_writer = writer
            self._artifact = RecordingArtifact(
                session_id=session_id,
                audio_path=audio_path,
                events_path=events_path,
                metadata_path=metadata_path,
            )
            self._metadata = {
                "session_id": session_id,
                "started_at": datetime.utcnow().isoformat() + "Z",
                "sample_rate": self._sample_rate,
                "config": config,
            }
            metadata_path.write_text(json.dumps(self._metadata, indent=2, ensure_ascii=False), encoding="utf-8")
            return self._artifact

    def write_audio(self, pcm_bytes: bytes):
        with self._lock:
            if self._wave_writer is None:
                return
            self._wave_writer.writeframes(pcm_bytes)

    def write_event(self, event: dict):
        with self._lock:
            if self._events_file is None:
                return
            self._events_file.write(json.dumps(event, ensure_ascii=False) + "\n")
            self._events_file.flush()

    def stop(self) -> Optional[RecordingArtifact]:
        with self._lock:
            artifact = self._artifact
            if artifact is None:
                return None

            if self._wave_writer is not None:
                self._wave_writer.close()
            if self._events_file is not None:
                self._events_file.close()

            if self._metadata is not None:
                self._metadata["stopped_at"] = datetime.utcnow().isoformat() + "Z"
                artifact.metadata_path.write_text(
                    json.dumps(self._metadata, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )

            self._wave_writer = None
            self._events_file = None
            self._artifact = None
            self._metadata = None
            return artifact

    @property
    def active_artifact(self) -> Optional[RecordingArtifact]:
        return self._artifact