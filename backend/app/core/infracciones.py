from __future__ import annotations

import re


def parse_infracciones_text(text: str) -> list[dict]:
    """
    Parse simple: lista separada por comas.
    Devuelve: [{"termino": "mayday"}, ...]
    """
    out: list[dict] = []
    vistos = set()

    for raw in (text or "").split(","):
        termino = raw.strip().lower()
        if not termino:
            continue
        if termino in vistos:
            continue
        vistos.add(termino)
        out.append({"termino": termino})

    return out

def detect_in_segments(filename: str, segments: list[dict], infracciones_cfg: list[dict], coincidencia_parcial: bool) -> list[dict]:
    """Detecta infracciones en una lista de segmentos"""
    hits = []
    for seg in segments:
        hits.extend(detectar_infracciones_en_texto(
            filename,
            seg.get('text', ''),
            seg.get('line', '').split(']')[0].replace('[', '').split('-')[0].strip() if 'line' in seg else str(seg.get('start', '')),
            seg.get('line', '').split(']')[0].replace('[', '').split('-')[1].strip() if 'line' in seg and '-' in seg['line'] else str(seg.get('end', '')),
            infracciones_cfg,
            coincidencia_parcial
        ))
    return hits

def detectar_infracciones_en_texto(
    archivo: str,
    texto: str,
    inicio: str,
    fin: str,
    infracciones_cfg: list[dict] | None,
    coincidencia_parcial: bool,
) -> list[dict]:
    """
    Detecta coincidencias de términos configurados dentro de un texto.
    Devuelve una lista de dicts con campos: archivo, termino, inicio, fin, texto.
    """
    if not texto or not infracciones_cfg:
        return []

    texto_l = texto.lower()
    halladas: list[dict] = []

    for item in infracciones_cfg:
        termino = str(item.get("termino", "")).strip().lower()
        if not termino:
            continue

        if coincidencia_parcial:
            ok = termino in texto_l
        else:
            ok = bool(re.search(rf"\b{re.escape(termino)}\b", texto, flags=re.IGNORECASE))

        if ok:
            halladas.append(
                {
                    "archivo": archivo,
                    "termino": termino,
                    "inicio": inicio,
                    "fin": fin,
                    "texto": texto,
                }
            )

    return halladas
