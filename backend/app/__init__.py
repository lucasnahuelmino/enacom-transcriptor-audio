"""
Flask Application Factory
"""
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from app.config import settings

socketio = SocketIO()


def create_app():
    """Factory para crear la aplicación Flask"""
    app = Flask(__name__)
    
    # Configuración
    app.config.from_object(settings)
    
    # CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": settings.CORS_ORIGINS,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # SocketIO para progreso en tiempo real
    socketio.init_app(
        app,
        cors_allowed_origins=settings.CORS_ORIGINS,
        async_mode='threading',
        message_queue=settings.REDIS_URL,
        logger=settings.DEBUG,
        engineio_logger=settings.DEBUG
    )
    
    # Registrar blueprints
    from app.api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    
    # Registrar eventos de WebSocket
    from app.api import websockets
    
    # Health check
    @app.route('/health')
    def health_check():
        return {'status': 'ok', 'service': 'enacom-transcriptor'}
    
    # Servir archivos estáticos (outputs)
    from flask import send_from_directory
    @app.route('/storage/<path:filename>')
    def download_file(filename):
        return send_from_directory(settings.OUTPUTS_DIR, filename)
    
    return app
