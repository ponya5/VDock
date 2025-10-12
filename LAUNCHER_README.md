# VDock Launcher

## Single Launch Button

I've created **3 different ways** to launch VDock with a single click:

### 1. `launch.bat` (Recommended)
- **Double-click** to start both servers
- Opens separate command windows for backend/frontend
- Automatically opens browser to http://localhost:3000
- Simple and reliable

### 2. `launch.ps1` (PowerShell)
- **Right-click** → "Run with PowerShell"
- Runs servers in background jobs
- Shows real-time status
- More advanced, cleaner interface

### 3. Desktop Shortcut
- Run `create_shortcut.bat` to create desktop icon
- **Double-click** desktop icon to launch
- Looks professional and convenient

## Quick Start

1. **First time setup**:
   ```bash
   setup.bat
   ```

2. **Launch VDock**:
   ```bash
   launch.bat
   ```

3. **Access app**:
   - Browser opens automatically
   - Login: `admin` / `admin`

## What the Launcher Does

1. ✅ Checks virtual environment exists
2. ✅ Starts backend server (port 5000)
3. ✅ Waits for backend to initialize
4. ✅ Starts frontend server (port 3000)
5. ✅ Opens browser automatically
6. ✅ Shows login credentials

## Stopping VDock

- **Batch version**: Close the command windows
- **PowerShell version**: Press Ctrl+C or close window
- **Desktop shortcut**: Same as batch version

## Troubleshooting

If launch fails:
1. Make sure you ran `setup.bat` first
2. Check that virtual environment exists (`.venv` folder)
3. Ensure no other apps are using ports 5000/3000

## Customization

You can modify the launcher scripts to:
- Change ports
- Add startup delays
- Modify browser behavior
- Add custom messages
