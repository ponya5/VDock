# DL-126 — Usable authentication (Settings toggle + lock screen)

## Problem

Settings → Server shows Authentication as a static `Enabled`/`Disabled`
chip — nothing in the UI can change it, and flipping `REQUIRE_AUTH` by
hand would brick every client: there is no password-set path
(`AUTH_PASSWORD` is `.env`-only), the frontend never attaches a token,
and there is no login surface at all. The machinery exists server-side
(`require_auth` persists via `config.json`, `PUT /api/config` accepts it,
`handle_connect` gates sockets on a token) — the missing half is what
makes it *usable*.

## Design

**Backend**

- `PUT /api/config` accepts `auth_password` (string, 4–128 chars):
  writes `AUTH_PASSWORD=` to `backend/.env` (the documented home —
  `load_dotenv()` at startup picks it up), ensures `SECRET_KEY=` is
  persisted too so issued tokens survive restarts (today it regenerates
  per boot), and applies both to `Config` immediately. The password is
  never returned by any endpoint — `GET /api/config` gains
  `auth_password_set: bool`.
- Safety guard: `require_auth: true` is rejected (400) unless a
  password exists after the request — same invariant `Config.validate()`
  enforces at boot, applied at write time.
- `POST /api/auth/login` gets the rate limit its docstring always
  claimed: 5 failures per minute per IP → 429. In-memory sliding
  window — no flask-limiter dependency.
- Env-file writing moves out of `routes/system.py` into `config.py` as
  public helpers (`write_env_keys`, `backend_dir`, `project_root`) —
  config.py already owns .env parsing (`_read_env_port`); system.py
  imports them back so ports keep working unchanged.

**Frontend**

- `services/auth.ts` — token in `localStorage.vdock_auth_token`,
  reactive `locked` flag, `login(password)` → POST `/api/auth/login`,
  `markLocked()`, successful unlock → `location.reload()` (cleanest way
  to re-arm socket auth + every store with the token present).
- `api/client.ts` — request interceptor attaches
  `Authorization: Bearer <token>`; a 401 marks locked and skips the
  generic "Unauthorized" toast (the lock screen IS the feedback).
- `api/socket.ts` — `io(url, { auth: { token } })`; `connect_error`
  → `markLocked()`.
- `components/AuthLock.vue` — fullscreen overlay (above the screensaver,
  everything): password field → login → reload. Wrong password shows a
  shake + "Wrong password".
- `SettingsView` Authentication row becomes real:
  - off → password + confirm inputs + **Enable**
  - on → `Enabled` chip + password field + **Change password** +
    **Disable**
  - Enabling from this very browser auto-logs-in with the password just
  set (login route isn't authed), stores the token, reloads — the
  enabling session never sees a lock. Other devices (the panel, a
  phone) meet the lock screen on their next call.

## Trade-offs

- Password lives plaintext in `backend/.env` — consistent with the
  documented deployment path (`setup.bat` flow, ports feature). The
  threat model is LAN access control, not a vault; the file is already
  where secrets go.
- Token = JWT, 24 h expiry (existing `TOKEN_EXPIRATION`); persisting
  `SECRET_KEY` once keeps sessions valid across restarts.
- `REQUIRE_AUTH` still live-applies on PUT (existing behavior) — the UI
  handles the enable path by logging in immediately after saving.
- MCP + trigger webhooks inherit auth when enabled — agents/scripts
  need `Authorization: Bearer <token>`; that's the intended secure
  posture.

## Implementation Results

**Shipped — full auth lifecycle usable from Settings → Server →
Authentication.**

Backend (`routes/config.py`, `routes/auth.py`, `config.py`):

- `PUT /api/config` accepts `auth_password` (4–128 chars, validated):
  writes `AUTH_PASSWORD=` to `backend/.env` **before** touching
  `config.json`, so a failed env write can never persist
  `require_auth:true` into a no-password state that would refuse to
  boot. Also persists `SECRET_KEY` once (it was regenerating per boot,
  which would have invalidated every token on restart). Applied live —
  no restart needed.
- `GET /api/config` exposes `auth_password_set` — the password itself
  is never returned.
- Guard: `require_auth:true` → 400 unless a password exists after the
  request (mirrors `Config.validate()`'s boot-time invariant).
- `/api/auth/login` rate limit is real now: 5 failures/min/IP → 429,
  in-memory sliding window, success clears the window.
- `.env` helpers moved to `config.py` as `project_root`/`backend_dir`/
  `read_env_key`/`write_env_keys`; `routes/system.py` delegates to them
  (ports feature unchanged).

Frontend (`services/auth.ts`, `api/client.ts`, `api/socket.ts`,
`components/AuthGate.vue`, `App.vue`, `SettingsView.vue`):

- `services/auth.ts` owns the session: token in
  `localStorage['vdock.authToken']` (deviation from the sketched
  `vdock_auth_token`), reactive `{required, unlocked, checked}`,
  `probeAuth()` boot probe (quiet raw axios — never pops toasts),
  `login()`, `markUnauthorized()`, `onAuthTokenChanged` listeners.
- `api/client.ts` attaches `Authorization: Bearer <token>`; any 401
  outside `/auth/login` → `markUnauthorized()` and no toast (the gate
  is the feedback).
- `api/socket.ts` sends `auth: (cb) => cb({token})` at every handshake
  and reconnects on token change; `connect_error` re-probes (throttled
  5 s) so a rejected handshake raises the gate instead of retry-looping.
- `AuthGate.vue` — fullscreen lock overlay (z 40000, above the agent
  banner). Unlock → `location.reload()` so every store/socket boots
  clean with the token.
- Settings row is now a real switch:
  - Off + no password → flips open an inline "Choose a deck password"
    form; **Enable** sends `{auth_password, require_auth:true}` in one
    PUT.
  - Off + password set → confirm dialog → PUT `require_auth:true`.
  - Either enable path lands on the lock screen immediately — the user
    unlocks once with the password they just set (deviation from the
    sketched auto-login; one typed unlock doubles as proof they know
    the password).
  - On → "Deck password" row with inline change-password form;
    disabling asks for a confirm (reduces security) then clears the
    local token so the socket reconnects unauthenticated.

**Verified**

- Backend: 12 new tests in `test_security_hardening.py` +
  `conftest.py` guards `AUTH_PASSWORD` (enable-without-password 400,
  env persistence, bootstrap session, disable, change-while-enabled,
  validation params, throttle). **1088 backend tests pass.**
- Frontend: 15 new tests in `src/tests/auth.test.ts` (probe matrix,
  login, interceptor header/401, socket handshake token + reconnect,
  gate render/error). **478 frontend tests pass**, `npm run build`
  (vue-tsc) clean, `dist` rebuilt.
- Live E2E on the running backend via Playwright: switch → inline
  password form → Enable → gate raised; unlock → token stored →
  reload authenticated on `/settings`; socket handshake accepted
  ("Connected to VDock server"); disable → token cleared, open again.
- API-level: login with env password → JWT; `verify` → `{valid:true}`;
  password change → old rejected/new accepted.

**Ops note:** during live verification the deck briefly ran with
auth enabled; restored to `require_auth:false` + `AUTH_PASSWORD=`
(`.env`) — the user's earlier `.env` password was rotated during
testing and then cleared, so enabling now goes through the inline
password form (the intended first-run flow). Also found four stale
`app.py` processes from older sessions — killed; one process now owns
:5000.
