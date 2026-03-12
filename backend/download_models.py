"""
ENACOM Transcriptor — Descarga de modelos Whisper
==================================================

Uso:
    python download_models.py               # descarga medium (por defecto)
    python download_models.py --large       # descarga large-v3 también
    python download_models.py --only-large  # descarga solo large-v3
"""

import sys
import os
import argparse
import time
from pathlib import Path

# ── Colores ANSI para Windows (si ANSICON o Windows Terminal) ─────────────────
def c(code, text): return f"\033[{code}m{text}\033[0m"
BLUE  = lambda t: c("94", t)
GREEN = lambda t: c("92", t)
AMBER = lambda t: c("93", t)
RED   = lambda t: c("91", t)
BOLD  = lambda t: c("1",  t)
DIM   = lambda t: c("2",  t)

# Habilitar colores en Windows
os.system("")

# ─────────────────────────────────────────────────────────────────────────────

MODELS = {
    "medium": {
        "repo_id":    "Systran/faster-whisper-medium",
        "size_gb":    1.5,
        "label":      "Medium (~1.5 GB) — Recomendado para uso diario",
        "files":      ["model.bin", "config.json", "tokenizer.json",
                       "vocabulary.txt", "preprocessor_config.json"],
    },
    "large-v3": {
        "repo_id":    "Systran/faster-whisper-large-v3",
        "size_gb":    3.1,
        "label":      "Large v3 (~3.1 GB) — Máxima precisión",
        "files":      ["model.bin", "config.json", "tokenizer.json",
                       "vocabulary.txt", "preprocessor_config.json"],
    },
}


def get_cache_dir() -> Path:
    """Devuelve el directorio de cache de HuggingFace."""
    hf_home = os.environ.get("HF_HOME") or os.environ.get("HUGGINGFACE_HUB_CACHE")
    if hf_home:
        return Path(hf_home)
    return Path.home() / ".cache" / "huggingface" / "hub"


def is_model_cached(repo_id: str, cache_dir: Path) -> bool:
    """Verifica si el model.bin ya está descargado y completo."""
    # HuggingFace guarda como models--Org--Name
    folder_name = "models--" + repo_id.replace("/", "--")
    model_dir = cache_dir / folder_name

    if not model_dir.exists():
        return False

    # Buscar model.bin en blobs (forma en que HF cachea)
    blobs = list(model_dir.glob("blobs/*"))
    # model.bin pesa más de 500 MB — si hay un blob grande, está descargado
    for blob in blobs:
        if blob.stat().st_size > 500 * 1024 * 1024:
            return True

    return False


def format_size(bytes_val: float) -> str:
    if bytes_val >= 1024**3:
        return f"{bytes_val / 1024**3:.2f} GB"
    elif bytes_val >= 1024**2:
        return f"{bytes_val / 1024**2:.1f} MB"
    else:
        return f"{bytes_val / 1024:.1f} KB"


def progress_callback(current: int, total: int, start_time: float, filename: str):
    """Callback de progreso para mostrar avance en tiempo real."""
    if total <= 0:
        return

    elapsed = time.time() - start_time
    pct = current / total * 100
    filled = int(pct / 2)
    bar = "█" * filled + "░" * (50 - filled)

    speed = current / elapsed if elapsed > 0 else 0
    remaining = (total - current) / speed if speed > 0 else 0

    remaining_str = (
        f"{int(remaining // 60)}m {int(remaining % 60)}s"
        if remaining < 3600
        else f"{int(remaining // 3600)}h {int((remaining % 3600) // 60)}m"
    )

    print(
        f"\r  [{BLUE(bar)}] "
        f"{BOLD(f'{pct:.1f}%')} "
        f"{DIM(format_size(current))} / {DIM(format_size(total))} "
        f"— {DIM(format_size(speed) + '/s')} "
        f"— ETA {AMBER(remaining_str)}   ",
        end="",
        flush=True,
    )


def download_model(model_key: str, cache_dir: Path) -> bool:
    """
    Descarga un modelo con progreso y soporte de reanudación.
    Retorna True si exitoso.
    """
    info    = MODELS[model_key]
    repo_id = info["repo_id"]

    print(f"\n{BOLD('▶ Descargando:')} {info['label']}")
    print(f"  {DIM('Repo:')} {repo_id}")
    print(f"  {DIM('Cache:')} {cache_dir}\n")

    try:
        from huggingface_hub import snapshot_download
        from huggingface_hub import HfApi
        import huggingface_hub

        # Verificar versión para saber si soporta progress_callback
        hf_version = tuple(int(x) for x in huggingface_hub.__version__.split(".")[:2])

        start_time = time.time()

        print(f"  {DIM('Conectando con HuggingFace...')}")

        # snapshot_download maneja reanudación automáticamente:
        # los archivos incompletos quedan como .incomplete y se retoman
        local_dir = snapshot_download(
            repo_id=repo_id,
            cache_dir=str(cache_dir),
            ignore_patterns=["*.msgpack", "*.h5", "flax_model*", "tf_model*", "rust_model*"],
        )

        elapsed = time.time() - start_time
        print(f"\n\n  {GREEN('✓ Descarga completada')} en {elapsed/60:.1f} minutos")
        print(f"  {DIM('Guardado en:')} {local_dir}\n")
        return True

    except KeyboardInterrupt:
        print(f"\n\n  {AMBER('⚠ Descarga interrumpida por el usuario.')}")
        print(f"  {DIM('Podés reanudarla ejecutando este script nuevamente.')}")
        print(f"  {DIM('El progreso ya descargado NO se pierde.')}\n")
        return False

    except Exception as e:
        print(f"\n\n  {RED('✗ Error durante la descarga:')}")
        print(f"  {RED(str(e))}\n")

        if "ConnectionError" in str(type(e).__name__) or "timeout" in str(e).lower():
            print(f"  {AMBER('→ Problema de conectividad. Intentá de nuevo más tarde.')}")
            print(f"  {DIM('El progreso parcial se conserva para reanudar.')}\n")
        elif "401" in str(e) or "403" in str(e):
            print(f"  {AMBER('→ Error de autenticación. El modelo puede requerir token HF.')}\n")
        else:
            print(f"  {AMBER('→ Ejecutá el script nuevamente para reintentar.')}\n")

        return False


