"""
thread_tasks.py — Reemplazo de celery_tasks para modo standalone (PyInstaller).

Expone la misma interfaz que celery_tasks para que routes.py funcione sin cambios:
  - process_transcription_task.apply_async(args=[...], task_id=...)
  - celery_app.AsyncResult(task_id)
  - celery_app.control.revoke(task_id, terminate=True)

Sin Celery, sin Redis. Las tareas corren en ThreadPoolExecutor en el mismo proceso.
El SocketIO emite directamente (sin message_queue Redis).

NO usar en el flujo de desarrollo normal — solo para el exe standalone.
"""
from __future__ import annotations

import datetime as dt
import logging
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

# ── Estado de tareas en memoria (mismo proceso) ───────────────────
_task_states: Dict[str, Dict] = {}
_cancel_flags: Dict[str, threading.Event] = {}
_executor = ThreadPoolExecutor(max_workers=2)

# ── Engine cache (evita recargar el modelo entre tareas) ──────────
_engine_cache: Dict[str, Any] = {}

# ── Referencias inyectadas por run_standalone.py ──────────────────
# run_standalone hace:
#   import app.tasks.thread_tasks as _tt
#   _tt._SOCKETIO = socketio
#   _tt._FLASK_APP = app
_SOCKETIO = None
_FLASK_APP = None


# ─────────────────────────────────────────────────────────────────
# Emisores SocketIO con app context correcto desde threads
# ─────────────────────────────────────────────────────────────────

def _emit(event: str, data: dict, room: str):
    try:
        if _SOCKETIO is not None:
            # Flask-SocketIO threading mode: emitir directo sin app_context
            _SOCKETIO.emit(event, data, room=room, namespace='/')
        else:
            import app as app_pkg
            app_pkg.socketio.emit(event, data, room=room, namespace='/')
    except Exception as e:
        # WARNING para ver el error en consola del exe
        logger.warning(f"[thread_tasks] emit '{event}' room={room} failed: {e}")


def _emit_progress(task_id: str, data: dict):
    _emit('task_progress', {'task_id': task_id, **data}, room=task_id)


def _emit_completion(task_id: str, data: dict):
    _emit('task_completed', {'task_id': task_id, **data}, room=task_id)


def _emit_error(task_id: str, error: str):
    _emit('task_error', {'task_id': task_id, 'error': error}, room=task_id)


# ─────────────────────────────────────────────────────────────────
# Mock AsyncResult — misma interfaz que Celery
# ─────────────────────────────────────────────────────────────────

class _AsyncResult:
    def __init__(self, task_id: str):
        self.id = task_id

    @property
    def state(self) -> str:
        s = _task_states.get(self.id, {}).get('status', 'pending')
        return {
            'pending':    'PENDING',
            'processing': 'PROGRESS',
            'completed':  'SUCCESS',
            'failed':     'FAILURE',
            'cancelled':  'FAILURE',
        }.get(s, 'PENDING')

    @property
    def info(self):
        state = _task_states.get(self.id, {})
        st = self.state
        if st == 'SUCCESS':
            return state.get('result')
        if st == 'PROGRESS':
            return {
                'progress':           state.get('progress', 0),
                'status':             'processing',
                'message':            state.get('message', ''),
                'current_file':       state.get('current_file'),
                'current_file_index': state.get('current_file_index', 0),
                'total_files':        state.get('total_files', 0),
            }
        if st == 'FAILURE':
            return Exception(state.get('error', 'Error desconocido'))
        return None


# ─────────────────────────────────────────────────────────────────
# Mock control / inspect — misma interfaz que Celery
# ─────────────────────────────────────────────────────────────────

class _Control:
    def revoke(self, task_id: str, terminate: bool = False):
        flag = _cancel_flags.get(task_id)
        if flag:
            flag.set()
        if task_id in _task_states:
            _task_states[task_id]['status'] = 'cancelled'

    def inspect(self):
        return _Inspect()


class _Inspect:
    def active(self):
        return {}


# ─────────────────────────────────────────────────────────────────
# Mock Celery app — misma interfaz que celery_app en celery_tasks
# ─────────────────────────────────────────────────────────────────

class _CeleryApp:
    def __init__(self):
        self.control = _Control()

    def AsyncResult(self, task_id: str) -> _AsyncResult:
        return _AsyncResult(task_id)


celery_app = _CeleryApp()


# ─────────────────────────────────────────────────────────────────
# Mock Task con apply_async — misma interfaz que @celery_app.task
# ─────────────────────────────────────────────────────────────────

