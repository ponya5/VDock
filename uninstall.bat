@echo off
setlocal EnableDelayedExpansion

REM ============================================================
REM  VDock Uninstall — source checkout
REM  Removes everything VDock installed or generated: processes,
REM  startup entry, desktop shortcut, agent hooks, Python venv,
REM  node_modules, the built frontend, logs and the Electron
REM  profile. Asks whether to also delete profiles and settings.
REM  The source folder stays so setup.bat can reinstall from it.
REM
REM  Non-interactive:  uninstall.bat --yes             keep profiles/settings
REM                    uninstall.bat --yes --complete  delete them too
REM ============================================================

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

set "COMPLETE="
set "UNATTENDED="
for %%a in (%*) do (
    if /i "%%~a"=="--yes" set "UNATTENDED=1"
    if /i "%%~a"=="--complete" set "COMPLETE=1"
)
if defined UNATTENDED goto :run

echo.
echo   ========================================================
echo     VDock Uninstall
echo   ========================================================
echo.
echo     Removes VDock from this PC: stops it, removes the
echo     startup entry, desktop shortcut and agent hooks, and
echo     deletes the installed dependencies, built frontend,
echo     logs and app cache.
echo.
echo     [1] Keep my profiles and settings (recommended)
echo         Running setup.bat later restores the same deck.
echo.
echo     [2] Complete uninstall
echo         Also deletes profiles, settings, uploads, themes,
echo         plugins and integration keys. Cannot be undone.
echo.
echo     [3] Cancel
echo.
set "MODE="
set /p "MODE=  Choose an option [1-3]: "
if "!MODE!"=="1" goto :run
if "!MODE!"=="2" (
    echo.
    set "CONFIRM="
    set /p "CONFIRM=  Delete all profiles and settings too? Type YES to confirm: "
    if /i "!CONFIRM!"=="YES" (
        set "COMPLETE=1"
        goto :run
    )
)
echo   Aborted. Nothing was changed.
exit /b 0

:run
echo.
echo   [1/6] Stopping VDock processes...

REM Ports the source install runs on. Read them from the .env files
REM setup wrote, falling back to the factory defaults.
set "BACKEND_PORT=5000"
set "FRONTEND_PORT=3000"
if exist "%ROOT%\backend\.env" (
    for /f "usebackq tokens=1,* delims==" %%a in (`findstr /b "PORT=" "%ROOT%\backend\.env"`) do set "BACKEND_PORT=%%b"
)
if exist "%ROOT%\frontend\.env" (
    for /f "usebackq tokens=1,* delims==" %%a in (`findstr /b "VITE_PORT=" "%ROOT%\frontend\.env"`) do set "FRONTEND_PORT=%%b"
)

REM Kill listeners on both ports plus any process whose command line
REM points inside this folder or names VDock-Launcher.py (the launcher
REM starts it with a relative path). Explicitly never match cmd.exe or
REM this script — CommandLine would contain %ROOT% and we'd kill the
REM shell running this file.
powershell -NoProfile -NonInteractive -Command ^
  "$root = '%ROOT%';" ^
  "$ports = @(%BACKEND_PORT%, %FRONTEND_PORT%);" ^
  "$pids = @();" ^
  "foreach ($port in $ports) {" ^
  "  try { Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction Stop | ForEach-Object { $pids += $_.OwningProcess } } catch {};" ^
  "}" ^
  "$procs = Get-CimInstance Win32_Process | Where-Object {" ^
  "  $_.Name -notmatch '^(cmd|powershell|pwsh)\.exe$' -and" ^
  "  $_.CommandLine -and" ^
  "  ($_.CommandLine.Contains($root) -or $_.CommandLine.Contains('VDock-Launcher.py') -or $_.CommandLine.Contains('vdock-backend'))" ^
  "};" ^
  "foreach ($p in $procs) { $pids += $p.ProcessId };" ^
  "foreach ($id in ($pids | Sort-Object -Unique)) {" ^
  "  try { Stop-Process -Id $id -Force -ErrorAction Stop; Write-Host ('   stopped pid ' + $id) } catch {}" ^
  "};" ^
  "if ($pids) { Start-Sleep -Seconds 2 }"
echo   [OK]    Process sweep done

echo.
echo   [2/6] Removing agent hooks...
REM Runs before the venv is deleted: the remover uses the backend's own
REM hook code and only touches VDock's entries.
set "HOOK_PY="
if exist "%ROOT%\backend\venv\Scripts\python.exe" (
    set "HOOK_PY=%ROOT%\backend\venv\Scripts\python.exe"
) else (
    where python >nul 2>&1
    if not errorlevel 1 set "HOOK_PY=python"
)
if defined HOOK_PY (
    "!HOOK_PY!" "%ROOT%\backend\scripts\remove_agent_hooks.py"
    if errorlevel 1 echo   [WARN]  Could not check agent hooks ^(needs the VDock Python venv^)
) else (
    echo   [ --]   Python not found - skipped agent hook removal
)

