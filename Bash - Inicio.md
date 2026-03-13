##### **Terminal 1**

###### **REDIS SERVER**

cd desktop/enacom-transcriptor-audio/

./start-dev.sh
o
./tools/redis/redis-server.exe


##### **Terminal 2**

cd desktop/enacom-transcriptor-audio/backend/

source venv/Scripts/activate

python run.py



##### **Terminal 3**

cd desktop/enacom-transcriptor-audio/backend/

source venv/Scripts/activate

celery -A celery\_worker.celery\_app worker --loglevel=info --pool=solo



##### **Terminal 4**

cd desktop/enacom-transcriptor-audio/frontend/

npm run dev









