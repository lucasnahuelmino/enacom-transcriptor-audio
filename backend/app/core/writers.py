from __future__ import annotations

import io
import json
import zipfile
import datetime as dt
from pathlib import Path

from app.core.utils import as_text


def write_txt(
    txt_path: Path,
    title: str,
    full_text: str,
    segmented_items: list[dict],
    infracciones_hits: list[dict],
) -> None:
    """
    Escribe el TXT de transcripción en este orden:
      1. Título
      2. Resumen de infracciones (si hay)
      3. TRANSCRIPCIÓN SEGMENTADA (con timestamps) ← primero, más útil
      4. TRANSCRIPCIÓN COMPLETA

    El orden segmentada → completa es el documentado en el README.
    """
    lines: list[str] = []
    lines.append(as_text(title))
    lines.append("")

    if infracciones_hits:
        lines.append("=== INFRACCIONES DETECTADAS ===")
        counter: dict[str, int] = {}
        for h in infracciones_hits:
            k = (as_text(h.get("termino")) or "").strip().lower()
            if not k:
                continue
            counter[k] = counter.get(k, 0) + 1
        for termino, n in sorted(counter.items(), key=lambda x: (-x[1], x[0])):
            lines.append(f"  - {termino}: {n} ocurrencia(s)")
        lines.append("")
        lines.append("Detalle por timestamp:")
        for h in infracciones_hits:
            lines.append(
                f"  [{h.get('inicio','')} - {h.get('fin','')}] "
                f"{h.get('termino','')} — {h.get('texto','')}"
            )
        lines.append("")
    lines.append("=== TRANSCRIPCIÓN SEGMENTADA (TIMESTAMPS) ===")
    if segmented_items:
        for it in segmented_items:
            ln = as_text(it.get("line", "")).strip()
            if ln:
                lines.append(ln)
    else:
        lines.append("(Sin timestamps)")
    lines.append("")
    lines.append("=== TRANSCRIPCIÓN COMPLETA ===")
    lines.append(as_text(full_text).strip())

    try:
        txt_path.write_text("\n".join(lines), encoding="utf-8")
    except Exception:
        pass


def make_zip_bytes(resultados: list[dict], lote: dict | None, meta: dict) -> bytes:
    buf = io.BytesIO()
    ts = meta.get("generado") or dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    base_dir = f"transcripciones_{as_text(ts).replace(':','').replace(' ','_')}"

    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr(
            f"{base_dir}/meta.json",
            json.dumps(meta or {}, ensure_ascii=False, indent=2).encode("utf-8"),
        )

        if lote:
            for ext in ("txt", "xlsx", "docx"):
                p = lote.get(ext)
                if p and Path(p).exists():
                    z.write(str(p), arcname=f"{base_dir}/LOTE/{Path(p).name}")

        for r in resultados or []:
            arch = (as_text(r.get("archivo")) or "archivo").strip()
            safe_dir = Path(arch).stem or "archivo"
            for ext in ("txt", "xlsx", "docx"):
                p = r.get(ext)
                if p and Path(p).exists():
                    z.write(str(p), arcname=f"{base_dir}/IND/{safe_dir}/{Path(p).name}")

    return buf.getvalue()


def read_timestamp_lines_from_txt(txt_path: str) -> list[tuple[str, str, str]]:
    """
    Devuelve [(inicio, fin, texto), ...] leyendo líneas:
    [00:00:05 - 00:00:21] texto...
    """
    out: list[tuple[str, str, str]] = []
    p = Path(txt_path)
    try:
        lines = p.read_text(encoding="utf-8").splitlines()
    except Exception:
        return out

    import re

    for ln in lines:
        ln = ln.strip()
        if not ln.startswith("["):
            continue
        m = re.match(r"^\[(.+?)\s*-\s*(.+?)\]\s*(.*)$", ln)
        if not m:
            continue
        ini, fin, txt = m.group(1), m.group(2), m.group(3)
        out.append((ini, fin, txt))
    return out