#!/bin/bash
# =============================================================================
# ENACOM Transcriptor v3.0 — Script de desarrollo
# Uso: ./start-dev.sh
# =============================================================================

set -e
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"

# Colores
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'; RESET='\033[0m'

log()  { echo -e "${BLUE}▶${RESET} $1"; }
ok()   { echo -e "${GREEN}✓${RESET} $1"; }
warn() { echo -e "${YELLOW}⚠${RESET} $1"; }
err()  { echo -e "${RED}✗${RESET} $1"; }

echo ""
echo -e "${BOLD}============================================================${RESET}"
echo -e "${BOLD}  ENACOM Transcriptor v3.0 — Entorno de desarrollo${RESET}"
echo -e "${BOLD}============================================================${RESET}"
echo ""

# ── 1. Redis ──────────────────────────────────────────────────────
log "Verificando Redis en puerto 6379..."

redis_running=false

# Intentar conectar con redis-cli si existe
if command -v redis-cli &>/dev/null; then
    if redis-cli ping &>/dev/null 2>&1; then
        redis_running=true
    fi
fi

# Alternativa: verificar con netstat si el puerto está escuchando
if ! $redis_running; then
    if netstat -an 2>/dev/null | grep -q "6379.*LISTEN\|6379.*LISTENING"; then
        redis_running=true
    fi
fi

if $redis_running; then
    ok "Redis ya está corriendo en el puerto 6379"
else
    log "Redis no detectado, intentando iniciar..."

    REDIS_EXE=""

    # Buscar por argumento, variable de entorno, PATH o rutas comunes
    if [ -n "$1" ] && [ -f "$1" ]; then
        REDIS_EXE="$1"
    elif [ -n "$REDIS_SERVER_PATH" ] && [ -f "$REDIS_SERVER_PATH" ]; then
        REDIS_EXE="$REDIS_SERVER_PATH"
    elif command -v redis-server &>/dev/null; then
        REDIS_EXE="redis-server"
    else
        SEARCH_PATHS=(
            "$REPO_ROOT/tools/redis/redis-server.exe"
            "/c/Users/$USERNAME/Apps/redis/redis-server.exe"
            "/c/Program Files/Redis/redis-server.exe"
            "/c/Redis/redis-server.exe"
            "/c/tools/redis/redis-server.exe"
        )
        for p in "${SEARCH_PATHS[@]}"; do
            if [ -f "$p" ]; then
                REDIS_EXE="$p"
                break
            fi
        done
    fi

    if [ -z "$REDIS_EXE" ]; then
        err "No se encontró redis-server."
        echo ""
        echo "  Opciones:"
        echo "  1. Pasá la ruta como argumento:  ./start-dev.sh 'C:/ruta/redis-server.exe'"
        echo "  2. Definí en backend/.env:        REDIS_SERVER_PATH=C:/ruta/redis-server.exe"
        echo "  3. Instalá Redis y agregalo al PATH"
        echo ""
        exit 1
    fi

    log "Iniciando Redis desde: $REDIS_EXE"
    "$REDIS_EXE" --daemonize no &
    REDIS_PID=$!

    # Esperar hasta 8 segundos a que Redis levante
    for i in {1..8}; do
        sleep 1
        if command -v redis-cli &>/dev/null && redis-cli ping &>/dev/null 2>&1; then
            ok "Redis listo (PID $REDIS_PID)"
            redis_running=true
            break
        fi
        # En Windows sin redis-cli, confiar en el tiempo de espera
        if [ $i -eq 4 ]; then
            ok "Redis iniciado (sin confirmación de ping en Windows)"
            redis_running=true
            break
        fi
    done

    if ! $redis_running; then
        err "Redis no respondió. Verificá si el puerto 6379 está ocupado."
        echo "  Podés verificar con:  netstat -ano | findstr 6379"
        exit 1
    fi
fi

# ── 2. Backend ────────────────────────────────────────────────────
mkdir -p "$REPO_ROOT/logs"
BACKEND_DIR="$REPO_ROOT/backend"

if [ ! -d "$BACKEND_DIR/venv" ]; then
    err "No se encontró el entorno virtual en backend/venv"
    echo "  Ejecutá: cd backend && python -m venv venv && venv/Scripts/pip install -r requirements.txt"
    exit 1
fi

log "Iniciando Celery worker..."
(
    cd "$BACKEND_DIR"
    source venv/Scripts/activate 2>/dev/null || source venv/bin/activate
    celery -A celery_worker.celery_app worker --loglevel=info --pool=solo \
        > "$REPO_ROOT/logs/celery.log" 2>&1
) &
CELERY_PID=$!
ok "Celery worker iniciado (PID $CELERY_PID)"

sleep 1

log "Iniciando Flask backend (puerto 5000)..."
(
    cd "$BACKEND_DIR"
    source venv/Scripts/activate 2>/dev/null || source venv/bin/activate
    python run.py > "$REPO_ROOT/logs/backend.log" 2>&1
) &
BACKEND_PID=$!
ok "Flask iniciado (PID $BACKEND_PID)"

# ── 3. Frontend ───────────────────────────────────────────────────
FRONTEND_DIR="$REPO_ROOT/frontend"

if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    log "node_modules no encontrado, instalando dependencias..."
    (cd "$FRONTEND_DIR" && npm install)
fi

log "Iniciando Vite (puerto 5174)..."
(
    cd "$FRONTEND_DIR"
    npm run dev > "$REPO_ROOT/logs/frontend.log" 2>&1
) &
FRONTEND_PID=$!

# Esperar a que Vite levante
sleep 3
ok "Frontend iniciado (PID $FRONTEND_PID)"

# ── 4. Resumen ────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}============================================================${RESET}"
echo -e "${GREEN}${BOLD}  ✓ Todo listo${RESET}"
echo ""
echo "  Frontend:  http://localhost:5174"
echo "  Backend:   http://localhost:5000"
echo "  Health:    http://localhost:5000/api/v1/health"
echo ""
echo "  Logs:"
echo "    Backend:  logs/backend.log"
echo "    Celery:   logs/celery.log"
echo "    Frontend: logs/frontend.log"
echo ""
echo -e "  ${YELLOW}Presioná Ctrl+C para detener todo${RESET}"
echo -e "${BOLD}============================================================${RESET}"
echo ""

# ── 5. Trap Ctrl+C para limpiar procesos ─────────────────────────
cleanup() {
    echo ""
    log "Deteniendo servicios..."
    kill $FRONTEND_PID $BACKEND_PID $CELERY_PID 2>/dev/null
    # No matamos Redis si ya estaba corriendo antes de que arranque el script
    if [ -n "$REDIS_PID" ]; then
        kill $REDIS_PID 2>/dev/null
    fi
    ok "Servicios detenidos"
    exit 0
}
trap cleanup SIGINT SIGTERM

# Mantener el script vivo
wait