"""
WebSocket handlers para progreso en tiempo real
"""
from flask import request
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


_emitter = None

def _get_emitter():
    global _emitter
    if _emitter is None:
        from flask_socketio import SocketIO
        from app.config import settings
        _emitter = SocketIO(message_queue=settings.REDIS_URL)
    return _emitter

def broadcast_progress(task_id: str, progress_data: dict):
    _get_emitter().emit(
        'task_progress',
        {'task_id': task_id, **progress_data},
        room=task_id,
        namespace='/'
    )

def broadcast_completion(task_id: str, result_data: dict):
    _get_emitter().emit(
        'task_completed',
        {'task_id': task_id, **result_data},
        room=task_id,
        namespace='/'
    )

def broadcast_error(task_id: str, error_message: str):
    _get_emitter().emit(
        'task_error',
        {'task_id': task_id, 'error': error_message},
        room=task_id,
        namespace='/'
    )