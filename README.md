# VDock - Virtual Stream Deck

A powerful, cross-platform virtual stream deck application that brings customizable control buttons to your computer. Control applications, execute commands, send hotkeys, and automate workflows with a beautiful, modern interface.

## Features

- **Fully Customizable Buttons**: Create unlimited buttons with custom icons, labels, and actions
- **Multiple Action Types**: 
  - Open URLs in your browser
  - Launch programs and applications
  - Execute shell commands
  - Send keyboard shortcuts/hotkeys
  - Control system functions (volume, media playback)
  - Chain multiple actions together
- **Multi-Page Layouts**: Organize buttons across multiple pages with folder navigation
- **Beautiful Themes**: Choose from built-in themes (dark, light, high contrast) or create your own
- **Profile Management**: Create multiple profiles for different workflows (streaming, work, gaming)
- **Plugin System**: Extend functionality with plugins (OBS Studio, Spotify, Discord, and more)
- **Cross-Platform**: Runs on Windows, with planned support for Linux and macOS
- **PWA Support**: Access from any device with a web browser
- **Desktop App**: Native desktop application with system tray and global hotkeys
- **Touch-Friendly**: Optimized for touchscreens and tablets

## Architecture

- **Backend**: Python Flask + Flask-SocketIO for real-time communication
- **Frontend**: Vue 3 + TypeScript + Pinia for state management
- **Desktop**: Electron wrapper for native desktop experience
- **PWA**: Progressive Web App support for browser-based access

## Installation

### Prerequisites

- Python 3.8 or higher
- Node.js 18 or higher
- npm or yarn
- Docker and Docker Compose (for production deployment)

### Quick Start (Development)

1. Clone the repository:
```bash
git clone <repository-url>
cd VDock
```

2. Run the setup script:
```bash
# Windows
setup.bat

# Linux/macOS
./setup.sh
```

3. Start the application:
```bash
# Windows
start_backend.bat
start_frontend.bat

# Linux/macOS
./start_backend.sh
./start_frontend.sh
```

### Production Deployment

For production deployment, see [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) for detailed instructions.

Quick production setup:
```bash
# Copy environment template
cp env.example .env

# Edit .env with your configuration
# Set SECRET_KEY and AUTH_PASSWORD

# Deploy with Docker
./deploy.sh  # Linux/macOS
deploy.bat   # Windows
```

### Manual Setup (Development)

#### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
- Windows: `venv\Scripts\activate`
- Linux/Mac: `source venv/bin/activate`

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Copy `.env.example` to `.env` and configure:
```bash
copy .env.example .env
```

6. Start the backend server:
```bash
python app.py
```

The backend will run on `http://localhost:5000` by default.

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The frontend will run on `http://localhost:3000` by default.

### Desktop App

1. Build the frontend:
```bash
cd frontend
npm run build
```

2. Start the Electron app:
```bash
cd electron
npm install
npm start
```

3. Build the installer (Windows):
```bash
npm run build
```

The installer will be created in `frontend/electron/dist-electron/`.

## Usage

### First Time Setup

1. Start the backend server
2. Open the frontend in your browser or launch the desktop app
3. Login with your password (default: `admin`, configurable in `.env`)
4. Create a new profile or load an existing one
5. Start adding buttons and configuring actions!

### Creating Buttons

1. Click the "Edit" button to enter edit mode
2. Click "Add Button" to create a new button
3. Configure the button:
   - Set label and icon
   - Choose an action type
   - Configure action-specific settings
   - Customize appearance
4. Click "Save" to save the button
5. Click "Save" in the toolbar to save the profile

### Using Actions

- **URL**: Opens websites in your default browser
- **Program**: Launches applications or opens files
- **Command**: Executes shell commands (use with caution)
- **Hotkey**: Sends keyboard shortcuts (e.g., Ctrl+C, Alt+Tab)
- **Multi-Action**: Executes multiple actions in sequence
- **System Control**: Controls volume, media playback, brightness

### Profiles

Profiles let you create different button layouts for different purposes:

- **Streaming**: Controls for OBS, audio, scene switching
- **Work**: Frequently used applications and documents
- **Gaming**: Game launchers and in-game macros
- **Media**: Music controls, video players

You can quickly switch between profiles or import/export them as JSON files.

## Configuration

### Backend Configuration

Edit `backend/.env`:

```env
# Server settings
HOST=127.0.0.1
PORT=5000

# Security
AUTH_PASSWORD=your-password-here
REQUIRE_AUTH=True

# Network
ALLOW_LAN=False  # Set to True to allow connections from other devices

# SSL (for HTTPS)
USE_SSL=False
SSL_CERT_PATH=cert.pem
SSL_KEY_PATH=key.pem
```

