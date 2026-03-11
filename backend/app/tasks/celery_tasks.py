
from celery import Celery, Task
from pathlib import Path
import logging
from typing import List, Dict, Any
import shutil
import datetime as dt

from app.core.audio_processor import ffprobe_duration_seconds, split_audio_to_wavs
from app.core.segmenter import (
    build_fixed_windows_from_duration,
    merge_text_into_fixed_windows,
    clean_boilerplate
)
from app.core.exporters import (
    generar_informe_word,
    ensure_excel_file,
    append_to_excel,
    write_infracciones_excel
)
from app.core.infracciones import detectar_infracciones_en_texto
from app.core.writers import write_txt, make_zip_bytes
from app.core.utils import safe_stem, fmt_hhmmss, as_text
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
    task_time_limit=settings.TASK_TIMEOUT_SECONDS,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=10
)


class CallbackTask(Task):
    """
    Clase base para tasks que emiten progreso vía WebSocket
    """
    
    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)
    
    def update_progress(self, progress: int, **extra_data):
        """
        Actualiza el progreso y lo broadcast vía SocketIO
        """
        from app.api.websockets import broadcast_progress
        
        self.update_state(
            state='PROGRESS',
            meta={'progress': progress, **extra_data}
        )
        
        broadcast_progress(self.request.id, {'progress': progress, **extra_data})


