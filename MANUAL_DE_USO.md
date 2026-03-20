# ENACOM Transcriptor v3.0

## Manual de uso

Este manual está dirigido al personal usuario de la aplicación ENACOM Transcriptor.

## 1. Finalidad de la aplicación

La aplicación permite transformar archivos de audio en texto, detectar términos configurados como infracciones y generar documentación exportable para análisis, resguardo y seguimiento.

## 2. Inicio de la aplicación

Una vez instalada, la aplicación puede abrirse desde:

- acceso directo del escritorio
- menú inicio

Al ejecutarse, se abrirá el navegador en la dirección local:

```text
http://127.0.0.1:5000
```

## 3. Pantalla principal

La pantalla principal se compone de tres áreas funcionales:

- panel de configuración y carga de archivos
- área de progreso y resultados
- historial de transcripciones previas

## 4. Carga de archivos de audio

En la sección Archivos de audio se pueden incorporar uno o varios archivos mediante:

- arrastrar y soltar archivos al recuadro
- hacer clic sobre el recuadro y seleccionarlos manualmente

Formatos admitidos:

- MP3
- WAV
- M4A
- OGG
- FLAC
- AAC
- Opus
- WebM

Límite informado por la interfaz:

- hasta 500 MB por archivo

## 5. Configuración del procesamiento

Antes de iniciar la transcripción, la aplicación permite configurar los siguientes campos.

### Nombre / Referencia

Campo libre utilizado como identificador de la corrida y como referencia en los informes.

Ejemplo:

- Acta 1542 - Operativo Centro

### Idioma del audio

Opciones disponibles:

- Español
- Inglés
- Portugués
- Detección automática

### Informe final

Permite elegir el modo de salida:

- Individual: genera resultados por cada archivo procesado
- Combinado: genera además un informe consolidado del lote

### Incluir ZIP

Si está activado, la corrida generará un archivo ZIP con todos los resultados disponibles.

### Modelo Whisper

La versión actual utiliza:

- Large

Está orientado a máxima precisión de transcripción.

### Detección de infracciones

Permite ingresar términos separados por coma para que el sistema los identifique dentro del texto transcripto.

Ejemplo:

```text
put, pelotud, bolud, forr, conch
```

## 6. Inicio del procesamiento

Luego de cargar los archivos y completar la configuración, presionar el botón:

- Procesar N archivo(s)

Durante la ejecución, la aplicación mostrará estado de avance, archivo actual y progreso general.

## 7. Resultados

Al finalizar el procesamiento, la aplicación presenta un bloque de resultados con:

- cantidad de archivos procesados
- modo utilizado
- modelo empleado
- referencia ingresada
- duración total
- cantidad de infracciones detectadas

## 8. Descargas disponibles

Por cada archivo pueden aparecer los siguientes formatos:

- TXT
- XLSX
- DOCX

Si la corrida fue combinada, también pueden aparecer:

- TXT combinado
- XLSX combinado
- DOCX combinado

Si se habilitó exportación comprimida, se mostrará además:

- Descargar transcripción completa (ZIP)

## 9. Historial

La sección Historial de transcripciones permite consultar corridas previas almacenadas localmente.

La tabla muestra:

- fecha
- referencia o identificador
- tipo de corrida
- cantidad de archivos
- tamaño
- descargas disponibles

Desde esa tabla se pueden volver a descargar:

- TXT
- XLSX
- DOCX
- ZIP

## 10. Recomendaciones de uso

- Utilizar referencias descriptivas para facilitar búsquedas posteriores
- Procesar archivos en lotes homogéneos cuando se requiera informe combinado
- Revisar la lista de términos antes de ejecutar para evitar falsos positivos o faltantes
- Mantener espacio suficiente en disco para corridas extensas

## 11. Problemas frecuentes

### La aplicación no abre en el navegador

Esperar unos segundos y verificar si se abrió la dirección local en forma automática. Si no ocurre, abrir manualmente:

```text
http://127.0.0.1:5000
```

### No puedo cargar un archivo

Verificar que el formato esté entre los admitidos y que no supere el tamaño permitido.

### La transcripción demora demasiado

La duración del proceso depende del tamaño del audio, de la cantidad de archivos y de la capacidad del equipo.

### No aparece el archivo ZIP

Verificar que la opción Incluir ZIP haya estado activada antes de iniciar la corrida.

### No encuentro una corrida anterior

Actualizar la sección Historial con el botón correspondiente.

## 12. Cierre de la aplicación

La aplicación funciona sobre un servicio local. Cuando no se necesite continuar trabajando, cerrar la ventana del navegador y, si correspondiera, cerrar la aplicación desde su proceso local.

## 13. Alcance institucional

El sistema es de uso interno ENACOM y está destinado a tareas operativas vinculadas al análisis de audio y generación de reportes.
