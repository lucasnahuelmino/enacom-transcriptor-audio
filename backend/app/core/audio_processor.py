from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def ffprobe_duration_seconds(audio_path: Path):
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return None
    try:
        cmd = [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
        ]
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True).strip()
        if not out:
            return None
        return float(out)
    except Exception:
        return None


def split_audio_to_wavs(in_path: Path, out_dir: Path, segment_seconds: int):
    try:
        segment_seconds = int(segment_seconds or 30)
    except Exception:
        segment_seconds = 30

    segment_seconds = max(10, min(120, segment_seconds))

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return [in_path]

    out_dir.mkdir(parents=True, exist_ok=True)

    for p in out_dir.glob("seg_*.wav"):
        try:
            p.unlink()
        except Exception:
            pass

    out_pattern = str(out_dir / "seg_%06d.wav")

    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(in_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-f",
        "segment",
        "-segment_time",
        str(segment_seconds),
        "-reset_timestamps",
        "1",
        out_pattern,
    ]

    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except Exception:
        return [in_path]

    segs = sorted(out_dir.glob("seg_*.wav"))
    return segs if segs else [in_path]


def try_read_audio_for_waveform(audio_path: str):
    try:
        import soundfile as sf  # type: ignore

        data, sr = sf.read(audio_path, always_2d=False)
        return int(sr), data
    except Exception:
        return None, None

def get_audio_duration(audio_path: Path) -> float:
    """Alias para ffprobe_duration_seconds"""
    return ffprobe_duration_seconds(audio_path) or 0.0

def split_audio(audio_path: Path, output_dir: Path, segment_seconds: int) -> list[Path]:
    """Alias para split_audio_to_wavs"""
    return split_audio_to_wavs(audio_path, output_dir, segment_seconds)