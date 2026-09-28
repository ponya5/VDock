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

## Follow-up (2026-09-28): remove the launch-on-startup option entirely

**Ask:** "remove the option to start vdock when windows, macos linux starts".
The audited toggle is gone — and so is the mechanism, not just the UI row:

- `SettingsView.vue` — "Launch VDock on startup" row + status line,
  `handleStartOnBootToggle`, `syncStartOnBootFromSystem`,
  `startOnBootStatus`, and the two search-index entries removed. The
  "Startup & navigation" panel keeps launcher-terminal + new-tab rows.
- `stores/settings.ts` — `startOnBoot` dropped from
  `PersistedUserSettings`, the ref, `buildSettingsPayload`,
  `applySettingsObject`, the defaults merge, and both return objects.
  Legacy blobs carrying the key are silently ignored and the key is
  dropped on next save.
- `backend/routes/user_settings.py` — `startOnBoot` removed from the
  allowlist so stale clients can't resurrect it.
- `backend/routes/system.py` — `GET/POST /api/system/autostart`,
  `_is_autostart_enabled`, `_windows_autostart`, `_macos_autostart`,
  `_linux_autostart`, `_resolve_launch_command`, and
  `AUTOSTART_REGISTRY_NAME` deleted; `os`/`platform`/`sys` imports that
  only served the helpers removed.
- `frontend/electron/main.js` — `auto-launch` package init, both IPC
  handlers (`toggle-auto-launch`, `is-auto-launch-enabled`), the boot-time
  `isEnabled` log, and the dead `setLoginItemSettings(openAtLogin:false)`
  block deleted. `preload.js` + `useElectron.ts` drop the matching bridge
  methods; `auto-launch` uninstalled from `frontend/electron/package.json`.
- `UserGuide.vue` "Auto-start" tip and the README Server blurb updated.
- This machine's existing `HKCU\...\Run\VDock` entry (enabled earlier per
  the audit above) deleted — removing the option must not leave VDock
  autostarting with no way to disable it. `uninstall.bat`/`uninstall.sh`
  still remove the legacy entry for any other install.

### Implementation Results (2026-09-28 follow-up)

- Frontend suite: **365 passed / 70 files** (same known vitest-worker
  teardown flake in `property6_settings.test.ts`); `vue-tsc --noEmit`
  clean; backend tests clean; `npm run build` green — `dist/` rebuilt.
- `reg query` confirms the `VDock` Run value is gone.
- Server tab still shows the remaining two rows; settings round-trip
  verified (45→44 keys, `startOnBoot` stripped from `user_settings.json`
  on next save).
