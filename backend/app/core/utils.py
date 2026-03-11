from __future__ import annotations

import datetime as dt
import re
from pathlib import Path


def as_text(x) -> str:
    if x is None:
        return ""
    if isinstance(x, str):
        return x
    return str(x)


def safe_stem(name: str) -> str:
    name = (as_text(name) or "audio").strip()
    stem = Path(name).stem
    stem = re.sub(r"[^\w\- ]+", "", stem, flags=re.UNICODE).strip()
    stem = stem.replace(" ", "_")
    return stem or "audio"


def fmt_hhmmss(total_seconds) -> str:
    try:
        total_seconds = int(round(float(total_seconds or 0)))
    except Exception:
        total_seconds = 0
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def sec_to_hhmmss(sec: float) -> str:
    try:
        sec = float(sec or 0.0)
    except Exception:
        sec = 0.0
    return str(dt.timedelta(seconds=int(round(sec))))


def clamp_int(v, lo: int, hi: int, default: int) -> int:
    try:
        v = int(v)
    except Exception:
        v = default
    return max(lo, min(hi, v))