# VDock Quick Reference Guide

## 🚀 Launch VDock

### Option 1: Batch Launcher (Easiest)
```cmd
Launch-VDock.bat
```

### Option 2: PowerShell Launcher
```powershell
.\Launch-VDock.ps1
```

### Option 3: Python Launcher
```cmd
python VDock-Launcher.py
```

### Option 4: Compiled EXE (After Building)
```cmd
.\dist\VDock-Launcher.exe
```

### Option 5: Original Launcher
```cmd
launch.bat
```

---

## 🔨 Build Tools

### Create Icon
```powershell
.\scripts\create-icon.ps1
```

### Build Launcher EXE
```powershell
# Without custom icon
.\scripts\build-launcher.ps1

# With custom icon
.\scripts\build-launcher.ps1 -WithIcon
```

### Build Portable Installer
```powershell
.\scripts\build-installer.ps1
```

---

## 📍 Access Points

| Service | URL | Notes |
|---------|-----|-------|
| Frontend | http://localhost:3000 | Web interface |
| Backend API | http://localhost:5000 | REST API |
| Default User | admin | - |
| Default Pass | admin | Change on first login |

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Main project documentation |
| `SETUP_COMPLETE.md` | Detailed setup guide |
| `IMPLEMENTATION_SUMMARY.txt` | Technical implementation details |
| `scripts/LAUNCHER_README.md` | Complete launcher documentation |
| `QUICK_REFERENCE.md` | This quick reference |

---

## 🐛 Troubleshooting

### Backend won't start
```cmd
# Check virtual environment
cd backend
venv\Scripts\activate.bat
python app.py
```

### Can't find Python
```powershell
# Check Python installation
python --version

# Add Python to PATH if needed
# System Settings → Environment Variables → PATH
```

### Port already in use
- Edit `backend/config.py` and change PORT
- Edit `frontend/vite.config.js` and change server port

### Run as Administrator
Right-click batch file → Run as Administrator

---

## 📦 Distribution

### Create portable package
```powershell
.\scripts\build-installer.ps1
# Outputs: dist/VDock-Portable.zip
```

### Create standalone EXE
```powershell
.\scripts\create-icon.ps1
.\scripts\build-launcher.ps1 -WithIcon
# Output: dist/VDock-Launcher.exe
```

### Create NSIS installer
```cmd
# 1. Download NSIS: https://nsis.sourceforge.io/
# 2. Modify VDock.nsi as needed
# 3. Run: makensis VDock.nsi
# Output: VDock-Installer.exe
```

---

## 💾 System Requirements

- **Windows**: 10 or later
- **Python**: 3.8+
- **Node.js**: 16+
- **RAM**: 4GB minimum
- **Disk**: 2GB
- **Ports**: 3000, 5000 available

---

## 🔧 Configuration

### Backend Configuration
File: `backend/config.py`
- Port: `PORT = 5000`
- Debug: `DEBUG = False`
- Host: `HOST = 'localhost'`

### Frontend Configuration
File: `frontend/.env` or `vite.config.js`
- Port: 3000
- API URL: http://localhost:5000

---

## 📝 File Structure

```
VDock/
├── Launch-VDock.bat              ← Easy launcher
├── Launch-VDock.ps1              ← PowerShell launcher
├── VDock-Launcher.py             ← Python launcher
├── VDock.nsi                     ← NSIS installer
├── setup.bat                   ← Initial setup
│
├── backend/
│   ├── app.py                    ← Main Flask app
│   ├── requirements.txt           ← Dependencies
│   ├── venv/                     ← Python environment
│   ├── config.py                 ← Configuration
│   └── routes/                   ← API endpoints
│
├── frontend/
│   ├── src/                      ← Vue.js source
│   ├── package.json              ← Dependencies
│   └── node_modules/             ← Node packages
│
├── scripts/
│   ├── build-launcher.ps1        ← Build EXE
│   ├── build-installer.ps1       ← Build portable
│   ├── create-icon.ps1           ← Generate icon
│   └── LAUNCHER_README.md        ← Full launcher docs
│
├── dist/                         ← Build outputs
│   ├── VDock-Launcher.exe        ← Compiled launcher
│   └── VDock-Portable/           ← Portable package
│
└── docs/                         ← Documentation
```

---

## ✅ Setup Checklist

- [ ] Run `setup.bat` (one-time setup)
- [ ] Test with `Launch-VDock.bat`
- [ ] Access http://localhost:3000
- [ ] Login with admin/admin
- [ ] Change default password
- [ ] Build installer for distribution (optional)
- [ ] Build EXE launcher for users (optional)

---

## 🆘 Support Commands

```powershell
# Check Python version
python --version

# Check Node.js version
npm --version

# Test backend startup
cd backend && venv\Scripts\activate.bat && python app.py

# Test frontend
cd frontend && npm run dev

# Install dependencies
cd backend && venv\Scripts\activate.bat && pip install -r requirements.txt
cd frontend && npm install

# View logs (if enabled)
type backend\data\vdock.log
```

---

## 🎯 Common Tasks

### First Time Setup
```cmd
setup.bat
Launch-VDock.bat
```

### Development
```cmd
# Terminal 1 - Backend
cd backend && venv\Scripts\activate.bat && python app.py

# Terminal 2 - Frontend
cd frontend && npm run dev
```

### Build for Distribution
```powershell
.\scripts\build-installer.ps1
# Share: dist/VDock-Portable.zip
```

### Create Desktop Shortcut
1. Right-click `Launch-VDock.bat`
2. Select "Create shortcut"
3. Move to Desktop
4. Right-click shortcut → Properties → Advanced → Check "Run as administrator"

### Pin to Taskbar
1. Right-click `Launch-VDock.bat`
2. Select "Pin to taskbar"

---

## 📞 Getting Help

1. **Error messages**: Read the console output carefully
2. **Documentation**: Check `scripts/LAUNCHER_README.md`
3. **Logs**: Check `backend/data/vdock.log`
4. **Browser console**: Press F12 to see frontend errors
5. **Configuration**: Review `backend/config.py` and `frontend` settings

---

**Last Updated**: 2025-10-22
**Status**: Ready for Production ✓
