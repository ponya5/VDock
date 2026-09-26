# DL-072: Release-readiness audit — install paths, packaging, repo hygiene

## Background

Goal: the repo must be publishable — `setup.bat`/`setup.sh` installs must
work on Windows and macOS, and no junk or sensitive data should ship.

## Findings

**Working (kept):** `setup.sh`/`setup.bat` → venv + platform-marked
requirements (pywin32/pycaw/comtypes/python-magic-bin are win32-only via
`sys_platform` markers) → npm installs → data dirs → `.env` → ports →
desktop launcher. `launch.sh`/`launch.bat` → `scripts/VDock-Launcher.py`
(cross-platform: `bin/python` on POSIX, `Scripts/python.exe` on Windows;
`VDOCK_SKIP_BACKEND_SPAWN` prevents Electron double-spawn). CI covers
py3.9/3.12 backend tests + frontend typecheck/test/build.

**Fixed:**

- `frontend/electron/main.js` dev spawn hardcoded `venv\Scripts\python.exe`
  (Windows-only — `npx electron .` on macOS could never start the backend).
  Now `bin/python` on POSIX. Prod spawn tries a bundled interpreter, else
  falls back to system `python3`/`python` instead of a guaranteed-missing
  `resourcesPath/backend/python.exe`.
- `scripts/VDock.nsi`: referenced missing `install.bat` (makensis fatal)
  and shortcutted `VDock-Launcher.exe` that was never copied into
  `$INSTDIR`. Now files `setup.bat` and shortcuts point at `launch.bat`.
  Also `$PROGRAMFILES` + `RequestExecutionLevel admin` → `$LOCALAPPDATA` +
  `user`: the backend writes `backend/data` under the install dir, so a
  Program Files install could never save profiles.
- `build-launcher.ps1`: resolved the launcher two dirs above the repo
  (`$ProjectRoot` double-parent bug) at `VDock-Launcher.py` root — it
  lives in `scripts/`. Fixed to `Join-Path $ScriptDir`.
- `build-installer.ps1`: copied nonexistent `install.bat`/`install.sh`/
  `launch.ps1` → now `setup.bat`/`setup.sh`; generated docs/launcher text
  referenced `install.bat` → `setup.bat`.
- Docs: stale `install.bat` refs in `LAUNCHER_README.md`,
  `QUICK_REFERENCE.md`, `DESKTOP_LAUNCHER.md` → `setup.bat`.
- Deleted empty stub `scripts/VDock-Launcher.spec` (build-launcher.ps1
  passes PyInstaller args directly; an empty spec only confuses).
- Untracked/removed junk: `backend/_diff{1,2,3}.txt`,
  `frontend/tsconfig.app.tsbuildinfo`, root `nul`; `.gitignore` gained
  `*.tsbuildinfo` + `_diff*.txt`.

**Verified clean:** no secrets/tokens/passwords/personal paths in tracked
files (`.env` ignored; only `.env.example` templates tracked); `backend/data`
tracks only shipped templates + `.gitkeep`s; `setup.sh`/`launch.sh` keep
mode 100755; `bash -n`, `py_compile`, `node --check` all pass.

## Known limitations (documented, not fixed)

- **electron-builder packaging is incomplete by design**: it bundles
  backend *source* but no frozen interpreter, so `npm run build-win`
  produces an app that still needs Python+deps on the host. The supported
  install path is the setup scripts / PyInstaller launcher / NSIS.
- Backend window-control features (focus/flash/keystroke targeting) are
  Windows-only; they degrade gracefully on macOS (guarded imports,
  `platform.system()` checks) — the app runs, those actions no-op.
- macOS has no `.app` bundle — install is source + `VDock.command`
  desktop launcher.
- `.devin/` skills are tracked (agent tooling, no secrets) — kept.
