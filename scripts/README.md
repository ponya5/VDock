# Scripts Directory

Utility scripts for **maintainers and advanced users**. End users only need the root launchers:

| File | Purpose |
|------|---------|
| [`../setup.bat`](../setup.bat) / [`../setup.sh`](../setup.sh) | Interactive setup menu (install, shortcut, launch) |
| [`../launch.bat`](../launch.bat) / [`../launch.sh`](../launch.sh) | Start VDock (backend + frontend + Electron) |

## Core

| Script | Purpose |
|--------|---------|
| `VDock-Launcher.py` | Cross-platform launcher used by `launch.bat` / `launch.sh` |
| `create_desktop_shortcut.bat` | Wrapper for `setup.bat --shortcut` |
| `setup.bat` | Wrapper for root `setup.bat` |
| `setup.sh` | Wrapper for root `setup.sh` |

## Build & distribution (maintainers)

| Script | Purpose |
|--------|---------|
| `build-launcher.ps1` | Build standalone `VDock-Launcher.exe` with PyInstaller |
| `build-installer.ps1` | Build Electron installer package |
| `build-portable.bat` | Create portable distribution |
| `create-icon.ps1` | Generate or copy app icon |
| `VDock.nsi` | NSIS installer script |

## Deployment

| Script | Purpose |
|--------|---------|
| `deploy.bat` | Docker deployment (Windows) |
| `deploy.sh` | Docker deployment (Linux/macOS) |

## Removed scripts

These were development duplicates and are no longer needed:

- `scripts/launchers/*.bat` — replaced by root `launch.bat` + `VDock-Launcher.py`
- `scripts/setup.bat` (old 6-step copy) — replaced by root interactive setup
- `start_backend.bat` / `start_frontend.bat` — dev-only helpers with broken paths

See [`docs/development/LAUNCHER_README.md`](../docs/development/LAUNCHER_README.md) for launcher details.
