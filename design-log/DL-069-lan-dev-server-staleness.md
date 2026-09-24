# DL-069: Mobile/LAN devices frozen on stale code while desktop always updates

**Date:** 2026-09-25
**Depends on:** DL-056 (LAN device connection), DL-068 (launcher freshness —
addressed the same symptom for the desktop/backend side)

## Problem

After DL-066/067/068 landed, the user confirmed desktop showed the update
but mobile still showed the old Cursor layout, no interactive action bar,
and no fullscreen prompt — even after clearing Chrome's cache on the phone.

## Root cause

The desktop Electron window (dev mode) loads `http://localhost:<frontend
port>` directly from the Vite dev server, so it always reflects the latest
source via HMR. The "Connect a device" QR code, however, was hardcoded to
point at **the backend port** — `SettingsView.vue`'s `lanUrl` comment said
so explicitly: *"the backend port, which serves the built frontend in
production. In dev, Vite only binds localhost."*

That backend route serves `frontend/dist/` — a **static build artifact**
that only updates when someone explicitly runs `npm run build`. A phone
scanning that QR code was never talking to the live dev server at all; it
was permanently pinned to whatever `dist/` contained the last time it was
built, regardless of how many times the app was relaunched or how much
source code changed since. Clearing the phone's browser cache doesn't fix
this because the problem isn't a client-side cache — the *server* was
handing out stale bytes on every single request, cache or not. (The
project's PWA plugin also registers a service worker that precaches the
build, which is a second, independent reason a phone can look "stuck" even
after a fresh `dist/` — Cache Storage isn't cleared by every browser's
"clear cache" action.)

Separately, while diagnosing this, `netstat` on the dev machine turned up
**five already-running Vite dev server processes** simultaneously bound to
ports 4444–4448, all pre-dating this session's launcher fix (DL-068). Only
port 4444 (the currently configured `VITE_PORT`) had live traffic; 4445–4448
were orphaned leftovers from earlier launches where a previous `npm run dev`
found the configured port taken and — Vite's default behavior — silently
tried the next one instead of failing. `ensure_fresh_frontend()` from
DL-068 only inspects the one *configured* port, so it can detect duplicates
piled up there, but it had no way to know these adjacent-port strays
existed at all.

## Fix

- **`vite.config.ts`**: `server.host` now binds every interface (instead of
  the Vite default of localhost-only) whenever LAN access is enabled —
  gated by a new `isLanAccessAllowed()` helper that reads
  `backend/data/config.json`'s `allow_lan` flag directly, mirroring the
  backend's own `ALLOW_LAN` gate (`config.py`) so this never exposes the
  dev server on the network when the user has that setting switched off.
- **`vite.config.ts`**: added `server.strictPort: true` — if the configured
  port is already taken, Vite now fails loudly instead of silently
  drifting to the next free one. This is what let five orphaned dev servers
  accumulate unnoticed on adjacent ports in the first place.
- **`SettingsView.vue`**'s `lanUrl` computed now branches on
  `import.meta.env.DEV`: in a dev session it points the QR code/address at
  the Vite dev server's own port (`import.meta.env.VITE_PORT`) instead of
  the backend port, so a LAN device gets the same always-fresh HMR source
  the desktop Electron window does. A built/packaged app (`import.meta.env
  .DEV` is `false`) keeps pointing at the backend port, since that's what
  actually serves `dist/` in that case — this only changes dev-mode
  behavior.
- Ran `npm run build` once during this session so `frontend/dist/` itself
  is no longer stale, covering anyone still on the backend-served path
  (production/packaged installs, or a dev session with LAN access
  disabled).

## Trade-offs

- `strictPort: true` means a genuine port conflict now blocks frontend
  startup entirely (visible in `vdock-frontend-launcher.log` and as a
  "frontend did not respond in time" warning from the launcher) rather
  than silently working on a different port. This is the intended
  trade-off — a loud, diagnosable failure beats an invisible stale server.
- This session could not clean up the five already-running stray dev
  server processes found on the dev machine — the agent's shell can
  observe them via `netstat` (PIDs 11020, 14724, 26008, 31324, 4124 on
  ports 4444–4448) but cannot enumerate or terminate them (`Get-Process`/
  `taskkill` return nothing for those PIDs from this shell — they belong to
  the user's interactive desktop session, a boundary this shell can't
  cross). The user needs to close them manually via Task Manager once;
  `ensure_fresh_frontend()` (DL-068) plus `strictPort` together prevent new
  strays from accumulating on every future launch.

## Verification Criteria

- Full frontend suite green; `vue-tsc --noEmit` clean.
- `npm run build` succeeds and populates `frontend/dist/`.
- `npx vite` (sanity run) confirms `strictPort` + LAN-gated `host` behave
  as expected — observed listening on `0.0.0.0` and all detected LAN
  addresses when `allow_lan` is `true` in `backend/data/config.json`.
- Not verified live end-to-end on the user's phone from this session — the
  user needs to close the stray dev-server processes once (see Trade-offs)
  and rescan the QR code from Settings → Connect a device.

## Implementation Results

- `vite.config.ts`: added `isLanAccessAllowed()`, `server.host` gated on
  it, `server.strictPort: true`.
- `SettingsView.vue`: `lanUrl` branches on `import.meta.env.DEV` to target
  the Vite port in dev, backend port in production.
- `frontend/dist/` rebuilt via `npm run build` (67 precached entries,
  `sw.js` regenerated).
- Full frontend suite: 59 files / 253 tests green; `vue-tsc --noEmit`
  clean.
