# DL-113 — Launcher console auto-close from any invocation

## Background

`launch.bat` runs `scripts/VDock-Launcher.py` in the invoking console and the
launcher honors `autoCloseLauncher` (Settings → Server, DL-090) by skipping the
"Press Enter" wait before exiting. That closes the window only when the console
is *owned* by the batch — double-click, the desktop `VDock.lnk` shortcut
(`TargetPath = launch.bat`), or setup.bat's `start "" launch.bat`: cmd exits at
end of script and the console disappears with it.

It does **not** work when `launch.bat` is invoked inside an existing terminal —
PowerShell/cmd/Windows Terminal, the way the user actually launches it. The
script exits back to the user's prompt and the window stays open (retitled
"VDock Launcher" by the script, compounding the confusion). Observed live
2026-09-29: stack came up correctly, the launcher printed "Launcher window will
close automatically", python exited — and the terminal remained, because it is
the user's shell and cannot be closed by the script.

## Problem

A script cannot close a console window owned by someone else's interactive
shell. Auto-close must therefore not depend on how `launch.bat` was invoked.

## Questions and Answers

**Q: Why not just `exit` at the end of the batch?**
A: `exit` would close the cmd subprocess — but when the bat runs as a child of
an interactive PowerShell, the console belongs to PowerShell and stays open
regardless. There is no batch-visible way to dismiss a foreign terminal window.

**Q: Why not detect "do we own this console" and only re-dispatch then?**
A: Distinguishing "double-clicked, own console" from "child cmd of PowerShell"
requires inspecting the console/parent process — fragile WMIC/PowerShell
probing for a cosmetic gain (a sub-second extra console flash on
shortcut/double-click launches). Unconditional re-dispatch is deterministic and
~5 lines.

**Q: Does this break `autoCloseLauncher` = off?**
A: No. The setting still controls whether the Python launcher waits for Enter —
in the transient window instead of the user's terminal. The window always
closes once the launcher exits.

## Design

`launch.bat` re-dispatches itself into a dedicated transient console:

```
start "VDock Launcher" cmd /c ""%~f0" --in-console %*"
```

- Invoking terminal (PowerShell, cmd, WT) returns to the prompt immediately.
- The transient window shows the normal launcher output and closes itself when
  python exits 0; on non-zero exit `pause` holds it open so errors stay
  readable (better than the pre-change auto-close-ON failure path, which the
  outer `pause` already covered anyway).
- `--in-console` is the recursion guard and doubles as an explicit debug mode:
  `launch.bat --in-console` runs in the current terminal exactly as before.
- `title VDock Launcher` moves into the inner branch so the caller's terminal
  is no longer retitled (the transient window gets its title from `start`).
- `%~x0` guard: if invoked as bare `launch` (no extension typed), `%~f0`
  resolves extensionless and `cmd /c` would not find the file — dispatch uses
  `"%~f0.bat"` in that case.
- `setup.bat :launch_vdock` passes `--in-console` inside its existing `start`
  so that path remains single-window instead of flash-then-respawn.
- `launch.sh` unchanged: POSIX terminals have no equivalent owned-console
  lifecycle, and the complaint path is Windows-specific.

```mermaid
flowchart LR
    A[any shell / shortcut / Run key] -->|launch.bat| B{arg == --in-console?}
    B -->|no| C["start \"VDock Launcher\" cmd /c launch.bat --in-console"]
    C --> D[caller exits / prompt returns]
    B -->|yes| E[python VDock-Launcher.py]
    E -->|exit 0| F[window closes]
    E -->|exit !=0| G[pause — error stays readable]
```

## Implementation Plan

- [x] `launch.bat`: re-dispatch block + `--in-console` inner branch
- [x] `setup.bat`: `:launch_vdock` starts `launch.bat --in-console` directly
- [x] Verify dispatch mechanics with a stub launcher (success + failure paths)

## Trade-offs

Shortcut/double-click launches gain a sub-second extra console flash (outer
window spawns the transient one, then exits). Accepted — deterministic
correctness over a cosmetic blink. Rejected alternatives: `exit`-the-console
(harms foreign shells or no-ops), console-owner detection (fragile probing),
`start` on the bat directly without `cmd /c` (close-on-exit semantics less
explicit).

## Verification Criteria

- `launch.bat` from an interactive PowerShell: prompt returns immediately; a
  "VDock Launcher" window shows startup output and closes itself on success.
- Stub forced to exit 1: transient window remains at `pause`.
- Desktop shortcut / `start ""` path: still ends with zero lingering windows.
- Backend on :5000 unaffected (services are detached — unchanged).

## Implementation Results

- `launch.bat`: `title` removed from the top (no longer retitles the caller's
  terminal) and applied inside the `:in_console` branch instead. Dispatch
  block sits after the env-var/PATH setup so toggles edited into the file
  propagate to the child console either way.
- `setup.bat :launch_vdock`: `start "" launch.bat` → `start "VDock Launcher"
  cmd /c ""%ROOT%\launch.bat" --in-console"` — one window, no flash-then-
  respawn on the setup → launch path.
- Verified with a verbatim copy of the edited `launch.bat` + stub
  `VDock-Launcher.py` (marker-file + `STUB_EXIT` knob):
  - `cmd /c launch.bat` (mirrors PowerShell invocation): caller returned
    immediately, transient window wrote the marker and closed itself; zero
    lingering cmd/python processes afterwards.
  - `launch` typed bare (no extension): `%~x0` guard dispatched
    `"%~f0.bat"`; marker written — extensionless invocation works.
  - `launch.bat --in-console`: ran in-place, no new window, exit 0.
  - `STUB_EXIT=1`: transient window held at `pause` (live `cmd /c
    "...--in-console"` process observed) — failures stay readable.
- Real stack not re-launched (Electron has no single-instance lock; a live
  run would have opened a second app window). The dispatch mechanics —
  the only thing that changed — are fully exercised by the stub.
- Follow-up (same session): owned-console launchers now pass
  `--in-console` directly, removing the flash-then-respawn on that path —
  `setup.bat :create_desktop_shortcut` writes `Arguments='--in-console'`,
  `VDock.nsi` Start-Menu/Desktop shortcuts pass it as the parameter, and
  the existing `~/Desktop/VDock.lnk` was updated in place (verified
  `Args=--in-console`). A shortcut console owns its window and self-closes
  at end of script, so re-dispatch would only add a flicker.
- Deviations: none.
