@echo off
chcp 65001 > nul
title ENACOM Transcriptor — Descarga de modelos

echo.
echo ============================================================
echo   ENACOM Transcriptor — Descarga de modelos Whisper
echo ============================================================
echo.
echo   Este proceso descarga los modelos de reconocimiento de voz.
echo   La descarga solo es necesaria UNA VEZ por computadora.
echo   Si se interrumpe, puede retomarse ejecutando este archivo
echo   nuevamente sin perder el progreso.
echo.
echo   Seleccione los modelos a descargar:
echo.
echo   [1] Solo Medium  (~1.5 GB) - Recomendado para uso diario
echo   [2] Solo Large v3 (~3.1 GB) - Maxima precision
echo   [3] Ambos modelos (~4.6 GB)
echo   [4] Solo verificar que modelos estan descargados
echo   [0] Salir
echo.
set /p choice="   Opcion: "

if "%choice%"=="0" goto :end
if "%choice%"=="4" goto :check

:: Activar entorno virtual
if not exist "%~dp0backend\venv\Scripts\activate.bat" (
    echo.
    echo   ERROR: No se encontro el entorno virtual.
    echo   Asegurese de haber ejecutado install.bat primero.
    echo.
    pause
    exit /b 1
)

call "%~dp0backend\venv\Scripts\activate.bat"

if "%choice%"=="1" (
    echo.
    echo   Descargando modelo Medium...
    echo   Tiempo estimado: 5-15 minutos segun conexion.
    echo.
    python "%~dp0backend\download_models.py"
    goto :done
)

if "%choice%"=="2" (
    echo.
    echo   Descargando modelo Large v3...
    echo   Tiempo estimado: 15-40 minutos segun conexion.
    echo.
    python "%~dp0backend\download_models.py" --only-large
    goto :done
)

if "%choice%"=="3" (
    echo.
    echo   Descargando ambos modelos...
    echo   Tiempo estimado: 20-60 minutos segun conexion.
    echo.
    python "%~dp0backend\download_models.py" --large
    goto :done
)

echo   Opcion invalida.
goto :end

:check
call "%~dp0backend\venv\Scripts\activate.bat"
python "%~dp0backend\download_models.py" --check
goto :done

:done
echo.
pause

:end