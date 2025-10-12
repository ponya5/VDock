# VDock Quick Start Guide

Get VDock up and running in minutes!

## Prerequisites

- **Python 3.8+**: [Download Python](https://www.python.org/downloads/)
- **Node.js 18+**: [Download Node.js](https://nodejs.org/)

## Automated Setup (Windows)

Run the setup script:

```bash
setup.bat
```

This will:
1. Check prerequisites
2. Create Python virtual environment
3. Install backend dependencies
4. Install frontend dependencies
5. Copy configuration files

## Manual Setup

### Backend Setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
copy .env.example .env
```

### Frontend Setup

```bash
cd frontend
npm install
copy .env.example .env
```

## Running the Application

### Option 1: Using Start Scripts (Windows)

Open two terminal windows:

**Terminal 1 - Backend:**
```bash
start_backend.bat
```

**Terminal 2 - Frontend:**
```bash
start_frontend.bat
```

### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
cd backend
venv\Scripts\activate  # or source venv/bin/activate on Linux/Mac
python app.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

## First Login

1. Open your browser to http://localhost:3000
2. Login with the default password: `admin`
3. **IMPORTANT**: Change the password in `backend/.env`

## Creating Your First Profile

1. Click "Profiles" in the header
2. Click "New Profile"
3. Enter a name and description
4. Click "Create"

## Adding Your First Button

1. Click the "Edit" icon in the header to enter edit mode
2. Click "Add Button" in the toolbar
3. Configure your button:
   - Label: "Google"
   - Icon: Click "Pick Icon" and select a globe icon
   - Action Type: "Open URL"
   - URL: "https://google.com"
4. Click "Save"
5. Click "Save" in the toolbar to save your profile

## Testing Your Button

1. Exit edit mode by clicking the eye icon
2. Click your new button
3. Google should open in your browser!

## Next Steps

- **Explore Action Types**: Try launching programs, sending hotkeys, and more
- **Customize Appearance**: Change themes in Settings
- **Create Multiple Pages**: Organize buttons across pages
- **Try Plugins**: Check out the OBS plugin example
- **Build the Desktop App**: See Electron setup instructions

## Troubleshooting

### Backend won't start

**Issue:** `Module not found` errors

**Solution:** Ensure virtual environment is activated and dependencies are installed:
```bash
cd backend
venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend won't start

**Issue:** `Cannot find module` errors

**Solution:** Reinstall dependencies:
```bash
cd frontend
rm -rf node_modules
npm install
```

### Can't connect to backend

**Issue:** Frontend shows connection errors

**Solution:**
1. Ensure backend is running on port 5000
2. Check `frontend/.env` has correct API URL
3. Check firewall settings

### Actions don't work

**Issue:** Buttons don't execute actions

**Solution:**
1. Check backend terminal for errors
2. Verify action configuration
3. For hotkeys, ensure `pynput` is installed
4. For system controls, check Windows permissions

## Configuration

### Changing the Password

Edit `backend/.env`:
```env
AUTH_PASSWORD=your-new-password-here
```

Restart the backend for changes to take effect.

### Enabling LAN Access

To access VDock from other devices on your network:

Edit `backend/.env`:
```env
ALLOW_LAN=True
HOST=0.0.0.0
```

Then access via: `http://YOUR_IP:5000`

**Security Warning:** Use a strong password and consider enabling SSL.

### Enabling SSL/HTTPS

1. Generate SSL certificates:
```bash
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
```

2. Edit `backend/.env`:
```env
USE_SSL=True
SSL_CERT_PATH=cert.pem
SSL_KEY_PATH=key.pem
```

3. Access via: `https://localhost:5000`

## Desktop App

To build and run the desktop application:

```bash
cd frontend
npm run build
cd electron
npm install
npm start
```

For production installer:
```bash
npm run build
```

Installer will be in `frontend/electron/dist-electron/`.

## Getting Help

- **Documentation**: See `docs/` directory
- **User Guide**: `docs/USER_GUIDE.md`
- **Developer Guide**: `docs/DEVELOPER_GUIDE.md`
- **API Reference**: `docs/API.md`
- **Issues**: Report bugs on GitHub

## Tips

1. **Save Often**: Click Save regularly when editing
2. **Test Actions**: Test new actions before relying on them
3. **Backup Profiles**: Export important profiles regularly
4. **Use Multiple Profiles**: Create profiles for different workflows
5. **Keyboard Shortcuts**: Learn the shortcuts for faster editing

## Example Profiles

### Streaming Profile

Buttons for:
- Start/Stop OBS recording
- Scene switching
- Audio controls
- Chat commands

### Work Profile

Buttons for:
- Launch frequently used apps
- Open common files
- Run scripts
- Send keyboard shortcuts

### Gaming Profile

Buttons for:
- Game launchers
- Voice chat controls
- In-game macros
- Discord status

---

Happy decking! 🎮

For detailed documentation, see [README.md](README.md) and the [User Guide](docs/USER_GUIDE.md).

