# DL-120 — Triggers / schedules engine + settings panel

Collab work item **W5** (`design-log/collab/ORCHESTRATION.md`, feature
research §4.1). Contracts consumed: `contracts/socket-events.md`
(`trigger_fired`, `navigate_scene`, `panel_notification`),
`contracts/rest-api.md` (`/api/triggers*`).

## Intent

The deck can act on the machine, but only when a finger touches a button.
Competing panels (Stream Deck + plugins, Macro Deck) ship schedules and
"when X happens" rules — the most asked-for ones being "at 07:30 switch to
the morning scene", "when Spotify is focused show the media scene", and
"when Claude Code blocks on a permission dialog ping the panel". All three
are the same shape: **event → action**. This builds that engine plus the
settings UI to manage it.

## Frictions

- Nothing persistent exists — there is no place a user can even express
  "every weekday at 08:00".
- The machinery to *run* an action already exists (`ActionExecutor`,
  socket broadcast) but nothing ties it to a clock, the foreground app, or
  agent state.
- Webhook callers (scripts, agent hooks, Task Scheduler) need an
  unauthenticated localhost surface — same trust model as
  `/api/agent-events`.
- A misfiring loop must never wedge the backend: one bad trigger fires
  `ok:false` and the engine keeps ticking.

## Design

### Storage — `services/triggers.py`

`Config.DATA_DIR / 'triggers.json'`, resolved lazily per access so tests
can point `Config.DATA_DIR` at a tmp dir. Writes are atomic (write
`<file>.tmp` then `os.replace`) and the whole store is guarded by one
`threading.Lock`. Corrupt/absent file → empty store, never a crash.

Trigger shape:

```json
{
  "id": "trg_<10 hex>",
  "label": "Morning scene",
  "enabled": true,
  "event":  { "type": "time", "at": "07:30", "days": [0,1,2,3,4] },
  "action": { "type": "switch_scene", "scene": "Morning" }
}
```

Events: `time {at:'HH:MM', days?:[0-6]}` (0 = Monday, Python
`weekday()`), `app_foreground {exe}`, `agent_state {source, state}`,
`webhook {key}` (`[A-Za-z0-9_-]{1,64}`, auto-generated when omitted).
Actions: `execute_action {action:{type,config}}` → injected executor,
`switch_scene {scene}` → `navigate_scene`, `show_notification
{title, message}` → `panel_notification` (source `'trigger'`).

Validation lives in the service (`_validate_event` / `_validate_action`)
raising `ValueError`; routes map that to 400. `update_trigger` is a
partial update — `event`/`action` are whole-object replacements when
present.

### Engine

Same seams as `services/volume_monitor.py` / `job_runner`:
`set_emitter`, `set_spawner`, `set_executor`, `start`, `stop`. One ~1 s
loop (spawned via `socketio.start_background_task` in app.py — threads
SocketIO didn't spawn can't emit in threading mode). Each tick:

- **time**: fire when `at` == now HH:MM and `days` empty-or-contains
  `now.weekday()`, at most once per minute — `_runtime[id].minute` marks
  the fired `YYYY-MM-DD HH:MM` *before* dispatch so a throwing action
  can't re-enter the same minute.
- **app_foreground**: one shared `utils.app_monitor.get_current_active_app()`
  read per tick (it is a one-shot getter — no monitor thread required);
  per trigger remember the previously observed exe and fire only on
  `prev != target → cur == target`. First observation is a baseline, not
  a fire — otherwise every backend restart while the app is focused would
  re-run the action.
- **agent_state**: one shared `integrations.agent_state.snapshot()` per
  tick; per trigger remember the previously observed state and fire only
  on `prev != target → cur == target` (same baseline rule; absent source
  counts as "not in state" and re-arms).
- **webhook**: never polled; `fire_webhook_key(key)` is called by the
  route and fires every *enabled* trigger bound to that key.

Every fire — success or failure — emits
`trigger_fired {id, label, ok, detail, ts}`. `_fire` wraps the whole
dispatch in try/except so a throwing executor degrades to `ok:false`,
never kills the loop. The outer tick is itself try-wrapped.

`fire_trigger(id)` is the test-fire seam used by
`POST /api/triggers/<id>/test`: fires regardless of `enabled` and returns
`(ok, detail)` for the response.

### Routes — `routes/triggers.py` (`triggers_bp`)

Per contract: `GET/POST /api/triggers`, `PUT/DELETE
/api/triggers/<id>`, `POST /api/triggers/<id>/test` under `@require_auth`;
`POST /api/triggers/fire/<key>` is localhost-only with no auth (same
`_localhost_only` check as `routes/agent_events.py` — scripts can't carry
UI tokens). A `set_emitter` delegating to the service gives app.py a
single wiring point.

### Frontend

- `services/triggersApi.ts` — thin axios wrapper over `apiClient`
  (list/create/update/remove/test) with the trigger interfaces.
- `components/settings/TriggersPanel.vue` — self-contained `<section
  class="panel">` in the SettingsView visual idiom (same CSS variables,
  declared locally so it renders outside `.settings-app` too): trigger
  rows (label, event/action summary, enable switch, test-fire, edit,
  delete) and an inline add/edit form with contextual fields per
  event/action type. Webhook keys are generated client-side for new
  triggers and shown with a copyable `POST` URL. Subscribes to
  `trigger_fired` to surface last-fire status inline.

## Core Loop

