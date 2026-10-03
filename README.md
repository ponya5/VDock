<div align="center">

<img src="docs/assets/vdock-banner.svg" alt="VDock — Virtual Stream Deck" width="880" />

### Your development wingman — on any screen you already own.

**VDock sits next to your editor and keeps your AI agents, your repo and your day moving. It tells you the moment Claude Code or Cursor needs you, lets you approve, prompt, review, test and ship from one tap — on a touch panel, a tablet, your phone or a browser tab. Free, open source, and 100% local.**

https://github.com/user-attachments/assets/0c438874-2f27-4973-8bab-998fb0ae19a8

**▶ [Launch video](docs/assets/vdock-launch.mp4)** · **▶ [1080p tour](docs/assets/vdock-readme.mp4)** · **▶ [Claude Code deep-dive](docs/assets/vdock2-intro.mp4)** — no sound

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-2.3.0-6ea8ff)](https://github.com/ponya5/VDock2/releases/latest)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](#quick-start)
[![Vue 3](https://img.shields.io/badge/Frontend-Vue%203%20%2B%20TypeScript-42b883)](frontend/)
[![Flask](https://img.shields.io/badge/Backend-Python%20Flask-black)](backend/)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](#contributing)

[Quick start](#quick-start) · [A day with VDock](#a-day-with-your-wingman) · [Agents](#built-for-ai-coding-agents) · [Any screen](#phone-and-tablet-as-the-touch-screen) · [Safe by design](#safe-by-design--it-runs-on-your-machine) · [Screensaver](#the-screensaver) · [Docs](docs/) · [Issues](https://github.com/ponya5/VDock2/issues)

</div>

---

## What is VDock?

Coding with AI agents changed the job. You start a session, the agent works, and then it **waits** — for a permission, an answer, a "continue". Meanwhile you're in another window, the build is red, a PR needs a look, and you only find out ten minutes later.

**VDock is the co-pilot seat for that loop.** It's a deck of on-screen buttons and live status tiles that runs beside your editor on any spare screen — a £30 USB touch panel, an old tablet, your phone, or just a browser tab. It watches your agents through their official hooks, knows your repo, and turns the things you do fifty times a day into one tap.

<div align="center">
<img src="docs/assets/screens/panel-on-desk.jpg" alt="A 7-inch touch panel above a keyboard showing VDock's ambient screensaver with clock, weather, headlines and market prices" width="760" />
<br /><em>A 7-inch panel above the keyboard. No vendor hardware, no account, no subscription.</em>
</div>

- **It knows when your agent needs you.** Claude Code, Cursor, Copilot, Codex, Devin and more report their state to VDock. The moment one stops to ask, a branded alert rises on the deck — and on your phone.
- **It talks back.** Approve or deny, send a preset prompt ("Continue", "Write tests", "Fix this error"), run a slash command, compact or resume a session — typed straight into your *live* session, not a new one.
- **It knows your repo.** Branch, changed files, diffs, test runs, dev servers, Docker, PRs, issues and CI checks as live buttons.
- **It's still a full stream deck.** 79 built-in actions (apps, hotkeys, media, system, webhooks, sliders), plus up to 160 more detected from the tools on your machine — **239 on a typical developer install**.

---

## A day with your wingman

| When | What VDock does for you |
|---|---|
| **Start of day** | One tap opens your editor and resumes yesterday's Claude Code session; live tiles show your branch and the dev servers that are up. |
| **Agent at work** | **Mission Control** lists every session — working, waiting, done. A green dot on the scene tab confirms VDock sees the live process. |
| **Agent waits** | A full-screen alert (Claude, Cursor, Copilot, Devin…) rises over the deck and the screensaver. **Approve / Deny** from the deck or your phone. |
| **Keep it moving** | **Agent Prompt** presets, **Dictate to Agent** (hold, speak, review, submit) and slash-command keys — sent to the session that's ready. |
| **Review** | **Review Changes** lists what the agent touched this turn; tap a file for its diff. **Run Tests** detects your test command and shows pass / fail. |
| **Ship** | Commit, push, open a PR and watch **CI checks** turn green — `gh`-powered buttons with live badges. |
| **Meetings** | A real Windows **mic mute** with a LIVE / MUTED face, camera, push-to-talk and a volume slider. |
| **Away from desk** | Your phone becomes an approval remote. Idle, the panel turns into an ambient dashboard — clock, weather, headlines, markets, or a music visualizer. |

---

## A dashboard you design

<img src="docs/assets/screens/dashboard-live.gif" alt="VDock's Media scene: translucent glass keys and a volume slider over a slowly swirling red-and-blue animated background" width="820" />

Every scene is a grid you lay out yourself — any size, any mix of buttons, sliders and live widgets. Then make it look the way you want: a **living background** (54 animated options, 5 gradients, or your own image — global, per scene, or per app), **see-through keys** (transparency up to 90%, capped so buttons never disappear), **ten key designs** with 16 overlay effects on top, **smooth virtual sliders** for volume and brightness, and **three dashboard fonts**.

<img src="docs/assets/screens/dashboard-deck-key.png" alt="The same Media scene with every key switched to the Deck Key design: dark recessed keycaps with blue glow, over a light animated background" width="820" />

*Same scene, one tap later: every key switched to the Deck Key design.*

### Add any action, anywhere

<img src="docs/assets/screens/dashboard-edit-mode.png" alt="VDock edit mode: each key shows remove, edit and duplicate badges, empty cells show a plus to add a button, a searchable Button Actions panel lists apps like Calculator, Notepad, Command Prompt, PowerShell, Paint and Snipping Tool, and the footer has grid size, Add Page, Delete Page and Save Profile" width="820" />

Tap the pencil and the whole deck opens up: tap an empty cell's **+** to search every action or browse by category, every key gets **remove / edit / duplicate** badges, **drag to reorder** with a mouse or a finger, resize a slider across cells or merge two into one, and set the grid, add pages, or fill the **docked sidebar** with keys that stay put everywhere.

Start from any of the **36 app templates** or import a scene pack someone shared — and every change saves itself.

---

## Built for AI coding agents

<img src="docs/assets/screens/mission-control.jpg" alt="VDock Mission Control with a simulated session: one Claude Code session needing approval with Approve, Deny and Open buttons, and a second one working" width="820" />

**Mission Control** lists every agent session — which one needs you, which is working — and lets you approve, deny or jump into it. When an agent stops to ask, a **branded alert** (Claude, Cursor, Copilot, Devin…) rises over the deck and the screensaver.

<img src="docs/assets/screens/claude-alert.jpg" alt="VDock showing a branded Claude Code alert: 'Claude Code needs you', the permission request, the project name and a Got it button over the Media scene" width="820" />

New in 2.3, each a button you can add from the action picker:

- **Agent Prompt** — send a preset (Continue, Write tests…) or your own text to the ready session
- **Review Changes** — the files the agent changed this turn; tap one for its diff
- **Run Tests** — detects your repo's test command and shows pass / fail
- **Agent Usage** — today's estimated spend and tokens, as a chip
- **Git Branch**, **Dev Servers**, **Docker** — live status faces with a tap menu (pull/push/stash, open/restart/stop, start/stop/logs)
- **Mic Mute** — a real Windows microphone mute with a LIVE / MUTED face
- **Dictate to Agent** — hold to speak via Windows voice typing, release, review, then submit yourself

Keystroke actions only fire when the target app is focused.

---

## Settings for every detail

<img src="docs/assets/screens/settings-overview.jpg" alt="VDock Settings, Overview: a Needs attention list (LAN without a deck password, GitHub token not set, 3 of 4 agents hooked) and four quick switches" width="820" />

Settings opens on **Overview**: what's set up, what needs you, and the switches you reach for most. Five sections sit underneath:

- **Appearance** — key size, transparency and design, backgrounds, fonts, docked sidebar, the [screensaver](#the-screensaver)
- **Agents & automation** — agent alerts and hooks (install or remove each agent's hook; only VDock's own entry is touched), auto scene switching, triggers, the MCP server
- **Integrations** — **Accounts & keys** and one-tap app templates (ChatGPT, Claude, Cursor, Figma, n8n…)
- **Devices & network** — Connect a device, deck password, ports and host
- **System** — logs (exportable), startup, About

<img src="docs/assets/screens/settings-accounts.jpg" alt="VDock Settings, Accounts & keys: Anthropic API key, GitHub token and WeatherAPI key all marked Not set with Set key and Get a key buttons, and GitHub CLI marked Found" width="820" />

**Accounts & keys** shows which keys and CLIs are configured and what each unlocks. Paste a key into **Set key** and it is saved to the `.env` file on the PC and active immediately — keys are only accepted from the PC itself, never shown again, and never sent to other devices (you can still edit the `.env` file by hand under **Advanced**). **Find a setting** jumps to any control, **Reset section** restores one page, and changes **save as you make them**.

---

## Phone and tablet as the touch screen

<table>
<tr>
<td width="32%"><img src="docs/assets/screens/phone-portrait.jpg" alt="VDock on a phone in portrait: a single-column deck with volume keys and slider" /></td>
<td width="68%"><img src="docs/assets/screens/tablet-portrait.jpg" alt="VDock on an 820 by 1180 tablet in portrait: a larger deck grid that fits the screen" /></td>
</tr>
<tr>
<td align="center"><sub>Phone, portrait</sub></td>
<td align="center"><sub>Tablet, portrait (820×1180)</sub></td>
</tr>
</table>

**No touchscreen? You already own one.** Any phone or tablet on your Wi-Fi becomes a deck — or just keep VDock in a browser tab or its desktop window and click. No app store, no account — it's the same VDock, served from your PC.

- **Phone = a remote.** Portrait layout, safe-area aware, with a Claude Code console and a **phone approval remote**: Approve / Deny a waiting agent from the couch.
- **Tablet = a full deck.** Portrait and landscape grids that fit the screen, with [edit mode](docs/assets/screens/tablet-edit.jpg) (rearrange keys on the tablet itself), and the screen stays awake while the deck is open.
- **Stays connected.** A reconnect banner appears only if the PC is really unreachable, the deck resumes on the right scene when the phone wakes, and edits on one device show up on the others.
- **Install as an app.** Add it to the Home Screen for a full-screen deck with no browser bars.

<img src="docs/assets/screens/connect-page.jpg" alt="VDock Settings, Connect a device: setup steps, Allow LAN access switch, password prompt and the deck address (masked in this screenshot)" width="820" />

**Connect in three steps:** same **Wi-Fi**; **Settings → Devices & network → Connect a device**, turn on **Allow LAN access** and relaunch once; **scan the QR code**. With a deck password set, the QR carries a single-use pairing token (10 minutes), so the phone signs in by scanning.

> **Security:** LAN access is off by default. Anyone on your Wi-Fi who can reach the deck can press your keys and answer your agents, so **set a deck password before turning on LAN access** (Connect page, same screen). Allow the Windows firewall prompt for `python.exe` the first time. See [SECURITY.md](SECURITY.md).

---

## The screensaver

<img src="docs/assets/screens/screensaver.png" alt="VDock screensaver: a large serif clock, date, weather, market price, four news headlines, four sports headlines and three world clocks on a dark background with a soft amber glow" width="820" />

Leave the deck idle and it turns into an ambient dashboard: a large **clock**, **weather**, rotating **news** and **sports** headlines from free RSS feeds, live **stock/crypto** quotes, and **world clocks** — all with **no API keys required**.

Or pick the **music visualizer** — 16 animated spectrum skins, from classic Winamp bars to 3D wave grids and a neon fly-through, reacting to whatever's playing on the PC. Shuffle mode crossfades between skins on a timer, and you can layer the widgets on top.

<img src="docs/assets/screens/settings-screensaver.png" alt="VDock Settings → Screen saver: idle-delay slider, Test and Customise layout buttons, a toggle and Options for each widget, widget text size, and a live screensaver preview" width="820" />

Toggle each widget and open its **Options** for feeds, tickers or cities; **Customise layout** opens a live drag-and-resize editor with snap guides; an idle delay from off to 10 minutes has its own **Test** button; and it gets its own background and a text size from 80–250%. If Claude Code needs you while it's up, the amber attention alert appears on top of it.

---

## Safe by design — it runs on your machine

VDock is built the way you'd want a tool that can type into your terminal to be built:

- **100% local.** The server runs on your PC; your phone or tablet talks to it over your own Wi-Fi. No cloud relay, no account, no telemetry or analytics.
- **Agents report in, locally.** Claude Code, Cursor and the other agents use their official hooks to post state to VDock's localhost-only endpoint. Install or remove each hook from Settings; only VDock's own entry is touched.
- **Your keys stay on the PC.** API keys and tokens live in a local `.env`, are accepted only from the PC itself, never shown again, never sent to other devices, and are stripped from logs and notifications.
- **Locked down by default.** LAN access is off until you turn it on; set a deck password and the QR code carries a single-use, 10-minute pairing token. Keystroke actions only fire when the target app is focused.
- **Open source, MIT.** Read every line. Startup refuses unsafe combinations (debug on the network, SSL without certificates, an example password). See [SECURITY.md](SECURITY.md).

The only outbound calls are the ones you switch on — weather, headlines and quotes for the screensaver, and GitHub when you add a token.

---

## Why VDock

Free and MIT (Elgato's virtual deck needs their hardware; Touch Portal's free tier is capped), runs on **Windows, macOS and Linux**, works on **any screen** — touch panel, tablet, phone or browser — and is the only deck with **agent-native actions and agent-waiting alerts** for Claude Code, Cursor, Copilot, Codex, Devin, VS Code and JetBrains. Beyond development: calls and recording (mic mute, camera, push-to-talk, OBS), anything with an HTTP endpoint (Home Assistant, n8n, Zapier, webhooks), and kiosk or workshop panels.

<details>
<summary><strong>Using a touchscreen as a second monitor (Windows)</strong> — fixing touch landing on the wrong screen</summary>

Windows will often route every tap to your *primary* display instead of a spare touchscreen monitor. Fix it in two steps:

1. Open **Tablet PC Settings** (Start menu search) → **Display** → **Setup**, then tap the touchscreen monitor when prompted.
2. If that doesn't stick, run Windows' own built-in digitizer-to-monitor mapping tool from a Command Prompt: `multidigimon -touch` (`MultiDigiMon.exe` ships with Windows in `System32` — run as Administrator if it appears to do nothing).

</details>

---

## Quick start

### 1. Get VDock

**Easiest — install the app.** Download the installer for your OS from the [latest release](https://github.com/ponya5/VDock2/releases/latest) (`VDock Setup x.y.z.exe` on Windows, `VDock-x.y.z-arm64.dmg` on macOS, `.AppImage`/`.deb` on Linux) and run it. The builds aren't code-signed yet, so your OS warns once — Windows SmartScreen → **More info → Run anyway**; macOS → right-click → **Open**.

**Or from source** — needs [Python 3.9+](https://www.python.org/downloads/) (tick "Add Python to PATH" on Windows) and [Node.js 20+](https://nodejs.org/):

```bash
git clone https://github.com/ponya5/VDock2.git
cd VDock2
```

- **Windows:** double-click **`setup.bat`** → choose **[1] Full setup**
- **macOS / Linux:** `chmod +x setup.sh launch.sh && ./setup.sh`

Setup installs dependencies and puts a **VDock icon on your desktop**.

### 2. Launch it

**Double-click the VDock icon on your desktop** — that's it, every day. (Or run `launch.bat` / `./launch.sh`.) It opens at `http://localhost:3000` after a few seconds, walks you through a short tour, and drops you into working **Media** and **Claude Code** scenes — no configuration needed.

**Optional tools** — none required, they unlock extra actions and stay greyed out with the reason shown until installed: [Claude Code](https://claude.com/product/claude-code) → 40 Claude actions · [GitHub CLI](https://cli.github.com) → PRs, issues, CI · Git → repo-aware actions.

**Uninstall:** installed app → remove it like any app (your profiles are kept). Source checkout → `uninstall.bat` / `./uninstall.sh`, then delete the folder.

---

## Features

<img src="docs/assets/screens/deck.png" alt="VDock's Media scene with mute, volume up and down, a draggable volume slider, and transport controls" width="820" />

**The deck:** scenes & pages with 6 transitions and auto-switch to the focused app, macros, two-state toggles synced across every open window, press-vs-release triggers (push-to-talk from a button), and a quick-deck overlay (`` ` `` in the window, `Ctrl+Shift+D` globally).

**Integrations:** **Claude Code** (prompts, slash commands, session resume/rewind/compact, approve/deny, transcript — using your existing login), **GitHub** (`gh`-powered PRs/issues/checks plus live badges), **Cursor · Copilot · VS Code · JetBrains · Visual Studio · Devin** (102 more commands), **OBS** (scenes, sources, streaming), and **HTTP/webhooks** (any REST endpoint, response value on the button). Keystroke actions only fire when the target editor is actually focused — deliberate, so keys never land in the wrong window.

---

## Configuration

Almost everything lives in **Settings** — searchable, autosaving. Server config is `backend/data/config.json` (created on first run, gitignored); ports via `setup.bat --ports` / `./setup.sh` option 4. Environment settings go in `.env` files copied from the committed templates — never commit the real ones:

| File | Template | What goes there |
|---|---|---|
| `backend/.env` (installed app: `<data dir>/.env`) | [`backend/.env.example`](backend/.env.example) | `SECRET_KEY` (generated on first run), `HOST`/`PORT`, `ALLOW_LAN`, `REQUIRE_AUTH`/`AUTH_PASSWORD`, `USE_SSL`, `DATA_DIR`, rate limits, and integration keys `ANTHROPIC_API_KEY`, `GITHUB_TOKEN`, `WEATHERAPI_KEY` |
| `frontend/.env` | [`frontend/.env.example`](frontend/.env.example) | `VITE_PORT`, `VITE_BACKEND_PORT`, `VITE_WS_URL` (dev server only) |

Secrets never reach the frontend — Settings shows only *whether* a key is set, and they're stripped from command output before any notification or log. Startup refuses unsafe combinations (debug mode on the network, SSL without certificates, an example password).

---

## Troubleshooting

- **Python/Node not found** — reinstall with PATH enabled, restart the terminal
- **Port 3000 or 5000 in use** — change ports in setup, or close the other process
- **Setup failed on npm** — delete `frontend/node_modules`, run setup option **2** again
- **Desktop window doesn't open** — open **http://localhost:3000** in a browser
- **macOS blocks the launcher** — right-click `VDock.command` → **Open**, first time only
- **Claude / GitHub buttons greyed out** — hover for the reason, usually the CLI isn't installed or `gh auth login` hasn't run
- **Keystroke actions do nothing** — they only fire when the target editor is focused; deliberate
- **Phone can't reach VDock** — **Settings → Devices & network → Connect a device**: allow LAN access, relaunch, allow the Windows firewall prompt for `python.exe`, check both devices are on the same Wi-Fi
- **Touch lands on the wrong monitor** — see [Using a touchscreen as a second monitor](#why-vdock), a Windows display-mapping issue, not a VDock bug
- **UI looks like an old build** — it self-heals on reload; if not, hard-refresh once
- **Something else** — **Settings → Logs**, tail or export the backend/frontend logs with your issue

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
# Tests — or run everything CI runs: scripts/check.ps1 (Windows) / scripts/check.sh
cd backend && pip install -r requirements-dev.txt && pytest
cd frontend && npm test
```

**Architecture:** Vue 3 + TypeScript front end, Python Flask + Socket.IO back end, Electron shell for the desktop build. Actions live in a catalog the frontend reads at runtime; integrations are self-detecting plugin packs under `backend/integrations/`.

[`docs/development/DEVELOPER_GUIDE.md`](docs/development/DEVELOPER_GUIDE.md) covers adding an action type or writing an integration pack.

Layout: `backend/` (Flask API, actions, integration packs) · `frontend/` (Vue UI, `electron/` shell) · `scripts/` · `docs/`. `frontend/dist` is a local build output (gitignored) that Flask serves — run `npm run build` after UI changes.

---

## Contributing

Issues and pull requests are welcome — fork, branch, PR. Good first contributions: a new integration pack, an app template, a background, or a bug fix. Full guide: [CONTRIBUTING.md](docs/CONTRIBUTING.md); by participating you agree to the [Code of Conduct](docs/CODE_OF_CONDUCT.md).

If you're reporting a bug, **Settings → Logs → Export** gives you a zip worth attaching. Security issues: report privately per [SECURITY.md](SECURITY.md) — a [GitHub security advisory](https://github.com/ponya5/VDock2/security/advisories) or ponya81@gmail.com — rather than a public issue.

---

## License

MIT — see [LICENSE](LICENSE). Use it, fork it, ship it.

<div align="center">
<br />

**VDock** · built by [Daniel Shalom (@ponya5)](https://github.com/ponya5)

If it saved you a click today, a ⭐ helps other people find it.

</div>
