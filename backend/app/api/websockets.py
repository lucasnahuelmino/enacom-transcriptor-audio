"""
WebSocket handlers para progreso en tiempo real
"""
from flask import request
from flask_socketio import emit, join_room, leave_room
from app import socketio
import logging

from app.signal_monitor import signal_monitor_service

logger = logging.getLogger(__name__)

SIGNAL_MONITOR_ROOM = 'signal_monitor'


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


@socketio.on('subscribe_signal_monitor')
def handle_subscribe_signal_monitor():
    join_room(SIGNAL_MONITOR_ROOM)
    logger.info(f"Cliente {request.sid} suscrito al monitor de señal")
    emit('signal_monitor_subscribed', signal_monitor_service.status())


@socketio.on('unsubscribe_signal_monitor')
def handle_unsubscribe_signal_monitor():
    leave_room(SIGNAL_MONITOR_ROOM)
    logger.info(f"Cliente {request.sid} desuscrito del monitor de señal")
    emit('signal_monitor_unsubscribed', {'room': SIGNAL_MONITOR_ROOM})


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


def broadcast_signal_monitor_state(payload: dict):
    _get_emitter().emit('signal_monitor_state', payload, room=SIGNAL_MONITOR_ROOM, namespace='/')


def broadcast_signal_monitor_spectrum(payload: dict):
    _get_emitter().emit('signal_monitor_spectrum', payload, room=SIGNAL_MONITOR_ROOM, namespace='/')


def broadcast_signal_monitor_audio(payload: dict):
    _get_emitter().emit('signal_monitor_audio', payload, room=SIGNAL_MONITOR_ROOM, namespace='/')


def broadcast_signal_monitor_transcription(payload: dict):
    _get_emitter().emit('signal_monitor_transcription', payload, room=SIGNAL_MONITOR_ROOM, namespace='/')


def broadcast_signal_monitor_event(payload: dict):
    _get_emitter().emit('signal_monitor_event', payload, room=SIGNAL_MONITOR_ROOM, namespace='/')


def broadcast_signal_monitor_error(payload: dict):
    _get_emitter().emit('signal_monitor_error', payload, room=SIGNAL_MONITOR_ROOM, namespace='/')


def broadcast_signal_monitor_activity_change(payload: dict):
    _get_emitter().emit('signal_monitor_activity_change', payload, room=SIGNAL_MONITOR_ROOM, namespace='/')


signal_monitor_service.bind_emitters(
    broadcast_signal_monitor_state,
    broadcast_signal_monitor_spectrum,
    broadcast_signal_monitor_audio,
    broadcast_signal_monitor_transcription,
    broadcast_signal_monitor_event,
    broadcast_signal_monitor_activity_change,
    broadcast_signal_monitor_error,
)