class _Task:
    def __init__(self, func):
        self._func = func

    def apply_async(self, args=None, task_id: str = None, **kwargs) -> _AsyncResult:
        # args ya contiene [task_id, audio_files, config] — NO agregar task_id de nuevo
        args = args or []
        _task_states[task_id] = {'status': 'pending', 'progress': 0}
        _cancel_flags[task_id] = threading.Event()
        future = _executor.submit(self._func, *args)
        # Capturar excepcion del thread para que no muera silencioso
        def _on_done(f):
            exc = f.exception()
            if exc:
                import traceback
                logger.error(f"[standalone] Tarea {task_id} fallo en thread: {exc}")
                logger.error(traceback.format_exc())
                _task_states[task_id] = {'status': 'failed', 'error': str(exc)}
        future.add_done_callback(_on_done)
        return _AsyncResult(task_id)


# ─────────────────────────────────────────────────────────────────
# Lógica de transcripción
# Replica celery_tasks._process_transcription_task sin decoradores Celery
# ─────────────────────────────────────────────────────────────────

def _run_transcription(task_id: str, audio_files: list, config: dict):
    from app.core import audio_processor, segmenter, exporters
    from app.core import infracciones as inf_module
    from app.config import settings
    from app.core.transcription import TranscriptionEngine

    cancel = _cancel_flags.get(task_id, threading.Event())

    def update(progress: int, **extra):
        _task_states[task_id].update({'progress': progress, **extra})
        logger.info(f"[standalone] task={task_id[:8]} progress={progress}% {extra.get('message','')}")
        _emit_progress(task_id, {'progress': progress, **extra})

    try:
        _task_states[task_id]['status'] = 'processing'

        referencia        = config.get('referencia', '')
        language          = config.get('language', 'es')
        if hasattr(language, 'value'):
            language = language.value
        if language == 'auto':
            language = None
        modo_lote         = config.get('modo_lote', 'individual')
        export_zip        = config.get('export_zip', True)
        infracciones_list = config.get('infracciones', [])
        coincidencia_parc = config.get('coincidencia_parcial', True)
        # config puede llegar con el enum sin deserializar (WhisperModelEnum.LARGE_V3)
        # extraemos el .value si es necesario
        _raw_model = config.get('whisper_model', settings.WHISPER_MODEL)
        model_size = _raw_model.value if hasattr(_raw_model, 'value') else str(_raw_model)
        infracciones_cfg  = [{'termino': t} for t in infracciones_list]

        # Engine cache — no recargar el modelo entre tareas
        if model_size not in _engine_cache:
            logger.info(f"[standalone] Cargando engine '{model_size}'...")
            _engine_cache[model_size] = TranscriptionEngine(model_size=model_size)
        engine = _engine_cache[model_size]

        resultados: list = []
        files_info: list = []
        all_hits: list   = []
        total_dur        = 0.0

        output_dir = settings.OUTPUTS_DIR / task_id
        output_dir.mkdir(parents=True, exist_ok=True)
        run_id  = dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
        n_files = len(audio_files)

        for i, path_str in enumerate(audio_files, start=1):
            if cancel.is_set():
                break
            audio_path = Path(path_str)
            filename   = audio_path.name

            try:
                update(
                    int((i - 1) / n_files * 100),
                    status='processing',
                    current_file=filename,
                    current_file_index=i,
                    total_files=n_files,
                    message=f'Procesando {filename}...'
                )

                duration  = audio_processor.get_audio_duration(audio_path) or 0.0
                segs_dir  = output_dir / f'_segs_{audio_path.stem}'
                seg_paths = audio_processor.split_audio(
                    audio_path, segs_dir, settings.SEGMENT_DURATION_SECONDS
                )

                segs_acc: list  = []
                text_parts: list = []
                offset           = 0.0

                for j, sp in enumerate(seg_paths, start=1):
                    if cancel.is_set():
                        break
                    update(
                        int(((i - 1) + j / len(seg_paths)) / n_files * 100),
                        status='processing',
                        current_file=filename,
                        message=f'Segmento {j}/{len(seg_paths)}'
                    )
                    ft, segs = engine.transcribe(sp, language=language)
                    if ft:
                        text_parts.append(ft)
                    for s in segs:
                        s['start'] += offset
                        s['end']   += offset
                        segs_acc.append(s)
                    sd = audio_processor.get_audio_duration(sp)
                    offset += sd if sd else settings.SEGMENT_DURATION_SECONDS

                shutil.rmtree(segs_dir, ignore_errors=True)

                dur_final     = duration if duration > 0 else offset
                fixed_windows = segmenter.build_fixed_windows(dur_final, settings.SEGMENT_DURATION_SECONDS)
                segmented     = segmenter.merge_into_windows(fixed_windows, segs_acc)
                full_text     = segmenter.clean_text(" ".join(text_parts))

                hits = inf_module.detect_in_segments(
                    filename, segmented, infracciones_cfg, coincidencia_parc
                )
                all_hits.extend(hits)

                base     = f"{audio_path.stem}_{run_id}"
                out_txt  = output_dir / f"{base}.txt"
                out_xlsx = output_dir / f"{base}.xlsx"
                out_docx = output_dir / f"{base}.docx"

                exporters.write_txt(out_txt, filename, full_text, segmented, hits)
                exporters.write_xlsx(out_xlsx, segmented, hits)
                meta_w = {
                    'referencia': referencia, 'generado': run_id,
                    'model_size': model_size, 'lang': language or 'auto',
                    'segment_duration': settings.SEGMENT_DURATION_SECONDS,
                    'total_files': 1,
                    'total_duration_hhmmss': segmenter.format_duration(dur_final),
                }
                wr = {'segments': segmented, 'text': full_text}
                exporters.write_docx(out_docx, filename, meta_w, wr, hits)

                total_dur += dur_final

                resultados.append({
                    'archivo':          filename,
                    'duracion_hhmmss':  segmenter.format_duration(dur_final),
                    'audio_url':        f'/api/v1/audio/{task_id}/{filename}',
                    'txt_url':          f'/api/v1/download/{task_id}/{out_txt.name}',
                    'xlsx_url':         f'/api/v1/download/{task_id}/{out_xlsx.name}',
                    'docx_url':         f'/api/v1/download/{task_id}/{out_docx.name}',
                    'infracciones': [
                        {'archivo': h['archivo'], 'termino': h['termino'],
                         'inicio': h['inicio'], 'fin': h['fin'], 'texto': h['texto']}
                        for h in hits
                    ],
                    'segmentos': [
                        {'start': s['start'], 'end': s['end'],
                         'text': s['text'], 'line': s['line']}
                        for s in segmented
                    ],
                    'texto_completo': full_text,
                })
                files_info.append({
                    'archivo':         filename,
                    'duracion_hhmmss': segmenter.format_duration(dur_final),
                    'whisper_result':  wr,
                })

            except Exception as e:
                logger.error(f"[standalone] Error en {filename}: {e}", exc_info=True)
                continue

        # ── Lote combinado ────────────────────────────────────────
        lote_urls: dict = {}
        if modo_lote == 'combinado' and len(resultados) > 1:
            update(95, status='processing', message='Generando lote combinado...')
            lb        = f"lote_{run_id}"
            lote_txt  = output_dir / f"{lb}.txt"
            lote_xlsx = output_dir / f"{lb}.xlsx"
            lote_docx = output_dir / f"{lb}.docx"
            exporters.write_combined_txt(lote_txt, resultados, referencia, run_id)
            exporters.write_combined_xlsx(lote_xlsx, files_info, all_hits)
            meta_l = {
                'referencia': referencia, 'generado': run_id,
                'model_size': model_size, 'lang': language or 'auto',
                'segment_duration': settings.SEGMENT_DURATION_SECONDS,
                'total_files': len(audio_files),
                'total_duration_hhmmss': segmenter.format_duration(total_dur),
            }
            exporters.write_combined_docx(
                lote_docx, f"LOTE - {run_id}", meta_l, files_info, all_hits
            )
            lote_urls = {
                'lote_txt_url':  f'/api/v1/download/{task_id}/{lote_txt.name}',
                'lote_xlsx_url': f'/api/v1/download/{task_id}/{lote_xlsx.name}',
                'lote_docx_url': f'/api/v1/download/{task_id}/{lote_docx.name}',
            }

        # ── ZIP ───────────────────────────────────────────────────
        zip_url = None
        if export_zip:
            update(98, status='processing', message='Generando ZIP...')
            zip_path = output_dir / f"corrida_{run_id}.zip"
            exporters.create_zip(zip_path, output_dir, resultados, lote_urls)
            zip_url = f'/api/v1/download/{task_id}/{zip_path.name}'

        result = {
            'task_id':    task_id,
            'status':     'completed',
            'created_at': dt.datetime.now().isoformat(),
            'completed_at': dt.datetime.now().isoformat(),
            'referencia': referencia,
            'modo':       modo_lote,
            'model_size': model_size,
            'language':   language or 'auto',
            'total_files': len(audio_files),
            'total_duration_hhmmss': segmenter.format_duration(total_dur),
            'infracciones_total': len(all_hits),
            'archivos_con_infracciones': len(set(h['archivo'] for h in all_hits)),
            'resultados': resultados,
            **lote_urls,
            'zip_url': zip_url,
        }

        _task_states[task_id] = {'status': 'completed', 'progress': 100, 'result': result}
        update(100, status='completed', message='Transcripcion completada!')
        _emit_completion(task_id, result)
        return result

    except Exception as e:
        logger.error(f"[standalone] Error tarea {task_id}: {e}", exc_info=True)
        _task_states[task_id] = {'status': 'failed', 'error': str(e)}
        _emit_error(task_id, str(e))
        raise


process_transcription_task = _Task(_run_transcription)