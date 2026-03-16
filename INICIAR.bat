@echo off
chcp 65001 >nul 2>&1
title ENACOM Transcriptor de audios — Iniciando...

cd /d "%~dp0"

echo.
echo ============================================================
echo   ENACOM Transcriptor de audios — Iniciando servicios
echo ============================================================
echo.

:: ── Verificar instalacion previa ─────────────────────────────────
if not exist "%~dp0backend\venv\Scripts\activate.bat" (
    echo   [ERROR] No se encontro el entorno virtual.
    echo   Ejecutar INSTALAR.bat primero.
    echo.
    pause
    exit /b 1
)

if not exist "%~dp0frontend\node_modules" (
    echo   [ERROR] No se encontraron las dependencias Node.js.
    echo   Ejecutar INSTALAR.bat primero.
    echo.
    pause
    exit /b 1
)

:: ── 1. Redis ──────────────────────────────────────────────────────
echo [1/4] Iniciando Redis...
if exist "%~dp0tools\redis\redis-server.exe" (
    start "Redis - ENACOM" /min /d "%~dp0tools\redis" redis-server.exe
) else (
    echo   [AVISO] redis-server.exe no encontrado en tools\redis\
    echo   Asegurarse de que Redis esta corriendo manualmente.
)
timeout /t 2 /nobreak >nul
echo        OK

:: ── 2. Celery worker ─────────────────────────────────────────────
echo [2/4] Iniciando Celery worker...
start "Celery - ENACOM" /d "%~dp0backend" cmd /k "venv\Scripts\activate && celery -A celery_worker.celery_app worker --loglevel=info --pool=solo"
timeout /t 3 /nobreak >nul
echo        OK

:: ── 3. Flask backend ─────────────────────────────────────────────
echo [3/4] Iniciando backend Flask...
start "Backend - ENACOM" /d "%~dp0backend" cmd /k "venv\Scripts\activate && python run.py"
timeout /t 3 /nobreak >nul
echo        OK

:: ── 4. Frontend Vite ─────────────────────────────────────────────
echo [4/4] Iniciando frontend...
start "Frontend - ENACOM" /d "%~dp0frontend" cmd /k "npm run dev"
timeout /t 5 /nobreak >nul
echo        OK

:: ── Abrir navegador ───────────────────────────────────────────────
echo.
echo ============================================================
echo   Servicios en ejecucion:
echo.
echo   Frontend:  http://localhost:5174
echo   Backend:   http://localhost:5000
echo   Health:    http://localhost:5000/api/v1/health
echo.
echo   Para detener la aplicacion:
echo   Cerrar las 3 ventanas de terminal (Celery, Backend, Frontend)
echo   y la ventana de Redis minimizada en la barra de tareas.
echo ============================================================
echo.

timeout /t 2 /nobreak >nul
start http://localhost:5174

echo   Navegador abierto. Esta ventana puede cerrarse.
echo.
pause
