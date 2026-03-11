"""
WebSocket handlers para progreso en tiempo real
"""
from flask_socketio import emit, join_room, leave_room
from app import socketio
import logging

logger = logging.getLogger(__name__)


@socketio.on('connect')
def handle_connect():
    """Cliente conectado"""
    logger.info(f"Cliente conectado: {request.sid}")
    emit('connected', {'message': 'Conectado al servidor de transcripción'})


@socketio.on('disconnect')
def handle_disconnect():
    """Cliente desconectado"""
    logger.info(f"Cliente desconectado: {request.sid}")


@socketio.on('subscribe_task')
def handle_subscribe_task(data):
    """
    Cliente se suscribe a updates de una tarea específica
    
    Args:
        data: {"task_id": "uuid-de-la-tarea"}
    """
    task_id = data.get('task_id')
    
    if not task_id:
        emit('error', {'message': 'task_id requerido'})
        return
    
    # Unirse a la room de esta tarea
    join_room(task_id)
    logger.info(f"Cliente {request.sid} suscrito a tarea {task_id}")
    
    emit('subscribed', {'task_id': task_id, 'message': f'Suscrito a tarea {task_id}'})


@socketio.on('unsubscribe_task')
def handle_unsubscribe_task(data):
    """
    Cliente se desuscribe de una tarea
    """
    task_id = data.get('task_id')
    
    if not task_id:
        return
    
    leave_room(task_id)
    logger.info(f"Cliente {request.sid} desuscrito de tarea {task_id}")
    
    emit('unsubscribed', {'task_id': task_id})


def broadcast_progress(task_id: str, progress_data: dict):
    """
    Broadcast de progreso a todos los clientes suscritos a una tarea
    
    Esta función se llama desde las Celery tasks
    
    Args:
        task_id: ID de la tarea
        progress_data: Dict con campos como:
            - progress: int (0-100)
            - status: str
            - current_file: str
            - message: str
            - segments: List[Dict]  # Transcripción en vivo
            - infracciones: List[Dict]
    """
    socketio.emit(
        'task_progress',
        {
            'task_id': task_id,
            **progress_data
        },
        room=task_id,
        namespace='/'
    )
    
    logger.debug(f"Progress broadcast para tarea {task_id}: {progress_data.get('progress', 0)}%")


def broadcast_completion(task_id: str, result_data: dict):
    """
    Notifica que una tarea se completó
    """
    socketio.emit(
        'task_completed',
        {
            'task_id': task_id,
            **result_data
        },
        room=task_id,
        namespace='/'
    )
    
    logger.info(f"Tarea completada: {task_id}")


def broadcast_error(task_id: str, error_message: str):
    """
    Notifica que una tarea falló
    """
    socketio.emit(
        'task_error',
        {
            'task_id': task_id,
            'error': error_message
        },
        room=task_id,
        namespace='/'
    )
    
    logger.error(f"Tarea fallida: {task_id} - {error_message}")
