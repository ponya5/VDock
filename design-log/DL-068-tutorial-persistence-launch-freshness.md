# DL-068: Tutorial re-showing on every launch + launcher not guaranteeing fresh code

**Date:** 2026-09-25

## Problem

Three related reports from the same user session, all traced back to the
app's launch sequence:

1. The first-run bubble tutorial (`useTutorial`, DL from the original
   onboarding work) reappeared on **every** launch via the desktop icon,
   even though it had already been completed and `tutorialCompleted` is a
   server-persisted setting specifically designed to survive restarts.
2. Because the tutorial's first step forces a navigation to `/profiles`
   (`TUTORIAL_STEPS[0].route`), the app appeared to "default to the
   Profiles screen" instead of the Dashboard on every launch — this turned
   out to be a symptom of (1), not a separate router bug: the router's
   actual default route is already `/` (Dashboard).
3. After a round of frontend fixes in [DL-066](DL-066-ide-agent-parity.md)
   and [DL-067](DL-067-mobile-fullscreen-prominence.md), the user relaunched
   the desktop app via `launch.bat` and did not see the changes, and asked
   whether a full `setup.bat` re-run was required.

## Root causes

### 1 & 2 — tutorial race condition

`DashboardView.vue` and `App.vue` are both mounted on every navigation to
`/`, but Vue fires a **child's** `onMounted` before its **parent's** —
`DashboardView` is a child of `App` (via `<router-view>`). `App.vue`'s
`onMounted` is what calls `settingsStore.loadSettingsFromServer()`, the
only thing that populates `tutorialCompleted` from its real, persisted
value; before that resolves, `tutorialCompleted` sits on its `ref(false)`
default.

`DashboardView.vue` calls `tour.consumePendingOrFirstRun()` on a fixed
800 ms `setTimeout` with no dependency on that fetch actually finishing.
On a freshly-spawned backend (as happens on every launch — the Python
process the launcher just started needs a moment to come up and answer
its first request) the `GET /api/user-settings` round trip can easily
exceed 800 ms, so the tour started against the stale default nearly every
time, not just on genuinely first runs.

### 3 — launcher not guaranteeing fresh frontend code

`ensure_fresh_backend()` already existed in `VDock-Launcher.py` and
specifically detects a stale/duplicate backend and restarts it before
reuse. `launch_frontend()` had no equivalent — every launch unconditionally
spawned a new `npm run dev`, with no check for whether one was already
running. Vite doesn't fail loudly on a port already in use; without
`strictPort` it just tries the next free port and logs a line to
`vdock-frontend-launcher.log` that nothing surfaces to the user. A leftover
dev server from an earlier session (e.g. one that survived a crashed
Electron window) would keep serving its old, unwatched-forever bundle
indefinitely, silently, while Electron kept pointing at the same
configured port regardless.

This is not the standard "why don't I see my change" case for a Vite dev
server — its file watcher normally pushes edits over HMR without a restart
— but it is a real, silent failure mode with no user-visible signal, so it
had to be closed off explicitly rather than assumed away.

## Fix

- **`settings.ts`**: added `ensureSettingsLoaded()` — a promise-deduped
  wrapper around `loadSettingsFromServer()` (same dedup pattern as
  `loadProfileMaps()` in DL-065's follow-up). `App.vue` and
  `DashboardView.vue` now both call this instead of `App.vue` alone calling
  `loadSettingsFromServer()` directly; whichever mounts first triggers the
  actual `GET`, the other awaits the same in-flight promise.
- **`DashboardView.vue`**: awaits `settingsStore.ensureSettingsLoaded()`
  immediately before the tutorial's `setTimeout`, so
  `consumePendingOrFirstRun()` only ever runs once the real
  `tutorialCompleted` value is in the store. No change was needed to fix
  the "defaults to Profiles" report — once the tour stops incorrectly
  auto-starting, the router's actual default (`/`, Dashboard) is what
  renders.
- **`VDock-Launcher.py`**: added `ensure_fresh_frontend()`, mirroring
  `ensure_fresh_backend()` — counts listeners on the frontend port, kills
  and restarts if more than one is found (the duplicate-process case), and
  reuses a single healthy one rather than spawning a redundant second
  `npm run dev` every launch. Wired into `main()` in place of the
  unconditional `launch_frontend()` call.

## Trade-offs

- `ensure_fresh_frontend()` does not deep-health-check the existing dev
  server the way `ensure_fresh_backend()` pings `/api/user-settings` —
  Vite has no equivalent lightweight endpoint to distinguish "healthy" from
  "bound but wedged." It only acts on the unambiguous duplicate-listener
  case. A single wedged-but-listening dev server (rare) still requires a
  manual process kill.
- This does not retroactively clean up any duplicate dev-server processes
  already accumulated from launches before this fix — the user should do
  one manual full stop (Task Manager: end any `node.exe`/`python.exe`
  processes under VDock, or Exit via the tray icon) before the next
  launch, after which `ensure_fresh_frontend()` keeps things clean going
  forward.

## Verification Criteria

- Full frontend suite green; `vue-tsc --noEmit` clean.
- `VDock-Launcher.py` compiles (`python -m py_compile`).
- Not verified live end-to-end (spawning the actual Electron shell/backend
  is outside this session) — the user should confirm after one full clean
  restart that: the tutorial does not reappear, the dashboard is what
  loads, and relaunching alone (no `setup.bat`) reflects further code
  changes going forward.

## Implementation Results

- `ensureSettingsLoaded()` added to `stores/settings.ts` and exported;
  `App.vue` switched to it; `DashboardView.vue` awaits it before the
  tutorial auto-start check.
- `ensure_fresh_frontend()` added to `scripts/VDock-Launcher.py`, wired
  into `main()`.
- Full frontend suite: 59 files / 253 tests green; `vue-tsc --noEmit`
  clean. Backend suite unaffected (854 passed, from the DL-066 follow-up
  work in the same session).
