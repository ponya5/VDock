# Changelog

All notable changes to VDock will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.5.2] — 2026-10-17

### Changed
- **Small window = icon buttons** — shrink the desktop window and the deck drops the text labels, scales the buttons down so every one stays visible, and the "Header" tab becomes a small chevron instead of covering buttons

## [2.5.1] — 2026-10-17

Theme: **a shorter, more useful first-run tour**.

### Changed
- **First-run tour is 7 short steps** (was 10) and covers scenes, your deck, agents & automation and phone access
- **Pick your apps** — tick Claude Code, Cursor, Codex, ChatGPT, Spotify and more and each gets a ready-made scene when you continue
- **Skip any time** — "Skip tour" on every card, the X, or the Escape key; skipping adds nothing
- The highlight now fits every screen size: the card never covers what it explains and its arrow points at it

## [2.5.0] — 2026-10-17

Theme: **friendlier settings and app scenes**.

### Added
- **App scenes set themselves up** — turning an app on under Agents & automation → Apps & scenes now creates its scene straight away; Spotify, Music, iTunes and VLC start with media buttons (play, next, volume, now playing)
- **Add any deck action to an app scene** — the app's gear dialog lists deck actions (media and volume first), not only keyboard shortcuts
- **"Fix it" shows you where** — settings links scroll to the exact setting and pulse it

### Changed
- **Agents, Automation and Integrations are one section** — Agents & automation, with four pages: Apps & scenes, AI agents, Automation, Accounts & keys (old links still work)
- The header's auto-hide countdown pauses while the mouse is over it
- The desktop window can be resized down to 480×360
- A missing GitHub token is no longer listed under "Needs attention"
- Faster start: vendor code split into separate files; Settings and Profiles load on demand (build warning gone)

### Fixed
- "Add shortcut" put the button on the scene on screen instead of the app's own scene
- The macOS Accessibility warning re-checks when you return from System Settings, and explains the off/on step when the entry is already on

### Not verified at release
- Windows hardware run; the macOS Accessibility stale-entry fix and the 480×360 window in the packaged app

## [2.4.1] — 2026-10-16

Theme: **macOS fixes** (patch on 2.4.0).

### Fixed
- **Approve/Deny (macOS)** — a keystroke button now refuses instead of typing when it cannot tell which Terminal window is the agent's (2.4.0 could type into another Terminal window)
- **Codex sessions** — one Codex CLI window now shows as one session (background helper processes and the desktop app were counted as extra sessions)
- **Update check on the Mac app** — the packaged macOS app could not check for updates (TLS certificate error); weather location and album art had the same fault
- Phone intro icon scales with screen width (also fixed a flaky CI test)

### Changed
- Release pages now carry install steps: which file to download, the macOS "Open Anyway" steps, Allow LAN access and Accessibility
- README: which app needs the macOS Accessibility permission (the installed VDock app)

### Not verified at release
- Windows hardware run of installer/setup scripts (CI-verified only); Windows one-tap update
- macOS build is not notarized (Gatekeeper "Open Anyway" needed on first launch)
- iPhone/Safari and real tablet (checked on a Samsung S21 only); phone screen's Codex Approve/Deny (server call verified)
- The TLS fix inside the packaged Mac app (needs this release; 2.4.0 installs must be reinstalled by hand once)

## [2.4.0] — 2026-10-16

Theme: **phone/tablet experience and macOS** (production pass on Windows + macOS).

### Added
- **One-step phone setup** — trusted host, lasting sign-ins, QR-first Connect card (larger QR for scanning)
- **Packaged app and installers** — Electron picks a free port (no AirPlay :5000 clash on macOS), single instance, backend restart policy, Windows firewall rule via setup.bat / NSIS
- **Agent tracking** — Codex hooks, Antigravity payload, out-of-order event handling, exact-session (pid) targeting so two terminals in one folder stay separate; Codex remote Approve/Deny
- **macOS** — media/volume actions, Mic Mute, Spotify now-playing, VS Code / Devin / Cursor / Copilot / JetBrains chords, focus safety
- **Packaged uninstall removes agent hooks**; packaged-aware firewall hints

