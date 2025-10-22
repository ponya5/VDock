# VDock - Virtual Stream Deck

VDock is a powerful virtual stream deck application that allows you to create customizable button layouts for controlling your computer, applications, and workflows.

## ✨ Features

- 🎛️ **Customizable Button Layouts** - Create unlimited button configurations with drag & drop
- 🎨 **Animated Backgrounds** - Beautiful animated backgrounds including floating paths and light beams  
- 🔧 **System Controls** - Volume, brightness, media controls, and system metrics
- 🌐 **Web Integration** - Open URLs, launch applications, and control web services
- 📱 **Cross-Platform** - Works on Windows, macOS, and Linux
- 🔄 **Real-time Monitoring** - Live CPU, RAM, and system status updates
- 🎯 **Global Shortcuts** - Quick access with customizable keyboard shortcuts
- 🚀 **Auto-start** - Launch automatically with your system

## 🚀 Quick Start

### Windows
```cmd
# Run the installer
install.bat

# Launch VDock (desktop shortcut created automatically)
# Or manually: launch.bat
```

### macOS / Linux
```bash
# Make installer executable and run
chmod +x install.sh
./install.sh

# Launch VDock
./launch.sh
```

**First Launch:**
1. Wait 3-5 seconds for the backend to start
2. Open your browser to http://localhost:3000
3. Default login: `admin` / `admin` ⚠️ *Change this in production!*
4. Create your first profile and start adding buttons

## 📋 System Requirements

- **Windows:** 10/11 (64-bit), 4GB RAM, 500MB disk space
- **macOS:** 10.15+ (Catalina), 4GB RAM, 500MB disk space  
- **Linux:** Ubuntu 18.04+, 4GB RAM, 500MB disk space
- **Dependencies:** Python 3.9+, Node.js 16+ (auto-installed by installer)

## 🎮 Button Types

VDock supports various button actions:

- **System Controls:** Volume up/down/mute, media play/pause/next/previous
- **Applications:** Launch programs, open files/folders
- **Web Actions:** Open URLs, web shortcuts
- **Hotkeys:** Send keyboard combinations (Ctrl+C, Alt+Tab, etc.)
- **Macros:** Execute sequences of actions with delays
- **System Metrics:** Display live CPU, RAM, disk usage
- **Custom Commands:** Run shell commands (advanced users)

## ⚙️ Configuration

### Auto-Start Setup
1. Open VDock → **Settings** → **System**
2. Enable **"Start VDock on System Boot"**
3. Requires administrator privileges on Windows

### Global Shortcuts (Default)
- **Ctrl+Shift+D** - Show/hide VDock window
- **Ctrl+Shift+M** - Toggle mute
- **Ctrl+Shift+F** - Toggle fullscreen

### Animated Backgrounds
1. Go to **Settings** → **Appearance** → **Dashboard Background**
2. Choose from static gradients or animated options:
   - Floating Paths, Light Beams, Aurora Borealis, Matrix Rain, etc.

## 🔧 Troubleshooting

### Common Issues

**"Backend failed to start"**
- Ensure Python 3.9+ is installed
- Check if port 5000 is available
- Run as administrator on Windows

**"Cannot connect to server"**  
- Wait 3-5 seconds after launching
- Check Windows Firewall settings
- Ensure no other app is using port 5000

**"Auto-start not working"**
- Run VDock as administrator at least once
- Check system startup settings
- Verify the auto-start option is enabled in Settings

**Button actions not working**
- Check button configuration in the editor
- Verify required permissions (e.g., for system controls)
- See logs in the browser console (F12)

### Getting Help
- **Issues:** [GitHub Issues](https://github.com/ponya5/VDock/issues)
- **Email:** ponya81@gmail.com
- **Documentation:** Check the `docs/` folder for detailed guides

## 🛠️ Development

### Building from Source
```bash
# Clone repository
git clone https://github.com/ponya5/VDock.git
cd VDock

# Install dependencies
cd backend && pip install -r requirements.txt
cd ../frontend && npm install

# Build application
# Windows: scripts\build-installer.bat
# macOS/Linux: ./scripts/build-installer.sh
```

### Project Structure
```
VDock/
├── backend/           # Python Flask API server
├── frontend/          # Vue.js web interface
│   ├── electron/     # Electron desktop wrapper  
│   └── src/          # Vue.js source code
├── docs/             # Documentation and guides
├── scripts/          # Build and deployment scripts
└── README.md         # This file
```

## 📄 File Organization

**Essential files (keep in root):**
- `README.md` - This documentation
- `LICENSE` - MIT license
- `install.bat/sh` - Main installers
- `launch.bat/ps1/sh` - Application launchers
- `docker-compose.yml` - Docker deployment

**Additional resources:**
- `docs/` - Detailed documentation and guides
- `scripts/` - Build scripts and utilities
- `backend/` - Python server code
- `frontend/` - Vue.js web interface

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🙏 Acknowledgments

- Built with Vue.js, Electron, and Flask
- Icons by Font Awesome
- Animated backgrounds inspired by modern web design
- Community contributions and feedback

---

**VDock** - Making productivity beautiful and efficient. 🎮✨

For detailed installation instructions, see `docs/guides/INSTALLATION.md`