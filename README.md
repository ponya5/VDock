<div align="center">

<img src="docs/assets/vdock-banner.svg" alt="VDock — Virtual Stream Deck" width="920" />

<br />

<img src="https://raw.githubusercontent.com/ponya5/ponya5/main/assets/vdock2-demo.gif" alt="VDock demo — custom button layouts, animated backgrounds, and system controls" width="920" />

<br />

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](README.md)
[![Vue 3](https://img.shields.io/badge/Frontend-Vue%203%20%2B%20TypeScript-42b883)](frontend/)
[![Flask](https://img.shields.io/badge/Backend-Python%20Flask-black)](backend/)

**Your customizable control deck — drive Claude Code, GitHub, Cursor and Copilot from real buttons, alongside system actions, live widgets, and animated backgrounds.**

[Quick Start](#-quick-start) · [Features](#-features) · [Integrations](docs/INTEGRATIONS.md) · [Setup Menu](#-one-setup-for-everything) · [Creator](#-creator) · [Docs](docs/) · [Issues](https://github.com/ponya5/VDock2/issues)

</div>

---

## What is VDock?

VDock is a **virtual stream deck** for your computer — no hardware required.

Build button grids for everyday tasks (launch apps, hotkeys, volume, CPU/GPU
monitoring, OBS scenes, weather) **and for the work you actually do all day**:
run a Claude Code prompt, open a pull request, check CI, fire Cursor's Composer,
or POST to any webhook — all from a button.

**117 built-in actions** across 12 categories. Use it as a **desktop app
(Electron)** or in your **browser**. Everything is editable: layouts, scenes,
pages, icons, backgrounds, and actions.

```mermaid
flowchart LR
  A[setup.bat / setup.sh] --> B[Install deps]
  B --> C[Desktop shortcut]
  C --> D[launch.bat / launch.sh]
  D --> E[Backend :5000]
  D --> F[Frontend :3000]
  D --> G[Electron window]
  G --> H[Your custom deck]
```

---

## ✨ Features

### Control deck
| | |
|---|---|
| 🎛️ **Custom grids** | Drag, resize, and arrange buttons freely |
| 🎬 **Scenes & pages** | Multiple layouts per profile with page navigation |
| 📌 **Docked sidebar** | Persistent buttons across all pages |
| 🧩 **Templates** | Pre-built button sets to get started fast |

### AI & developer integrations
| | |
|---|---|
| 🤖 **Claude Code** | Run prompts and slash commands (`/code-review`, `/commit`), resume sessions. Uses your existing `claude` login |
| 💬 **Claude API** | One-shot prompts straight to the clipboard (optional API key) |
| 🐙 **GitHub** | PRs, issues, checks, workflow runs via `gh` — plus live PR count and CI status **on the button face** |
| ✨ **Cursor** | Composer, AI chat, inline edit, accept/reject diff |
| 🧑‍✈️ **GitHub Copilot** | Chat, inline suggestions, `/explain` `/fix` `/tests` `/doc` |
| 🪝 **HTTP / webhooks** | Any REST endpoint — Discord, Slack, n8n, Zapier, Home Assistant |

> Integrations are optional and self-detecting. VDock works fully with none of
> them installed; actions it can't run are greyed out with the reason.

### Actions & automation
| | |
|---|---|
| ⌨️ **Hotkeys & macros** | Keyboard shortcuts and chained actions |
| 🖥️ **System control** | Volume, brightness, media, power, window management |
| 🚀 **Apps & URLs** | Launch programs, open sites, run commands |
| 🔀 **Toggles & random** | Two-state switches (mute/unmute) and shuffle keys |
| 🧭 **Scene navigation** | Jump to a page, switch scenes, auto-switch by focused app |
| 🎬 **OBS integration** | Scenes, sources, streaming controls |

### Live widgets
| | |
|---|---|
| 📊 **System metrics** | CPU, RAM, GPU, disk, network |
| 🌤️ **Weather** | Auto or manual city, no API key needed |
| 🕐 **Time widgets** | World clock, timer, countdown |
| 📰 **News carousel** | RSS/Atom headlines that slide through on the screensaver — no API key |
| 🔔 **Live button state** | Spinner while an action runs, badges for PR counts and CI status |

### Look & feel
| | |
|---|---|
| 🌈 **26+ animated backgrounds** | Aurora, light rays, silk, iridescence, and more |
| 🖼️ **Custom wallpapers** | Upload dashboard and button backgrounds |
| ✨ **Touch modes** | Normal, touch-friendly, and tablet sizing |
| 🌙 **Dark UI** | Polished dashboard with optional header and sidebar |

---

## 🚀 Quick Start

### Prerequisites

**Required**

| Requirement | Version | Download |
|-------------|---------|----------|
| Python | 3.9+ | [python.org](https://www.python.org/downloads/) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org/) |

> **Windows:** During Python install, check **"Add Python to PATH"**.

**Optional — only for the integrations you want**

| Tool | Unlocks | Install |
|------|---------|---------|
| [Claude Code](https://claude.com/product/claude-code) | Claude prompt, slash command and session actions | `npm i -g @anthropic-ai/claude-code` |
| [GitHub CLI](https://cli.github.com) | PR, issue, checks and workflow actions | `winget install GitHub.cli` then `gh auth login` |
| Git | Repo-aware actions (branch, CI status) | [git-scm.com](https://git-scm.com/) |

Setup detects each of these and tells you what it found. Nothing here is
required to run VDock.

### 1. Get the code

```bash
git clone https://github.com/ponya5/VDock2.git
cd VDock2
```

Or download and extract the ZIP from GitHub.

### 2. Run setup (one menu for everything)

<details open>
<summary><strong>Windows</strong></summary>

Double-click **`setup.bat`** at the repo root, or run:

```cmd
setup.bat
```

</details>

<details>
<summary><strong>macOS / Linux</strong></summary>

```bash
chmod +x setup.sh launch.sh
./setup.sh
```

</details>

### 3. Launch

After setup, either:

- **Double-click the desktop shortcut** (`VDock` on Windows, `VDock.command` on macOS)
- Or run **`launch.bat`** (Windows) / **`./launch.sh`** (macOS/Linux)

Wait **5–10 seconds** for services to start. VDock opens at **http://localhost:3000**.

---

## 🧰 One setup for everything

The setup menu handles all first-run tasks:

```
========================================================
  VDock Setup
========================================================

  [1] Full setup (recommended)
      Install Python + Node deps, Electron, desktop shortcut,
      create backend/.env, detect integration CLIs

  [2] Install dependencies only
      Skip desktop shortcut creation

  [3] Create desktop shortcut only
      Adds a VDock icon to your Desktop

  [4] Launch VDock now

  [5] Exit
```

**Non-interactive flags** (for scripts/CI):

```cmd
setup.bat --full       REM install + shortcut
setup.bat --deps       REM dependencies only
setup.bat --shortcut   REM desktop shortcut only
setup.bat --launch     REM start VDock
```

---

## 📁 Project structure

```
VDock/
├── setup.bat / setup.sh     ← Start here (interactive installer)
├── launch.bat / launch.sh   ← Daily launcher
├── backend/                 ← Python Flask API
├── frontend/                ← Vue 3 + TypeScript UI
│   └── electron/            ← Desktop app shell
├── docs/                    ← Guides and assets
└── scripts/                 ← Maintainer build/deploy tools
    └── VDock-Launcher.py    ← Launcher engine
```

---

## ⚙️ Configuration

| What | Where |
|------|-------|
| App settings (UI) | **Settings** gear in the dashboard |
| Server config template | `backend/data/config.example.json` |
| Local server config | `backend/data/config.json` (created on first run, not in git) |
| Backend secrets | `backend/.env` (copy from `backend/.env.example`) |

### Useful settings

- **Appearance** — button size, backgrounds, animations, touch mode
- **Server** — auto-start on boot, open settings in new browser tab
- **Widgets & Integration** — weather location, RSS news feeds, screensaver
  widgets, auto scene switching per app

### Optional API keys

Everything below is optional; the matching actions are greyed out with an
explanation until you set them. Edit `backend/.env`:

| Variable | Needed for | Notes |
|----------|-----------|-------|
| `ANTHROPIC_API_KEY` | "Ask Claude (API)" only | The Claude **Code** actions use your existing `claude` login and need no key |
| `GITHUB_TOKEN` | Live PR / CI / notification widgets only | The `gh` actions use your existing `gh auth login`. Needs `repo` + `notifications` scopes |
| `VDOCK_DEFAULT_REPO_PATH` | Fallback repo when VDock can't infer one | Optional |

> VDock never sends these to the frontend — the action list exposes only
> whether an integration is configured, and secrets are stripped from any
> command output before it reaches a notification or the log.

---

## 🔧 Troubleshooting

| Problem | Try this |
|---------|----------|
| Python/Node not found | Reinstall with PATH enabled, restart terminal |
| Port 5000 or 3000 in use | Close other Python/Node processes in Task Manager |
| Setup failed on npm | Delete `frontend/node_modules`, run setup option **2** again |
| Electron doesn't open | Open **http://localhost:3000** manually in your browser |
| macOS blocks launcher | Right-click `VDock.command` → **Open** the first time |
| Claude / GitHub buttons greyed out | Hover for the reason. Usually the CLI isn't installed or `gh auth login` hasn't been run |
| Keystroke actions do nothing | They only fire when the target editor is focused — this is deliberate, so keys never land in the wrong window |

More help: [`docs/QUICKSTART.md`](docs/QUICKSTART.md) · [`docs/INTEGRATIONS.md`](docs/INTEGRATIONS.md) · [`docs/setup/DESKTOP_LAUNCHER.md`](docs/setup/DESKTOP_LAUNCHER.md)

---

## 🛠️ Development

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

### Tests

```bash
# Backend (install test deps once)
cd backend && pip install -r requirements-dev.txt && pytest

# Frontend
cd frontend && npm test
```

See [`docs/development/DEVELOPER_GUIDE.md`](docs/development/DEVELOPER_GUIDE.md)
for architecture, how to add an action type, and how to write an integration
pack.

---

## 👤 Creator

<div align="left">
  <a href="https://github.com/ponya5">
    <img src="https://raw.githubusercontent.com/ponya5/ponya5/main/assets/icons/Daniel%20fire.gif" alt="Daniel Shalom" width="420" />
  </a>
</div>

<div align="center">

<img src="https://raw.githubusercontent.com/ponya5/ponya5/main/assets/ezgif-8ddb65fe506d34b8.gif" alt="Daniel Shalom" width="420" style="border-radius: 20px;" />

</div>

### Head of AI · Head of Delivery & QA | Site Management @ [employer]  
**AI Innovator · Multi-Agent Systems Builder · Automation Architect**

<p align="left">
  <img src="https://raw.githubusercontent.com/ponya5/ponya5/main/assets/icons/social-media.gif" width="64" height="64" align="middle" alt="" />
  <b style="font-size: 1.35em; margin-left: 10px;">Let's Connect</b>
</p>

<p align="left">
  <a href="https://www.linkedin.com/in/daniel-shalom-13987a1a/"><img src="https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn" /></a>
  <a href="https://github.com/ponya5"><img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub" /></a>
  <a href="https://www.daniel-shalom.com"><img src="https://img.shields.io/badge/Website-www.daniel--shalom.com-green?style=for-the-badge&logo=googlechrome&logoColor=white" alt="Website" /></a>
  <a href="https://www.instagram.com/daniel.shalom.ai/"><img src="https://img.shields.io/badge/Instagram-E4405F?style=for-the-badge&logo=instagram&logoColor=white" alt="Instagram" /></a>
</p>

<p align="left">
  <img src="https://img.shields.io/badge/AI%20Innovator-%F0%9F%A4%96-purple?style=for-the-badge" alt="AI Innovator" />
  <img src="https://img.shields.io/badge/Head%20of%20AI-%F0%9F%9A%80-blue?style=for-the-badge" alt="Head of AI" />
  <img src="https://img.shields.io/badge/Delivery%20%26%20QA%20Leader-%F0%9F%9A%80-navy?style=for-the-badge" alt="Delivery and QA Leader" />
  <img src="https://img.shields.io/badge/Multi--Agent%20Systems-%F0%9F%94%AE-orange?style=for-the-badge" alt="Multi-Agent Systems" />
  <img src="https://img.shields.io/badge/Automation%20Architect-%E2%9A%99%EF%B8%8F-teal?style=for-the-badge" alt="Automation Architect" />
</p>

> **VDock2** is a fun project by **[Daniel Shalom (@ponya5)](https://github.com/ponya5)** — part of a portfolio of automation tools, AI apps, and creative builds.  
> See more projects on [github.com/ponya5](https://github.com/ponya5).

---

## 📜 License

MIT — see [LICENSE](LICENSE).

## 🤝 Contributing

Issues and pull requests are welcome. Fork → branch → PR.

---

<div align="center">

**VDock2** — put your most-used controls one click away.

Built by [Daniel Shalom](https://github.com/ponya5)

</div>