### Changed
- Mobile/tablet: 44px tap-target floor on all touch surfaces, firmer tiles over image wallpapers, compact session-chip labels, tablet header/footer capped
- Backend runs on Python 3.9–3.14

### Fixed
- Feedback throttle blocked the first post on some runtimes
- Cross-platform CI failures (Windows, macOS, Linux)
- Dependency CVE bump (http-cache-semantics)

### Not verified at release
- Windows hardware run of installer/setup scripts (CI-verified only)
- Real phone/tablet hardware (emulation only); Codex `/hooks` trust flow; Gatekeeper on a downloaded DMG (build is ad-hoc signed, not notarized)

## [2.1.0] — 2026-09-26

### Added
- **Self-contained installers** — one-click Windows Setup + Portable exe (PyInstaller-frozen backend bundled into Electron; no Python needed); macOS `.dmg`/`.zip` and Linux `.AppImage`/`.deb` via the new per-OS release pipeline
- **Agent session targeting** — pick and pin which Claude Code session a button drives (multi-window support), with session chips in the mobile console
- **Agent state-aware actions** — hook-driven ready/working/permission states, action bar, and scene buttons that type into the live CLI
- **Mobile agent console** — dedicated control surface on agent scenes: state card, last prompt/reply, action buttons, shortcut grid
- **Dedicated mobile experience** — landscape-only deck gate, mobile chrome (scene rail, page steppers), sparse phone screensaver, portrait rotate prompt
- **Guided first-run tour rewrite** — routed steps across dashboard/settings with conditional auto-skip; expanded in-app Help guide with Troubleshooting
- **New app icon** — real 1024px keycap-grid art replacing the 32px placeholder; multi-size ico, tray PNG, and favicons

