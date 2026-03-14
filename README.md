# VDock — Virtual Stream Deck

> A powerful, browser-based virtual stream deck that puts your most-used controls at your fingertips. Build custom button layouts, automate workflows, monitor system stats, and control everything from a single, beautiful interface.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](README.md)
[![Vue 3](https://img.shields.io/badge/Frontend-Vue%203%20%2B%20TypeScript-42b883)](frontend/)
[![Flask](https://img.shields.io/badge/Backend-Python%20Flask-black)](backend/)

---

## ✨ Features

### 🎛️ Button & Layout System
- **Customizable Grid Layouts** — Drag, drop, resize, and reorder buttons freely
- **Scenes** — Multiple button layouts per profile (e.g. Work, Gaming, Streaming)
- **Pages** — Stack multiple pages inside each scene with circular navigation
- **Docked Sidebar** — Persistent buttons pinned across all pages/scenes
- **Template Gallery** — Jump-start with pre-built button sets

### 🖥️ System Controls
- Volume up/down/mute, microphone toggle
- Brightness control, media play/pause/next/previous
- Screen lock, sleep, shutdown, restart
- Window management (minimize, maximize, close, Alt+Tab)
- Show Desktop, Task Manager, Control Panel

### 📊 Real-time Monitoring
- Live CPU usage, frequency, temperature
- RAM / Memory usage
- Hard disk usage
- GPU core usage, GPU memory, GPU temperature, GPU frequency
- Internet speed

### 🌐 Web & App Integration
- Open URLs in browser, launch applications, open files/folders
- Run shell commands and scripts
- Send keyboard hotkeys (single keys or full combinations)
- Macros — chain multiple actions with optional delays
- Copy text to clipboard, type text via virtual keyboard

### 🌤️ Widgets
- **World Clock** — Display time in any timezone
- **Timer** — Countdown and stopwatch widgets
- **Weather** — Live weather for any city

### 🎬 Streaming (OBS)
- Switch OBS scenes, toggle sources/filters
- Start/stop streaming and recording

### 🎨 Appearance
- 26+ animated dashboard backgrounds (Floating Paths, Light Beams, Aurora, Matrix Rain, etc.)
- Custom background image upload
- Per-page background color, gradient, or image
- Button animations, labels, tooltips, and icon customization
- Asset library for custom icons, GIFs, and videos

### 🚀 Convenience
- Global keyboard shortcuts (configurable)
- Auto-start on system boot
- Multi-profile support with avatars
- Profile import / export
- Quick Search for buttons and actions

---

## 🚀 Quick Start

### Windows
```cmd
# Run the launcher directly
launch.bat
```

### First Launch
1. Wait **5–10 seconds** for the backend to initialize
2. Open your browser: **http://localhost:3000**
3. Default login: `admin` / `admin` ⚠️ *Change this in Settings → Security!*
4. Pick a template or start blank → customize your first button layout

---

## 📋 System Requirements

| Component   | Minimum                          |
|-------------|----------------------------------|
| OS          | Windows 10/11, macOS 10.15+, Ubuntu 18.04+ |
| RAM         | 4 GB                             |
| Disk        | 500 MB                           |
| Python      | 3.9+                             |
| Node.js     | 16+                              |
| Browser     | Chrome, Firefox, Edge (modern)   |

---

## 🎮 Button Action Types

| Action         | Description                                      |
|----------------|--------------------------------------------------|
| **Hotkey**     | Send any keyboard shortcut (Ctrl+C, Win+D, etc.) |
| **Program**    | Launch any application                           |
| **URL**        | Open a website in the default browser            |
| **Command**    | Run a shell command or script                    |
| **Macro**      | Chain multiple actions with delays               |
| **System**     | Volume, brightness, media, power, window control |
| **Metrics**    | Live display of CPU, RAM, GPU, disk, network     |
| **Weather**    | Current weather for a chosen city                |
| **Time**       | World clock, timer, or countdown display         |
| **OBS**        | Scene/source/filter control + streaming toggle   |
| **Custom Media** | Custom icon, GIF, video, or sound on-button    |
| **Navigation** | Jump to next/previous page or home page          |
| **Clipboard**  | Copy predefined text to clipboard                |

---

## ⚙️ Configuration

### Changing Settings
1. Open VDock → click **Settings** (top-right ⚙️)
2. Available sections: **Appearance**, **Button Layout**, **System**, **Security**

### Key Settings
| Setting              | Default       | Description                              |
|----------------------|---------------|------------------------------------------|
| Dashboard Background | Default       | Static or animated background            |
| Button Size          | Medium        | Scale all buttons up/down                |
| Show Labels          | On            | Show/hide text labels on buttons         |
| Show Header          | On            | Toggle the top navigation bar            |
| Docked Sidebar       | Off           | Enable persistent sidebar buttons        |
| Auto-start           | Off           | Launch VDock on system boot              |

### Global Shortcuts (Defaults)
| Shortcut          | Action                    |
|-------------------|---------------------------|
| `Ctrl+Shift+D`    | Show/hide VDock window    |
| `Ctrl+Shift+M`    | Toggle mute               |
| `Ctrl+Shift+F`    | Toggle fullscreen         |

---

## 🔧 Troubleshooting

| Problem | Solution |
|---|---|
| **Backend failed to start** | Ensure Python 3.9+ is installed; check port 5000 is free; try running as administrator |
| **Cannot connect to server** | Wait 10 seconds, then refresh; check Windows Firewall; verify nothing else uses port 5000 |
| **Buttons disappeared** | Hard-refresh browser (`Ctrl+Shift+R`) to clear cached state |
| **Hotkeys not working** | Restart the backend; verify the button action type is set to `hotkey` |
| **Changes not saving** | Click the **Save Profile** button in the footer while in Edit Mode |
| **Auto-start not working** | Run VDock as administrator at least once; check startup settings |

### Getting Help
- **In-app:** Click the **Help** button in the top-right header → full User Guide
- **Issues:** [GitHub Issues](https://github.com/ponya5/VDock/issues)
- **Email:** ponya81@gmail.com
- **Docs:** see the `docs/` folder for detailed guides

---

## 🛠️ Development

### Building from Source
```bash
# Clone repository
git clone https://github.com/ponya5/VDock.git
cd VDock

# Backend dependencies
cd backend
pip install -r requirements.txt

# Frontend dependencies
cd ../frontend
npm install
npm run dev
```

### Project Structure
```
VDock/
├── backend/           # Python Flask API server
│   ├── app.py         # Main server entry point
│   └── requirements.txt
├── frontend/          # Vue 3 + TypeScript web interface
│   ├── src/
│   │   ├── components/   # Reusable Vue components
│   │   ├── views/        # Page-level views (Dashboard, Settings, Profiles)
│   │   ├── stores/       # Pinia state stores
│   │   └── types/        # TypeScript type definitions
│   └── package.json
├── docs/              # Documentation and guides
├── scripts/           # Build and utility scripts
├── launch.bat         # Windows launcher
├── docker-compose.yml # Docker deployment
└── README.md
```

---

## 📜 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m 'Add my feature'`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

## 🙏 Acknowledgments

- Built with **Vue 3**, **TypeScript**, **Pinia**, **Flask**, and **Python**
- Icons by **Font Awesome**
- Animated backgrounds inspired by modern web design trends
- Community contributions and feedback

---

**VDock** — Making productivity beautiful and efficient. 🎮✨