; =============================================================================
; ENACOM Transcriptor v3.0 — Script de instalación Inno Setup
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
Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
OutputDir=Output
OutputBaseFilename=ENACOM-Transcriptor-v3.0-Setup
WizardStyle=modern
WizardSizePercent=120
SetupIconFile=assets\enacom.ico
UninstallDisplayIcon={app}\assets\enacom.ico
WizardImageFile=assets\wizard-banner.bmp
WizardSmallImageFile=assets\wizard-icon.bmp
RestartIfNeededByRun=no
DisableWelcomePage=no

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[CustomMessages]
spanish.InstallingPython=Instalando Python 3.11...
spanish.InstallingNode=Instalando Node.js 20 LTS...
spanish.InstallingDeps=Instalando dependencias (puede tardar varios minutos)...
spanish.Done=Instalación completada.

[Tasks]
Name: "desktopicon";   Description: "Crear acceso directo en el &Escritorio";  GroupDescription: "Accesos directos:"
Name: "startmenuicon"; Description: "Crear acceso directo en el menú &Inicio"; GroupDescription: "Accesos directos:"

[Files]
; ── Código fuente ─────────────────────────────────────────────────
Source: "backend\*";  DestDir: "{app}\backend";  Flags: ignoreversion recursesubdirs createallsubdirs; \
  Excludes: "venv\*,storage\uploads\*,storage\outputs\*,__pycache__\*,*.pyc,*.log"

Source: "frontend\*"; DestDir: "{app}\frontend"; Flags: ignoreversion recursesubdirs createallsubdirs; \
  Excludes: "node_modules\*,dist\*,*.log"

; ── Tools portables — excluir npm-cache para no copiar dos veces ──
Source: "tools\*"; DestDir: "{app}\tools"; Flags: ignoreversion recursesubdirs createallsubdirs; \
  Excludes: "npm-cache\*"

; ── Cache npm para instalación offline ────────────────────────────
Source: "tools\npm-cache\*"; DestDir: "{app}\tools\npm-cache"; Flags: ignoreversion recursesubdirs createallsubdirs

; ── Scripts y docs ────────────────────────────────────────────────
Source: "INICIAR.bat";    DestDir: "{app}"; Flags: ignoreversion
Source: "INSTALACION.md"; DestDir: "{app}"; Flags: ignoreversion

; ── Assets ────────────────────────────────────────────────────────
Source: "assets\enacom.ico"; DestDir: "{app}\assets"; Flags: ignoreversion

; ── Post-install (queda en disco para diagnóstico) ────────────────
Source: "setup\post-install.bat"; DestDir: "{app}"; Flags: ignoreversion

; ── Python 3.11 ───────────────────────────────────────────────────
Source: "redist\python-3.11.9-amd64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

; ── Node.js 20 LTS ────────────────────────────────────────────────
Source: "redist\node-v20.19.0-x64.msi"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{autodesktop}\{#AppName}"; \
  Filename: "{app}\INICIAR.bat"; \
  WorkingDir: "{app}"; \
  IconFilename: "{app}\assets\enacom.ico"; \
  Tasks: desktopicon; \
  Comment: "Iniciar ENACOM Transcriptor v3.0"

Name: "{group}\{#AppName}"; \
  Filename: "{app}\INICIAR.bat"; \
  WorkingDir: "{app}"; \
  IconFilename: "{app}\assets\enacom.ico"; \
  Tasks: startmenuicon

Name: "{group}\Desinstalar {#AppName}"; \
  Filename: "{uninstallexe}"

[Dirs]
Name: "{app}\backend\storage\uploads"
Name: "{app}\backend\storage\outputs"
Name: "{app}\logs"

[Run]
; ── 1. Python ─────────────────────────────────────────────────────
Filename: "{tmp}\python-3.11.9-amd64.exe"; \
  Parameters: "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_doc=0"; \
  StatusMsg: "{cm:InstallingPython}"; \
  Check: not IsPythonInstalled

; ── 2. Node.js ────────────────────────────────────────────────────
Filename: "msiexec.exe"; \
  Parameters: "/i ""{tmp}\node-v20.19.0-x64.msi"" /quiet /norestart ADDLOCAL=ALL"; \
  StatusMsg: "{cm:InstallingNode}"; \
  Check: not IsNodeInstalled

; ── 3. Post-install (venv + pip + npm) ────────────────────────────
Filename: "{cmd}"; \
  Parameters: "/c ""{app}\post-install.bat"" ""{app}"""; \
  WorkingDir: "{app}"; \
  StatusMsg: "{cm:InstallingDeps}"; \
  Flags: runhidden

; ── 4. Abrir app al finalizar (opcional) ──────────────────────────
Filename: "{app}\INICIAR.bat"; \
  WorkingDir: "{app}"; \
  Description: "Iniciar ENACOM Transcriptor ahora"; \
  Flags: postinstall nowait unchecked shellexec

[Code]

function IsPythonInstalled: Boolean;
var
  PythonPath: string;
begin
  Result := False;
  if RegQueryStringValue(HKLM, 'SOFTWARE\Python\PythonCore\3.13\InstallPath', '', PythonPath) then begin Result := True; Exit; end;
  if RegQueryStringValue(HKLM, 'SOFTWARE\Python\PythonCore\3.12\InstallPath', '', PythonPath) then begin Result := True; Exit; end;
  if RegQueryStringValue(HKLM, 'SOFTWARE\Python\PythonCore\3.11\InstallPath', '', PythonPath) then begin Result := True; Exit; end;
  if RegQueryStringValue(HKLM, 'SOFTWARE\Python\PythonCore\3.10\InstallPath', '', PythonPath) then begin Result := True; Exit; end;
  if RegQueryStringValue(HKCU, 'SOFTWARE\Python\PythonCore\3.13\InstallPath', '', PythonPath) then begin Result := True; Exit; end;
  if RegQueryStringValue(HKCU, 'SOFTWARE\Python\PythonCore\3.12\InstallPath', '', PythonPath) then begin Result := True; Exit; end;
  if RegQueryStringValue(HKCU, 'SOFTWARE\Python\PythonCore\3.11\InstallPath', '', PythonPath) then begin Result := True; Exit; end;
  if RegQueryStringValue(HKCU, 'SOFTWARE\Python\PythonCore\3.10\InstallPath', '', PythonPath) then begin Result := True; Exit; end;
end;

function IsNodeInstalled: Boolean;
var
  NodePath: string;
begin
  Result := False;
  if RegQueryStringValue(HKLM, 'SOFTWARE\Node.js', 'InstallPath', NodePath) then begin Result := True; Exit; end;
  if FileExists(ExpandConstant('{pf}\nodejs\node.exe')) then begin Result := True; Exit; end;
end;

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

function InitializeUninstall: Boolean;
begin
  Result := MsgBox(
    '¿Confirma que desea desinstalar ENACOM Transcriptor?' + #13#10 + #13#10 +
    'Los archivos en backend\storage\ NO serán eliminados.',
    mbConfirmation, MB_YESNO
  ) = IDYES;
end;
