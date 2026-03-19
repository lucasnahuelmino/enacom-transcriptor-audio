' =============================================================
' iniciar-servicios.vbs - ENACOM Transcriptor v3.0
' Lanza Redis, Celery, Flask y Vite completamente ocultos.
' Recibe la ruta raiz como argumento: cscript iniciar-servicios.vbs "C:\ruta\"
' =============================================================

Dim oShell, oFSO
Dim sRoot, sBackend, sFrontend, sLogs
Dim sRedis, sCelery, sFlask, sVite

Set oShell = CreateObject("WScript.Shell")
Set oFSO   = CreateObject("Scripting.FileSystemObject")

' Ruta raiz (pasada como argumento o detectada automaticamente)
If WScript.Arguments.Count > 0 Then
    sRoot = WScript.Arguments(0)
Else
    sRoot = oFSO.GetParentFolderName(WScript.ScriptFullName) & "\"
End If

' Asegurar barra final
If Right(sRoot, 1) <> "\" Then sRoot = sRoot & "\"

sBackend  = sRoot & "backend\"
sFrontend = sRoot & "frontend\"
sLogs     = sRoot & "logs\"

' Crear carpeta logs si no existe
If Not oFSO.FolderExists(sLogs) Then
    oFSO.CreateFolder(sLogs)
End If

' ── 1. Redis ─────────────────────────────────────────────────────
Dim sRedisExe
sRedisExe = sRoot & "tools\redis\redis-server.exe"

If oFSO.FileExists(sRedisExe) Then
    sRedis = """" & sRedisExe & """"
    oShell.Run sRedis, 0, False
    WScript.Sleep 2000
End If

' ── 2. Celery worker ─────────────────────────────────────────────
sCelery = "cmd /c """ & _
    "cd /d """ & sBackend & """ && " & _
    "call venv\Scripts\activate.bat && " & _
    "celery -A celery_worker.celery_app worker --loglevel=info --pool=solo" & _
    " >> """ & sLogs & "celery.log"" 2>&1"""

oShell.Run sCelery, 0, False
WScript.Sleep 3000

' ── 3. Flask backend ─────────────────────────────────────────────
sFlask = "cmd /c """ & _
    "cd /d """ & sBackend & """ && " & _
    "call venv\Scripts\activate.bat && " & _
    "python run.py" & _
    " >> """ & sLogs & "backend.log"" 2>&1"""

oShell.Run sFlask, 0, False
WScript.Sleep 3000

' ── 4. Frontend Vite ─────────────────────────────────────────────
sVite = "cmd /c """ & _
    "cd /d """ & sFrontend & """ && " & _
    "npm run dev" & _
    " >> """ & sLogs & "frontend.log"" 2>&1"""

oShell.Run sVite, 0, False

Set oShell = Nothing
Set oFSO   = Nothing