Create trigger → persisted to `triggers.json` → engine tick observes the
event edge → action runs → `trigger_fired` broadcasts → the panel row
shows the outcome. Scripts fire webhooks over localhost without tokens.

## Design Proof

- Unit tests drive `_tick` with an injectable `now`, fake app getter and
  fake snapshot — covering minute-edge (fires once per minute), on-entry
  only, re-arming, webhook dispatch, executor dispatch, `ok:false` on a
  throwing action, and store roundtrip.
- Route tests cover auth on CRUD and localhost-only on `fire/<key>`.
- Corrupt `triggers.json` → engine still starts with an empty store.

## Implementation Results

Implemented per the design above; all deliverables in place and green.

**Built**

- `backend/services/triggers.py` — the full engine: lazy JSON store at
  `Config.DATA_DIR/'triggers.json'` (atomic tmp+`os.replace` writes, one
  `threading.Lock`, corrupt file → empty store), CRUD
  (`list_triggers`/`get_trigger`/`add_trigger`/`update_trigger`/
  `remove_trigger`) returning deep copies, `trg_<10hex>` ids, full
  event/action validation raising `ValueError` for the route to map to 400.
  Webhook keys auto-generate (`whk_<16hex>`) when omitted. Engine seams:
  `set_emitter`/`set_spawner`/`set_executor`/`start`/`stop`; the ~1 s loop
  binds each generation to its own `threading.Event` so a stale loop can't
  be resurrected by a later `start()`. `time` fires once per matching
  minute (`_runtime[id].minute` marked before dispatch); `app_foreground`
  and `agent_state` fire only on the observed transition into the target,
  with the first observation treated as a baseline (never a fire) —
  documented in the module docstring. `_fire` wraps dispatch fully:
  exceptions become `trigger_fired {ok:false, detail}` and the loop keeps
  going. `fire_trigger(id)` (test seam, ignores `enabled`) and
  `fire_webhook_key(key)` (enabled matches only, returns count).
- `backend/routes/triggers.py` — `triggers_bp` with the exact contract
  routes; `@require_auth` on everything except `POST
  /api/triggers/fire/<key>`, which uses the same `_localhost_only` check as
  `routes/agent_events.py`. `set_emitter` delegates to the service so
  app.py has one wiring point.
- `frontend/src/services/triggersApi.ts` — typed axios wrapper
  (list/create/update/remove/test) over `apiClient`.
- `frontend/src/components/settings/TriggersPanel.vue` — self-contained
  panel: trigger rows (label, `event → action` summary, enable switch,
  Test fire, edit, two-tap delete), inline add/edit form with per-type
  contextual fields (time + 7 day chips; exe; source/state selects;
  webhook key with generated `whk_` key, copyable `POST` URL and
  regenerate button; execute_action type select + JSON config textarea
  with client-side JSON validation; scene; title+message). Subscribes to
  `trigger_fired` for a per-row last-fired/failed line. Styles duplicate
  the SettingsView variable block locally so the panel renders correctly
  wherever it is mounted.
- `backend/tests/test_triggers.py` — 39 tests covering everything the
  spec lists plus edge cases (baseline suppression, absent-source re-arm,
  per-minute edge, webhook multi-binding + disabled skip, loop surviving a
  throwing `_tick`).

**Verified**

- `cd backend && ./venv/Scripts/python.exe -m pytest tests/test_triggers.py -q`
  → 39 passed.
- Full backend suite: 1057 passed, no regressions.
- `cd frontend && npx vue-tsc --noEmit` → clean.

**Deviations / decisions made**

- Polled events (`app_foreground`, `agent_state`) treat the first
  observation as a baseline rather than a fire, so a backend restart while
  the condition already holds does not re-run actions. `update_trigger`
  drops the trigger's edge state, making an edit re-baseline.
- `POST /api/triggers/fire/<key>` returns `{success, fired: 0}` for an
  unmatched key rather than 404 — the contract shape is fixed.
- `_run_action` reports `ok:false`/`"No socket emitter wired"` when an
  emit-action fires with no emitter injected, so a test-fire never claims
  a delivery that did not happen.
- CRUD returns deep copies; the store never aliases returned dicts.

**Integration notes for the orchestrator** (also in
`collab/messages/triggers.md`): app.py needs `triggers_bp` registered +
`limiter.exempt`, `services.triggers.set_emitter/set_spawner/set_executor`
wired like `volume_monitor`, and `triggers.start()` under `__main__`;
SettingsView mounts `components/settings/TriggersPanel.vue`.

### Follow-up — Settings configurability pass

Added a persisted **master switch**: `enabled` is stored top-level in
`triggers.json` (default true), read/written through
`is_enabled()`/`set_enabled()`. While off, `_tick` returns early and
`fire_webhook_key` returns 0; manual `fire_trigger` test-fires still work
(honest smoke test). `set_enabled` clears `_runtime` so edges re-baseline —
a condition that came true while paused does not fire on resume.

Routes: `GET /api/triggers` now also returns `enabled`; new
`PUT /api/triggers/enabled {enabled}` under `@require_auth`.
`triggersApi.ts` grew `fetchTriggersState()`/`setTriggersEnabled()`;
`TriggersPanel.vue` shows a head-level master switch + "Paused" chip and
dims rows while paused. Backend tests cover pause, webhook suppression,
manual-fire, persistence roundtrip, resume re-baseline, and the route.
