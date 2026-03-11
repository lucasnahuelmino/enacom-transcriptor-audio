"""
API REST Endpoints
"""
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from pathlib import Path
import logging
from typing import List
import uuid

from app.config import settings
from app.models.schemas import (
    TranscriptionRequest,
    TranscriptionResultResponse,
    TaskStatusEnum,
    HistoryItemResponse
)
from app.tasks.celery_tasks import process_transcription_task

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)


@api_bp.route('/transcription/upload', methods=['POST'])
def upload_files():
    """
    Endpoint para subir archivos de audio y iniciar transcripción
    
    Form data:
        - files: List[File] - Archivos de audio
        - config: JSON - Configuración (TranscriptionRequest)
    """
    try:
        # Validar archivos
        if 'files' not in request.files:
            return jsonify({'error': 'No se enviaron archivos'}), 400
        
        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            return jsonify({'error': 'No se seleccionaron archivos'}), 400
        
        # Validar configuración
        try:
            config_json = request.form.get('config', '{}')
            import json
            config_dict = json.loads(config_json)
            config = TranscriptionRequest(**config_dict)
        except Exception as e:
            return jsonify({'error': f'Configuración inválida: {str(e)}'}), 400
        
        # Crear directorio para esta tarea
        task_id = str(uuid.uuid4())
        task_dir = settings.UPLOADS_DIR / task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        
        # Guardar archivos
        saved_files = []
        total_size = 0
        
        for file in files:
            # Validar extensión
            ext = Path(file.filename).suffix.lstrip('.').lower()
            if ext not in settings.SUPPORTED_FORMATS:
                return jsonify({
                    'error': f'Formato {ext} no soportado. Formatos válidos: {", ".join(settings.SUPPORTED_FORMATS)}'
                }), 400
            
            # Validar tamaño
            file.seek(0, 2)  # Ir al final
            file_size = file.tell()
            file.seek(0)  # Volver al inicio
            
            if file_size > settings.MAX_AUDIO_SIZE_MB * 1024 * 1024:
                return jsonify({
                    'error': f'{file.filename} excede el límite de {settings.MAX_AUDIO_SIZE_MB}MB'
                }), 400
            
            total_size += file_size
            
            # Guardar archivo
            filename = secure_filename(file.filename)
            filepath = task_dir / filename
            file.save(str(filepath))
            saved_files.append(str(filepath))
            
            logger.info(f"Archivo guardado: {filename} ({file_size / 1024 / 1024:.2f}MB)")
        
        logger.info(
            f"Task {task_id}: {len(saved_files)} archivos guardados "
            f"({total_size / 1024 / 1024:.2f}MB total)"
        )
        
        # Encolar tarea de Celery
        task = process_transcription_task.apply_async(
            args=[task_id, saved_files, config.model_dump()],
            task_id=task_id
        )
        
        return jsonify({
            'task_id': task_id,
            'status': 'pending',
            'files_count': len(saved_files),
            'total_size_mb': round(total_size / 1024 / 1024, 2)
        }), 202
        
    except Exception as e:
        logger.error(f"Error en upload: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@api_bp.route('/transcription/status/<task_id>', methods=['GET'])
def get_task_status(task_id: str):
    """
    Obtiene el estado de una tarea
    """
    from app.tasks.celery_tasks import celery_app
    
    try:
        task = celery_app.AsyncResult(task_id)
        
        if task.state == 'PENDING':
            return jsonify({
                'task_id': task_id,
                'status': 'pending',
                'progress': 0
            })
        elif task.state == 'PROGRESS':
            return jsonify({
                'task_id': task_id,
                'status': 'processing',
                **task.info  # Contiene progress, current_file, etc.
            })
        elif task.state == 'SUCCESS':
            result = task.info
            return jsonify({
                'task_id': task_id,
                'status': 'completed',
                'result': result
            })
        elif task.state == 'FAILURE':
            return jsonify({
                'task_id': task_id,
                'status': 'failed',
                'error': str(task.info)
            }), 500
        else:
            return jsonify({
                'task_id': task_id,
                'status': task.state.lower()
            })
            
    except Exception as e:
        logger.error(f"Error obteniendo estado: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@api_bp.route('/transcription/result/<task_id>', methods=['GET'])
def get_transcription_result(task_id: str):
    """
    Obtiene el resultado completo de una transcripción
    """
    from app.tasks.celery_tasks import celery_app
    
    try:
        task = celery_app.AsyncResult(task_id)
        
        if task.state != 'SUCCESS':
            return jsonify({
                'error': f'Tarea no completada. Estado: {task.state}'
            }), 400
        
        result = task.info
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error obteniendo resultado: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@api_bp.route('/transcription/cancel/<task_id>', methods=['POST'])
def cancel_task(task_id: str):
    """
    Cancela una tarea en progreso
    """
    from app.tasks.celery_tasks import celery_app
    
    try:
        celery_app.control.revoke(task_id, terminate=True)
        return jsonify({
            'task_id': task_id,
            'status': 'cancelled'
        })
    except Exception as e:
        logger.error(f"Error cancelando tarea: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@api_bp.route('/history', methods=['GET'])
def get_history():
    """
    Obtiene el historial de transcripciones
    """
    try:
        outputs_dir = settings.OUTPUTS_DIR
        
        # Agrupar archivos por base name
        files_by_base = {}
        
        for file_path in outputs_dir.glob('**/*'):
            if not file_path.is_file():
                continue
            
            if file_path.suffix.lower() not in ['.txt', '.xlsx', '.docx', '.zip']:
                continue
            
            base_name = file_path.stem
            ext = file_path.suffix.lstrip('.').lower()
            
            if base_name not in files_by_base:
                files_by_base[base_name] = {
                    'base_name': base_name,
                    'mtime': file_path.stat().st_mtime,
                    'size': 0,
                    'files': {}
                }
            
            files_by_base[base_name]['files'][ext] = str(file_path)
            files_by_base[base_name]['size'] += file_path.stat().st_size
            files_by_base[base_name]['mtime'] = max(
                files_by_base[base_name]['mtime'],
                file_path.stat().st_mtime
            )
        
        # Convertir a lista y ordenar por fecha
        history_items = []
        for base_name, data in files_by_base.items():
            # Determinar tipo
            if base_name.startswith('lote_'):
                tipo = 'LOTE'
            elif base_name.startswith('corrida_'):
                tipo = 'ZIP'
            else:
                tipo = 'INDIVIDUAL'
            
            from datetime import datetime
            history_items.append({
                'base_name': base_name,
                'tipo': tipo,
                'fecha': datetime.fromtimestamp(data['mtime']).isoformat(),
                'tamaño_bytes': data['size'],
                'archivos_disponibles': list(data['files'].keys())
            })
        
        # Ordenar por fecha (más reciente primero)
        history_items.sort(key=lambda x: x['fecha'], reverse=True)
        
        return jsonify(history_items)
        
    except Exception as e:
        logger.error(f"Error obteniendo historial: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@api_bp.route('/download/<path:filename>', methods=['GET'])
def download_file(filename: str):
    """
    Descarga un archivo generado
    """
    try:
        file_path = settings.OUTPUTS_DIR / filename
        
        if not file_path.exists():
            return jsonify({'error': 'Archivo no encontrado'}), 404
        
        # Verificar que está dentro de OUTPUTS_DIR (seguridad)
        if not str(file_path.resolve()).startswith(str(settings.OUTPUTS_DIR.resolve())):
            return jsonify({'error': 'Acceso denegado'}), 403
        
        return send_file(
            str(file_path),
            as_attachment=True,
            download_name=file_path.name
        )
        
    except Exception as e:
        logger.error(f"Error descargando archivo: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@api_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    from app.core.transcription import transcription_engine
    from app.tasks.celery_tasks import celery_app
    
    try:
        # Verificar Redis
        try:
            import redis
            r = redis.from_url(settings.REDIS_URL)
            r.ping()
            redis_ok = True
        except:
            redis_ok = False
        
        # Verificar workers de Celery
        try:
            inspect = celery_app.control.inspect()
            workers = inspect.active()
            worker_count = len(workers) if workers else 0
        except:
            worker_count = 0
        
        return jsonify({
            'status': 'ok',
            'service': 'enacom-transcriptor-backend',
            'whisper_model_loaded': transcription_engine.is_loaded(),
            'redis_connected': redis_ok,
            'celery_workers': worker_count
        })
        
    except Exception as e:
        logger.error(f"Error en health check: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500
