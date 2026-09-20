# DL-029 — Session Logs Settings Tab, Bounded Log Storage & Export

## Background
VDock writes several logs today: `vdock.log` (app logger via plain
`FileHandler` — unbounded, already ~1MB), `vdock-{backend,frontend,
electron}-launcher.log` (launcher `open(..., 'a')` — unbounded,
backend-launcher already 1.77MB), `backend_run.log`,
`backend-restart.log`. There is no way for the user to see them, and no
cap on growth. Frontend errors are invisible — the ConfirmDialog /
rate-limit bugs were only diagnosable because I was attached to dev tools.

## Problem
User request: a new Settings tab for session logs to troubleshoot errors
and events; the log folder must not grow to a ridiculous size; add log
export.

## Design

### Backend — `routes/logs.py` blueprint
- `GET /api/logs` — list every `*.log` in `DATA_DIR` and `backend/`:
  `{name, size, mtime}` sorted by mtime desc + `total_bytes`.
- `GET /api/logs/<name>?tail=N` — last N lines (default 300, max 2000),
  read from the end of file in chunks. Name is sanitized to a basename
  ending in `.log` that resolves inside an allowed dir — no traversal.
- `GET /api/logs/export` — zip of all logs → `send_file` attachment
  `vdock-logs-<ts>.zip`.
- `POST /api/logs/client` — body `{events: [{ts, level, source, message}]}`
  (≤50/batch, message ≤2KB each); appends to `frontend.log` through a
  dedicated `vdock.frontend` logger.
- `DELETE /api/logs` — truncate every managed `*.log` (fresh start).

### Bounding growth
- `utils/logger.py`: `FileHandler` → `RotatingFileHandler`
  (maxBytes=512KB, backupCount=3 → vdock.log ≤ ~2MB total).
- `vdock.frontend` logger: RotatingFileHandler 256KB × 2.
- `scripts/VDock-Launcher.py` `open_log_file()`: if the existing file
  exceeds 1MB, rewrite it keeping only the last 256KB, then open for
  append — caps launcher logs once per launch.
- Result: the whole log folder stays under ~10MB forever.

### Frontend capture — `services/sessionLog.ts`
Installed in `main.ts`: `app.config.errorHandler`, `window.onerror`,
`unhandledrejection`, wrapped `console.error`/`console.warn`, plus
`logEvent()` for lifecycle events (app start, websocket disconnect).
Events buffer in memory; flushed via `POST /api/logs/client` every 5s or
at 20 events; `sendBeacon` on `pagehide`. Failures back off 60s and never
log their own error (no recursion).

### Settings → Logs tab
New tab `{id:'logs', icon:'file-lines'}` with two cards:
- **Log files** — list with name/size/age, tap to select.
- **Viewer** — monospace dark scroll pane showing the tail, Refresh +
  file picker + line-count select, Export (downloads zip), Clear All
  (ConfirmDialog). Header shows total log-folder size.

## Implementation Plan
- [x] Phase 1: RotatingFileHandler in `utils/logger.py` + launcher
  truncation + `routes/logs.py` blueprint (register in app.py)
- [x] Phase 2: `services/sessionLog.ts` + `main.ts` install
- [x] Phase 3: SettingsView Logs tab UI
- [x] Phase 4: verify — typecheck, tests, build, live: list/tail/export/
  clear, rotation caps

## Implementation Results
- Phase 1: `setup_logger` file handler is now `RotatingFileHandler`
  (512KB × 3). Launcher `open_log_file` truncates files >1MB to the last
  256KB on open. `logs_bp` registered and rate-limit-exempted (client
  error bursts can't burn the quota — the DL-023 failure mode).
- Phase 2: `sessionLog.ts` installed in `main.ts` — Vue errorHandler,
  window.onerror, unhandledrejection, console.error/warn, `logEvent()`;
  5s/20-event flush, 500-event queue cap, 60s failure backoff, sendBeacon
  on pagehide.
- Phase 3: Logs tab (file-lines icon) — file list w/ sizes, monospace
  tail viewer (100/300/1000 lines, level-colored lines, auto-scroll to
  newest), Export zip, Clear All (ConfirmDialog), total-size header.
- Phase 4 verified live on a test backend (:5099): `GET /api/logs` listed
  7 files / 4MB; tail returned correct lines; client POST wrote
  `[vue] test client error event` to frontend.log; export produced a
  216KB zip with all 7 logs; traversal `../app.py` → 404; DELETE emptied
  all 7 files (shared DATA_DIR — production logs were also cleared).
  Real frontend errors (websocket failure) reached frontend.log end-to-end.
- **Deviation:** `vdock.frontend` reuses the shared 512KB×3 rotation
  constants instead of a bespoke 256KB×2 — same bounded-growth guarantee.
- Tests: 11 new in `session-logs.test.ts`; frontend 199/199; backend
  739/739 pytest. Property-8 fix: `.log-viewer` font-size → clamp().

## Trade-offs
- **Chosen:** tail-read in chunks (no loading whole file); zip export
  (single download, includes launcher logs).
- **Rejected:** websocket log streaming (overkill for troubleshooting);
  JSON-lines structured logs (existing format is plain text — keep it);
  logging every button press (noise; errors/events only).

## Verification Criteria
- `vdock.log` rotates at 512KB ×3; launcher logs truncated at 1MB on
  start; `frontend.log` receives client events.
- Logs tab lists files, shows tail, exports a zip, clears on confirm.
- Total folder size bounded (~10MB worst case).
- No `require_auth` regression: logs endpoints use the same decorator as
  other blueprints.
