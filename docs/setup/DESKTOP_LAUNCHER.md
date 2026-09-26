# VDock Desktop Launcher - Quick Setup

## 🚀 Simplest Way to Launch VDock

Copy `Launch-VDock.bat` to your desktop and double-click it!

## Quick Start

### Option 1: Manual Copy (Fastest)

1. **Find** `Launch-VDock.bat` in the VDock folder
2. **Right-click** → **Copy**
3. **Right-click** on Desktop → **Paste Shortcut**
4. **Rename** to "VDock" (optional)
5. **Double-click** to launch!

### Option 2: Automated Shortcut Creator (With Icon)

Run this command in the VDock folder:

```cmd
scripts\create-desktop-shortcut.bat
```

This creates a shortcut on your desktop with the VDock icon.

## 🎯 Launch Process

When you double-click the launcher:

1. ✓ Checks for Python and Node.js
2. ✓ Verifies virtual environment is set up
3. ✓ Starts backend server (port 5000)
4. ✓ Starts frontend server (port 3000)
5. ✓ Opens VDock in your browser automatically

**First launch:** May take 10-30 seconds  
**Subsequent launches:** ~10 seconds

## 📋 Requirements

Before first launch, make sure you've run:

```cmd
setup.bat
```

This sets up all dependencies.

## 🔐 Default Login

- **Username:** `admin`
- **Password:** `admin`

⚠️ Change these after first login!

## 🎨 Customization

### Pin to Taskbar

1. Right-click the launcher → **Pin to taskbar**
2. Click the pinned icon anytime to launch

### Run on Startup

1. Copy launcher to Startup folder (`Win+R` → `shell:startup`)
2. VDock will launch automatically when you log in

### Run Minimized

1. Right-click launcher → **Properties**
2. Under "Run:", select **"Minimized"**
3. No console windows will appear

## 🛠️ Troubleshooting

### "Python not found"
- Install Python from https://python.org
- Check "Add Python to PATH" during installation

### "Node.js not found"
- Install Node.js from https://nodejs.org

### "Virtual environment not found"
- Run `setup.bat` first to set up dependencies

### Port already in use
- Close any apps using ports 3000 or 5000
- Or modify ports in config files

## 📂 Files

- **`Launch-VDock.bat`** - Simple batch launcher (use this!)
- **`scripts/create-desktop-shortcut.bat`** - Creates proper shortcut
- **`dist/VDock-Launcher.exe`** - Compiled EXE version (optional)

## ✅ That's It!

Your desktop launcher is ready. Just double-click and start using VDock!

---

*For more details, see: `docs/QUICK_START_DESKTOP.md`*