echo.
echo   [3/6] Removing startup entry...
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v VDock /f >nul 2>&1
if errorlevel 1 (
    echo   [ --]   No startup entry found
) else (
    echo   [OK]    Removed VDock from Windows startup
)

echo.
echo   [4/6] Removing desktop shortcut...
if not defined DESKTOP_DIR (
    for /f "usebackq delims=" %%d in (`powershell -NoProfile -NonInteractive -Command "[Environment]::GetFolderPath('Desktop')"`) do set "DESKTOP_DIR=%%d"
)
if not defined DESKTOP_DIR set "DESKTOP_DIR=%USERPROFILE%\Desktop"
if exist "%DESKTOP_DIR%\VDock.lnk" (
    del "%DESKTOP_DIR%\VDock.lnk" >nul 2>&1
    echo   [OK]    Removed %DESKTOP_DIR%\VDock.lnk
) else (
    echo   [ --]   No desktop shortcut found
)

echo.
echo   [5/6] Removing installed files...
set "LEFTOVER="
for %%p in (
    "backend\venv"
    "backend\.pytest_cache"
    "frontend\node_modules"
    "frontend\electron\node_modules"
    "frontend\dist"
    "frontend\.vite"
) do (
    if exist "%ROOT%\%%~p" (
        rmdir /s /q "%ROOT%\%%~p" 2>nul
        if exist "%ROOT%\%%~p" (
            echo   [WARN]  Could not fully remove %%~p ^(a file is in use^)
            set "LEFTOVER=1"
        ) else (
            echo   [OK]    Removed %%~p
        )
    )
)
del /q "%ROOT%\frontend\*.tsbuildinfo" 2>nul
for /d /r "%ROOT%\backend" %%d in (__pycache__) do if exist "%%d" rmdir /s /q "%%d" 2>nul
for /d /r "%ROOT%\scripts" %%d in (__pycache__) do if exist "%%d" rmdir /s /q "%%d" 2>nul
del /q "%ROOT%\backend\data\*.log" "%ROOT%\backend\data\*.log.*" "%ROOT%\backend\data\now_playing_art.bin" 2>nul
echo   [OK]    Removed caches and logs

REM The VDock window's Electron profile: HTTP + service-worker caches
REM (which can keep serving an old frontend), local storage, GPU caches.
if exist "%APPDATA%\vdock-electron" (
    rmdir /s /q "%APPDATA%\vdock-electron" 2>nul
    if exist "%APPDATA%\vdock-electron" (
        echo   [WARN]  Could not fully remove %APPDATA%\vdock-electron
        set "LEFTOVER=1"
    ) else (
        echo   [OK]    Removed app cache %APPDATA%\vdock-electron
    )
)

echo.
echo   [6/6] Profiles and settings...
if not defined COMPLETE (
    echo   [OK]    Kept profiles, settings and integration keys
    echo           ^(backend\data, backend\.env, frontend\.env^)
    goto :done
)
del /q "%ROOT%\backend\.env" "%ROOT%\frontend\.env" 2>nul
REM Delete everything in backend\data except the files that ship with
REM VDock (config.example.json, templates\, the .gitkeep placeholders),
REM so the checkout is left exactly as cloned.
powershell -NoProfile -NonInteractive -Command ^
  "$data = '%ROOT%\backend\data';" ^
  "if (Test-Path -LiteralPath $data) {" ^
  "  Get-ChildItem -LiteralPath $data -Force | Where-Object { @('config.example.json', 'templates') -notcontains $_.Name } | ForEach-Object {" ^
  "    if ($_.PSIsContainer) {" ^
  "      Get-ChildItem -LiteralPath $_.FullName -Force | Where-Object { $_.Name -ne '.gitkeep' } | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue" ^
  "    } else { Remove-Item -LiteralPath $_.FullName -Force -ErrorAction SilentlyContinue }" ^
  "  }" ^
  "}"
echo   [OK]    Deleted profiles, settings, uploads and integration keys

:done
echo.
echo   ========================================================
echo     VDock is uninstalled.
if defined LEFTOVER (
    echo     Some files were in use - close any VDock or editor
    echo     windows and run uninstall.bat again to finish.
)
echo.
echo     To reinstall fresh: run setup.bat.
echo     To remove VDock for good: delete this folder:
echo       %ROOT%
echo   ========================================================
echo.
if not defined UNATTENDED pause
exit /b 0
