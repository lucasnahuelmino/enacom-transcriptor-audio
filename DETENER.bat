@echo off
chcp 65001 >nul 2>&1
title ENACOM Transcriptor - Detener servicios

echo.
echo ============================================================
echo   ENACOM Transcriptor v3.0 - Deteniendo servicios
echo ============================================================
echo.

echo Deteniendo Redis...
taskkill /f /im redis-server.exe >nul 2>&1

echo Deteniendo Celery y Flask (Python)...
taskkill /f /im python.exe >nul 2>&1

echo Deteniendo frontend (Node)...
taskkill /f /im node.exe >nul 2>&1

echo.
echo Todos los servicios detenidos.
echo.
pause
