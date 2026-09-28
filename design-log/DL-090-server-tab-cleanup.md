# DL-090 — Server tab: drop sub-nav + full settings audit

## Problem / ask

The Server sidebar item had two sub-links ("Startup & navigation",
"Connection") duplicating a page with only two panels — user asked to
remove them, and to live-test every control on the Server screen.

## Changes

- `SettingsView.vue` — removed the `nav-sub` collapse under Server
  (Startup & navigation / Connection buttons) and its chevron.
  `scrollToPanel` stays — search results still deep-link to panel ids.

## Implementation Results — full Server-screen audit (live, Windows)

| Control | Result |
|---|---|
| Launch VDock on startup | ON→registry `HKCU\...\Run\VDock = "…\launch.bat"`, GET reads `true`; OFF deletes the value. UI toggle drives the same endpoint. |
| Close launcher terminal after startup | PUT `autoCloseLauncher:false` persists to `user_settings.json`; `VDock-Launcher.should_auto_close_launcher()` returns `False` (window waits for Enter). `true` → auto-closes. `VDOCK_AUTO_CLOSE_LAUNCHER` env still overrides. |
| Open settings in a new browser tab | ON → Settings button calls `window.open('/settings?standalone=1')`; OFF → in-place `router.push('/settings')`. Verified via stubbed `window.open` spy. |
| Host | `GET /api/config` → `127.0.0.1` displayed verbatim (read-only). |
| Authentication | `require_auth:false` → "Disabled" warn chip (read-only). |
| Ports — Check | free ports → "Both ports are available."; `80` → per-field range error; same port twice → "must differ"; real collision (5040, WSDAPI) → "Port 5040 is already in use"; configured ports pass (collision probe skips self). |
| Ports — Save | writes `backend/.env PORT` + `frontend/.env VITE_PORT/VITE_BACKEND_PORT`, mirrors `config.port`, returns `restart_required:true` with the new URL. |

- Quirk found: `PUT /api/user-settings` requires a nested
  `{settings: {…}}` body — a flat key object returns
  `{"error":"settings object is required"}` (correct behavior; the UI
  always sends the nested shape).
- Quirk found: the settings store re-syncs its cached value to the
  server on load — direct-API edits while a frontend page is open can
  be overwritten back. Noted, not a defect of this feature.
- Sub-nav removal verified live (nav list shows bare "Server"),
  `vue-tsc` clean, `dist` rebuilt.
- Ref: `design-log/refs/server-tab-no-subnav-*.png`
