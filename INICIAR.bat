@echo off
chcp 65001 >nul 2>&1
title ENACOM Transcriptor v3.0

cd /d "%~dp0"
set "ROOT=%~dp0"
set "BACKEND=%ROOT%backend"
set "FRONTEND=%ROOT%frontend"

echo.
echo ============================================================
echo   ENACOM Transcriptor v3.0
echo ============================================================
echo.

:: Verificar instalacion
if not exist "%BACKEND%\venv\Scripts\activate.bat" (
    echo [ERROR] Entorno virtual no encontrado.
    echo Reinstalar la aplicacion con el instalador.
    echo.
    pause
    exit /b 1
)

if not exist "%FRONTEND%\node_modules" (
    echo [ERROR] Dependencias Node.js no encontradas.
    echo Reinstalar la aplicacion con el instalador.
    echo.
    pause
    exit /b 1
)

:: Crear carpeta de logs si no existe
if not exist "%ROOT%logs" mkdir "%ROOT%logs"

echo Iniciando servicios en segundo plano...
echo Los logs se guardan en la carpeta "logs\"
echo.

:: Lanzar todo oculto via VBScript
cscript //nologo "%ROOT%iniciar-servicios.vbs" "%ROOT%"

:: Esperar a que los servicios levanten
echo Esperando que los servicios inicien...
timeout /t 8 /nobreak >nul

echo.
echo ============================================================
echo   Todo listo.
echo.
echo   Aplicacion:  http://localhost:5174
echo   Backend API: http://localhost:5000
echo.
echo   Logs en:     %ROOT%logs\
echo     - redis.log
echo     - celery.log
echo     - backend.log
echo     - frontend.log
echo.
echo   Para detener los servicios usar: DETENER.bat
echo ============================================================
echo.

timeout /t 2 /nobreak >nul
start http://localhost:5174

echo   Esta ventana puede cerrarse.
pause