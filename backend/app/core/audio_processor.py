from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
import logging
import sys
import os

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Prioridad de búsqueda de ffmpeg:
# 1. tools/ffmpeg/bin/ffmpeg (portable local)
# 2. PATH del sistema
# ─────────────────────────────────────────────────────────────────────────────

def get_ffmpeg_path() -> str:

    # Opción 1: Buscar en tools/ffmpeg (portable local)
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    local_ffmpeg = project_root / "tools" / "ffmpeg" / "bin"
    
    if sys.platform == "win32":
        ffmpeg_exe = local_ffmpeg / "ffmpeg.exe"
    else:
        ffmpeg_exe = local_ffmpeg / "ffmpeg"
    
    if ffmpeg_exe.exists():
        logger.info(f"Using portable ffmpeg: {ffmpeg_exe}")
        return str(ffmpeg_exe)
    
    # Opción 2: Buscar en PATH del sistema
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        logger.info(f"Using system ffmpeg: {ffmpeg_path}")
        return ffmpeg_path
    
    # No encontrado
    logger.warning("ffmpeg not found in tools/ffmpeg or system PATH")
    return "ffmpeg"  # Intentará ejecutar ffmpeg del PATH de todas formas


def get_ffprobe_path() -> str:
    """
    Obtiene la ruta a ffprobe con siguiente prioridad:
    1. tools/ffmpeg/bin/ffprobe (portable local)
    2. ffprobe en PATH del sistema
    """
    # Opción 1: Buscar en tools/ffmpeg (portable local)
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    local_ffprobe = project_root / "tools" / "ffmpeg" / "bin"
    
    if sys.platform == "win32":
        ffprobe_exe = local_ffprobe / "ffprobe.exe"
    else:
        ffprobe_exe = local_ffprobe / "ffprobe"
    
    if ffprobe_exe.exists():
        logger.info(f"Using portable ffprobe: {ffprobe_exe}")
        return str(ffprobe_exe)
    
    # Opción 2: Buscar en PATH del sistema
    ffprobe_path = shutil.which("ffprobe")
    if ffprobe_path:
        logger.info(f"Using system ffprobe: {ffprobe_path}")
        return ffprobe_path
    
    # No encontrado
    logger.warning("ffprobe not found in tools/ffmpeg or system PATH")
    return "ffprobe"


def ffprobe_duration_seconds(audio_path: Path):
    ffprobe = get_ffprobe_path()
    
    if not Path(ffprobe).exists() and ffprobe != "ffprobe":
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

    ffmpeg = get_ffmpeg_path()
    
    # Verificar que ffmpeg existe
    if not Path(ffmpeg).exists() and ffmpeg != "ffmpeg":
        logger.warning(f"ffmpeg not found at {ffmpeg}, trying system PATH")
        ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
    
    if not Path(ffmpeg).exists() if ffmpeg != "ffmpeg" else True:
        if ffmpeg == "ffmpeg":
            logger.warning("ffmpeg not found in PATH, returning original file without splitting")
            return [in_path]

    out_dir.mkdir(parents=True, exist_ok=True)

    # Limpiar segmentos previos
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
        # ✅ Capturar stderr para saber si ffmpeg falló
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            logger.error(
                f"ffmpeg segmentation failed for {in_path.name}\n"
                f"Command: {' '.join(cmd)}\n"
                f"stderr: {result.stderr}\n"
                f"stdout: {result.stdout}"
            )
            return [in_path]
            
        # Buscar segmentos creados
        segs = sorted(out_dir.glob("seg_*.wav"))
        
        if not segs:
            logger.warning(
                f"ffmpeg did not create segments for {in_path.name}, "
                f"returning original file"
            )
            return [in_path]
        
        logger.info(f"Successfully split {in_path.name} into {len(segs)} segments")
        return segs
        
    except Exception as e:
        logger.error(f"Unexpected error during ffmpeg segmentation: {str(e)}")
        return [in_path]


def try_read_audio_for_waveform(audio_path: str):
    try:
        import soundfile as sf 

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