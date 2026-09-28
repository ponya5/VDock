# DL-112 — Production launch: serve dist via the backend, skip the Vite dev server

## Background

Launching from the desktop icon (`launch.bat` → `VDock-Launcher.py`) always
spun up three things: the Flask backend, a **Vite dev server**
(`npm run dev`, a cmd/npm/vite process tree), and Electron. Two issues the
user hit:

1. **Two consoles** — the launcher's own window plus the `cmd /c npm run
   dev` console tree; on some systems the npm.cmd chain surfaces a window.
2. **"development server" wording** — Vite's banner ("dev server running
   at http://localhost:4444") and `dev server` prints in the launcher read
   like a dev setup, while the install is used as a production dashboard.

The backend already serves `frontend/dist` (`app.py` → `frontend_index`),
which is exactly what the touch panel and LAN phones load — the Vite dev
server only exists for hot-reload while editing frontend sources.

Electron's mode is decided by `isDev = fs.existsSync(../../backend)` —
always true inside a repo checkout — so it loads the Vite URL. There was
no way to launch the built bundle without hand-starting the backend.

## Design

### Launcher (`scripts/VDock-Launcher.py`)

- `production_frontend_available()`: `frontend/dist/index.html` exists
  and `VDOCK_DEV_SERVER` is not set. `VDOCK_DEV_SERVER=1` is the opt-out
  for actual frontend development (documented in `launch.bat`).
- Production path: no vite spawn, no "dev server" prints; the banner
  prints the backend URL as the app address.
- `launch_electron()` receives `VDOCK_PRODUCTION=1` in `electron_env`.
- `open_browser()` targets the backend URL when in production.
- Waiting: the backend `/api/config` wait already covers readiness — the
  60s frontend wait is dev-only.
- Dev path unchanged when dist is absent (clean checkout still works).

### Electron (`frontend/electron/main.js`)

- `isDev = existsSync(backend) && process.env.VDOCK_PRODUCTION !== '1'`.
  Under the flag the URL switches to `http://localhost:<backendPort>`
  (Flask serves dist). `VDOCK_SKIP_BACKEND_SPAWN=1` — already set by the
  launcher — keeps the bundled-exe path dormant, so the only behavioral
  change is which URL loads.
- Packaged installs are unaffected (no `backend/` dir → `isDev` stays
  false; the env flag is a repo-launcher concern).

## Implementation Results

- `VDock-Launcher.py`: `production_frontend_available()` gates the vite
  spawn on `dist/index.html` existing and `VDOCK_DEV_SERVER` unset.
  Production launches print `App: http://localhost:<backend> (built
  bundle)` — nothing says "dev server" — and the browser fallback opens
  the backend URL. `launch_electron` exports `VDOCK_PRODUCTION=1`.
- `electron/main.js`: `isDev` now ANDs the repo-layout check with
  `VDOCK_PRODUCTION !== '1'`; `VDOCK_SKIP_BACKEND_SPAWN` (already set)
  keeps the bundled-backend path dormant, so the only flip is loading
  `http://localhost:<backendPort>` — the same page the panel/phones get.
- `launch.bat` documents the `VDOCK_DEV_SERVER=1` opt-in for HMR
  development.
- `docs/setup/DESKTOP_LAUNCHER.md` launch-process section updated (was
  still describing "frontend server on port 3000" + browser-only).
- Verified: `python -m ast` + `node --check` clean;
  `production_frontend_available()` returns True with dist present and
  False under `VDOCK_DEV_SERVER=1`. Live launch not executed here — it
  would fullscreen Electron over the physical panel; verification
  lands on next real launch.
- Note: a `npm run dev` orphan left from earlier sessions keeps port
  4444 until reboot — the launcher no longer touches it.
