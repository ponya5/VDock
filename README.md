<div align="center">

<img src="docs/assets/vdock-banner.svg" alt="VDock — Virtual Stream Deck" width="880" />

### Your desktop. On real buttons.

**A free, open-source stream deck that runs on a screen you already own — and the only one that speaks fluent Claude Code.**

https://github.com/user-attachments/assets/0c438874-2f27-4973-8bab-998fb0ae19a8

**▶ [Download the 1080p tour](docs/assets/vdock-readme.mp4)** · **▶ [Claude Code deep-dive](docs/assets/vdock2-intro.mp4)** — no sound

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-2.0.1-6ea8ff)](#whats-new-in-20)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](#requirements)
[![Vue 3](https://img.shields.io/badge/Frontend-Vue%203%20%2B%20TypeScript-42b883)](frontend/)
[![Flask](https://img.shields.io/badge/Backend-Python%20Flask-black)](backend/)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](#contributing)

[Quick start](#quick-start) · [Dashboard](#a-dashboard-you-design) · [Settings](#settings-for-every-detail) · [Mobile](#control-it-from-your-phone) · [Screensaver](#the-screensaver) · [Use cases](#real-use-cases) · [Docs](docs/) · [Issues](https://github.com/ponya5/VDock2/issues)

</div>

---

## Contents

- [What is VDock?](#what-is-vdock)
- [A dashboard you design](#a-dashboard-you-design)
- [Settings for every detail](#settings-for-every-detail)
- [Control it from your phone](#control-it-from-your-phone)
- [The screensaver](#the-screensaver)
- [Why VDock](#why-vdock)
- [Real use cases](#real-use-cases)
- [Quick start](#quick-start)
- [Features](#features)
- [What's new in 2.0](#whats-new-in-20)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [What VDock isn't (yet)](#what-vdock-isnt-yet)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

---

## What is VDock?

A stream deck is a grid of physical buttons that fire the things you do all day — mute the mic, switch the scene, run the build. The good ones cost £150–£250 and lock you to one vendor's store.

**VDock is that deck, in software, for free.** Point any spare screen at it — a £30 USB touch panel, an old tablet, your phone, or just a browser tab — and you get a grid of buttons you design yourself.

<div align="center">
<img src="docs/assets/screens/panel-on-desk.jpg" alt="A 7-inch touch panel above a keyboard showing VDock's ambient screensaver with clock, weather, headlines and market prices" width="760" />
<br /><em>A 7-inch panel above the keyboard. No hardware from a vendor, no account, no subscription.</em>
</div>

Out of the box it ships **79 actions** across 11 categories — apps, hotkeys, media, system control, metrics, webhooks, sliders. It then **detects the tools already on your machine** and adds up to **160 more**, so a developer's install ends up with **239 actions** and a designer's install stays lean. Nothing is configured; nothing that can't run is offered.

What makes it different from every other deck is the last part: **VDock was built around AI coding agents.** Claude Code gets 40 actions of its own, a button that shows whether your session is actually alive, and a full-screen alert the moment your agent stops and waits for you.

---

## A dashboard you design

<img src="docs/assets/screens/dashboard-live.gif" alt="VDock's Media scene: translucent glass keys and a volume slider over a slowly swirling red-and-blue animated background" width="820" />

Every scene is a grid you lay out yourself — any size, any mix of buttons, sliders and live widgets. Then make it look the way you want:

- **A living background.** Pick from 54 animated backgrounds (the one above is real footage), 5 gradients, or upload your own image — globally, per scene, or per app.
- **See-through keys.** A transparency slider lets the background glow through every key, capped at 90% so buttons never disappear.
- **Ten key designs.** Classic, Glass, Glow Glass, Gem, Neon Rim, Watermark, Deck Key, Status Key, Full Art and Folder — per button, or one tap to restyle every key at once. Add any of 16 overlay effects on top.
- **Sliders that behave like hardware.** Drag or scroll for volume and brightness, or jump straight to mute / 25 / 50 / 75 / 100 with the preset chips.
- **Your typography.** Modern Sans, Editorial (the screensaver's serif look) or Terminal Mono across the whole deck.

<img src="docs/assets/screens/dashboard-deck-key.png" alt="The same Media scene with every key switched to the Deck Key design: dark recessed keycaps with blue glow, over a light animated background" width="820" />

*Same scene, one tap later: every key switched to the Deck Key design.*

### Add any action, anywhere

<img src="docs/assets/screens/dashboard-edit-mode.png" alt="VDock edit mode: each key shows remove, edit and duplicate badges, empty cells show a plus to add a button, a searchable Button Actions panel lists apps like Calculator, Notepad, Command Prompt, PowerShell, Paint and Snipping Tool, and the footer has grid size, Add Page, Delete Page and Save Profile" width="820" />

Tap the pencil and the whole deck opens up:

- **Tap any empty cell's +** to add a button, then pick its action from the **Button Actions** panel — search across all 239 actions, or browse by category (apps, system, media, web, metrics, AI agents…).
- **Every key gets three badges:** remove, edit (icon, label, colour, design, action) and duplicate.
- **Drag to reorder** — with a mouse or a finger on a touch panel. Resize a slider to span several cells, or merge two sliders into one.
- **Set the grid** (rows × columns) per page, **add pages** for more room, and fill the **docked sidebar** with keys that stay put on every page.

Start from any of the **36 app templates** or import a scene pack someone shared — and every change saves itself.

---

## Settings for every detail

<img src="docs/assets/screens/settings-buttons.png" alt="VDock Settings, Appearance → Buttons: touch mode presets, resolved touch targets, button size and transparency sliders, the key design picker, and a live preview with an in-context grid" width="820" />

Everything is adjustable, and nothing is guesswork — the **live preview** renders a real key with your current size, labels, touch mode, design and background, and an **in-context grid** shows how a whole page will look before you apply anything.

| Section | What you control |
|---|---|
| **Appearance → Buttons** | Touch mode (Normal 1.0× · Touch-friendly 1.5× · Tablet 2.0×), minimum touch target, key size (0.5×–2×), transparency, key design, animations, press sound |
| **Appearance → Layout & sidebar** | Dashboard font, docked sidebar width and key height, notification level |
| **Appearance → Background** | Animated, gradient or uploaded background for the dashboard |
| **Appearance → Screen saver** | Idle delay, widgets, feeds, text size, layout and its own background — [see below](#the-screensaver) |
| **Templates** | 36 one-tap scenes for ChatGPT, Claude, Gemini, Claude Code, Copilot, Cursor, Figma, n8n and more |
| **Server** | Launch on startup, connection details, how Settings opens |
| **Integrations** | Detected apps, auto scene switching, the Claude Code attention-alert hook |
| **Connect a device** | LAN access and the QR code for your phone — [see below](#control-it-from-your-phone) |
| **Logs** | Tail backend and frontend logs, export them as a zip |

<img src="docs/assets/screens/app-templates.png" alt="VDock Settings → Templates: AI Assistants and AI Coding template cards, each with an Add Scene button and a preview of its actions" width="820" />

Three things make it pleasant to live with: **Find a setting** jumps straight to the right page and scrolls to the control, **Reset section** puts one page back to defaults without touching the rest, and changes **save as you make them** — no Save button to forget.

---

## Control it from your phone

<table>
<tr>
<td width="50%"><img src="docs/assets/screens/mobile-media.jpg" alt="VDock on a phone in landscape: Media scene with mute, volume, a volume slider with preset chips, and transport keys" /></td>
<td width="50%"><img src="docs/assets/screens/mobile-claude-code.jpg" alt="VDock on a phone: Claude Code scene with a status card, a session picker, Submit, Continue and Interrupt buttons, and shortcut keys" /></td>
</tr>
</table>

Any phone or tablet on your Wi-Fi becomes a second deck. There's no app to install and no account — it's the same VDock, served from your PC.

**What you get on the phone:**

- **A layout built for touch, not a shrunken desktop.** A slim scene rail across the top (one tap to switch scenes), page steppers, and a prominent fullscreen button. The deck runs in landscape — hold the phone upright and it asks you to rotate.
- **Sliders and presets** that work with a thumb.
- **A Claude Code console.** Pick up the phone and drive the agent from the couch: a status card shows whether Claude is ready, working, or waiting for permission; **Submit**, **Continue** and **Interrupt** fire into the live terminal session; a session picker chooses which `claude` terminal to target when you have several open; and your scene's shortcuts (Review, Commit, Explain, Fix Tests…) sit underneath.
- **A pocket screensaver** — just the clock and world clocks, sized for a small screen.

The phone is a **control surface only**: no edit mode, no settings. You can't accidentally rearrange your deck from a small screen.

<img src="docs/assets/screens/settings-connect-device.png" alt="VDock Settings → Connect a device: three setup steps, the Allow LAN access switch, the deck address with a Copy button, and a QR code" width="820" />

**Connect in three steps:**

1. Put the phone on the **same Wi-Fi** as your PC.
2. **Settings → Connect a device → Allow LAN access**, then relaunch VDock once (the network address is chosen at startup).
3. **Scan the QR code** with the phone's camera, or type the address shown next to it.

LAN access is **off by default**, the QR encodes nothing but a local address, and on Windows you'll need to **allow the firewall prompt for `python.exe` on private networks** the first time.

---

## The screensaver

<img src="docs/assets/screens/screensaver.png" alt="VDock screensaver: a large serif clock, date, weather, market price, four news headlines, four sports headlines and three world clocks on a dark background with a soft amber glow" width="820" />

Leave the deck idle and it turns into an ambient dashboard worth glancing at:

| Widget | What it shows |
|---|---|
| **Clock** | Large time and date, always on |
| **Weather** | Current temperature and conditions — automatic or a city you set |
| **News** | Rotating headlines from free RSS feeds (BBC, Reuters, AP, The Verge, Hacker News, Ars Technica and more — or add your own) |
| **Sports** | Sports headlines from free RSS feeds |
| **Stocks / Crypto** | Live quotes for the tickers you choose |
| **World clock** | Time in the cities you care about |

**No API keys for any of it.**

<img src="docs/assets/screens/settings-screensaver.png" alt="VDock Settings → Screen saver: idle-delay slider, Test and Customise layout buttons, a toggle and Options for each widget, widget text size, and a live screensaver preview" width="820" />

It's as customisable as the deck:

- **Choose the widgets** — toggle each one, and open its **Options** to set feeds, tickers, cities or location.
- **Arrange the layout** — **Customise layout** opens a live editor: drag a widget to move it, drag its corner to resize, with snap guides to line things up.
- **Set the timing** — an idle delay from off to 10 minutes, and a **Test** button to see it instantly.
- **Give it its own look** — a separate background from the dashboard, and a widget text size from 80% to 250%.

And if Claude Code needs you while the screensaver is up, the amber attention alert appears on top of it.

---

## Why VDock

|  | VDock | Elgato Virtual SD | Touch Portal | WebDeck |
|---|---|---|---|---|
| **Price** | Free, MIT | Free **only if** you own Elgato hardware | Free tier is 4×2, 2 pages; Pro $13.99 | Free, GPLv3 |
| **Host OS** | Windows · macOS · Linux | Windows · macOS | Windows · macOS | **Windows only** |
| **AI agent actions** | **Claude Code (40), Copilot, Cursor, Devin, VS Code, JetBrains** | — | — | — |
| **Agent-waiting alerts** | **Yes** | — | — | — |
| **Ambient dashboard when idle** | **Yes** — clock, weather, news, markets | — | — | — |
| **Account required** | No | Yes | Yes | No |
| **Plugin marketplace** | Templates + scene packs | Large | **Largest** | Small |

**In one line:** free, agent-native, ambient, and yours — with an honest gap on ecosystem size that [we're upfront about below](#what-vdock-isnt-yet).

---

## Real use cases

### 1. Driving an AI coding agent without leaving the keyboard

<img src="docs/assets/screens/claude-code-scene.png" alt="VDock's Claude Code scene: Open Claude, Review /code-review, Commit /commit, claude.ai, Explain, Write Tests, Fix Tests, Continue" width="820" />

The scene above is in the default profile. Tap **Review** and `/code-review` lands in your live Claude Code session — not a new one, the one you're already in. **Continue** resumes after a context compact. **Commit** runs `/commit`.

Two details that make this actually usable:

- **The green dot on the scene tab** means VDock can see the agent process running right now, so you know the button will land somewhere before you press it.
- **Agent attention alerts** — when Claude stops to ask permission or a question, VDock raises a pulsing amber card over everything, including the screensaver. You see it from across the room instead of finding it ten minutes later. One click in **Settings → Integrations** installs the Claude hook; any agent can drive it by POSTing to `/api/agent-events`.

### 2. A second screen that earns its desk space

Leave VDock idle and it becomes an ambient dashboard — clock, weather, headlines, sports, markets, world clocks, no API keys. Put it on a spare panel beside your monitor and it earns its place even when you aren't pressing anything. [More on the screensaver.](#the-screensaver)

### 3. Calls and recording

Mute, camera, push-to-talk (a button can fire on press and a different action on release), OBS scene switching, and a **volume slider you drag** rather than a button you tap eleven times.

### 4. Anything with an HTTP endpoint

One `http_request` action covers Home Assistant, n8n, Zapier, Discord webhooks, your own CI. Point a button at a JSON endpoint and show a value from the response **on the button face** — build status, queue depth, whatever you watch.

### 5. A phone as a spare deck

Scan the QR code in **Settings → Connect a device** and your phone is a second deck — mute from across the room, or drive Claude Code from the couch while a long task runs. [How it works.](#control-it-from-your-phone)

### 6. A kiosk or workshop panel

Tablet touch mode, 44px minimum targets, and a first-run tour mean you can hand a panel to someone who has never seen it.

---

## Quick start

### Requirements

| Required | Version | Get it |
|---|---|---|
| Python | 3.9+ | [python.org](https://www.python.org/downloads/) — on Windows tick **"Add Python to PATH"** |
| Node.js | 18+ | [nodejs.org](https://nodejs.org/) |

Everything else is optional. VDock runs fully with none of the tools below installed — actions it can't run are greyed out **with the reason shown**, never hidden and never failing on press.

| Optional | Unlocks | Install |
|---|---|---|
| [Claude Code](https://claude.com/product/claude-code) | 40 Claude Code actions | `npm i -g @anthropic-ai/claude-code` |
| [GitHub CLI](https://cli.github.com) | PRs, issues, CI checks, live badges | `winget install GitHub.cli` → `gh auth login` |
| Git | Repo-aware actions | [git-scm.com](https://git-scm.com/) |

### Install

```bash
git clone https://github.com/ponya5/VDock2.git
cd VDock2
```

<details open>
<summary><strong>Windows</strong></summary>

Double-click **`setup.bat`**, or run it from a terminal. Choose **[1] Full setup**.

</details>

<details>
<summary><strong>macOS / Linux</strong></summary>

```bash
chmod +x setup.sh launch.sh
./setup.sh
```

</details>

Setup installs dependencies, creates a desktop shortcut, writes `backend/.env`, and reports which optional tools it found.

### Run

Double-click the **VDock** desktop shortcut, or run `launch.bat` / `./launch.sh`. Give it **5–10 seconds**, then it opens at **http://localhost:3000** (or the port you chose).

First launch walks you through a **13-step tour** — profiles, scenes, edit mode, the sidebar, settings, the screensaver — and drops you into a starter profile with four working scenes: **Media**, **Claude Code**, **Cursor** and **Websites**. Every button in it works with no keys and no config.

---

## Features

### The deck

<img src="docs/assets/screens/deck.png" alt="VDock's Media scene with mute, volume up and down, a draggable volume slider, and transport controls" width="820" />

| | |
|---|---|
| **Scenes & pages** | Multiple layouts per profile, page navigation, 6 transition styles, auto-switch to follow the focused app |
| **Docked sidebar** | Buttons that stay put across every page |
| **Sliders** | Drag or scroll for volume, brightness and VDock's own dimmer — merge two side-by-side sliders into one wide one |
| **Macros** | One press runs an ordered list of actions, each with its own delay |
| **Toggles** | Two-state buttons with their own icon, colour and label per state, synced across every open window |
| **Press vs release** | Fire on touch or on lift, with an optional second action on release — push-to-talk from a button |
| **Quick-deck overlay** | A floating mini deck over whatever you're doing: `` ` `` in the window, `Ctrl+Shift+D` globally in the desktop build |
| **Scene packs** | Export a scene as JSON and import it anywhere — buttons only, no settings, no secrets, safe to share |

### Build it

<img src="docs/assets/screens/dashboard-edit-mode.png" alt="VDock edit mode: buttons with remove, edit and duplicate badges, a searchable Button Actions panel, and grid size controls" width="820" />

Tap the pencil, drag buttons around, resize the grid, search the action list, save. On a touch panel you drag with a finger. Changes save themselves.

### Integrations

| | |
|---|---|
| **Claude Code** | 40 actions — prompts, slash commands, session resume/rewind/compact, mode and model switches, approve/deny, todos, transcript. Uses your existing `claude` login |
| **GitHub** | `gh`-powered PRs, issues, checks, workflow runs — plus live PR count, CI status and notification badges on the button face |
| **Cursor · Copilot · VS Code · JetBrains · Visual Studio · Devin** | 102 more editor and agent commands, per-app keymaps |
| **OBS** | Scenes, sources, streaming controls |
| **HTTP / webhooks** | Any REST endpoint, any method, and a value from the JSON response rendered on the button |

> Keystroke actions only fire when the target editor is actually focused. That's deliberate — keys never land in the wrong window.

### Look and feel

<table>
<tr>
<td width="50%"><img src="docs/assets/screens/key-designs.png" alt="The Key Design picker in Settings: ten live swatches — Classic, Glass, Glow Glass, Gem, Neon Rim, Watermark, Deck Key, Status Key, Full Art and Folder" /></td>
<td width="50%"><img src="docs/assets/screens/glass-keys.png" alt="The Media scene with translucent glass keys and a volume slider over a red-and-blue animated background" /></td>
</tr>
<tr>
<td align="center"><sub>Pick a key design from live swatches</sub></td>
<td align="center"><sub>Translucent keys over an animated background</sub></td>
</tr>
</table>

| | |
|---|---|
| **10 button designs** | Classic, Glass, Glow Glass, Gem, Neon Rim, Watermark, Deck Key, Status Key, Full Art, Folder — picked from live swatches, not a dropdown |
| **16 overlay effects** | Fire, plasma, aurora, scanline, rain, holographic, metallic, liquid and more, on top of any design |
| **54 animated backgrounds** | Aurora, light rays, silk, iridescence, prism, ferrofluid… (60 catalogue entries with gradients and your own uploads), per-scene and per-app |
| **3 dashboard fonts** | Modern Sans, Editorial (Instrument Serif), Terminal Mono |
| **3 touch modes** | Normal 1.0× · Touch-Friendly 1.5× · Tablet 2.0×, with a 44px minimum target (WCAG 2.1 AA), auto-selected on small or touch screens |
| **Press feedback** | An optional synthesized click so a glass panel feels like it has keys |

### Templates

**36 ready-made scenes** across AI Assistants, AI Coding, AI Image & Video, Design & Creative, Automation & Dev, and AI Models & Platforms. One tap adds a working scene.

### Live widgets

CPU · RAM · GPU · disk · network · weather · world clock · timer · countdown · RSS news · sports · free stock and crypto quotes · spinner while an action runs · PR and CI badges.

---

## What's new in 2.0

**Settings, rebuilt.** Sidebar navigation instead of nested tab bars, a live preview rail beside the controls, search that jumps straight to the right page and scrolls to the setting, per-section reset, and a savebar that tells you the truth — changes save themselves, so there's no fake "unsaved" counter.

**Eight power features**, closing the gaps against Touch Portal and Elgato: macros, toggles, sliders, the quick-deck overlay, QR/LAN connect, press feedback, scene packs, and on-press/on-release triggers.

**Agent attention alerts** and the **scene live dot** — the two things that make an AI coding deck genuinely useful rather than a novelty.

**Mobile, done properly.** A dedicated phone layout with a scene rail, a Claude Code console, a pocket screensaver and a one-scan connect page.

**A first-run tour** and a starter profile that works with zero configuration.

**Under the hood:** auth on every API route, path-traversal containment, upload type whitelist, a 16MB request cap, a service worker that reloads onto new builds instead of serving stale ones, and frontend errors shipped to logs you can read in **Settings → Logs** and export as a zip.

---

## Configuration

| What | Where |
|---|---|
| Everything you'd normally change | **Settings** in the app — searchable, autosaving |
| Server config | `backend/data/config.json` (created on first run, gitignored) |
| Secrets | `backend/.env` (copy from `backend/.env.example`) |
| Ports | `setup.bat --ports` / `./setup.sh` option 4 |

### Optional API keys

You probably need none of these.

| Variable | Needed for | Note |
|---|---|---|
| `ANTHROPIC_API_KEY` | "Ask Claude (API)" only | The Claude **Code** actions use your existing `claude` login — no key |
| `GITHUB_TOKEN` | Live PR / CI / notification badges only | The `gh` actions use `gh auth login`. Needs `repo` + `notifications` |
| `VDOCK_DEFAULT_REPO_PATH` | Fallback repo when VDock can't infer one | Optional |

Secrets never reach the frontend — the action list exposes only *whether* an integration is configured, and secrets are stripped from command output before it reaches a notification or a log.

---

## Troubleshooting

| Problem | Try this |
|---|---|
| Python/Node not found | Reinstall with PATH enabled, restart the terminal |
| Port 3000 or 5000 in use | Change ports in setup, or close the other process |
| Setup failed on npm | Delete `frontend/node_modules`, run setup option **2** again |
| Desktop window doesn't open | Open **http://localhost:3000** in a browser |
| macOS blocks the launcher | Right-click `VDock.command` → **Open**, first time only |
| Claude / GitHub buttons greyed out | Hover for the reason — usually the CLI isn't installed or `gh auth login` hasn't run |
| Keystroke actions do nothing | They only fire when the target editor is focused. Deliberate |
| Phone can't reach VDock | **Settings → Connect a device**: allow LAN access, **relaunch**, allow the Windows firewall prompt for `python.exe`, and check both devices are on the same Wi-Fi |
| UI looks like an old build | It self-heals on reload; if not, hard-refresh once |
| Something else | **Settings → Logs** — tail backend and frontend logs, or export them with your issue |

---

## What VDock isn't (yet)

Being straight about this, because a README that only lists wins isn't useful:

- **No plugin marketplace.** Touch Portal and Elgato have large third-party ecosystems. VDock has 36 templates and shareable scene packs, which covers most of it — but not all of it.
- **Shallow logic model.** Two-state toggles, yes. Global variables, events and conditionals like Touch Portal's? Not yet.
- **The global summon hotkey is desktop-only.** `Ctrl+Shift+D` from anywhere works in the Electron build. In a browser tab, `` ` `` only works while VDock has focus — browsers can't register OS-global hotkeys, and no amount of wanting changes that.
- **Mobile is the web UI over LAN, not a native app.** Zero install, but also no push notifications or background running.
- **macOS and Linux volume/brightness sliders** are implemented with the right fallbacks but have had less real-device testing than Windows. Reports welcome.

---

## Development

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate         # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py

# Frontend (second terminal)
cd frontend
npm install
npm run dev
```

```bash
# Tests
cd backend && pip install -r requirements-dev.txt && pytest
cd frontend && npm test
```

**Architecture:** Vue 3 + TypeScript front end, Python Flask + Socket.IO back end, Electron shell for the desktop build. Actions live in a catalog the frontend reads at runtime; integrations are self-detecting plugin packs under `backend/integrations/`.

Every change is written up in **[`design-log/`](design-log/)** — one numbered entry with the problem, the design, and how it was verified. Start there if you want to understand why something is the way it is. [`docs/development/DEVELOPER_GUIDE.md`](docs/development/DEVELOPER_GUIDE.md) covers adding an action type or writing an integration pack.

```
VDock2/
├── setup.bat / setup.sh      ← interactive installer
├── launch.bat / launch.sh    ← daily launcher
├── backend/                  ← Flask API, actions, integration packs
├── frontend/                 ← Vue 3 + TypeScript UI
│   └── electron/             ← desktop shell
├── design-log/               ← numbered design decisions
└── docs/                     ← guides and assets
```

---

## Contributing

Issues and pull requests are welcome — fork, branch, PR. Good first contributions: a new integration pack, an app template, a background, or a fix for something in [What VDock isn't](#what-vdock-isnt-yet).

If you're reporting a bug, **Settings → Logs → Export** gives you a zip worth attaching.

Security issues: please use [GitHub security advisories](https://github.com/ponya5/VDock2/security/advisories) rather than a public issue.

---

## License

MIT — see [LICENSE](LICENSE). Use it, fork it, ship it.

<div align="center">
<br />

**VDock2** · built by [Daniel Shalom (@ponya5)](https://github.com/ponya5)

If it saved you a click today, a ⭐ helps other people find it.

</div>
