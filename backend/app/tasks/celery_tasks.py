from celery import Celery, Task
from pathlib import Path
import logging
from typing import List, Dict, Any
import shutil
import datetime as dt

from app.config import settings

logger = logging.getLogger(__name__)

# Crear app de Celery
celery_app = Celery(
    'enacom_transcriptor',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Argentina/Buenos_Aires',
    enable_utc=True,
    task_track_started=True,
    # Sin límite de tiempo — transcripciones largas pueden durar horas
    task_time_limit=None,
    task_soft_time_limit=None,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=10
)

_engine_cache: Dict[str, Any] = {}


def _get_engine(model_size: str):
    """Devuelve (o crea) el TranscriptionEngine para el model_size pedido."""
    if model_size not in _engine_cache:
        from app.core.transcription import TranscriptionEngine
        logger.info(f"Cargando engine para modelo '{model_size}'…")
        _engine_cache[model_size] = TranscriptionEngine(model_size=model_size)
    return _engine_cache[model_size]


# ─── Tarea base con soporte de progreso ───────────────────────────────────────

class CallbackTask(Task):
    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    def update_progress(self, progress: int, **extra_data):
        from app.api.websockets import broadcast_progress
        self.update_state(state='PROGRESS', meta={'progress': progress, **extra_data})
        broadcast_progress(self.request.id, {'progress': progress, **extra_data})


# ─── Tarea principal ──────────────────────────────────────────────────────────

