# DL-030 — Production Security Hardening & Best-Practice Audit

## Background
Repo-wide audit requested: make VDock production-ready on security and
coding best practices, with self-testing of anything changed.

## Problem — audit findings

### Critical
1. **Arbitrary file read (CONFIRMED LIVE)** — `app.py` catch-all
   `/<path:path>` builds `frontend/dist/<path>` and calls `send_file` with
   no containment check. `GET /..%2F..%2Fbackend%2F.env` → HTTP 200 served
   `backend/.env` (SECRET_KEY, AUTH_PASSWORD, API keys). Verified against
   the running production backend.
2. **Arbitrary file write** — `routes/assets.py` `/api/assets/upload`
   writes `FRONTEND_ASSETS_DIR / asset_type / category / file.filename`
   with `asset_type`, `category`, and `file.filename` all unsanitized
   user input (`../../` + raw filename) → write anywhere on disk.

### High — auth coverage gaps
`require_auth` is a no-op when `REQUIRE_AUTH=False` (the default), so
most blueprints never added the decorator. When a user *does* enable
auth, these endpoints still bypass it — false sense of protection:
- `config.py` `PUT /api/config` flips `require_auth`, `use_ssl`,
  `allow_lan`, `enable_plugins` — unauthenticated remote security-flag
  changes.
- `upload.py` `/api/upload` — unauthenticated file upload.
- `system.py` — autostart toggle + `.env` port rewrites.
- `system_metrics.py` (22 routes), `assets.py` (9), `templates.py` (6),
  `user_settings.py` (2), `weather.py` (1), `app_profiles.py` (1).

### Medium
3. No `MAX_CONTENT_LENGTH` — upload size is checked after Werkzeug has
   already buffered the whole body.
4. Password compare uses `==` — timing-attackable (`hmac.compare_digest`).
5. `serve_uploaded_file` relies on a `'..' in filename` substring check —
   replace with resolve+`is_relative_to`.
6. npm audit: axios (<1.17, 4 advisories), ws (via engine.io-client),
   follow-redirects — `npm audit fix`.
7. `requirements.txt`: requests 2.31.0 (CVE-2024-35195), Werkzeug 3.0.1
   (CVE-2024-49766/49767), Flask 3.0.0 → patch bumps.

### Already OK (verified, no change)
- `profiles.py` `PROFILES_DIR / f"{id}.json"` — Flask `<profile_id>`
  cannot contain `/`; traversal unreachable.
- `secrets.py` — env-only, never serialized. `.env*` gitignored.
- SocketIO `connect` verifies JWT when REQUIRE_AUTH on; `ui_command` is
  an allowlist. Security headers + CORS origins + rate limiter present.
- RSS `is_allowed_feed_url` (http/https) + byte cap; upload ext
  whitelist on `/api/upload`; `v-html` only on static SVG constants.
- `SECRET_KEY` random per-boot when unset; DEBUG off by default; HOST
  loopback default; `ALLOW_COMMAND_EXECUTION` opt-in.

## Design / Fixes
- `app.py` catch-all: `resolve()` + `is_relative_to(dist_root)` → 404;
  add `MAX_CONTENT_LENGTH = 16MB`.
- `assets.py upload_asset`: whitelist `asset_type`, `secure_filename`
  filename + category, resolve+containment on the final path.
- Blanket `@require_auth` on every route lacking it (no-op by default;
  protects the moment auth is enabled). `require_auth` on `/api/upload`
  + `/api/uploads/<path>`.
- `auth_manager.authenticate`: `hmac.compare_digest`.
- `requirements.txt`: requests→2.32.4, Werkzeug→3.0.6, Flask→3.0.3.
- `npm audit fix` for axios/follow-redirects/ws.

## Verification
- Traversal returns 404/403 on the fixed code (live test).
- Upload with `../../` names rejected; normal upload still works.
- 739 backend pytest + 199 frontend tests green; typecheck clean.
- `npm audit` post-fix shows the advisories resolved.

## Implementation Plan
- [x] Phase 1: app.py catch-all containment + MAX_CONTENT_LENGTH
- [x] Phase 2: assets.py upload sanitization + blanket require_auth
- [x] Phase 3: auth compare_digest + serve_uploaded_file containment
- [x] Phase 4: dependency bumps (npm audit fix + requirements.txt), venv
  install, test
