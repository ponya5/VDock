# VDock Installation Guide

## Quick Install

### Windows

1. **Run the installer:**
   ```cmd
   install.bat
   ```

2. **Desktop shortcut** will be created automatically
3. **Double-click "VDock"** on your desktop to launch

### macOS / Linux

1. **Make installer executable:**
   ```bash
   chmod +x install.sh
   ```

2. **Run the installer:**
   ```bash
   ./install.sh
   ```

3. **Launch VDock:**
   - macOS: Double-click "VDock.command" on your desktop
   - Linux: Run `./launch.sh`

---

## Manual Installation

### Prerequisites

- **Python 3.9+** - [Download](https://www.python.org/downloads/)
- **Node.js 16+** - [Download](https://nodejs.org/)
- **Git** (optional) - [Download](https://git-scm.com/)

### Step-by-Step

#### 1. Clone or Download VDock
```bash
git clone https://github.com/ponya5/VDock.git
cd VDock
```

#### 2. Backend Setup
```bash
cd backend
python -m venv venv

# Windows:
venv\Scripts\activate.bat

# macOS/Linux:
source venv/bin/activate

# Install dependencies:
pip install -r requirements.txt
cd ..
```

#### 3. Frontend Setup
```bash
cd frontend
npm install
cd ..
```

#### 4. Create Data Directories
```bash
# Windows:
mkdir backend\data\profiles
mkdir backend\data\uploads

# macOS/Linux:
mkdir -p backend/data/profiles
mkdir -p backend/data/uploads
```

---

## Running VDock

### Windows
```cmd
launch.bat
```

### macOS / Linux
```bash
./launch.sh
```

### Manual Start

**Backend:**
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate.bat on Windows
python app.py
```

**Frontend:**
```bash
cd frontend
npm run dev
```

---

## Desktop Launchers

### Windows

**Option 1: Using VBS Launcher (Silent)**
- Double-click `VDock-Launcher.vbs`
- Runs in background without console window

**Option 2: Using Batch File**
- Double-click `launch.bat`
- Shows console window with logs

### macOS

- Double-click `VDock.command` on desktop
- Or create Automator app:
  1. Open Automator
  2. New Application
  3. Add "Run Shell Script"
  4. Script: `cd /path/to/VDock && ./launch.sh`
  5. Save as "VDock.app"

### Linux

Create `.desktop` file:
```bash
cat > ~/.local/share/applications/vdock.desktop << EOF
[Desktop Entry]
Type=Application
Name=VDock
Comment=Virtual Stream Deck
Exec=/path/to/VDock/launch.sh
Icon=/path/to/VDock/frontend/public/favicon.ico
Terminal=false
Categories=Utility;
EOF
```

---

## Auto-Start on System Boot

### Via Settings UI (Recommended)

1. Open VDock
2. Go to **Settings** > **Server Configuration**
3. Enable **"Start VDock on System Boot"**
4. Click checkbox to enable

### Manual Configuration

#### Windows (Registry)

```cmd
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v VDock /t REG_SZ /d "C:\path\to\VDock\VDock-Launcher.vbs" /f
```

#### macOS (LaunchAgent)

Create `~/Library/LaunchAgents/com.vdock.launcher.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.vdock.launcher</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/VDock/launch.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
```

Then: `launchctl load ~/Library/LaunchAgents/com.vdock.launcher.plist`

#### Linux (systemd)

Create `~/.config/systemd/user/vdock.service`:
```ini
[Unit]
Description=VDock Virtual Stream Deck

[Service]
Type=simple
ExecStart=/path/to/VDock/launch.sh
Restart=on-failure

[Install]
WantedBy=default.target
```

Enable: `systemctl --user enable vdock.service`

---

## Accessing VDock

Once running:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:5000
- **Default Login:** `admin` / `admin`

**⚠️ Important:** Change the default password in production!

---

## Troubleshooting

### Backend won't start

**Error: "Python not found"**
- Install Python 3.9+
- Ensure Python is in PATH
- Windows: Reinstall Python with "Add to PATH" checked

**Error: "No module named..."**
- Activate virtual environment
- Run: `pip install -r requirements.txt`

### Frontend won't start

**Error: "node command not found"**
- Install Node.js 16+

**Error: "Port 3000 already in use"**
- Frontend will try ports 3001, 3002, etc.
- Or stop other apps using port 3000

### Can't access VDock

**Check backend is running:**
```bash
curl http://localhost:5000
# Should return: "VDock API is running"
```

**Check frontend is running:**
```bash
curl http://localhost:3000
# Should return HTML
```

**Firewall blocking:**
- Add exception for Python/Node.js
- Windows: `netsh advfirewall firewall add rule ...`

### Auto-start not working

**Windows:**
- Run as Administrator to modify registry
- Check: `reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v VDock`

**macOS:**
- Check: `launchctl list | grep vdock`
- View logs: `tail -f ~/Library/Logs/vdock.log`

**Linux:**
- Check status: `systemctl --user status vdock.service`
- View logs: `journalctl --user -u vdock.service`

---

## Uninstallation

### Remove VDock

1. **Disable auto-start** (via Settings or manually)
2. **Delete VDock folder**
3. **Remove desktop shortcuts**

### Remove auto-start entries

**Windows:**
```cmd
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v VDock /f
```

**macOS:**
```bash
launchctl unload ~/Library/LaunchAgents/com.vdock.launcher.plist
rm ~/Library/LaunchAgents/com.vdock.launcher.plist
```

**Linux:**
```bash
systemctl --user disable vdock.service
rm ~/.config/systemd/user/vdock.service
```

---

## Updating VDock

1. **Backup your data:**
   - Copy `backend/data/profiles/` folder
   - Export profiles via Settings

2. **Pull latest changes:**
   ```bash
   git pull origin main
   ```

3. **Update dependencies:**
   ```bash
   cd backend
   source venv/bin/activate
   pip install -r requirements.txt --upgrade
   cd ../frontend
   npm install
   ```

4. **Restart VDock**

---

## Additional Resources

- **User Guide:** `docs/USER_GUIDE.md`
- **Changelog:** `docs/CHANGELOG.md`
- **Support:** ponya81@gmail.com
- **GitHub:** https://github.com/ponya5/VDock

---

**Enjoy VDock! 🎮**
