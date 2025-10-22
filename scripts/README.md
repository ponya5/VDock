# VDock Scripts Directory

This directory contains utility scripts for VDock setup, building, and deployment.

## 📋 Script Overview

### 🚀 Launchers

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `build-launcher.ps1` | Build VDock-Launcher.exe | When you want a standalone EXE |
| `create-desktop-shortcut.bat` | Create desktop shortcut | Quick access to VDock |

### 📦 Build Scripts

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `build-installer.bat` | Build Electron installer | Production distribution |
| `build-installer.ps1` | PowerShell build script | Alternative to batch version |
| `build-portable.bat` | Create portable package | Portable distribution |
| `create-icon.ps1` | Generate app icon | Creating custom icon |

### 🔧 Development Scripts

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `setup.bat` | Initial setup | First-time installation |
| `start_backend.bat` | Start backend only | Development mode |
| `start_frontend.bat` | Start frontend only | Development mode |
| `restart_backend.bat` | Restart backend | After backend changes |
| `verify_launch.bat` | Check if servers running | Troubleshooting |

### 🚢 Deployment Scripts

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `deploy.bat` | Docker deployment | Production with Docker |
| `deploy.sh` | Linux deployment | Linux production |

## 🎯 Quick Reference

### For End Users

**Simplest setup:**
1. Run `install.bat` (in root directory)
2. Copy `Launch-VDock.bat` to desktop
3. Double-click to launch

**Create desktop shortcut:**
```cmd
scripts\create-desktop-shortcut.bat
```

### For Developers

**Build launcher EXE:**
```powershell
.\scripts\build-launcher.ps1
```

**Build portable package:**
```cmd
scripts\build-portable.bat
```

**Build installer:**
```cmd
scripts\build-installer.bat
```

## 📁 Files Removed (Redundant)

The following redundant scripts were removed:

- ~~`build-vdock-exe.bat`~~ → Use `build-launcher.ps1` instead
- ~~`create_shortcut.bat`~~ → Use `create-desktop-shortcut.bat` instead
- ~~`create-distribution.bat`~~ → Use `build-portable.bat` instead
- ~~`launch_fixed.bat`~~ → Use root `Launch-VDock.bat` instead
- ~~`VDock-Launcher.vbs`~~ → No longer needed

## 🔍 Script Purposes

### `VDock-Launcher.py`
Python launcher source code. Used to build `VDock-Launcher.exe`.

### `VDock-Launcher.spec`
PyInstaller spec file for building the EXE.

### `VDock.nsi`
NSIS installer script for creating Windows installer.

### `LAUNCHER_README.md`
Detailed launcher documentation.

## 📖 Documentation

- **Desktop Launcher**: `DESKTOP_LAUNCHER.md` (root)
- **Portable Distribution**: `docs/deployment/PORTABLE_DISTRIBUTION.md`
- **Launcher Guide**: `scripts/LAUNCHER_README.md`

## ⚙️ Recommended Workflow

### Fresh Installation
1. Run `install.bat` in root directory
2. Run `scripts\create-desktop-shortcut.bat`
3. Launch from desktop shortcut

### Daily Use
- Double-click desktop shortcut
- Or use `Launch-VDock.bat` in root directory

### Building for Distribution
1. `scripts\build-launcher.ps1` - Create EXE
2. `scripts\build-portable.bat` - Create portable zip
3. `scripts\build-installer.bat` - Create installer

## 🎉 Summary

All redundant scripts have been removed. Use:
- **`Launch-VDock.bat`** for simple launching
- **`scripts\create-desktop-shortcut.bat`** for desktop shortcut
- **`scripts\build-launcher.ps1`** for EXE building

That's it! Simple and clean. 🚀