def check_disk_space(required_gb: float) -> bool:
    """Verifica que haya espacio suficiente en disco."""
    import shutil
    cache_drive = Path.home().drive + "\\" if sys.platform == "win32" else "/"
    try:
        free = shutil.disk_usage(cache_drive).free
        free_gb = free / 1024**3
        if free_gb < required_gb + 1:  # +1 GB de margen
            print(f"  {RED(f'✗ Espacio insuficiente: {free_gb:.1f} GB libres, se necesitan {required_gb + 1:.1f} GB')}")
            return False
        print(f"  {DIM(f'Espacio disponible: {free_gb:.1f} GB  ✓')}")
        return True
    except Exception:
        return True  # Si no podemos verificar, continuamos


def main():
    parser = argparse.ArgumentParser(
        description="Descarga modelos Whisper para ENACOM Transcriptor"
    )
    parser.add_argument("--large",      action="store_true", help="Descargar también large-v3")
    parser.add_argument("--only-large", action="store_true", help="Descargar solo large-v3")
    parser.add_argument("--check",      action="store_true", help="Solo verificar qué modelos están descargados")
    args = parser.parse_args()

    # ── Banner ────────────────────────────────────────────────────────────────
    print()
    print(BOLD(BLUE("═" * 60)))
    print(BOLD(BLUE("  ENACOM Transcriptor — Descarga de modelos Whisper")))
    print(BOLD(BLUE("═" * 60)))
    print()

    cache_dir = get_cache_dir()
    print(f"  {DIM('Directorio de cache:')} {cache_dir}")
    print()

    # ── Determinar qué descargar ──────────────────────────────────────────────
    if args.only_large:
        to_download = ["large-v3"]
    elif args.large:
        to_download = ["medium", "large-v3"]
    else:
        to_download = ["medium"]

    # ── Estado actual ─────────────────────────────────────────────────────────
    print(BOLD("  Estado de modelos:"))
    for key, info in MODELS.items():
        cached = is_model_cached(info["repo_id"], cache_dir)
        status = GREEN("✓ Descargado") if cached else DIM("✗ No descargado")
        print(f"    {status}  {info['label']}")
    print()

    if args.check:
        return

    # ── Descargar ─────────────────────────────────────────────────────────────
    pending = [k for k in to_download if not is_model_cached(MODELS[k]["repo_id"], cache_dir)]

    if not pending:
        print(GREEN("  ✓ Todos los modelos solicitados ya están descargados."))
        print(DIM("  No se requiere hacer nada más.\n"))
        return

    total_gb = sum(MODELS[k]["size_gb"] for k in pending)
    print(f"  {BOLD('Modelos a descargar:')} {len(pending)}")
    print(f"  {BOLD('Tamaño total aprox:')} {total_gb:.1f} GB")
    print()

    # Verificar espacio
    if not check_disk_space(total_gb):
        sys.exit(1)

    print()
    print(f"  {AMBER('IMPORTANTE:')} No cierres esta ventana durante la descarga.")
    print(f"  {DIM('Si se interrumpe, ejecutá el script nuevamente — retoma desde donde quedó.')}")
    print()

    success_all = True
    for key in pending:
        ok = download_model(key, cache_dir)
        if not ok:
            success_all = False
            break  # No intentar el siguiente si hubo error grave

    # ── Resumen final ─────────────────────────────────────────────────────────
    print(BOLD(BLUE("═" * 60)))
    if success_all:
        print(GREEN(BOLD("  ✓ Descarga completada exitosamente.")))
        print(DIM("  Ya podés iniciar ENACOM Transcriptor con start.bat"))
    else:
        remaining = [k for k in pending if not is_model_cached(MODELS[k]["repo_id"], cache_dir)]
        if remaining:
            print(AMBER(BOLD("  ⚠ Descarga incompleta.")))
            print(DIM("  Ejecutá este script nuevamente para retomar."))
        else:
            print(GREEN(BOLD("  ✓ Modelos descargados correctamente.")))
    print(BOLD(BLUE("═" * 60)))
    print()


if __name__ == "__main__":
    main()