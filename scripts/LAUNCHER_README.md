# VDock Launcher Setup Guide

This guide explains how to create and use the VDock launcher executable.

## Overview

There are three ways to launch VDock:

1. **Simple Batch Launcher** - `Launch-VDock.bat` (included with installer)
2. **PowerShell Launcher** - `Launch-VDock.ps1` (included with installer)
3. **Compiled EXE Launcher** - `VDock-Launcher.exe` (built with PyInstaller)

## Building the EXE Launcher

### Prerequisites
- Python 3.8+
- PyInstaller (will be installed automatically)
- Administrator access (recommended)

### Option 1: Build with Default Icon
```powershell
.\scripts\build-launcher.ps1
```

### Option 2: Build with Custom Icon
First, create the icon:
```powershell
.\scripts\create-icon.ps1
```

Then build with the icon:
```powershell
.\scripts\build-launcher.ps1 -WithIcon
```

### Build Output
The compiled executable will be created at:
```
.\dist\VDock-Launcher.exe
```

## Using the Launcher

### Method 1: Command Line
```cmd
VDock-Launcher.exe
```

### Method 2: Desktop Shortcut
1. Right-click `VDock-Launcher.exe` → **Create shortcut**
2. Move shortcut to Desktop
3. Right-click shortcut → **Properties** → **Advanced** → check "Run as administrator"
4. Double-click to launch

### Method 3: Taskbar Pin
1. Right-click `VDock-Launcher.exe` → **Pin to taskbar**
2. Click the pinned icon to launch

### Method 4: Start Menu Shortcut
1. Press `Win + R`, type `shell:startup`
2. Create shortcut in the Startup folder
3. Shortcut will launch VDock on system startup

## What the Launcher Does

When you run VDock-Launcher.exe, it:

1. ✓ Checks for Python and Node.js installation
2. ✓ Verifies the virtual environment setup
3. ✓ Starts the backend Flask server (port 5000)
4. ✓ Starts the frontend Vite server (port 3000)
5. ✓ Opens VDock in your default browser
6. ✓ Keeps servers running in background

## Troubleshooting

### "Python not found" error
- Ensure Python 3.8+ is installed
- Add Python to system PATH:
  1. Go to Environment Variables
  2. Add Python installation directory to PATH
  3. Restart the launcher

### "Node.js not found" error
- Download and install from https://nodejs.org/
- Add Node.js to system PATH if not automatically added
- Restart the launcher

### "Virtual environment not found" error
1. Run `install.bat` first to set up dependencies
2. Wait for installation to complete
3. Then launch the app

### Port already in use
- If 3000 or 5000 are busy, modify:
  - Backend: `backend/config.py` → change `PORT = 5000`
  - Frontend: `frontend/vite.config.js` → change server port

### Launcher closes immediately
1. Run from Command Prompt to see error messages:
   ```cmd
   cmd /k VDock-Launcher.exe
   ```
2. Check error output to diagnose issue
3. Ensure install.bat was run successfully

## Building the Full Installer

To create a complete installer package for distribution:

```powershell
.\scripts\build-installer.ps1
```

This creates:
- `dist/VDock-Portable/` - Complete portable VDock folder
- `dist/VDock-Portable.zip` - Compressed archive for distribution

## System Requirements

- **OS**: Windows 10 or later
- **Python**: 3.8+
- **Node.js**: 16+
- **RAM**: 4GB minimum (8GB recommended)
- **Disk Space**: 2GB (includes dependencies)
- **Ports**: 3000, 5000 (must be available)

## Default Credentials

- **Username**: admin
- **Password**: admin

⚠️ Change these on first login!

## File Structure

```
VDock/
├── VDock-Launcher.exe          ← Run this to launch
├── VDock-Launcher.py           ← Source code for launcher
├── Launch-VDock.bat            ← Alternative batch launcher
├── Launch-VDock.ps1            ← Alternative PowerShell launcher
├── install.bat                 ← Run once for setup
├── backend/                    ← Flask server
├── frontend/                   ← Vue.js application
├── docs/                       ← Documentation
└── scripts/                    ← Build scripts
    ├── build-launcher.ps1      ← Build EXE launcher
    ├── build-installer.ps1     ← Build distribution package
    ├── create-icon.ps1         ← Generate icon
    └── LAUNCHER_README.md      ← This file
```

## Advanced Usage

### Running without GUI
To run headless (no window):
1. Create a shortcut to VDock-Launcher.exe
2. Edit shortcut target: Add `-WindowStyle Hidden` to PowerShell version
3. Use VDock via browser at http://localhost:3000

### Custom Configuration
Edit configuration before launching:
- Backend: `backend/config.py`
- Frontend: `frontend/.env` or `frontend/vite.config.js`

### Debugging
Run launcher from PowerShell to see debug output:
```powershell
& ".\dist\VDock-Launcher.exe"
```

## Building for Distribution

For production distribution:

1. Build installer:
   ```powershell
   .\scripts\build-installer.ps1
   ```

2. Test in clean environment:
   - Extract to new folder
   - Run install.bat
   - Run launcher

3. Create installer with NSIS (optional):
   - Download NSIS from https://nsis.sourceforge.io/
   - Modify VDock.nsi as needed
   - Run: `makensis VDock.nsi`

## Support

For issues:
1. Check error messages in console
2. Review troubleshooting section above
3. Check `backend/logs/vdock.log` for server errors
4. Check browser console (F12) for frontend errors

## License

See LICENSE file in the main VDock directory.
