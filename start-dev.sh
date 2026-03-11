#!/bin/bash

echo "🚀 Iniciando Redis..."
/c/Users/SNCTE/Apps/redis/redis-server.exe &

echo "🚀 Iniciando Backend..."
cd backend
source venv/Scripts/activate
python run.py &

echo "🚀 Iniciando Celery..."
celery -A celery_worker.celery_app worker --loglevel=info --pool=solo &

echo "🚀 Iniciando Frontend..."
cd ../frontend
npm run dev

wait