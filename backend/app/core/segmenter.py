from __future__ import annotations

import datetime as dt
import re
from typing import List, Dict


from app.core.text_ops import clean_boilerplate, should_skip_segment
from app.core.utils import sec_to_hhmmss


def windowed_segments(segments: List[Dict], window_s: int) -> List[Dict]:
    try:
        window_s = int(window_s or 20)
    except Exception:
        window_s = 20
    window_s = max(5, min(120, window_s))

    segs: List[Dict] = []
    for s in segments or []:
        if should_skip_segment(s):
            continue
        txt = clean_boilerplate(str(s.get("text", "") or "").strip())
        if not txt:
            continue
        s2 = dict(s)
        s2["text"] = txt
        segs.append(s2)

    if not segs:
        return []

    out: List[Dict] = []
    bucket_start = None
    bucket_end = None
    bucket_text: List[str] = []

    def flush():
        nonlocal bucket_start, bucket_end, bucket_text
        if bucket_start is None or bucket_end is None:
            return
        txt = " ".join([x.strip() for x in bucket_text if x.strip()]).strip()
        txt = re.sub(r"\s+", " ", txt).strip()
        if not txt:
            txt = "Silencio"
        out.append(
            {
                "start": float(bucket_start),
                "end": float(bucket_end),
                "text": txt,
                "line": f"[{sec_to_hhmmss(bucket_start)} - {sec_to_hhmmss(bucket_end)}] {txt}",
            }
        )
        bucket_start = None
        bucket_end = None
        bucket_text = []

    for s in segs:
        stt = float(s.get("start", 0.0) or 0.0)
        end = float(s.get("end", 0.0) or 0.0)
        txt = str(s.get("text", "") or "").strip()

        if bucket_start is None:
            bucket_start = stt
            bucket_end = end
            bucket_text = [txt] if txt else []
            continue

        if (end - bucket_start) <= window_s:
            bucket_end = max(bucket_end, end)
            if txt:
                bucket_text.append(txt)
        else:
            flush()
            bucket_start = stt
            bucket_end = end
            bucket_text = [txt] if txt else []

    flush()
    return out


def build_fixed_windows_from_duration(duration_s: float, window_s: int) -> List[Dict]:
    try:
        duration_s = float(duration_s or 0.0)
    except Exception:
        duration_s = 0.0
    try:
        window_s = int(window_s or 20)
    except Exception:
        window_s = 20
    window_s = max(5, min(120, window_s))

    if duration_s <= 0:
        return [{"start": 0.0, "end": float(window_s), "text": "Silencio"}]

    out: List[Dict] = []
    start = 0.0
    while start < duration_s:
        end = min(duration_s, start + window_s)
        out.append({"start": start, "end": end, "text": "Silencio"})
        start = end
    return out


def merge_text_into_fixed_windows(fixed_windows: List[Dict], segments: List[Dict]) -> List[Dict]:
    """
    Distribuye los segmentos de Whisper (con offset ya corregido)
    dentro de las ventanas fijas.
    """
    out = []
    for w in fixed_windows:
        ws = float(w["start"])
        we = float(w["end"])
        parts: List[str] = []

        for s in segments or []:
            if should_skip_segment(s):
                continue
            ss = float(s.get("start", 0.0) or 0.0)
            se = float(s.get("end", 0.0) or 0.0)
            if se <= ws or ss >= we:
                continue
            txt = clean_boilerplate(str(s.get("text", "") or "").strip())
            if txt:
                parts.append(txt)

        txt = " ".join(parts).strip()
        if not txt:
            txt = "Silencio"

        out.append(
            {
                "start": ws,
                "end": we,
                "text": txt,
                "line": f"[{sec_to_hhmmss(ws)} - {sec_to_hhmmss(we)}] {txt}",
            }
        )
    return out