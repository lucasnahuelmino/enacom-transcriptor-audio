@echo off
chcp 65001 >nul 2>&1
::
:: post-install.bat — ENACOM Transcriptor v3.0
:: Llamado por Inno Setup. Recibe ruta de instalacion como %1
::

set "APPDIR=%~1"
if "%APPDIR%"=="" set "APPDIR=%~dp0"

:: Quitar barra final si la tiene
if "%APPDIR:~-1%"=="\" set "APPDIR=%APPDIR:~0,-1%"

set "BACKEND=%APPDIR%\backend"
set "FRONTEND=%APPDIR%\frontend"
set "LOGFILE=%APPDIR%\logs\post-install.log"

if not exist "%APPDIR%\logs" mkdir "%APPDIR%\logs"

echo ============================================================ > "%LOGFILE%"
echo   ENACOM Transcriptor v3.0 - Post-instalacion              >> "%LOGFILE%"
echo   %date% %time%                                             >> "%LOGFILE%"
echo ============================================================ >> "%LOGFILE%"

:: ── Buscar Python por ruta fija (no depender del PATH) ───────────
:: Inno Setup acaba de instalar Python — el PATH nuevo aun no
:: se propago al proceso actual, por eso buscamos por ruta fija.
echo [1/4] Buscando Python... >> "%LOGFILE%"

set "PYTHON_CMD="
if exist "C:\Program Files\Python313\python.exe"               set "PYTHON_CMD=C:\Program Files\Python313\python.exe"
if exist "C:\Program Files\Python312\python.exe"               set "PYTHON_CMD=C:\Program Files\Python312\python.exe"
if exist "C:\Program Files\Python311\python.exe"               set "PYTHON_CMD=C:\Program Files\Python311\python.exe"
if exist "C:\Program Files\Python310\python.exe"               set "PYTHON_CMD=C:\Program Files\Python310\python.exe"
if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" set "PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set "PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" set "PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python310\python.exe"

:: Fallback: ya estaba instalado antes
if "%PYTHON_CMD%"=="" (
    where python >nul 2>&1
    if %errorlevel% equ 0 set "PYTHON_CMD=python"
)

if "%PYTHON_CMD%"=="" (
    echo [FATAL] Python no encontrado en ninguna ruta conocida. >> "%LOGFILE%"
    exit /b 1
)
"%PYTHON_CMD%" --version >> "%LOGFILE%" 2>&1
echo   OK: %PYTHON_CMD% >> "%LOGFILE%"

:: ── Buscar npm por ruta fija ──────────────────────────────────────
echo [2/4] Buscando Node.js / npm... >> "%LOGFILE%"

set "NPM_CMD="
if exist "C:\Program Files\nodejs\npm.cmd"       set "NPM_CMD=C:\Program Files\nodejs\npm.cmd"
if exist "C:\Program Files (x86)\nodejs\npm.cmd" set "NPM_CMD=C:\Program Files (x86)\nodejs\npm.cmd"

if "%NPM_CMD%"=="" (
    where npm >nul 2>&1
    if %errorlevel% equ 0 set "NPM_CMD=npm"
)

if "%NPM_CMD%"=="" (
    echo [FATAL] npm no encontrado. >> "%LOGFILE%"
    exit /b 1
)
"%NPM_CMD%" --version >> "%LOGFILE%" 2>&1
echo   OK: %NPM_CMD% >> "%LOGFILE%"

:: ── Crear entorno virtual Python ──────────────────────────────────
echo [3/4] Creando entorno virtual... >> "%LOGFILE%"
cd /d "%BACKEND%"

if not exist "%BACKEND%\venv" (
    "%PYTHON_CMD%" -m venv "%BACKEND%\venv" >> "%LOGFILE%" 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] No se pudo crear el entorno virtual. >> "%LOGFILE%"
        exit /b 1
    )
)

:: Usar pip del venv directamente — sin depender de activate
set "VENV_PIP=%BACKEND%\venv\Scripts\pip.exe"
set "VENV_PYTHON=%BACKEND%\venv\Scripts\python.exe"

echo [3/4] Instalando dependencias Python... >> "%LOGFILE%"
"%VENV_PYTHON%" -m pip install --upgrade pip --quiet >> "%LOGFILE%" 2>&1
"%VENV_PIP%" install -r "%BACKEND%\requirements.txt" >> "%LOGFILE%" 2>&1

if %errorlevel% neq 0 (
    echo [ERROR] Fallo pip install. Ver log para detalles. >> "%LOGFILE%"
    exit /b 1
)
echo   OK - Dependencias Python instaladas >> "%LOGFILE%"

:: ── Instalar dependencias Node.js ─────────────────────────────────
echo [4/4] Instalando dependencias Node.js... >> "%LOGFILE%"
cd /d "%FRONTEND%"

:: --prefer-offline usa cache local si existe, evita errores de red
"%NPM_CMD%" install --prefer-offline --cache "%APPDIR%\tools\npm-cache" >> "%LOGFILE%" 2>&1

if %errorlevel% neq 0 (
    echo [ERROR] Fallo npm install. Ver log para detalles. >> "%LOGFILE%"
    exit /b 1
)
echo   OK - Dependencias Node.js instaladas >> "%LOGFILE%"

:: ── Crear carpetas de storage ─────────────────────────────────────
if not exist "%BACKEND%\storage\uploads"  mkdir "%BACKEND%\storage\uploads"
if not exist "%BACKEND%\storage\outputs"  mkdir "%BACKEND%\storage\outputs"

:: ── Listo ─────────────────────────────────────────────────────────
echo. >> "%LOGFILE%"
echo Post-instalacion completada. %date% %time% >> "%LOGFILE%"
exit /b 0