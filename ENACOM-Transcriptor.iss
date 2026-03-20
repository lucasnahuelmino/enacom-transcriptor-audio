; =============================================================================
; ENACOM Transcriptor v3.0 — Instalador Standalone (PyInstaller)
;
; Precondiciones:
;   1) npm run build en frontend/
;   2) pyinstaller ENACOM-Transcriptor-standalone.spec (en raíz del repo)
;
; Resultado esperado para empaquetar:
;   - dist\ENACOM-Transcriptor\ENACOM-Transcriptor.exe
;   - tools\ffmpeg\...
;   - tools\models\...
;
; Salida del instalador:
;   Output\ENACOM-Transcriptor-standalone-v3.0-Setup.exe
; =============================================================================

#define AppName      "ENACOM Transcriptor"
#define AppVersion   "3.0"
#define AppPublisher "ENACOM — Dirección Nacional de Control y Fiscalización"
#define AppURL       "https://www.enacom.gob.ar"
#define AppExeName   "ENACOM-Transcriptor.exe"

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
OutputBaseFilename=ENACOM-Transcriptor-standalone-v3.0-Setup
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

[Tasks]
Name: "desktopicon";   Description: "Crear acceso directo en el &Escritorio";  GroupDescription: "Accesos directos:"
Name: "startmenuicon"; Description: "Crear acceso directo en el menú &Inicio"; GroupDescription: "Accesos directos:"

[Files]
; Runtime standalone generado por PyInstaller
Source: "dist\ENACOM-Transcriptor\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Recursos externos requeridos por run_standalone.py
Source: "tools\ffmpeg\*"; DestDir: "{app}\tools\ffmpeg"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "tools\models\*"; DestDir: "{app}\tools\models"; Flags: ignoreversion recursesubdirs createallsubdirs

; Íconos / branding para accesos directos y desinstalador
Source: "assets\enacom.ico"; DestDir: "{app}\assets"; Flags: ignoreversion

[Dirs]
; Persistencia de archivos generados por la app
Name: "{app}\storage"
Name: "{app}\storage\uploads"
Name: "{app}\storage\outputs"
Name: "{app}\logs"

[Icons]
Name: "{autodesktop}\{#AppName}"; \
  Filename: "{app}\{#AppExeName}"; \
  WorkingDir: "{app}"; \
  IconFilename: "{app}\assets\enacom.ico"; \
  Tasks: desktopicon; \
  Comment: "Iniciar ENACOM Transcriptor v3.0"

Name: "{group}\{#AppName}"; \
  Filename: "{app}\{#AppExeName}"; \
  WorkingDir: "{app}"; \
  IconFilename: "{app}\assets\enacom.ico"; \
  Tasks: startmenuicon

Name: "{group}\Desinstalar {#AppName}"; \
  Filename: "{uninstallexe}"

[Run]
Filename: "{app}\{#AppExeName}"; \
  WorkingDir: "{app}"; \
  Description: "Iniciar ENACOM Transcriptor ahora"; \
  Flags: postinstall nowait unchecked

[Code]
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
    'Los archivos en storage\\ no serán eliminados.',
    mbConfirmation, MB_YESNO
  ) = IDYES;
end;
