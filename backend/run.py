"""
Entry point para ejecutar el servidor Flask + SocketIO
"""
from app import create_app, socketio
from app.config import settings
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Crear app
app = create_app()

if __name__ == '__main__':
    logger.info("Iniciando servidor ENACOM Transcriptor Backend...")
    logger.info(f"Modo debug: {settings.DEBUG}")
    logger.info(f"CORS origins: {settings.CORS_ORIGINS}")
    logger.info(f"Modelo Whisper: {settings.WHISPER_MODEL}")
    logger.info(f"Dispositivo: {settings.WHISPER_DEVICE}")
    
    # Ejecutar con SocketIO
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=settings.DEBUG,
        use_reloader=settings.DEBUG
    )
