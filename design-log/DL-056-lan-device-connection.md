# DL-056 — LAN device connection (QR code → black screen)

**Date**: 2026-09-21
**Status**: Implemented

## Background

Scanning the "Connect a device" QR (`http://<lan-ip>:5000`) from a phone
produced a black screen. The Settings toggle "Allow LAN access" was on,
but the phone couldn't reach the server — and even with connectivity,
two more layers would have failed underneath.

## Analysis — three stacked defects

1. **Toggle never took effect.** `PUT /api/config` writes `allow_lan` to
   `data/config.json` and updates the runtime `Config`, but `app.py`'s
   bind decision reads `Config.ALLOW_LAN` — set only from env vars at
   import. `load_config()` was never applied at startup, so "applies on
   next launch" never happened: `netstat` showed `127.0.0.1:5000` despite
   the saved `allow_lan: true`. The black screen was most likely the PWA
   service worker serving a cached dark shell with zero connectivity.
2. **Socket URL hardcoded.** `socket.ts` connected to
   `http://127.0.0.1:5000` — on the phone that's the phone itself.
3. **Socket origin rejected.** `cors_allowed_origins` listed only
   `localhost:3000/3001`. python-engineio rejects any `Origin` not in the
   list — including same-origin `http://192.168.1.173:5000` — with a 400
   "Not an accepted origin". This same defect silently killed the
   localhost dev socket (`localhost:5173/4444` weren't listed either).

## Changes

- **`backend/config.py`** — `Config.apply_saved_toggles()`: re-applies
  `require_auth`/`allow_lan`/`use_ssl`/`enable_plugins` from `config.json`
  over env defaults; called from `init_app` before `validate()` so a
  file-set `REQUIRE_AUTH` still hits the no-password guard. Moved the
  `lan_ip()` helper here from `routes/config.py` (shared). Added
  `Config.socket_origins()`: env list + backend-port origins +
  frontend-port origins (reads `frontend/.env` `VITE_PORT` like the
  launcher) + LAN-IP origins when `allow_lan` is on.
- **`backend/app.py`** — `apply_saved_toggles()` runs before the socketio
  init so the CORS decision sees the file value; `socketio` now uses
  `Config.socket_origins()`; the `__main__` bind then honors `allow_lan`.
- **`frontend/src/api/socket.ts`** — socket URL derives from
  `window.location.hostname` + `VITE_BACKEND_PORT` (env override kept).
  A phone on `192.168.1.173` now dials the machine's LAN address instead
  of itself; localhost dev unchanged.

## Implementation Results

- Backend restarted: `netstat` shows `0.0.0.0:5000` listening.
- `curl http://192.168.1.173:5000/` → 200 + fresh bundle; `/api/profiles`
  → 200; socket.io polling handshake with `Origin:
  http://192.168.1.173:5000` → **200 + session** (was 400).
- Dev origin `localhost:4444` handshake → 200 (previously dead).
- `npm run build` regenerated `dist/` (the phone's serving path).
- 238/238 tests green; `vue-tsc` clean via the build's typecheck step.

## Notes for the user

- The phone may need **one reload** — the PWA service worker serves the
  old bundle once, then `controllerchange` reloads into the new build.
- If it still won't load, check the Windows Firewall prompt for
  `python.exe` on private networks — binding `0.0.0.0` exposes the port
  but the firewall rule must allow it.

### Follow-up (2026-09-28): configurable deck address

User request: "is it possible to be able to configure the deck address?"

The auto-detected `lan_ip()` (UDP-connect probe) picks the *primary* NIC —
wrong on multi-NIC/VPN machines — and shows a raw IP where a hostname
like `deck.local` would be friendlier. Since `ALLOW_LAN` binds 0.0.0.0,
the server answers on every interface, so the displayed address is purely
informational and a host override is safe.

Design: `deck_host` — an optional persisted override (config.json +
`DECK_HOST` env seed), validated as a bare hostname/IPv4 (no scheme,
port, or path). Empty/null restores auto-detect. `GET /api/config`
returns it alongside `lan_ip`; the frontend's `lanUrl` prefers it. The
QR + Copy follow automatically. `socket_origins()` whitelists BOTH the
auto IP and the override — otherwise a phone loading
`http://deck.local:PORT` gets its Socket.IO handshake rejected. Port
stays the real bind port; an override doesn't change what the server
listens on.

#### Implementation results (2026-09-28, deck_host follow-up)

- `backend/config.py`: `DECK_HOST` env seed + `DECK_HOST_RE` (bare
  hostname/IPv4, no scheme/port/path); `apply_saved_toggles` re-applies a
  regex-clean `deck_host` from config.json; `socket_origins()` whitelists
  BOTH `lan_ip()` and `DECK_HOST` so a phone on the override host keeps
  its Socket.IO handshake.
- `backend/routes/config.py`: GET returns `deck_host` (null = auto);
  PUT accepts `deck_host` — null/'' clears, non-string or non-hostname
  (e.g. 'http://x:4444', 'a b', 'h/p') → 400; persists to config.json
  and updates `Config.DECK_HOST` live.
- `frontend/src/types/index.ts`: `ServerConfig.deck_host?: string | null`.
- `SettingsView.vue`: `lanUrl` prefers `deck_host` over `lan_ip`; new
  "Custom address" row under Deck address — input (placeholder shows the
  auto IP), Apply enabled only when dirty, Enter or click saves via the
  existing `updateServerConfig`, toast on success/failure, QR re-renders
  through the `lanUrl` watcher.
- `conftest.py`: added `DECK_HOST` to `_GUARDED_SETTINGS` — the override
  mutates class state, same leak class the fixture exists to prevent.
- Tests: 3 new cases in `test_security_hardening.py` — set + GET echo,
  reject full URLs/non-strings, clear restores auto. 19/19 file green.

Verified live: PUT deck.local → GET echoes it → address row shows
http://deck.local:4444; clear → back to http://192.168.1.173:4444.
Screenshot: `design-log/refs/deck-host-row-*.png`. `vue-tsc` clean,
`dist` rebuilt. Backend restarted (no reloader under DEBUG=False) —
socket clients reconnected automatically.

Note: the bind itself is unchanged — the override only changes what the
QR/address advertises. That is the correct scope: the server already
answers on every interface when ALLOW_LAN is on.