@celery_app.task(bind=True, base=CallbackTask, name='process_transcription')
def process_transcription_task(
    self,
    task_id: str,
    audio_files: List[str],
    config: Dict[str, Any]
) -> Dict[str, Any]:
    from app.core import audio_processor, segmenter, exporters, infracciones
    from app.api.websockets import broadcast_completion, broadcast_error

    try:
        logger.info(f"Iniciando tarea {task_id} con {len(audio_files)} archivos")

        # ── Configuración ────────────────────────────────────────────────────
        referencia          = config.get('referencia', '')
        language            = config.get('language', 'es')
        if language == 'auto':
            language = None

        modo_lote           = config.get('modo_lote', 'individual')
        export_zip          = config.get('export_zip', True)
        infracciones_list   = config.get('infracciones', [])
        coincidencia_parcial= config.get('coincidencia_parcial', True)
        whisper_model_size  = config.get('whisper_model', settings.WHISPER_MODEL)

        infracciones_cfg = [{'termino': t} for t in infracciones_list]

        # ── Obtener engine según modelo elegido ──────────────────────────────
        engine = _get_engine(whisper_model_size)

        # ── Preparar directorios ─────────────────────────────────────────────
        resultados          = []
        files_info          = []
        infracciones_hits_all = []
        total_duration      = 0.0

        output_dir = settings.OUTPUTS_DIR / task_id
        output_dir.mkdir(parents=True, exist_ok=True)

        run_id = dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
        n_files = len(audio_files)

        # ── Procesar cada archivo ────────────────────────────────────────────
        for i, audio_path_str in enumerate(audio_files, start=1):
            audio_path = Path(audio_path_str)
            filename   = audio_path.name

            try:
                self.update_progress(
                    int((i - 1) / n_files * 100),
                    status='processing',
                    current_file=filename,
                    current_file_index=i,
                    total_files=n_files,
                    message=f'Procesando {filename}…'
                )
                logger.info(f"[{i}/{n_files}] Procesando {filename}")

                # 1. Duración
                duration = audio_processor.get_audio_duration(audio_path) or 0.0

                # 2. Split
                segments_dir   = output_dir / f'_segs_{audio_path.stem}'
                segment_paths  = audio_processor.split_audio(
                    audio_path, segments_dir, settings.SEGMENT_DURATION_SECONDS
                )

                # 3. Transcribir segmentos
                segments_acc = []
                text_parts   = []
                offset       = 0.0
                total_segs   = len(segment_paths)

                for j, seg_path in enumerate(segment_paths, start=1):
                    file_progress = ((i - 1) + (j / total_segs)) / n_files
                    self.update_progress(
                        int(file_progress * 100),
                        status='processing',
                        current_file=filename,
                        message=f'Segmento {j}/{total_segs}'
                    )

                    full_text, segs = engine.transcribe(seg_path, language=language)

                    if full_text:
                        text_parts.append(full_text)

                    for seg in segs:
                        seg['start'] += offset
                        seg['end']   += offset
                        segments_acc.append(seg)

                    seg_dur = audio_processor.get_audio_duration(seg_path)
                    offset += seg_dur if seg_dur else settings.SEGMENT_DURATION_SECONDS

                shutil.rmtree(segments_dir, ignore_errors=True)

                # 4. Ventanas fijas
                dur_final      = duration if duration > 0 else offset
                fixed_windows  = segmenter.build_fixed_windows(dur_final, settings.SEGMENT_DURATION_SECONDS)
                segmented_items= segmenter.merge_into_windows(fixed_windows, segments_acc)

                # 5. Texto completo
                full_text = segmenter.clean_text(" ".join(text_parts))

                # 6. Infracciones
                hits = infracciones.detect_in_segments(
                    filename, segmented_items, infracciones_cfg, coincidencia_parcial
                )
                infracciones_hits_all.extend(hits)

                # 7. Exportar
                base_name = f"{audio_path.stem}_{run_id}"
                out_txt   = output_dir / f"{base_name}.txt"
                out_xlsx  = output_dir / f"{base_name}.xlsx"
                out_docx  = output_dir / f"{base_name}.docx"

                exporters.write_txt(out_txt, filename, full_text, segmented_items, hits)
                exporters.write_xlsx(out_xlsx, segmented_items, hits)

                meta_word = {
                    'referencia':           referencia,
                    'generado':             run_id,
                    'model_size':           whisper_model_size,
                    'lang':                 language or 'auto',
                    'segment_duration':     settings.SEGMENT_DURATION_SECONDS,
                    'total_files':          1,
                    'total_duration_hhmmss': segmenter.format_duration(dur_final)
                }
                whisper_result = {'segments': segmented_items, 'text': full_text}
                exporters.write_docx(out_docx, filename, meta_word, whisper_result, hits)

                total_duration += dur_final

                # ── URL de audio para el frontend (reproducción / waveform) ──
                audio_url = f'/api/v1/audio/{task_id}/{filename}'

                resultados.append({
                    'archivo':          filename,
                    'duracion_hhmmss':  segmenter.format_duration(dur_final),
                    'audio_url':        audio_url,
                    'txt_url':          f'/api/v1/download/{task_id}/{out_txt.name}',
                    'xlsx_url':         f'/api/v1/download/{task_id}/{out_xlsx.name}',
                    'docx_url':         f'/api/v1/download/{task_id}/{out_docx.name}',
                    'infracciones':     [
                        {'archivo': h['archivo'], 'termino': h['termino'],
                         'inicio': h['inicio'], 'fin': h['fin'], 'texto': h['texto']}
                        for h in hits
                    ],
                    'segmentos': [
                        {'start': s['start'], 'end': s['end'],
                         'text': s['text'], 'line': s['line']}
                        for s in segmented_items
                    ],
                    'texto_completo': full_text
                })

                files_info.append({
                    'archivo':          filename,
                    'duracion_hhmmss':  segmenter.format_duration(dur_final),
                    'whisper_result':   whisper_result
                })

                logger.info(f"[{i}/{n_files}] {filename} completado")

            except Exception as e:
                logger.error(f"Error procesando {filename}: {str(e)}", exc_info=True)
                continue

        # ── Lote combinado ───────────────────────────────────────────────────
        lote_urls = {}
        if modo_lote == 'combinado' and len(resultados) > 1:
            self.update_progress(95, status='processing', message='Generando lote combinado…')

            lote_base = f"lote_{run_id}"
            lote_txt  = output_dir / f"{lote_base}.txt"
            lote_xlsx = output_dir / f"{lote_base}.xlsx"
            lote_docx = output_dir / f"{lote_base}.docx"

            exporters.write_combined_txt(lote_txt, resultados, referencia, run_id)
            exporters.write_combined_xlsx(lote_xlsx, files_info, infracciones_hits_all)

            meta_lote = {
                'referencia':           referencia,
                'generado':             run_id,
                'model_size':           whisper_model_size,
                'lang':                 language or 'auto',
                'segment_duration':     settings.SEGMENT_DURATION_SECONDS,
                'total_files':          len(audio_files),
                'total_duration_hhmmss': segmenter.format_duration(total_duration)
            }
            exporters.write_combined_docx(
                lote_docx, f"LOTE — {run_id}", meta_lote, files_info, infracciones_hits_all
            )

            lote_urls = {
                'lote_txt_url':  f'/api/v1/download/{task_id}/{lote_txt.name}',
                'lote_xlsx_url': f'/api/v1/download/{task_id}/{lote_xlsx.name}',
                'lote_docx_url': f'/api/v1/download/{task_id}/{lote_docx.name}'
            }

        # ── ZIP final ────────────────────────────────────────────────────────
        zip_url = None
        if export_zip:
            self.update_progress(98, status='processing', message='Generando ZIP…')
            zip_path = output_dir / f"corrida_{run_id}.zip"
            exporters.create_zip(zip_path, output_dir, resultados, lote_urls)
            zip_url = f'/api/v1/download/{task_id}/{zip_path.name}'

        # ── Resultado final ──────────────────────────────────────────────────
        result = {
            'task_id':                  task_id,
            'status':                   'completed',
            'created_at':               dt.datetime.now().isoformat(),
            'completed_at':             dt.datetime.now().isoformat(),
            'referencia':               referencia,
            'modo':                     modo_lote,
            'model_size':               whisper_model_size,
            'language':                 language or 'auto',
            'total_files':              len(audio_files),
            'total_duration_hhmmss':    segmenter.format_duration(total_duration),
            'infracciones_total':       len(infracciones_hits_all),
            'archivos_con_infracciones': len(set(h['archivo'] for h in infracciones_hits_all)),
            'resultados':               resultados,
            **lote_urls,
            'zip_url':                  zip_url
        }

        self.update_progress(100, status='completed', message='¡Transcripción completada!')
        broadcast_completion(task_id, result)
        logger.info(f"Tarea {task_id} completada exitosamente")
        return result

    except Exception as e:
        logger.error(f"Error en tarea {task_id}: {str(e)}", exc_info=True)
        broadcast_error(task_id, str(e))
        raise