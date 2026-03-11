"""
Celery Worker
Ejecutar con: celery -A celery_worker.celery_app worker --loglevel=info
"""
from app.tasks.celery_tasks import celery_app
from app.config import settings
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info("Iniciando Celery Worker...")
    logger.info(f"Broker: {settings.CELERY_BROKER_URL}")
    logger.info(f"Backend: {settings.CELERY_RESULT_BACKEND}")
    
    celery_app.start()
