from __future__ import annotations

import re

from app.core.utils import as_text, sec_to_hhmmss


def highlight_query_md(text: str, query: str) -> str:
    t = as_text(text)
    q = (as_text(query) or "").strip()
    if not q:
        return f"```text\n{t}\n```" if t else ""
    try:
        pat = re.compile(re.escape(q), flags=re.IGNORECASE)
        return pat.sub(lambda m: f"**{m.group(0)}**", t)
    except Exception:
        return t


def clean_boilerplate(text: str) -> str:
    t = (as_text(text) or "").strip()
    if not t:
        return ""
    t = re.sub(r"\s+", " ", t).strip()

    patterns = [
        r"subt[ií]tulos?\s+por\s+la\s+comunidad\s+de\s+amara\.org\.?",
        r"\bsuscr[ií]bete\b[:!¡\.\s]*",
        r"\bsubscribe\b[:!¡\.\s]*",
    ]
    for pat in patterns:
        t = re.sub(pat, "", t, flags=re.IGNORECASE)

    if len(t) >= 40:
        t = re.sub(
            r"(\b(?:\w+\b\s+){2,7}\w+\b)(?:\s+\1){2,}",
            r"\1 \1",
            t,
            flags=re.IGNORECASE,
        )

    t = re.sub(r"\s+", " ", t).strip()
    return t


def should_skip_segment(seg: dict) -> bool:
    try:
        ns = float(seg.get("no_speech_prob", 0.0) or 0.0)
    except Exception:
        ns = 0.0

    raw = as_text(seg.get("text", "")).strip()
    cleaned = clean_boilerplate(raw)

    if ns >= 0.80 and len(cleaned) < 8:
        return True
    if len(cleaned) < 2:
        return True
    return False


def format_segments_lines(segments: list[dict], window_s: int) -> list[dict]:
    """
    items:
      {"start": float, "end": float, "line": "[HH:MM:SS - HH:MM:SS] ...", "text": "..."}
    """
    try:
        window_s = int(window_s or 20)
    except Exception:
        window_s = 20
    window_s = max(5, min(120, window_s))

    segs = []
    for s in segments or []:
        if should_skip_segment(s):
            continue
        txt = clean_boilerplate(as_text(s.get("text", "")).strip())
        if not txt:
            continue
        s2 = dict(s)
        s2["text"] = txt
        segs.append(s2)

    if not segs:
        return []

    out: list[dict] = []
    bucket_start = None
    bucket_end = None
    bucket_text: list[str] = []

    def flush():
        nonlocal bucket_start, bucket_end, bucket_text
        if bucket_start is None or bucket_end is None:
            return
        txt = " ".join([x.strip() for x in bucket_text if x.strip()]).strip()
        txt = re.sub(r"\s+", " ", txt).strip()
        if txt:
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
        txt = as_text(s.get("text", "")).strip()
        if not txt:
            continue

        if bucket_start is None:
            bucket_start = stt
            bucket_end = end
            bucket_text = [txt]
            continue

        if (end - bucket_start) <= window_s:
            bucket_end = max(bucket_end, end)
            bucket_text.append(txt)
        else:
            flush()
            bucket_start = stt
            bucket_end = end
            bucket_text = [txt]

    flush()
    return out