- [x] Phase 5: full verify + commit

## Implementation Results

### What changed

**app.py** — catch-all now resolves the candidate path and rejects anything
outside `frontend/dist` (`is_relative_to`), plus `MAX_CONTENT_LENGTH=16MB`
so Werkzeug refuses oversized bodies before route-level checks run.

**routes/assets.py** — `/api/assets/upload`: `asset_type` whitelisted
against the extensions map, `category` + filename passed through
`secure_filename`, final path resolved + containment-checked against
`FRONTEND_ASSETS_DIR`. Sanitized values flow into metadata (no more raw
`file.filename`). All 9 routes gained `@require_auth`.

**Blanket `@require_auth`** — script-applied to every route missing it:
config (2), system (4), system_metrics (11), templates (6), upload (2),
user_settings (2), weather (1), app_profiles (1). No-op while
`REQUIRE_AUTH=False`; closes the false-sense-of-protection gap when on.

**routes/config.py** — `PUT /api/config` now requires strict booleans for
the four security toggles (`"false"` would have persisted a truthy string)
and `get_json(silent=True)` instead of raising on non-JSON.

**routes/upload.py** — `serve_uploaded_file` substring check replaced with
resolve+`is_relative_to` containment.

**auth/auth_manager.py** — password check via `hmac.compare_digest`,
strict `Bearer <token>` header parsing (2-part, correct scheme, non-empty),
`datetime.now(timezone.utc)` replacing deprecated `utcnow()`.

**Dependencies** — `requirements.txt`: Flask 3.0.3, Flask-CORS 4.0.2,
Flask-SocketIO 5.3.7, Flask-Limiter 3.8.0, python-socketio 5.11.4,
requests 2.32.3, Werkzeug 3.0.6, PyJWT 2.9.0, bcrypt 4.2.1, psutil 6.0.0,
pynput 1.7.7, pyperclip 1.9.0, python-dotenv 1.0.1, pytz 2024.2.
Frontend lockfile regenerated (npm arborist bug — fresh install crashed
on `edgesOut`; fixed by npm 10.9.2→10.9.9 + `--legacy-peer-deps`).
vite 5→6.4.3, plugin-vue 5.2.4, vite-plugin-pwa 0.21.2.
**npm audit: 28 vulnerabilities → 0.**

### Verified

- **Live exploit re-test**: `GET /..%2F..%2Fbackend%2F.env` → **404**
  (was 200 with env contents). config.py traversal → 404, uploads
  traversal → 400, SPA fallback + index → 200.
- **16 new pytest cases** in `tests/test_security_hardening.py`:
  encoded/backslash traversal, SPA fallback, uploads containment,
  oversize rejection, asset-upload sanitization (category/filename/
  type), auth on config when enabled, token acceptance, malformed
  Bearer headers, strict-bool config validation. Upload tests
  monkeypatch `FRONTEND_ASSETS_DIR` to `tmp_path` — no repo pollution.
- **755/755 backend**, **199/199 frontend**, `vue-tsc` clean,
  `vite build` clean (6.4.3).

### Deviations

- npm `audit fix`/`install` crashed with arborist `edgesOut` on npm
  10.9.2 — root cause was npm itself, not the lockfile; upgraded npm
  to 10.9.9 and regenerated the lockfile under `--legacy-peer-deps`.
- `is_relative_to` needs Python 3.9+ — repo targets modern Python, and
  venv confirmed working.
- esbuild/vite moderate advisory (dev-server-only, GHSA-67mh-4wv8-2f99)
  resolved via vite 6.4.3 — still a major bump but plugin-vue/pwa peers
  accept it; build + all 199 tests verified on the new major.
- `backend/frontend/` test artifacts cleaned; upload tests now isolate
  to `tmp_path`.

### Remaining known limits (documented, not fixed)

- CSP keeps `'unsafe-inline'`/`'unsafe-eval'` — required by Vue/Electron;
  tightening breaks the app.
- `shell=True` in cross_platform_action is gated behind
  `ALLOW_COMMAND_EXECUTION` (off by default) — core feature, documented
  trust boundary.
- Plugin loading (`ENABLE_PLUGINS=True` default) executes local Python —
  trusted-local boundary; plugins dir isn't network-writable.
- RSS fetch validates scheme + caps bytes; DNS-rebinding/private-IP
  checks not added (local app, feeds are user-configured).
