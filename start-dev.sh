#!/bin/bash

echo "🚀 Iniciando Redis..."

# 1. Argumento manual: ./start-dev.sh "C:/ruta/redis-server.exe"
if [ -n "$1" ]; then
    "$1" &
    exit 0
fi

# 2. Variable de entorno
if [ -n "$REDIS_SERVER_PATH" ]; then
    "$REDIS_SERVER_PATH" &
    exit 0
fi

# 3. En el PATH del sistema
if command -v redis-server &> /dev/null; then
    redis-server &
    exit 0
fi

# 4. Rutas comunes en Windows
COMMON_PATHS=(
    "/c/Users/$USERNAME/Apps/redis/redis-server.exe"
    "/c/Program Files/Redis/redis-server.exe"
    "/c/Redis/redis-server.exe"
    "/c/tools/redis/redis-server.exe"
)

for path in "${COMMON_PATHS[@]}"; do
    if [ -f "$path" ]; then
        echo "Redis encontrado en: $path"
        "$path" &
        exit 0
    fi
done

echo "❌ No se encontró redis-server."
echo "   Opciones:"
echo "   1. Pasá la ruta como argumento: ./start-dev.sh 'C:/ruta/redis-server.exe'"
echo "   2. Agregá REDIS_SERVER_PATH al archivo .env del backend"
echo "   3. Instalá Redis y agregalo al PATH del sistema"
exit 1
```

Y en el `.env` del backend de cada PC nueva simplemente agregan su ruta:
```
REDIS_SERVER_PATH=C:/Users/FULANO/Apps/redis/redis-server.exe