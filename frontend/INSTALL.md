# 🚀 Guía de Instalación - ENACOM Transcriptor de audios Frontend

## 📋 Requisitos previos

- **Node.js** v18 o superior
- **npm** v9 o superior  
- Backend Flask corriendo en puerto 5000
- Redis corriendo (para WebSockets)

Verificá tus versiones:
```bash
node --version   # Debe ser v18+
npm --version    # Debe ser v9+
```

---

## 🔧 Instalación Paso a Paso

### 1️⃣ Navegar al directorio

```bash
cd frontend
```

### 2️⃣ Instalar dependencias

```bash
npm install
```

Esto instalará:
- Vue 3.4
- Pinia 2.1
- Axios 1.6
- socket.io-client 4.6
- Tailwind CSS 3.4
- Vite 5.0

**Tiempo estimado:** 2-3 minutos

---

### 3️⃣ Verificar instalación

```bash
npm list --depth=0
```

Deberías ver todas las dependencias listadas sin errores.

---

## ▶️ Ejecución

### Modo Desarrollo

```bash
npm run dev
```

Esto iniciará el servidor de desarrollo en:
- **URL:** http://localhost:5173
- **Hot reload:** activado
- **Proxy:** configurado automáticamente a http://localhost:5000

### Build para Producción

```bash
npm run build
```

Genera archivos optimizados en `dist/`.

### Preview del Build

```bash
npm run preview
```

Previsualiza el build de producción localmente.

---

## 🌐 Configuración de URLs

El frontend se conecta al backend mediante proxy configurado en `vite.config.js`:

```javascript
proxy: {
  '/api': {
    target: 'http://localhost:5000',
    changeOrigin: true
  },
  '/socket.io': {
    target: 'http://localhost:5000',
    ws: true
  }
}
```

Si tu backend corre en otro puerto, editá `vite.config.js`.

---

## 🔍 Verificación de Funcionamiento

### 1. Verificar backend activo

```bash
curl http://localhost:5000/api/v1/health
```

Debe responder: `{"status": "ok"}`

### 2. Verificar Redis activo

```bash
redis-cli ping
```

Debe responder: `PONG`

### 3. Verificar frontend cargando

Abrí http://localhost:5173 en tu navegador.

Deberías ver:
- ✅ Header azul de ENACOM
- ✅ Panel de configuración
- ✅ Sin errores en consola del navegador

---

## 🛠️ Troubleshooting

### ❌ Error: "Cannot find module 'vue'"

```bash
rm -rf node_modules package-lock.json
npm install
```

### ❌ Error: "Failed to fetch dynamically imported module"

Refrescá el navegador con Ctrl+F5 (hard reload).

### ❌ WebSocket no conecta

1. Verificá que Redis esté corriendo: `redis-cli ping`
2. Verificá que el backend Flask esté en puerto 5000
3. Revisá la consola del navegador (F12) para ver errores

### ❌ Archivos no se suben

1. Verificá que el backend esté corriendo
2. Revisá la consola del navegador (F12)
3. Verificá el tamaño del archivo (máx 500MB)

---

## 📁 Estructura del Proyecto

```
frontend/
├── index.html               # HTML principal
├── package.json             # Dependencias
├── vite.config.js           # Configuración Vite + proxy
├── tailwind.config.js       # Colores ENACOM
├── postcss.config.js        # PostCSS para Tailwind
├── jsconfig.json            # Alias @/
├── src/
│   ├── main.js              # Entry point
│   ├── App.vue              # Componente raíz
│   ├── components/          # Componentes Vue
│   │   ├── Header.vue
│   │   ├── ConfigPanel.vue
│   │   ├── ProgressBar.vue
│   │   ├── TranscriptionView.vue
│   │   ├── DownloadsPanel.vue
│   │   └── HistoryPanel.vue
│   ├── stores/              # Pinia stores
│   │   └── transcription.js
│   ├── services/            # Servicios HTTP/WS
│   │   ├── api.js
│   │   └── websocket.js
│   ├── utils/               # Utilidades
│   │   └── formatters.js
│   └── assets/              # Estilos
│       └── main.css
└── README.md                # Documentación
```

---

## 🎯 Próximos Pasos

1. ✅ **Frontend instalado** - Continuá con la Fase 1 del backend
2. 📝 **Leé el README.md** - Para más detalles técnicos
3. 🔌 **Conectá con el backend** - Seguí las instrucciones del backend README

---

## 💡 Comandos Útiles

```bash
# Desarrollo
npm run dev

# Build
npm run build

# Preview
npm run preview

# Limpiar caché y reinstalar
rm -rf node_modules package-lock.json dist
npm install

# Ver árbol de dependencias
npm list --depth=1
```

---

## ✅ Checklist de Instalación

- [ ] Node.js v18+ instalado
- [ ] npm instalado
- [ ] `npm install` ejecutado sin errores
- [ ] Backend corriendo en puerto 5000
- [ ] Redis corriendo
- [ ] Frontend abre en http://localhost:5173
- [ ] No hay errores en consola del navegador
- [ ] WebSocket conecta correctamente

---

**Desarrollado por ENACOM - Dirección Nacional de Control y Fiscalización**