### Frontend Configuration

Edit frontend settings through the Settings page in the application:

- Theme selection
- Button size scaling
- Animation preferences
- Display options

## Plugin Development

Create custom plugins to extend VDock functionality:

```python
from backend.plugins import BasePlugin, PluginInfo

class Plugin(BasePlugin):
    def get_info(self):
        return PluginInfo(
            id='my_plugin',
            name='My Plugin',
            version='1.0.0',
            author='Your Name',
            description='Plugin description',
            actions=['my_action']
        )
    
    def initialize(self):
        # Initialize your plugin
        return True
    
    def execute_action(self, action_id, config):
        # Execute the action
        return {'success': True, 'message': 'Action executed'}
    
    def get_action_schema(self, action_id):
        # Return JSON schema for action configuration
        return {}
```

Place your plugin file in `backend/data/plugins/`.

## API Documentation

### REST API

- `POST /api/auth/login` - Authenticate and get token
- `GET /api/profiles` - List all profiles
- `POST /api/profiles` - Create new profile
- `GET /api/profiles/<id>` - Get profile details
- `PUT /api/profiles/<id>` - Update profile
- `DELETE /api/profiles/<id>` - Delete profile
- `POST /api/actions/execute` - Execute an action

### WebSocket Events

- `execute_action` - Execute action in real-time
- `action_result` - Receive action execution result

## Keyboard Shortcuts

- `Ctrl+Shift+D` - Summon/hide deck window (Desktop app only)
- `Ctrl+E` - Toggle edit mode
- `Ctrl+S` - Save current profile
- `Ctrl+Z` - Undo
- `Ctrl+Y` - Redo
- `Ctrl+,` - Open settings

## Troubleshooting

### Backend won't start

- Check that Python 3.8+ is installed
- Verify all dependencies are installed
- Check if port 5000 is already in use
- Review backend logs in `backend/data/vdock.log`

### Frontend can't connect to backend

- Ensure backend is running
- Check CORS settings in backend `.env`
- Verify firewall settings
- Check browser console for errors

### Actions not working

- For hotkeys: Ensure `pynput` library is installed
- For system controls: Check Windows audio permissions
- For commands: Verify command syntax and permissions

## Security Considerations

- **Command Execution**: Be cautious with the command action type. Only use trusted commands.
- **Remote Access**: If enabling LAN access, use a strong password and consider using SSL/HTTPS.
- **Plugins**: Only install plugins from trusted sources.
- **Production Security**: See [docs/security/SECURITY.md](docs/security/SECURITY.md) for comprehensive security guidelines.
- **Authentication**: Change default passwords immediately in production environments.

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open-source. See LICENSE file for details.

## Documentation

- **[Documentation Hub](docs/README.md)** - Complete documentation overview
- **[User Guide](docs/USER_GUIDE.md)** - Complete user manual
- **[Quick Start](docs/QUICKSTART.md)** - Get started quickly
- **[API Documentation](docs/API.md)** - Backend API reference

### For Developers
- **[Developer Guide](docs/development/DEVELOPER_GUIDE.md)** - Development setup and contribution guidelines
- **[Launcher Documentation](docs/development/LAUNCHER_README.md)** - Launcher system documentation

### For Administrators
- **[Production Deployment](docs/deployment/PRODUCTION_DEPLOYMENT.md)** - Complete production deployment guide
- **[Security Policy](docs/security/SECURITY.md)** - Security policies and best practices
- **[Maintenance Guide](docs/maintenance/MAINTENANCE.md)** - Maintenance and troubleshooting procedures
- **[Installation Notes](docs/deployment/INSTALL_NOTES.md)** - Installation troubleshooting

## Support

- **Documentation**: See [docs/](docs/) directory for comprehensive guides
- **Issues**: Report bugs and feature requests on GitHub
- **Production Support**: See [Maintenance Guide](docs/maintenance/MAINTENANCE.md) for maintenance and troubleshooting
- **Security**: See [Security Policy](docs/security/SECURITY.md) for security policies and reporting
- **Community**: Join our Discord server (link TBD)

## Roadmap

- [ ] Linux and macOS support
- [ ] Cloud profile sync
- [ ] Mobile companion app
- [ ] Plugin marketplace
- [ ] Voice activation
- [ ] Hardware device integration
- [ ] Community themes and icon packs

## Credits

Inspired by Elgato's Stream Deck and WebDeck.

Built with:
- Flask
- Vue 3
- Electron
- Font Awesome
- And many other amazing open-source projects

---

Made with ❤️ for the community

