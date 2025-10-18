# VDock - Easy Installation Guide

## 🚀 Quick Start

### Windows Users
1. Double-click `install.bat`
2. Wait for installation to complete
3. Double-click "VDock" shortcut on your desktop
4. Done! 🎉

### macOS / Linux Users
1. Open Terminal in VDock folder
2. Run: `chmod +x install.sh && ./install.sh`
3. Double-click "VDock.command" on desktop (macOS)
4. Done! 🎉

---

## 📦 What Gets Installed

- ✅ Python virtual environment
- ✅ Backend dependencies (Flask, etc.)
- ✅ Frontend dependencies (Vue, Vite, etc.)
- ✅ Data directories for profiles & uploads
- ✅ Desktop shortcut for easy launching

---

## 🎯 First Launch

1. **Start VDock** using desktop shortcut
2. **Browser opens** automatically to http://localhost:3000
3. **Login** with:
   - Username: `admin`
   - Password: `admin`
4. **Change password** in Settings!

---

## ⚙️ Features

### Auto-Start on Boot
1. Open VDock → Settings → Server Configuration
2. Enable "Start VDock on System Boot"
3. VDock will launch automatically when you start your computer!

### Desktop Launchers

**Windows:**
- `VDock-Launcher.vbs` - Silent launch (no console)
- `launch.bat` - Shows console with logs

**macOS:**
- `VDock.command` - Desktop launcher

**Linux:**
- `launch.sh` - Shell script launcher

---

## 🔧 System Requirements

### Required:
- **Python 3.9+** ([Download](https://www.python.org/downloads/))
- **Node.js 16+** ([Download](https://nodejs.org/))

### Recommended:
- **4GB RAM** minimum
- **500MB disk space**
- **Windows 10+**, **macOS 10.14+**, or **Linux** (Ubuntu 20.04+, Fedora 33+)

---

## 📖 Documentation

- **Full Installation Guide:** `docs/INSTALLATION.md`
- **User Guide:** `docs/USER_GUIDE.md`
- **Troubleshooting:** `docs/INSTALLATION.md#troubleshooting`

---

## ❓ Need Help?

### Quick Fixes

**Can't install?**
- Make sure Python & Node.js are installed
- Run installer as Administrator (Windows)

**Can't start?**
- Check if ports 5000 & 3000 are free
- Restart computer and try again

**Hotkeys not working?**
- Restart backend: run `restart_backend.bat`
- Make sure target application is focused

### Get Support

- **Email:** ponya81@gmail.com
- **GitHub Issues:** https://github.com/ponya5/VDock/issues
- **Documentation:** See `docs/` folder

---

## 🎨 What Can You Do With VDock?

- ⌨️ **Hotkeys** - Send keyboard shortcuts to apps
- 🚀 **Launch Programs** - Start applications with one click
- 🌐 **Open URLs** - Quick access to websites
- 📊 **System Metrics** - Monitor CPU, RAM, GPU
- 🎵 **Media Controls** - Volume, playback, brightness
- 🤖 **Macros** - Automate multi-step tasks
- 🎯 **Scenes** - Different layouts for different workflows
- 📄 **Multiple Pages** - Organize buttons across pages

---

## 🔐 Security Note

**⚠️ IMPORTANT:** Change the default password!

1. Go to Settings > Server Configuration
2. Change from `admin`/`admin` to secure credentials
3. Save settings

---

**Ready to start? Run the installer and enjoy! 🎮**

For detailed documentation, see: `docs/USER_GUIDE.md`
