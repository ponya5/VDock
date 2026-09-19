# DL-006 — Dev-first Running Applications list

**Date:** 2026-09-20
**Branch:** `feat/unified-background`
**Status:** Implemented

## Problem

Settings → Widgets & Integration → *Running Applications* lists every
process with a window, alphabetically and undifferentiated. On a 7" touch
panel that means scrolling past dozens of system/background apps to find
the ones VDock can actually drive. VDock's direction is a **development
companion** — dev tools first, machine/misc apps second.

## Design

Two additions to the Running Applications card (`SettingsView.vue`):

**Smart search** — a filter input above the list matching app name and exe
(case-insensitive substring), plus a small alias table so "terminal" finds
`windowsterminal.exe`/`cmd.exe`/`powershell.exe`, "vscode" finds
`code.exe`, "browser" finds the installed browsers, etc. Result count is
shown while filtering; a distinct empty state covers "no matches".

**Dev-first ordering** — three tiers, alphabetical within each:

1. **Controllable** — the app's exe appears in a backend app profile
   (`/api/app-profiles`: Cursor, Copilot, Claude Code terminals). These get
   an accent badge with the profile label — this is the strongest signal
   since it means "VDock has real actions for this".
2. **Dev tool** — exe is in a curated `DEV_APP_EXES` set (editors, IDEs,
   terminals, git clients, API/database tools, container tooling,
   runtimes). Gets a subtle `dev` chip.
3. Everything else.

Profiles are fetched once via the existing `fetchAppProfiles()` API module
and cached in a ref; re-fetches happen only alongside the list refresh.
Sorting is a computed, so toggling an integration or typing in the search
re-orders immediately without another backend call.

## Rejected

- **Backend-side ranking** — the list is a presentation concern; the
  `/metrics/running-apps` payload stays a flat process list.
- **Usage-frequency tracking** — no telemetry exists; "common" is defined
  by VDock's own integration surface instead, which is more honest.
- **Fuzzy matching** — substring + aliases is predictable; fuzzy scoring
  would surface surprising matches for a 3-letter query.

## Implementation Results

Shipped as designed, frontend-only in `SettingsView.vue`:

- Search toolbar above the list: icon input with clear button, filters on
  name/exe substring plus the `APP_ALIASES` table (covers `terminal`,
  `vscode`, `claude`, `browser`, `git`, `docker`, `jetbrains`, `editor`,
  …); shows `N of M` while filtering and a "No apps match" row inside the
  list frame.
- Ordering: `filteredApps` computed sorts profiled apps (accent badge with
  the profile label + primary left border), then `DEV_APP_EXES` members
  (`Dev` chip + left border), then the rest — alphabetical within tiers.
- `fetchAppProfiles()` is fetched once lazily on the first
  `refreshRunningApps()` call and cached; a failed fetch resets the flag so
  the next refresh retries.
- Settings search index entry keywords updated (`filter search dev tools`).

Verified: `vue-tsc --noEmit` clean; **138 frontend tests pass**.
