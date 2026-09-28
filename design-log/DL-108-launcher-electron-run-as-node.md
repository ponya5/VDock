# DL-108: Launcher sanitizes ELECTRON_RUN_AS_NODE before spawning Electron

**Date:** 2026-09-28

## Problem

Found while live-testing the uninstall/reinstall cycle: after
`uninstall.bat` stopped the stack and `launch.bat` brought it back, the
Electron window never appeared. `vdock-electron-launcher.log` showed
`main.js:377` crashing on `ipcMain.handle('window-pin', ...)` with
`TypeError: Cannot read properties of undefined (reading 'handle')`,
stack rooted in `node:electron/js2c/node_init` / Node.js v24.

## Root cause

`launch_electron()` builds `electron_env = os.environ.copy()`. The
launching shell carried `ELECTRON_RUN_AS_NODE=1` (ambient in the agent/
tool shell that invoked `launch.bat` — not a User/Machine env var). With
that var set, the `electron` binary executes `main.js` as **plain Node**:
`require('electron')` resolves to the npm package stub (a path string),
so `ipcMain` — and every other destructured API — is `undefined`. The
first handler registration throws, main.js exits, and the launcher
quietly falls back to the browser.

Any environment that sets this var (Electron-based IDE terminals, agent
harnesses, CI) reproduces it; the failure looks like "VDock didn't open."

## Fix

`scripts/VDock-Launcher.py`: `electron_env.pop("ELECTRON_RUN_AS_NODE",
None)` before spawning `npx electron .`. The var is meaningless for a
real app launch and poisonous here; scrubbing it is always correct.

## Implementation Results

- Added the pop + comment. Verified live: spawned `electron .` from a
  shell *without* the var → main/renderer/GPU processes all came up;
  the earlier crash reproduced deterministically *with* the var set.
- Confirmed during the same session's uninstall/install test:
  `uninstall.bat --yes` stopped all VDock processes, cleared the
  autostart path (none was set) and removed `VDock.lnk`;
  `setup.bat --full` recreated the shortcut and preserved `.env`
  contents; `launch.bat` restored backend (`0.0.0.0:5000`, LAN still on)
  and Vite (`:::3000`, all interfaces).
