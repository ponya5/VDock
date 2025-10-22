# Quick Start: Creating a Desktop Shortcut for VDock

This guide shows you how to create a desktop shortcut to launch VDock easily.

## 🎯 Quick Steps

### Method 1: Using the Automated Script (Recommended)

1. **Open Command Prompt or PowerShell** in the VDock directory
2. **Run the shortcut creator**:
   ```cmd
   scripts\create-desktop-shortcut.bat
   ```
3. **Done!** The shortcut will appear on your desktop

### Method 2: Manual Creation

1. **Right-click on your desktop** → **New** → **Shortcut**
2. **Enter the path** to the launcher:
   ```
   C:\path\to\VDock\dist\VDock-Launcher.exe
   ```
   Or if the EXE doesn't exist yet:
   ```
   C:\path\to\VDock\launch.bat
   ```
3. **Click Next**
4. **Name it**: "VDock"
5. **Click Finish**

## 🚀 Launching VDock

After creating the shortcut:

1. **Double-click** the shortcut on your desktop
2. Wait for both servers to start (~10 seconds)
3. VDock will open automatically in your browser at `http://localhost:3000`

## 🎨 Customizing the Shortcut

### Run as Administrator

1. Right-click the shortcut → **Properties**
2. Click **Advanced**
3. Check **"Run as administrator"**
4. Click **OK**

This may be needed for certain system actions.

### Change Icon

1. Right-click the shortcut → **Properties**
2. Click **Change Icon**
3. Browse to your custom `.ico` file
4. Click **OK**

### Pin to Taskbar

1. Right-click the shortcut → **Pin to taskbar**
2. Click the pinned icon anytime to launch VDock

### Pin to Start Menu

1. Right-click the shortcut → **Pin to Start**
2. Access VDock from the Start menu

## 🛠️ Building the EXE Launcher (Optional)

If you want a standalone EXE file instead of a batch file:

### Using PowerShell:

```powershell
.\scripts\build-launcher.ps1
```

This creates `dist\VDock-Launcher.exe` which can be placed anywhere.

### Benefits of EXE Launcher:

- ✅ No console window (runs in background)
- ✅ More professional appearance
- ✅ Can be placed in a custom location
- ✅ Can be signed with digital certificate

## 📝 Troubleshooting

### "Python not found" Error

**Solution:**
1. Install Python from https://python.org
2. **IMPORTANT:** Check "Add Python to PATH" during installation
3. Restart your computer
4. Try the shortcut again

### "Node.js not found" Error

**Solution:**
1. Install Node.js from https://nodejs.org
2. Accept all defaults during installation
3. Restart your computer
4. Try the shortcut again

### Shortcut Opens but Nothing Happens

**Solution:**
1. Check if ports 3000 and 5000 are available
2. Close any other applications using these ports
3. Try running `launch.bat` manually to see error messages
4. Check Windows Firewall settings

### Port Already in Use

**Solution:**
If you see "Address already in use":
1. Press `Ctrl + Shift + Esc` to open Task Manager
2. Find and end any Python or Node.js processes
3. Try launching again

## 🔍 What the Launcher Does

When you click the shortcut, it:

1. ✓ Checks for Python installation
2. ✓ Checks for Node.js installation
3. ✓ Checks for virtual environment
4. ✓ Starts the backend Flask server (port 5000)
5. ✓ Starts the frontend Vite server (port 3000)
6. ✓ Opens VDock in your default browser
7. ✓ Keeps servers running in the background

## 🎮 Auto-Start on Login (Optional)

To launch VDock automatically when you log in:

1. Press `Win + R`
2. Type: `shell:startup`
3. Press Enter
4. Copy your VDock shortcut to this folder
5. Restart your computer

Now VDock will start automatically!

## 📂 File Locations

- **Project Root**: `C:\Users\YourName\CursorRepo\VDock\`
- **Launcher EXE**: `dist\VDock-Launcher.exe`
- **Launcher Batch**: `launch.bat`
- **Backend**: `backend\app.py`
- **Frontend**: `frontend\dist\`

## 🔐 Default Login

When VDock opens in your browser:

- **Username**: `admin`
- **Password**: `admin`

⚠️ **Important:** Change these credentials after first login!

## 🎨 Customization Tips

### Change Browser

If you want VDock to open in a specific browser:

1. Right-click shortcut → **Properties**
2. Change Target to:
   ```
   "C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe" "http://localhost:3000"
   ```
3. Replace with your browser's path

### Run Minimized

To run without showing windows:

1. Right-click shortcut → **Properties**
2. Under "Run:", select **"Minimized"**
3. Click **OK**

### Add Command Line Arguments

Edit the shortcut target and add arguments:

```
"dist\VDock-Launcher.exe" --port 3001
```

## 📞 Need Help?

If you encounter issues:

1. Check the console window for error messages
2. Read `docs/QUICKSTART.md` for setup instructions
3. Check `backend/data/vdock.log` for server errors
4. Press F12 in browser to see frontend errors

## 🎉 Enjoy VDock!

Once the shortcut is set up, launching VDock is as simple as:
**Double-click → Wait 10 seconds → Start using VDock!**

---

*Last updated: December 2024*

