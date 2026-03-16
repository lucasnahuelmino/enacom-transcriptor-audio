; =============================================================================
; ENACOM Transcriptor v3.0 — Script de instalación Inno Setup
;
; Requisitos para compilar este script:
;   1. Inno Setup 6.x  →  https://jrsoftware.org/isinfo.php
;   2. Colocar en la carpeta  redist\  (al lado de este .iss):
;        redist\python-3.11.9-amd64.exe   (descargado de python.org)
;        redist\node-v20.19.0-x64.msi     (descargado de nodejs.org)
;   3. Colocar el ícono en:
;        assets\enacom.ico
;   4. Compilar con Inno Setup: Ctrl+F9 o Build → Compile
;
; El instalador resultante queda en:  Output\ENACOM-Transcriptor-v3.0-Setup.exe
; =============================================================================

#define AppName      "ENACOM Transcriptor"
#define AppVersion   "3.0"
#define AppPublisher "ENACOM — Dirección Nacional de Control y Fiscalización"
#define AppURL       "https://www.enacom.gob.ar"
#define AppExeName   "INICIAR.bat"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
DefaultDirName={autopf}\ENACOM\Transcriptor
DefaultGroupName={#AppName}
AllowNoIcons=no
; Compresión máxima — importante dado el tamaño del modelo Whisper
Compression=lzma2/ultra64
SolidCompression=yes
; Solo 64 bits
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; Requiere admin para instalar Python/Node en Program Files
PrivilegesRequired=admin
; Salida
OutputDir=Output
OutputBaseFilename=ENACOM-Transcriptor-v3.0-Setup
; Interfaz
WizardStyle=modern
WizardSizePercent=120
SetupIconFile=assets\enacom.ico
UninstallDisplayIcon={app}\assets\enacom.ico
; Licencia (opcional — crear un archivo LICENSE.txt si corresponde)
; LicenseFile=LICENSE.txt
; Pantalla de bienvenida
WizardImageFile=assets\wizard-banner.bmp
WizardSmallImageFile=assets\wizard-icon.bmp
; No reiniciar después de instalar
RestartIfNeededByRun=no
DisableWelcomePage=no

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[CustomMessages]
spanish.InstallingPython=Instalando Python 3.11...
spanish.InstallingNode=Instalando Node.js 20 LTS...
spanish.InstallingDeps=Instalando dependencias Python (puede tardar varios minutos)...
spanish.InstallingNodeDeps=Instalando dependencias Node.js...
spanish.CreatingVenv=Creando entorno virtual Python...
spanish.Done=Instalación completada.

; =============================================================================
; Tareas opcionales (casillas en el instalador)
; =============================================================================
[Tasks]
Name: "desktopicon";   Description: "Crear acceso directo en el &Escritorio";   GroupDescription: "Accesos directos:"
Name: "startmenuicon"; Description: "Crear acceso directo en el menú &Inicio";  GroupDescription: "Accesos directos:"

; =============================================================================
; Archivos a instalar
; =============================================================================
[Files]
; ── Código fuente ─────────────────────────────────────────────────
Source: "backend\*";    DestDir: "{app}\backend";    Flags: ignoreversion recursesubdirs createallsubdirs; \
  Excludes: "venv\*,storage\uploads\*,storage\outputs\*,__pycache__\*,*.pyc,*.log"

Source: "frontend\*";   DestDir: "{app}\frontend";   Flags: ignoreversion recursesubdirs createallsubdirs; \
  Excludes: "node_modules\*,dist\*,*.log"

; ── Tools portables (ffmpeg, Redis, modelo Whisper) ───────────────
Source: "tools\*";      DestDir: "{app}\tools";      Flags: ignoreversion recursesubdirs createallsubdirs

; ── Scripts de arranque ───────────────────────────────────────────
Source: "INICIAR.bat";         DestDir: "{app}"; Flags: ignoreversion
Source: "INSTALACION.md";      DestDir: "{app}"; Flags: ignoreversion

; ── Assets (ícono, etc.) ──────────────────────────────────────────
Source: "assets\enacom.ico";   DestDir: "{app}\assets"; Flags: ignoreversion

; ── Script de post-instalación ────────────────────────────────────
; Sin deleteafterinstall — queda en disco para poder diagnosticar si algo falla
Source: "setup\post-install.bat"; DestDir: "{app}"; Flags: ignoreversion

; ── Python 3.11 (incluido en redist\) ────────────────────────────
; Se instala solo si Python 3.10+ no está presente (ver sección [Code])
Source: "redist\python-3.11.9-amd64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

; ── Node.js 20 LTS (incluido en redist\) ─────────────────────────
Source: "redist\node-v20.19.0-x64.msi";  DestDir: "{tmp}"; Flags: deleteafterinstall

; =============================================================================
; Accesos directos
; =============================================================================
[Icons]
; Escritorio
Name: "{autodesktop}\{#AppName}"; \
  Filename: "{app}\INICIAR.bat"; \
  WorkingDir: "{app}"; \
  IconFilename: "{app}\assets\enacom.ico"; \
  Tasks: desktopicon; \
  Comment: "Iniciar ENACOM Transcriptor v3.0"

; Menú inicio
Name: "{group}\{#AppName}"; \
  Filename: "{app}\INICIAR.bat"; \
  WorkingDir: "{app}"; \
  IconFilename: "{app}\assets\enacom.ico"; \
  Tasks: startmenuicon

Name: "{group}\Desinstalar {#AppName}"; \
  Filename: "{uninstallexe}"

; =============================================================================
; Crear directorios necesarios en tiempo de instalación
; =============================================================================
[Dirs]
Name: "{app}\backend\storage\uploads"
Name: "{app}\backend\storage\outputs"
Name: "{app}\logs"

; =============================================================================
; Ejecutar post-instalación
; =============================================================================
[Run]
; ── 1. Python (silencioso, solo si no está instalado) ─────────────
; waituntilterminated es el default — no se necesita flag explícito
Filename: "{tmp}\python-3.11.9-amd64.exe"; \
  Parameters: "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_doc=0"; \
  StatusMsg: "{cm:InstallingPython}"; \
  Check: not IsPythonInstalled

; ── 2. Node.js (silencioso, solo si no está instalado) ────────────
Filename: "msiexec.exe"; \
  Parameters: "/i ""{tmp}\node-v20.19.0-x64.msi"" /quiet /norestart ADDLOCAL=ALL"; \
  StatusMsg: "{cm:InstallingNode}"; \
  Check: not IsNodeInstalled

; ── 3. Script de post-instalación (venv + pip + npm) ──────────────
; Los .bat no soportan runhidden si se llaman directo — se usa {cmd} /c
Filename: "{cmd}"; \
  Parameters: "/c ""{app}\post-install.bat"" ""{app}"""; \
  WorkingDir: "{app}"; \
  StatusMsg: "{cm:InstallingDeps}"; \
  Flags: runhidden

; ── 4. Abrir la app en el navegador (opcional, al finalizar) ──────
Filename: "{app}\INICIAR.bat"; \
  WorkingDir: "{app}"; \
  Description: "Iniciar ENACOM Transcriptor ahora"; \
  Flags: postinstall nowait unchecked shellexec

; =============================================================================
; Lógica Pascal para detección de Python y Node.js
; =============================================================================
[Code]

// ── Detección de Python 3.10+ ──────────────────────────────────────
function IsPythonInstalled: Boolean;
var
  PythonPath: string;
begin
  Result := False;

  // Buscar en registro (instalación para todos los usuarios)
  if RegQueryStringValue(HKLM, 'SOFTWARE\Python\PythonCore\3.11\InstallPath', '', PythonPath) then
  begin Result := True; Exit; end;
  if RegQueryStringValue(HKLM, 'SOFTWARE\Python\PythonCore\3.10\InstallPath', '', PythonPath) then
  begin Result := True; Exit; end;
  if RegQueryStringValue(HKLM, 'SOFTWARE\Python\PythonCore\3.12\InstallPath', '', PythonPath) then
  begin Result := True; Exit; end;

  // Buscar en registro (instalación solo usuario actual)
  if RegQueryStringValue(HKCU, 'SOFTWARE\Python\PythonCore\3.11\InstallPath', '', PythonPath) then
  begin Result := True; Exit; end;
  if RegQueryStringValue(HKCU, 'SOFTWARE\Python\PythonCore\3.10\InstallPath', '', PythonPath) then
  begin Result := True; Exit; end;
  if RegQueryStringValue(HKCU, 'SOFTWARE\Python\PythonCore\3.12\InstallPath', '', PythonPath) then
  begin Result := True; Exit; end;
end;

// ── Detección de Node.js 18+ ───────────────────────────────────────
function IsNodeInstalled: Boolean;
var
  NodePath: string;
begin
  Result := False;

  if RegQueryStringValue(HKLM, 'SOFTWARE\Node.js', 'InstallPath', NodePath) then
  begin Result := True; Exit; end;

  // Buscar node.exe en PATH como fallback
  if FileExists(ExpandConstant('{pf}\nodejs\node.exe')) then
  begin Result := True; Exit; end;
end;

// ── Advertencia si el equipo es 32 bits ───────────────────────────
function InitializeSetup: Boolean;
begin
  Result := True;
  if not Is64BitInstallMode then
  begin
    MsgBox(
      'ENACOM Transcriptor requiere Windows de 64 bits.' + #13#10 +
      'Este equipo no es compatible.',
      mbCriticalError, MB_OK
    );
    Result := False;
  end;
end;

// ── Confirmación al desinstalar ────────────────────────────────────
function InitializeUninstall: Boolean;
begin
  Result := MsgBox(
    '¿Confirma que desea desinstalar ENACOM Transcriptor?' + #13#10 + #13#10 +
    'Los archivos de transcripciones generadas en backend\storage\ ' +
    'NO serán eliminados.',
    mbConfirmation, MB_YESNO
  ) = IDYES;
end;
