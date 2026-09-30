# Contract — REST endpoints

FIXED route shapes. The orchestrator registers blueprints + rate-limit
exemptions in `backend/app.py`; workers only create the blueprint modules.
Follow existing conventions: `@require_auth` for client-facing reads/writes,
localhost-only for machine-to-machine posts (see `routes/agent_events.py`
`_localhost_only`).

## W1 — `routes/now_playing.py` → blueprint `now_playing_bp`

- `GET /api/now-playing` → `{success: true, available: bool,
  track: <now_playing payload>|null}` — `available:false` when SMTC support is
  missing (no winsdk / unsupported platform); `track:null` when supported but
  nothing plays. `@require_auth`.
- `GET /api/now-playing/art` → image bytes (`image/jpeg` or `image/png`),
  404 when no art. `@require_auth`. Art cached under `Config.DATA_DIR`.

## W5 — `routes/triggers.py` → blueprint `triggers_bp`

- `GET    /api/triggers` → `{success, triggers:[…]}` — auth
- `POST   /api/triggers` body = trigger object → `{success, trigger}` — auth
- `PUT    /api/triggers/<id>` partial update → `{success, trigger}` — auth
- `DELETE /api/triggers/<id>` → `{success}` — auth
- `POST   /api/triggers/<id>/test` fire now → `{success, ok, detail}` — auth
- `POST   /api/triggers/fire/<key>` → `{success, fired: n}` — **localhost
  only**, no auth (webhook surface for scripts).

## W6 — `routes/mcp.py` → blueprint `mcp_bp`

- `POST /api/mcp` — JSON-RPC 2.0, single endpoint. Localhost-only; when
  `Config.REQUIRE_AUTH` is true also accept `Authorization: Bearer <jwt>`.
  `GET` → 405 with `{error}` JSON (some clients probe it for SSE — answer
  cleanly rather than 404).

## Injection seams (orchestrator wires in app.py)

Each module exposes plain setters, mirroring `job_runner`/`volume_monitor`:

- `services.now_playing`: `set_emitter(fn)`, `set_spawner(fn)`, `start()`
- `services.audio_spectrum`: `set_emitter(fn)`, `set_spawner(fn)`,
  `set_enabled(bool)`, `start()`
- `services.triggers`: `set_emitter(fn)`, `set_spawner(fn)`,
  `set_executor(action_executor)`, `start()`, `stop()`
- `routes.mcp`: `set_emitter(fn)`, `set_executor(action_executor)`
- `routes.triggers`: `set_emitter(fn)` (optional; service emit covers most)

Emit signature everywhere: `fn(event_name: str, payload: dict) -> None`
(=`socketio.emit`).
