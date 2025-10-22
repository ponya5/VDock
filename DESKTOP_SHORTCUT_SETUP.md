# VDock Desktop Shortcut - Quick Setup

## 🚀 Fastest Way to Launch VDock

Create a desktop shortcut to launch VDock with one click!

## Step 1: Build the Launcher EXE (One-time setup)

Open PowerShell in the VDock directory and run:

```powershell
.\scripts\build-launcher.ps1
```

This creates `dist\VDock-Launcher.exe`

## Step 2: Create Desktop Shortcut

Run this command:

```cmd
scripts\create-desktop-shortcut.bat
```

Or manually:
1. Right-click desktop → New → Shortcut
2. Browse to: `C:\path\to\VDock\dist\VDock-Launcher.exe`
3. Name it: "VDock"
4. Click Finish

## Step 3: Launch!

1. Double-click the shortcut on your desktop
2. Wait ~10 seconds for servers to start
3. VDock opens automatically in your browser at `http://localhost:3000`

## 🎯 Login Credentials

- **Username**: `admin`
- **Password**: `admin`

⚠️ Change these after first login!

## 🎨 Optional Customizations

### Pin to Taskbar
Right-click shortcut → Pin to taskbar

### Run on Startup
1. Copy shortcut to Startup folder (`Win+R` → `shell:startup`)
2. VDock will launch automatically when you log in

### Run as Administrator
Right-click shortcut → Properties → Advanced → "Run as administrator"

## 🛠️ Troubleshooting

### "Python not found"
Install Python from https://python.org (check "Add to PATH")

### "Node.js not found"  
Install Node.js from https://nodejs.org

### Port already in use
Close any apps using ports 3000 or 5000, then try again

## 📖 Full Documentation

For detailed setup instructions, see: `docs/QUICK_START_DESKTOP.md`

---

**Enjoy using VDock!** 🎉

