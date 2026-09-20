# DL-007 — Port Configuration in Server Settings

**Date:** 2026-09-20
**Branch:** `upgrade/upgrade--keypad`
**Status:** Implemented

## Problem

VDock's ports are only configurable through `setup.bat → Configure ports` or
hand-editing `.env` files. Port 3000 is the most common dev-server port on any
machine — collisions are routine, and the user hit the worktree/main-checkout
confusion partly because two instances fought over different ports. The Server
settings screen shows host/port as **read-only** with a note saying "edit
backend/.env and restart".

## Design

**Backend** — `routes/system.py` gains `GET/PUT /api/system/ports`:

- `GET` returns the configured ports (backend from `Config.PORT`, frontend
  from `frontend/.env` `VITE_PORT`) and whether each is currently listening.
- `PUT` accepts `{frontend_port, backend_port, check_only}`. Validation:
  numeric, 1024–65535, distinct from each other. Each port is probed with
  `connect_ex`; "in use" is reported per-field — **except** a port already
  bound by this VDock instance (re-saving current values is not an error).
  `check_only` validates without writing, backing the UI's Check button.
- Writing reuses the setup.bat contract in Python:
  `backend/.env` gets `PORT=` + `CORS_ORIGINS=`; `frontend/.env` gets
  `VITE_PORT=` + `VITE_BACKEND_PORT=`. The writer is line-preserving — it
  rewrites only those keys in place, keeping comments and unrelated keys
  (unlike setup.bat's `findstr` strip), satisfying the DL-002 .env-safety
  rule. `CORS_ORIGINS` keeps any non-loopback origins the user added and
  refreshes only the managed `localhost`/`127.0.0.1` pair. `data/config.json`'s
  `port` is updated too so `GET /api/config` stays truthful.

**Frontend** — the Connection card becomes editable: frontend + backend port
inputs, a Check button (probes availability without saving) and a Save button.
On save, a persistent notice states the new URL and that a restart via
`launch.bat` is required — ports bind at process start and the launcher does
not supervise/respawn, so no self-restart is offered.

## Rejected

- **Backend self-restart endpoint** — killing the API mid-request with no
  supervisor means the restart can simply strand the user; launch.bat is the
  supported path.
- **config.json as the port source of truth** — `.env` → env var is what the
  process actually binds; config.json only mirrors it for `GET /api/config`.
- **Editing HOST** — out of scope; ALLOW_LAN already gates the bind address.

## Implementation Results

Shipped as designed:

- `routes/system.py` — `GET /api/system/ports` reports configured ports +
  live listening state; `PUT /api/system/ports` validates (numeric,
  1024–65535, distinct), probes `connect_ex` for collisions with an
  exemption for the ports VDock itself occupies, and supports
  `check_only`. `_write_env_keys` rewrites only the managed keys
  (`PORT`/`CORS_ORIGINS`, `VITE_PORT`/`VITE_BACKEND_PORT`) — comments and
  unrelated keys survive, verified by test. `CORS_ORIGINS` keeps user-added
  non-loopback origins and refreshes the managed pair. `config.json`'s
  `port` mirrors the new backend port.
- `SettingsView.vue` Connection card — Host/Auth stay read-only; two port
  inputs with per-field error text, **Check availability** and **Save
  Ports** buttons, and a restart-required notice naming `launch.bat`.
- `test_system_ports.py` — 8 tests covering GET, every validation branch,
  the own-port exemption, check-only no-write, and comment/origin
  preservation.

Verified: **727 backend tests pass**; `vue-tsc` clean.
