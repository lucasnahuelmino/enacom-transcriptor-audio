# ENACOM Transcriptor v3.0

## Guía de instalación del paquete standalone

Este documento describe la instalación de la versión distribuible para Windows del sistema ENACOM Transcriptor.

La versión actual se instala mediante un ejecutable generado con Inno Setup y despliega una aplicación standalone que no requiere instalar por separado Python, Node.js o Redis en el equipo usuario.

## Requisitos mínimos del equipo

| Componente | Requisito |
|---|---|
| Sistema operativo | Windows 10 o Windows 11 de 64 bits |
| Memoria RAM | 8 GB mínimo, 16 GB recomendado |
| Espacio libre en disco | 8 GB o superior |
| Permisos de usuario | Usuario estándar |

## Características de la instalación

La instalación actual:

- no requiere permisos de administrador
- se instala por usuario
- utiliza carpeta de instalación bajo el perfil local del usuario
- crea accesos directos opcionales en escritorio y menú inicio
- incluye ejecutable, frontend buildado, ffmpeg portable y modelos locales

Ruta por defecto de instalación:

```text
%LOCALAPPDATA%\Programs\ENACOM\Transcriptor
```

## Instalación paso a paso

### 1. Ejecutar el instalador

Abrir el archivo:

```text
ENACOM-Transcriptor-standalone-v3.0-Setup.exe
```

### 2. Seleccionar carpeta de destino

Se recomienda mantener la ruta propuesta por defecto. Si el área técnica lo requiere, puede elegirse otra carpeta dentro del perfil del usuario.

### 3. Elegir accesos directos

El instalador permite:

- crear acceso directo en escritorio
- crear acceso directo en menú inicio

### 4. Finalizar instalación

Al terminar, se puede iniciar la aplicación desde el instalador o desde los accesos directos generados.

## Qué instala el paquete

La instalación despliega como mínimo los siguientes elementos:

- ejecutable principal ENACOM-Transcriptor.exe
- recursos del frontend ya compilado
- binarios ffmpeg y ffprobe portables
- modelos Whisper locales
- carpeta de almacenamiento local para uploads y outputs
- carpeta de logs

## Primer inicio

Al iniciar la aplicación:

- el sistema levanta un servicio local en el equipo usuario
- abre automáticamente el navegador en http://127.0.0.1:5000
- crea, si no existen, las carpetas locales de trabajo

## Carpetas operativas creadas por la aplicación

Dentro de la carpeta de instalación se crean o utilizan:

```text
storage\uploads
storage\outputs
logs
```

## Desinstalación

La desinstalación puede realizarse desde:

- menú inicio
- aplicaciones instaladas de Windows
- desinstalador incluido por Inno Setup

La confirmación de desinstalación informa que los archivos almacenados en storage pueden permanecer en disco.

## Validaciones realizadas por el instalador

El instalador verifica:

- compatibilidad con Windows de 64 bits

## Problemas frecuentes

### El instalador no inicia

Verificar que el archivo no haya sido bloqueado por el sistema o por herramientas de seguridad corporativas.

### La aplicación no abre luego de instalar

Verificar:

- que la instalación haya concluido correctamente
- que no exista otro proceso ocupando el puerto 5000
- que la carpeta de instalación contenga tools/ffmpeg y tools/models

### El equipo no permite instalar en Program Files

La versión actual ya no utiliza Program Files y está preparada para instalarse con usuario estándar.

## Soporte interno

Para validación funcional y soporte técnico, utilizar la documentación complementaria del repositorio:

- README.md
- MANUAL_DE_USO.md

## Uso interno

Documento de uso interno ENACOM.