### Fixed
- Backend crash on macOS at startup (`pynput Key.insert` doesn't exist on darwin)
- Linux/macOS tray + window icons not rendering (`.ico` → platform-aware PNG)
- LAN/mobile devices stuck on stale frontend in dev mode; service-worker self-heal on open tabs
- Save & Apply mass-applies key designs and surfaces real save errors
- Installer lands in a user-writable dir (`%LOCALAPPDATA`), NSIS references real files
- CI portability: backend tests no longer assume Windows paths/.exe suffixes

### Changed
- Tray menu trimmed to Show / Settings / Exit
- Install dirs and release docs consolidated (`docs/RELEASING.md`)

## [2.2.0] — 2026-10-02

### Added
- **Spectrum visualizer screensaver** — 16 animated skins (Winamp, Mono Bars, UV Bars, RGB Bars, Iso Field, Scope, Aurora, Ember, Rotor 3D, Swarm, Waveform, Wave Ring, Mirror Bars, Radial Pulse, Wave Grid, Neon Flight) reacting to desktop audio, with ambient backdrops, soft crossfade transitions, and a Shuffle mode that rotates skins on a timer
- **Widgets over the visualizer** — clock, weather, news and system widgets can overlay the spectrum, positioned with the same drag-and-resize layout editor
- **Animated weather glyph** — the saver's weather is a live scene: orbiting sun rays, spinning moon, rain/snow/fog/thunder, driven by the real condition and day/night
- **Merged media transport + brand-aware now playing** — single play/stop button, playing-site detection ("YouTube — Brave"), brand icons, larger readable card
- **Mobile header reveal** — a floating button on phones reveals the real deck header; the guide gains a side-nav rail with its own scrollport

### Fixed
- **Settings sync stomp** — a fresh mobile/compact client could overwrite server settings with factory defaults; sync is now field-level (server-side merge, changed-keys PUT/broadcast, pre-sync gate, reconnect resync)
- **Saver frame rate** — ambient layers render into a low-res offscreen canvas, the hidden dashboard background suspends under the saver, and Swarm draws via cached sprites; all skins hold a locked 60 fps

### Changed
- **README rebuilt for onboarding** — two-step per-OS quick start, deduplicated content, hero banner refresh; governance docs (Code of Conduct, Security, Contributing) linked with real contact info; repo root tidied

## [Unreleased]

### Added
- **Circular Page Navigation**: Next/Previous page buttons now loop around (next on last page returns to first, previous on first page goes to last)
- **Quick Add Page Button**: Added "Add Page" button in dashboard footer for quick page creation
- **Explicit Save Profile Button**: Added "Save Profile" button in footer with toast notifications
- **Larger Scene Buttons**: Increased scene button size for better accessibility (44px minimum height, larger fonts and icons)
- **Navigation Action Category**: Added Next Page, Previous Page, and Home Page button actions in sidebar
- **Hotkey Backward Compatibility**: Support for both legacy string format (`"Ctrl+Shift+P"`) and new array format (`["ctrl", "shift", "p"]`)
- **Docked Sidebar System**: Persistent sidebar with pinned buttons across all pages
- **Production Readiness**: Added `.env.example`, production checklist, and comprehensive `.gitignore`

### Fixed
- **Cursor Button Hotkeys**: Fixed "Invalid configuration" error for Cursor scene hotkey buttons
- **Scene Button Persistence**: Scenes now properly save and persist when navigating away
- **Page Auto-Save**: Pages automatically save to backend when created or modified
- **Action Validation**: All 13 buttons across 3 scenes now validate and execute correctly

### Changed
- **Scene Navigation UI**: Improved button styling, spacing, and visual hierarchy
- **Footer Layout**: Better organization with spacers and aligned buttons
- **Test Coverage**: Added comprehensive action testing script (`test_all_actions.py`)

### Security
- Updated `.gitignore` to exclude sensitive data and temporary files
- Added `.env.example` template for secure configuration

## [0.1.0] - Previous Release

### Initial Features
- Multi-profile system with avatar support
- Customizable button grid with drag-and-drop
- 26+ dashboard backgrounds
- Multiple action types (URL, Program, Command, Hotkey, System Control)
- System metrics monitoring (CPU, RAM, GPU, etc.)
- Time widgets (World Clock, Timer, Countdown)
- Weather integration
- Scene management system
- Button animations and effects
- Asset management system
- Cross-platform action support
- Flask backend with Python 3.13
- Vue 3 frontend with TypeScript
- Real-time action execution
- Profile import/export

## Testing Status

### Latest Test Results (2025-10-18)
```
Total buttons tested: 13
Unique action types: 3
Action types: cross_platform, hotkey, system_control

Results:
  ✅ Valid:       13
  ⚠️  Invalid:     0
  ❌ Unsupported: 0
  ❌ Errors:      0
```

**Scenes Tested:**
- Main Scene (5 buttons): Full Screen, Mute, Volume Up, Brightness Up, Stop
- Cursor Scene (8 buttons): Command Palette, Quick Open, AI Chat, Find in Files, Toggle Terminal, Multi-Cursor, Select Next Match, Comment Line
- Demo Scene: GPU Memory Frequency metric

**All action types validated:**
- ✅ `system_control` - Fullscreen toggle
- ✅ `cross_platform` - Volume, brightness, media controls
- ✅ `hotkey` - Keyboard shortcuts (both formats)

---

## Migration Notes

### Upgrading to Latest Version

**Backend:**
1. Restart backend server to load updated hotkey action code
2. No database migrations required
3. Profile data structure is backward compatible

**Frontend:**
1. Clear browser cache if scene buttons don't appear
2. Hard refresh (Ctrl+Shift+R) recommended

**Features:**
- Existing hotkey buttons will work with both old and new formats
- New navigation buttons available in sidebar under "Navigation" category
- Scenes persist automatically, but can use "Save Profile" button for explicit saving

---

[Unreleased]: https://github.com/yourusername/VDock/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/VDock/releases/tag/v0.1.0
