# DL-070 — Tray menu trim

## Background

The Electron tray menu (`frontend/electron/main.js`) grew four entries:
Show VDock / Settings / Fix Firewall / Exit. Two of them are broken:

- **Fix Firewall** builds a `powershell -Command "Start-Process -Verb RunAs
  -FilePath "cmd" -ArgumentList "/c", "netsh advfirewall ..." -Wait"` string by
  hand. The escaped quotes break the argument list — PowerShell reports
  "A positional parameter cannot be found that accepts argument 'advfirewall'"
  (confirmed live). Even fixed, it would raise one UAC prompt per rule and is a
  one-time setup step that does not belong on a tray menu.
- **Settings** opens a legacy modal `BrowserWindow` whose Save button calls
  `window.postMessage(...)` — nothing listens (main.js expects an
  `ipcMain.handle('settings-update')` invoke), the Theme dropdown is dead, and
  the window shows the default File/Edit/View/Window menu bar. The real
  settings surface is the Vue app's `/settings` route (`SettingsView.vue`).

## Problem

The tray menu advertises two entries that don't work. Menu should be minimal
and every entry functional.

## Questions and Answers

**Q: Which items stay?**
A: User picked "Show, Settings, Exit". Fix Firewall is removed entirely
(deleting `fixFirewall()`); Settings routes the main window to `/settings`
instead of opening the broken modal (deleting `openSettings()`).

**Q: Where does firewall fixing live now?**
A: Nowhere — removed, not relocated. `netsh advfirewall` rules are a setup
concern; if it resurfaces it belongs as a button on the real settings page,
not a tray entry.

## Design

- Tray menu: `Show VDock` (show + focus), separator, `Settings`, separator,
  `Exit`. `isAutoLaunchEnabled` lookup in `createTrayMenu` was already unused —
  drop it.
- Settings navigation without a full reload: main sends
  `webContents.send('navigate-to', '/settings')`; preload exposes
  `onNavigate(handler)`; `App.vue` registers it once and calls
  `router.push(path)`. Same IPC pattern as `quick-deck-toggle`.
- `fixFirewall()` and `openSettings()` deleted outright — no callers remain.

## Implementation Plan

- [ ] Phase 1: `preload.js` — add `onNavigate`.
- [ ] Phase 2: `App.vue` — wire `onNavigate` → `router.push`.
- [ ] Phase 3: `main.js` — trim menu, delete `fixFirewall`/`openSettings`,
      Settings sends `navigate-to`.

## Trade-offs

Chose removing Fix Firewall over repairing the quoting: the feature was a
niche workaround, the error path told users to add rules manually anyway, and
every additional tray entry is clutter on the primary surface. Chose IPC +
`router.push` over `loadURL('.../settings')`: a load tears down the socket
and re-mounts the SPA; a push keeps the session alive.

## Verification Criteria

- Tray menu shows exactly Show VDock / Settings / Exit.
- Settings click shows the main window on `/settings` (no reload flicker, no
  stray modal window, no native menu bar).
- No references to `fixFirewall`/`openSettings` remain.

## Implementation Results

- `main.js`: `fixFirewall()` and `openSettings()` deleted (~135 lines);
  menu is Show VDock / Settings / Exit. `createTrayMenu` is now synchronous
  (the auto-launch lookup it awaited was already unused); the orphaned
  `updateTrayMenu()` and the `settings-update` IPC handler (only caller was
  the deleted modal's `postMessage`) removed too.
- `preload.js`: added `onNavigate(handler)` for `navigate-to`.
- `App.vue`: registers `onNavigate` → `router.push(path)`, paths validated
  to start with `/`.
- Deviations: none — the dead-code cleanup (`settings-update` handler,
  `updateTrayMenu`) was implied by removing the modal but worth recording.
- Verified: `node --check` on both Electron files; frontend `vue-tsc` clean;
  vitest 251 tests green. Live tray behaviour needs one manual restart of
  the Electron app.