@celery_app.task(bind=True, base=CallbackTask, name='process_transcription')
def process_transcription_task(
    self,
    task_id: str,
    audio_files: List[str],
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Tarea principal de transcripción
    
    Args:
        task_id: ID único de la tarea
        audio_files: Lista de paths a los archivos de audio
        config: Configuración (TranscriptionRequest serializado)
    
    Returns:
        Dict con resultados completos
    """
    from app.core.transcription import transcription_engine
    from app.core import audio_processor, segmenter, exporters, infracciones
    from app.api.websockets import broadcast_completion, broadcast_error
    
    try:
        logger.info(f"Iniciando tarea {task_id} con {len(audio_files)} archivos")
        
        # Configuración
        referencia = config.get('referencia', '')
        language = config.get('language', 'es')
        if language == 'auto':
            language = None
        
        modo_lote = config.get('modo_lote', 'individual')
        export_zip = config.get('export_zip', True)
        infracciones_list = config.get('infracciones', [])
        coincidencia_parcial = config.get('coincidencia_parcial', True)
        
        # Preparar infracciones
        infracciones_cfg = [{'termino': t} for t in infracciones_list]
        
        # Resultados
        resultados = []
        files_info = []
        infracciones_hits_all = []
        total_duration = 0.0
        
        # Directorios
        output_dir = settings.OUTPUTS_DIR / task_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        run_id = dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
        
        # Procesar cada archivo
        n_files = len(audio_files)
        
        for i, audio_path_str in enumerate(audio_files, start=1):
            audio_path = Path(audio_path_str)
            filename = audio_path.name
            
            try:
                self.update_progress(
                    int((i - 1) / n_files * 100),
                    status='processing',
                    current_file=filename,
                    current_file_index=i,
                    total_files=n_files,
                    message=f'Procesando {filename}...'
                )
                
                logger.info(f"[{i}/{n_files}] Procesando {filename}")
                
                # 1. Obtener duración
                duration = audio_processor.get_audio_duration(audio_path)
                if not duration:
                    duration = 0.0
                
                # 2. Split en segmentos
                segments_dir = output_dir / f'_segs_{audio_path.stem}'
                segment_paths = audio_processor.split_audio(
                    audio_path,
                    segments_dir,
                    settings.SEGMENT_DURATION_SECONDS
                )
                
                # 3. Transcribir segmentos
                segments_acc = []
                text_parts = []
                offset = 0.0
                
                total_segments = len(segment_paths)
                
                for j, seg_path in enumerate(segment_paths, start=1):
                    # Actualizar progreso
                    file_progress = ((i - 1) + (j / total_segments)) / n_files
                    self.update_progress(
                        int(file_progress * 100),
                        status='processing',
                        current_file=filename,
                        message=f'Segmento {j}/{total_segments}'
                    )
                    
                    # Transcribir
                    full_text, segs = transcription_engine.transcribe(
                        seg_path,
                        language=language
                    )
                    
                    if full_text:
                        text_parts.append(full_text)
                    
                    # Ajustar timestamps con offset
                    for seg in segs:
                        seg['start'] += offset
                        seg['end'] += offset
                        segments_acc.append(seg)
                    
                    # Actualizar offset con duración real del segmento
                    seg_duration = audio_processor.get_audio_duration(seg_path)
                    offset += seg_duration if seg_duration else settings.SEGMENT_DURATION_SECONDS
                
                # Limpiar segmentos temporales
                shutil.rmtree(segments_dir, ignore_errors=True)
                
                # 4. Construir ventanas fijas
                dur_final = duration if duration > 0 else offset
                fixed_windows = segmenter.build_fixed_windows(dur_final, settings.SEGMENT_DURATION_SECONDS)
                segmented_items = segmenter.merge_into_windows(fixed_windows, segments_acc)
                
                # 5. Texto completo
                full_raw = " ".join(text_parts)
                full_text = segmenter.clean_text(full_raw)
                
                # 6. Detectar infracciones
                hits = infracciones.detect_in_segments(
                    filename,
                    segmented_items,
                    infracciones_cfg,
                    coincidencia_parcial
                )
                infracciones_hits_all.extend(hits)
                
                # 7. Exportar
                base_name = f"{audio_path.stem}_{run_id}"
                out_txt = output_dir / f"{base_name}.txt"
                out_xlsx = output_dir / f"{base_name}.xlsx"
                out_docx = output_dir / f"{base_name}.docx"
                
                # TXT
                exporters.write_txt(out_txt, filename, full_text, segmented_items, hits)
                
                # XLSX
                exporters.write_xlsx(out_xlsx, segmented_items, hits)
                
                # DOCX
                meta_word = {
                    'referencia': referencia,
                    'generado': run_id,
                    'model_size': settings.WHISPER_MODEL,
                    'lang': language or 'auto',
                    'segment_duration': settings.SEGMENT_DURATION_SECONDS,
                    'total_files': 1,
                    'total_duration_hhmmss': segmenter.format_duration(dur_final)
                }
                
                whisper_result = {
                    'segments': segmented_items,
                    'text': full_text
                }
                
                exporters.write_docx(
                    out_docx,
                    filename,
                    meta_word,
                    whisper_result,
                    hits
                )
                
                # Guardar en resultados
                total_duration += dur_final
                
                resultados.append({
                    'archivo': filename,
                    'duracion_hhmmss': segmenter.format_duration(dur_final),
                    'txt_url': f'/api/v1/download/{task_id}/{out_txt.name}',
                    'xlsx_url': f'/api/v1/download/{task_id}/{out_xlsx.name}',
                    'docx_url': f'/api/v1/download/{task_id}/{out_docx.name}',
                    'infracciones': [
                        {
                            'archivo': h['archivo'],
                            'termino': h['termino'],
                            'inicio': h['inicio'],
                            'fin': h['fin'],
                            'texto': h['texto']
                        }
                        for h in hits
                    ],
                    'segmentos': [
                        {
                            'start': s['start'],
                            'end': s['end'],
                            'text': s['text'],
                            'line': s['line']
                        }
                        for s in segmented_items
                    ],
                    'texto_completo': full_text
                })
                
                files_info.append({
                    'archivo': filename,
                    'duracion_hhmmss': segmenter.format_duration(dur_final),
                    'whisper_result': whisper_result
                })
                
                logger.info(f"[{i}/{n_files}] {filename} completado")
                
            except Exception as e:
                logger.error(f"Error procesando {filename}: {str(e)}", exc_info=True)
                # Continuar con el siguiente archivo
                continue
        
        # Lote combinado (si corresponde)
        lote_urls = {}
        if modo_lote == 'combinado' and len(resultados) > 1:
            self.update_progress(95, status='processing', message='Generando lote combinado...')
            
            lote_base = f"lote_{run_id}"
            lote_txt = output_dir / f"{lote_base}.txt"
            lote_xlsx = output_dir / f"{lote_base}.xlsx"
            lote_docx = output_dir / f"{lote_base}.docx"
            
            # TXT combinado
            exporters.write_combined_txt(lote_txt, resultados, referencia, run_id)
            
            # XLSX combinado
            exporters.write_combined_xlsx(lote_xlsx, files_info, infracciones_hits_all)
            
            # DOCX combinado
            meta_lote = {
                'referencia': referencia,
                'generado': run_id,
                'model_size': settings.WHISPER_MODEL,
                'lang': language or 'auto',
                'segment_duration': settings.SEGMENT_DURATION_SECONDS,
                'total_files': len(audio_files),
                'total_duration_hhmmss': segmenter.format_duration(total_duration)
            }
            
            exporters.write_combined_docx(
                lote_docx,
                f"LOTE — {run_id}",
                meta_lote,
                files_info,
                infracciones_hits_all
            )
            
            lote_urls = {
                'lote_txt_url': f'/api/v1/download/{task_id}/{lote_txt.name}',
                'lote_xlsx_url': f'/api/v1/download/{task_id}/{lote_xlsx.name}',
                'lote_docx_url': f'/api/v1/download/{task_id}/{lote_docx.name}'
            }
        
        # ZIP final
        zip_url = None
        if export_zip:
            self.update_progress(98, status='processing', message='Generando ZIP...')
            
            zip_path = output_dir / f"corrida_{run_id}.zip"
            exporters.create_zip(zip_path, output_dir, resultados, lote_urls)
            zip_url = f'/api/v1/download/{task_id}/{zip_path.name}'
        
        # Resultado final
        result = {
            'task_id': task_id,
            'status': 'completed',
            'created_at': dt.datetime.now().isoformat(),
            'completed_at': dt.datetime.now().isoformat(),
            'referencia': referencia,
            'modo': modo_lote,
            'model_size': settings.WHISPER_MODEL,
            'language': language or 'auto',
            'total_files': len(audio_files),
            'total_duration_hhmmss': segmenter.format_duration(total_duration),
            'infracciones_total': len(infracciones_hits_all),
            'archivos_con_infracciones': len(set(h['archivo'] for h in infracciones_hits_all)),
            'resultados': resultados,
            **lote_urls,
            'zip_url': zip_url
        }
        
        # Broadcast completion
        self.update_progress(100, status='completed', message='¡Transcripción completada!')
        broadcast_completion(task_id, result)
        
        logger.info(f"Tarea {task_id} completada exitosamente")
        
        return result
        
    except Exception as e:
        logger.error(f"Error en tarea {task_id}: {str(e)}", exc_info=True)
        broadcast_error(task_id, str(e))
        raise
