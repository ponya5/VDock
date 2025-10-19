# VDock - Virtual Stream Deck

VDock is a powerful virtual stream deck application that allows you to create customizable button layouts for controlling your computer, applications, and workflows.

## Features

- 🎛️ **Customizable Button Layouts** - Create unlimited button configurations
- 🎨 **Animated Backgrounds** - Beautiful animated backgrounds including floating paths and light beams
- 🔧 **System Controls** - Volume, brightness, media controls, and more
- 🌐 **Web Integration** - Open URLs, launch applications, and control web services
- 📱 **Responsive Design** - Works on desktop and mobile devices
- 🔄 **Real-time Updates** - Live system monitoring and status updates
- 🎯 **Global Shortcuts** - Quick access with keyboard shortcuts
- 🚀 **Auto-start** - Launch automatically with Windows/macOS

## Installation

### Windows

#### Option 1: Installer (Recommended)
1. Download `VDock Setup.exe` from the releases page
2. Run the installer as administrator
3. Follow the installation wizard
4. Choose installation directory (default: `C:\Program Files\VDock`)
5. Select whether to create desktop and start menu shortcuts
6. Click "Install" and wait for completion
7. Launch VDock from the desktop shortcut or start menu

#### Option 2: Portable Version
1. Download `VDock-Portable.exe` from the releases page
2. Extract to any folder (e.g., `C:\VDock`)
3. Double-click `VDock-Portable.exe` to run
4. No installation required - runs directly from the folder

#### Option 3: Manual Installation
1. Download the latest release ZIP file
2. Extract to your desired location
3. Install Python 3.8+ from [python.org](https://python.org)
4. Install Node.js 18+ from [nodejs.org](https://nodejs.org)
5. Open Command Prompt in the extracted folder
6. Run the build script:
   ```cmd
   scripts\build-installer.bat
   ```
7. Follow the build process instructions

### macOS

#### Option 1: DMG Installer (Recommended)
1. Download `VDock.dmg` from the releases page
2. Double-click the DMG file to mount it
3. Drag VDock to your Applications folder
4. Eject the DMG file
5. Launch VDock from Applications or Spotlight

#### Option 2: Manual Installation
1. Download the latest release ZIP file
2. Extract to your desired location
3. Install Python 3.8+ using Homebrew:
   ```bash
   brew install python
   ```
4. Install Node.js 18+ using Homebrew:
   ```bash
   brew install node
   ```
5. Open Terminal in the extracted folder
6. Run the build script:
   ```bash
   chmod +x scripts/build-installer.sh
   ./scripts/build-installer.sh
   ```

## First Launch

1. **Launch VDock** - Double-click the application icon
2. **Wait for Backend** - The app will start the backend server (takes 3-5 seconds)
3. **Create Profile** - Set up your first profile with buttons
4. **Configure Settings** - Adjust appearance, shortcuts, and auto-start options

## Configuration

### Auto-Start Options

VDock offers two auto-start methods:

#### 1. System Boot (Web Version)
- Go to **Settings** → **System** → **Start VDock on System Boot**
- This starts the web server automatically when your computer boots
- Requires administrator privileges on Windows

#### 2. Windows Startup (Desktop App)
- Go to **Settings** → **System** → **Start with Windows (Desktop App)**
- This launches the desktop application when Windows starts
- Only available in the desktop application version

### Global Shortcuts

- **Ctrl+Shift+D** - Show/hide VDock window
- **Ctrl+Shift+M** - Toggle mute
- **Ctrl+Shift+F** - Toggle fullscreen

### Background Customization

1. Go to **Settings** → **Appearance** → **Dashboard Background**
2. Choose from:
   - **Static Gradients** - Ocean Breeze, Sunset Glow, Forest Mist, etc.
   - **Animated Backgrounds** - Floating Paths, Beams Background, Aurora Borealis, etc.

## System Requirements

### Windows
- Windows 10/11 (64-bit)
- 4GB RAM minimum, 8GB recommended
- 500MB free disk space
- Python 3.8+ (for manual installation)
- Node.js 18+ (for manual installation)

### macOS
- macOS 10.15+ (Catalina or later)
- 4GB RAM minimum, 8GB recommended
- 500MB free disk space
- Python 3.8+ (for manual installation)
- Node.js 18+ (for manual installation)

## Troubleshooting

### Common Issues

#### "Backend failed to start"
- Ensure Python is installed and in PATH
- Check if port 5000 is available
- Run as administrator on Windows

#### "Cannot connect to server"
- Wait 3-5 seconds after launching
- Check Windows Firewall settings
- Ensure no other application is using port 5000

#### "Auto-start not working"
- Run VDock as administrator at least once
- Check Windows Startup folder
- Verify registry entries (Windows)

#### "Animated backgrounds not showing"
- Ensure you've selected an animated background in Settings
- Check browser console for errors
- Try refreshing the page

### Getting Help

- **GitHub Issues** - Report bugs and request features
- **Email Support** - Contact: ponya81@gmail.com
- **Documentation** - Check the `docs/` folder for detailed guides

## Development

### Building from Source

1. Clone the repository:
   ```bash
   git clone https://github.com/ponya5/VDock.git
   cd VDock
   ```

2. Install dependencies:
   ```bash
   # Backend
   cd backend
   pip install -r requirements.txt
   
   # Frontend
   cd ../frontend
   npm install
   
   # Electron
   cd electron
   npm install
   ```

3. Build the application:
   ```bash
   # Windows
   scripts\build-installer.bat
   
   # macOS/Linux
   ./scripts/build-installer.sh
   ```

### Project Structure

```
VDock/
├── backend/           # Python Flask backend
├── frontend/          # Vue.js frontend
│   ├── electron/     # Electron desktop wrapper
│   └── src/          # Vue.js source code
├── docs/             # Documentation
├── scripts/          # Build and deployment scripts
└── README.md         # This file
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Acknowledgments

- Built with Vue.js, Electron, and Flask
- Icons by Font Awesome
- Animated backgrounds inspired by modern web design trends

---

**VDock** - Making productivity beautiful and efficient.