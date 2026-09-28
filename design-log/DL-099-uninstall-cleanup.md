# DL-099: Uninstall cleanup — scripts for source installs + NSIS uninstall hook

## Problem

Nothing removes the state VDock creates *outside* its own folder/install dir:

- **Source checkout** (`setup.bat`/`setup.sh`): desktop launchers (`VDock.lnk`,
  `VDock.command`, `VDock.sh` + `vdock.desktop`) and the opt-in autostart
  entries (HKCU Run `VDock`, `~/Library/LaunchAgents/com.vdock.launcher.plist`,
  `~/.config/autostart/vdock.desktop`). Deleting the repo folder leaves dead
  shortcuts and a boot-time invocation of a missing path.
- **Packaged builds**: electron-builder's NSIS uninstaller only removes what
  the installer created — the runtime-written autostart entry survives.
  macOS (dmg/zip) and Linux (AppImage/deb) have no uninstaller convention at
  all; user data dirs (`userData/vdock-data` → `%APPDATA%/VDock`,
  `~/Library/Application Support/VDock`, `~/.config/VDock`) persist by design
  (`deleteAppDataOnUninstall: false`).

## Design

### Source installs: `uninstall.bat` / `uninstall.sh`

Mirrors the setup scripts' style and flags. Scope is deliberately narrow —
everything the installer wrote *outside* the repo, plus stopping running
processes; the repo folder itself is deleted by hand so the script never has
to self-delete mid-run.

Steps:

1. Stop running VDock processes — targeted by install root, not image name
   (Windows: PowerShell `Get-CimInstance Win32_Process` filtered on
   CommandLine containing the root path; POSIX: `pkill -f "$ROOT"`). Covers
   `VDock-Launcher.py`, the venv backend, the Vite dev server, and dev
   Electron.
2. Remove the autostart entry for the current OS (all three mechanisms,
   matching `backend/routes/system.py`'s `_windows_autostart` /
   `_macos_autostart` / `_linux_autostart` — `launchctl unload` before
   deleting the plist).
3. Remove the desktop launcher(s) the matching setup script created
   (PS-resolved Desktop path on Windows; `~/Desktop` on POSIX, honoring
   `XDG_DESKTOP_DIR`).
4. Print the finish step: `delete <ROOT>` (data lives in `backend/data` so
   profiles/settings die with the folder — no separate wipe needed).

Flags: none beyond a `--yes` non-interactive form; the default path asks for
confirmation before killing processes.

### Packaged Windows: NSIS `customUnInstall`

`frontend/electron/installer.nsh` with a `customUnInstall` macro that
`DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "VDock"`
— that single value name is written by both the backend autostart toggle and
the Electron `auto-launch` package, so one delete covers both. Wired via
`"nsis": { "include": "installer.nsh" }`. Harmless no-op when absent.

### macOS/Linux packaged: documentation

README gains an "Uninstalling" section: dmg/zip → drag to Trash +
delete `~/Library/Application Support/VDock` + remove the LaunchAgent;
AppImage → delete file; deb → `apt remove` + `rm -rf ~/.config/VDock`;
and the desktop-file autostart removal on each OS.

## Implementation Plan

- [ ] `uninstall.bat` + `uninstall.sh` at repo root
- [ ] `frontend/electron/installer.nsh` + `nsis.include` wiring
- [ ] README "Uninstalling" section
- [ ] Manual verification: script dry-run on this machine (autostart + shortcut removal paths)

## Implementation Results

All four plan items landed; two implementation refinements vs. the design:

- `uninstall.bat` — PowerShell `Win32_Process` sweep matches CommandLine
  containing the root path, `VDock-Launcher.py` (the launcher invokes it
  with a *relative* path, so root-match alone misses it), and
  `vdock-backend`; plus a port-listener kill on the configured backend/
  frontend ports (read from `backend/.env`/`frontend/.env`, defaults
  5000/3000) as backstop for processes whose cmdline carries no path —
  e.g. `npm run dev` spawned with a cwd. `cmd|powershell|pwsh` image
  names are excluded so the script can't kill its own shell. `reg delete`
  for the Run value, PS-resolved Desktop for `VDock.lnk`.
- `uninstall.sh` — `pgrep -f "$ROOT"` piped through `grep -vx $$/PPID`
  instead of bare `pkill` (the script's own cmdline contains `$ROOT`;
  plain `pkill` would self-terminate). Same `VDock-Launcher.py|vdock-backend`
  pattern pass. `launchctl unload` + plist rm on Darwin;
  `~/.config/autostart/vdock.desktop` on Linux; desktop launchers removed
  honoring `XDG_DESKTOP_DIR`. `chmod +x` set in the git index (mode 100755).
- `frontend/electron/installer.nsh` — `customUnInstall` macro deletes the
  HKCU Run `VDock` value; wired via `"nsis": { "include": "installer.nsh" }`.
- README — "### Uninstall" added under Quick start (per-OS matrix for
  installed apps + the source-checkout scripts), and the stale "four
  working scenes" line fixed to two (Media + Claude Code, DL-100).

**Verification:** `bash -n uninstall.sh` clean; `uninstall.bat` reviewed
line-by-line (no live dry-run — the machine this was built on is the dev
checkout itself, and the sweep kills processes by root path). NSIS macro
is exercised only at package-build/uninstall time; the value name matches
both writers (`backend/routes/system.py`, `auto-launch` default).
