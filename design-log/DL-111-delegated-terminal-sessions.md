# DL-111: Session detection misses Windows-Terminal-delegated consoles

**Date:** 2026-10-02

## Problem

Two live Claude Code windows were open while the session picker reported
"No live session windows found". `GET /api/agent-sessions?source=claude`
returned `sessions: []` even though `iter_session_pids('claude')` found
both `claude.exe` processes.

## Root cause

`_session_host_candidates` maps a session process to a host window by
walking **up the ancestor chain** (and each ancestor's children) until a
PID owns a visible window.

On this machine, Windows Terminal is the *default terminal application*:
when the VDock backend spawned `cmd /c claude --continue || claude`,
Windows handed the console to Windows Terminal instead of a classic
conhost window. The observed topology:

- Session chain: `claude.exe -> cmd.exe -> python.exe (backend)` — none
  own a window.
- `cmd.exe` gains a `conhost.exe 0x4` child (the delegated/headless
  console server) — owns no visible window.
- An `OpenConsole.exe` spawns ~30-50ms after the conhost, parented to
  `svchost` — the WT-hosted console server; owns no window.
- The visible "✳ Claude Code" windows are top-level
  `CASCADIA_HOSTING_WINDOW_CLASS` windows owned by `WindowsTerminal.exe`
  — a **disconnected process tree**. No parent/child or
  window-hierarchy edge leads from the session to its window, so the
  ancestor walk cannot reach it.

This breaks both `list_session_hosts` (empty picker) and
`find_session_host_window` (Submit/Continue buttons can't resolve a
target). It affects every console session on a box where WT (or another
registered terminal) is the default console host — an increasingly
common default.

## Fix

Add a **delegated-terminal fallback tier** to `_session_host_candidates`:

- After the ancestor walk, sessions with no host window look for visible
  top-level windows owned by known terminal-host exes
  (`windowsterminal.exe`, `openconsole.exe`, `wezterm-gui.exe`,
  `tabby.exe`, `alacritty.exe`, `hyper.exe`, `fluent-terminal.exe`,
  `wave.exe`, `warp.exe`) **whose title contains the marker**
  (delegated consoles title their host window after the running app —
  "✳ Claude Code" for `claude`).
- Pairing is deterministic, newest-session-first in EnumWindows
  (Z) order — the freshest delegated window is usually topmost.
  Sessions beyond the window count share the last window (the data
  model already allows several sessions per hwnd).
- Fallback candidates report `self_owned=False` and the session's real
  cwd tier, so existing ranking (cwd > hosted > title > newest) is
  unchanged; ancestor-walk hits always win over fallback guesses.

Residual risk: with N sessions and N identically-titled terminal
windows, pid↔window pairing can be wrong (identify could flash the
sibling window). Bounded — the picker surfaces sessions again and
button presses reach *a* live session of the right agent; window-level
identity is unrecoverable without a terminal-app API.

## Implementation Results

Implemented the fallback tier in `_session_host_candidates`:

- `_delegated_terminal_windows()` scans `_visible_windows_by_pid()` for
  marker-titled windows whose owner is a registered console host
  (`_TERMINAL_HOST_NAMES`: windowsterminal, wezterm-gui, alacritty,
  WindowsTerminalPreview).
- Sessions that survive the ancestor walk without a host claim free
  windows newest-session-first against enumeration order; claimed hwnds
  are removed so each session gets its own window.
- `iter_session_pids` pids with no in-tree window stay invisible unless a
  marker-titled terminal window exists — a browser tab titled "claude
  tutorial" cannot be claimed (non-terminal owner rejected).

Verified:

- Live: two real `claude.exe` sessions spawned through VDock's own
  `claude_continue` action (cmd /c claude --continue) under Windows
  Terminal default-terminal delegation — previously `sessions: []`, now
  both map to distinct `✳ Claude Code` hwnds.
- End-to-end after backend restart: spawned a fresh session via
  `POST /api/actions/execute`, `GET /api/agent-sessions?source=claude`
  returns the row with hwnd/project/state — picker populates.
- Tests: `test_session_targeting.py` +4 (19/19 green) — pairing,
  non-terminal rejection, N-session pairing, in-tree host precedence;
  `test_window_focus_escalation` + `test_agent_state_events` 68/68 green.

Residual risk noted in Fix section stands (title-only pairing can swap
same-titled windows).
