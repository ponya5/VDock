# Feature Research Implementation — Orchestration

Seven features from `FEATURE-RESEARCH.html` built in parallel by worker agents.
The orchestrator (the top-level Devin session) owns this file, assigns work,
collects reports, and performs the final integration pass.

## How this works

1. Every worker has a **work item (W#)**, a pre-assigned design-log number, and a
   strict file-ownership set (`contracts/file-ownership.md`).
2. Cross-feature communication happens ONLY through the fixed contracts in
   `contracts/` — socket event names/payloads and REST routes are decided here,
   up front, so no worker waits on another's code.
3. Workers report by (a) updating their row in `STATUS.md` (their own row
   only), (b) leaving notes in `messages/<worker>.md` if they discover
   something another worker or the orchestrator must know, and (c) ending with
   a structured report to the orchestrator.
4. The orchestrator owns all shared files and wires everything together after
   all workers finish: `backend/app.py`, `backend/requirements.txt`,
   `frontend/src/utils/screensaverLayout.ts`,
   `frontend/src/components/ScreenSaver.vue`,
   `frontend/src/views/SettingsView.vue`, `frontend/src/stores/settings.ts`,
   `frontend/src/composables/useUiCommands.ts`, `design-log/README.md`.

## Rules every worker must follow

- **Read first**: this file, `contracts/file-ownership.md`, the contract files
  your spec references, and `AGENTS.md` at the repo root.
- **Design log before code**: create `design-log/DL-<NNN>-<slug>.md` (number
  pre-assigned below) with Background/Problem/Design/Implementation Plan
  BEFORE writing code. Append `## Implementation Results` when done. Do NOT
  touch `design-log/README.md` — the orchestrator updates the index.
- **Own only your files.** Never edit a file owned by another worker or the
  orchestrator, even for a "tiny fix" — write a note in
  `messages/<worker>.md` instead.
- **Update STATUS.md**: set your row to `working` when you start and `done` /
  `blocked` when you finish, with a one-line note. Edit ONLY your own row.
- **No `pip install`, no `npm install`.** Optional runtime deps (winsdk,
  soundcard, numpy) are installed by the orchestrator during integration.
  Code must import them lazily and degrade gracefully when absent.
- **No `npm run build`, no git commits.** The orchestrator builds once at the
  end.
- Match existing code conventions: docstrings explain *why*, comments are
  sparse and explain non-obvious decisions. Read neighboring files first.
- Optional deps pattern: `try: import x` at module level or inside the
  function that needs it; when missing, report an honest "unavailable" state
  rather than raising (see `actions/cross_platform_action.py` and
  `services/volume_monitor.py` for precedent).
- Tests: backend `cd backend && ./venv/Scripts/python.exe -m pytest tests/<file>.py -q`;
  frontend `cd frontend && npx vitest run src/tests/<file>.test.ts`.
  Write tests that do NOT require the optional deps or real OS APIs
  (inject fakes via the emitter/spawner seams, as existing tests do).
- The project root is `C:\Users\Daniel\CursorRepo\VDock2`. Platform: Windows
  with a bash shell; use forward-slash paths in commands.

## Work items

| W# | Feature (research doc ref) | DL | Worker slug |
|---|---|---|---|
| W1 | SMTC now-playing monitor + screensaver widget (§2a) | DL-116 | now-playing |
| W2 | Winamp-style spectrum screensaver (§2b) | DL-117 | spectrum |
| W3 | System stats screensaver widget (quick win) | DL-118 | system-stats |
| W4 | Notification-to-panel, multi-agent waiting (§1) | DL-119 | notification |
| W5 | Triggers / schedules engine + panel (§4.1) | DL-120 | triggers |
| W6 | MCP server — Streamable HTTP subset (§3) | DL-121 | mcp |
| W7 | Timer/stopwatch buttons + conditional button UI (§1, §4) | DL-122 | timer-rules |

## Feature specs

### W1 — Now Playing (SMTC) — DL-116

Windows SMTC (`GlobalSystemMediaTransportControlsSessionManager`) via the
`winsdk` package exposes track title/artist/album, album art, play state and
source app. Build a monitor mirroring `services/volume_monitor.py`:

- `backend/services/now_playing.py`: same `set_emitter`/`set_spawner`/`start`
  contract as `volume_monitor`. Poll ~1.5 s; emit socket event `now_playing`
  per `contracts/socket-events.md` only on change (first read always emits;
  also emit when nothing is playing if state changed). Must not raise when
  `winsdk` is missing or the platform is unsupported — the monitor then just
  idles (the REST endpoint reports `available: false` so the widget can show
  its honest unavailable state).
- `backend/routes/now_playing.py`: `GET /api/now-playing` →
  `{success, available, track|null}` and `GET /api/now-playing/art` → cached
  album-art image bytes (404 when none). Keep art in `Config.DATA_DIR /
  'now_playing_art.*'`; serve with `send_file`. Blueprint name
  `now_playing_bp`, url_prefix `/api`. `@require_auth` like other routes.
- `frontend/src/services/nowPlaying.ts`: reactive singleton like
  `services/agentState.ts` — subscribes `now_playing`, re-syncs via GET on
  connect, exports `useNowPlaying()` → `{ track, playing, available, artUrl }`.
  `artUrl` should be `/api/now-playing/art?ts=<track ts>` when art exists.
- `frontend/src/components/screensaver/NowPlayingWidget.vue`: widget per
  `contracts/widget-contract.md` — album art (fallback music icon), title,
  artist, source-app tag, play/pause glyph, progress bar when duration known.
  Honest "unavailable" state when `available === false` or no data.
- `backend/tests/test_now_playing.py`: monitor emit-on-change logic with a
  fake SMTC reader injected (module seam), route shape, art 404.

### W2 — Spectrum screensaver — DL-117

WASAPI loopback → FFT → bars. Backend:

- `backend/services/audio_spectrum.py`: `set_emitter`/`set_spawner`/`start`/
  `set_enabled` (enabled flag gates the capture loop — orchestrator starts it
  enabled on Windows). Capture via `soundcard`
  (`sc.all_microphones(include_loopback=True)`, default speaker's loopback,
  record ~2048-frame chunks @ 48 kHz) + `numpy` rfft into 20 log-spaced bands
  30 Hz–16 kHz → ints 0–100 with per-band normalization + decay.
  Emit `audio_spectrum` per the socket contract, capped ~14 Hz, only when
  bands changed meaningfully; emit `{live: false}` heartbeat ~2 s when silent
  so the widget can idle gracefully. Own thread, own COM objects — never
  inside the audio worker. Lazy imports; missing deps → module stays inert.
- `frontend/src/services/audioSpectrum.ts`: reactive singleton subscribing
  `audio_spectrum` → `{ bands, level, live, lastSeenAt }`.
- `frontend/src/components/screensaver/SpectrumWidget.vue`: canvas bars in
  the classic Winamp look — thin vertical bars, green→yellow→red vertical
  gradient, brighter peak-hold cap per bar that falls slowly, ~20 bands,
  small gaps, dark translucent chrome matching the other widgets
  (`.ss-section` aesthetic). Flat idle line when `live` is false; unavailable
  state when nothing ever arrived. ~15 fps redraw via rAF, no library.
- `backend/tests/test_audio_spectrum.py`: band-mapping/normalization math on
  synthetic FFT input (no soundcard needed — structure code so the DSP is a
  pure function), emit throttle logic with injected clock.

### W3 — System stats screensaver widget — DL-118

- `frontend/src/composables/useSystemStats.ts`: poll `GET /api/metrics/all`
  every ~2.5 s only while subscribed (start/stop API like `useWeather`),
  expose `{ stats, loading, error, stale }`.
- `frontend/src/components/screensaver/SystemStatsWidget.vue`: compact strip
  per `contracts/widget-contract.md`: CPU %, MEM %, GPU % (only if the
  payload carries GPU data), NET up/down, DISK % — label + thin meter bar +
  value, section head "System". Honest offline state.
- No backend changes — `/api/metrics/all` already exists. Check
  `utils/system_metrics.py` for exact payload keys before coding the UI.

### W4 — Notification-to-panel — DL-119

Today: one `_current_alert` in `routes/agent_events.py` — a second waiting
agent overwrites the first, dismissing forgets who was waiting, and nothing
persists on the panel. Deliver a real "which agent needs you" surface:

- Backend (`routes/agent_events.py` only): keep a per-source alert map instead
  of a single alert. Broadcast `agent_alert` with BOTH legacy `alert` (the
  newest, for back-compat) and `alerts` (full list) — see socket contract.
  `GET /api/agent-events/current` gains `alerts` alongside `alert`.
  `DELETE /api/agent-events/current` accepts `?source=` to clear one source;
  no param clears all. Keep DL-105's prompted gate and the TTL semantics.
- `frontend/src/services/agentAlerts.ts`: track the alert map + legacy field;
  expose `alerts` (list), `alert` (newest), `dismiss(source?)`, and a
  `panelNotifications` list fed by the `panel_notification` socket event
  (per contract — MCP/triggers push through it) → each becomes a
  notification-store entry so they land in the bell history + toasts.
- `frontend/src/components/AgentAlertOverlay.vue`: show up to 2 stacked cards
  ("N agents need you" rollup when more), each naming its source/project and
  dismissing independently.
- New `frontend/src/components/AgentWaitingDock.vue`: a persistent pulsing
  corner dock listing each waiting agent (icon + source label + project),
  visible whenever ≥1 agent waits — including after the overlay is dismissed —
  so the panel always flags *who* needs attention. Mount via `Teleport` like
  the overlay does; render it inside `AgentAlertOverlay.vue` so no shared
  file changes are needed. Tapping a chip emits
  `sendUiCommand`-independent local nav — dispatch a `vdock:navigate-scene`
  CustomEvent with `{source}` (orchestrator wires the listener); don't import
  the dashboard store.
- Update `frontend/src/tests/agent-waiting.test.ts`-adjacent coverage with a
  new `frontend/src/tests/notification-panel.test.ts`.

### W5 — Triggers / schedules — DL-120

- `backend/services/triggers.py`: JSON store at `Config.DATA_DIR /
  'triggers.json'`; trigger = `{id, label, enabled, event, action}` —
  - events: `{type:'time', at:'HH:MM', days?:[0-6]}`,
    `{type:'app_foreground', exe:'spotify.exe'}`,
    `{type:'agent_state', source:'claude', state:'permission'}`,
    `{type:'webhook', key:'<random or user string>'}` (fires on POST
    `/api/triggers/fire/<key>` — localhost only).
  - actions: `{type:'execute_action', action:{type,config}}` (runs through the
    injected `action_executor`), `{type:'switch_scene', scene:'<name>'}` and
    `{type:'show_notification', title, message}` (emit `navigate_scene` /
    `panel_notification` socket events per contract).
  - Engine: `set_emitter`/`set_spawner`/`set_executor`/`start`/`stop`;
    single ~1 s loop: time triggers fire once per minute when matched (edge,
    not sustained); app triggers poll `utils.app_monitor.get_current_active_app()`
    and fire on foreground *change into* the exe; agent triggers subscribe by
    polling `integrations.agent_state.snapshot()` and fire on *entry into*
    the state; every fire emits `trigger_fired` per contract. CRUD functions
    `list/add/update/remove` with atomic file writes.
- `backend/routes/triggers.py`: `GET/POST /api/triggers`,
  `PUT/DELETE /api/triggers/<id>`, `POST /api/triggers/fire/<key>`,
  `POST /api/triggers/<id>/test` (fire now). `require_auth` except `fire`
  which is localhost-only like agent events. Blueprint `triggers_bp`.
- `frontend/src/components/settings/TriggersPanel.vue`: self-contained
  settings panel (list, enable toggle, add/edit form with event+action pickers,
  fire-now test button, delete). Style it like existing settings rows — read
  `views/SettingsView.vue` sections for the row/head conventions but do NOT
  edit it; the orchestrator mounts the panel.
- `frontend/src/services/triggersApi.ts`: thin axios wrapper.
- `backend/tests/test_triggers.py`: event matching edges (time once-per-minute,
  app on-entry only, webhook), action dispatch through a fake executor,
  persistence roundtrip, route auth/localhost rules.

### W6 — MCP server — DL-121

- `backend/routes/mcp.py`: `POST /api/mcp` speaking JSON-RPC 2.0 (single
  endpoint, POST-only — the subset of Streamable HTTP transport that tool
  clients need; document the no-SSE limitation). Methods: `initialize`
  (protocolVersion `2025-06-18`, capabilities `{tools:{}}`, serverInfo
  vdock/version), `ping`, `tools/list`, `tools/call`, `notifications/*` →
  empty ack. Batch arrays supported. Errors per JSON-RPC (-32600/-32601/
  -32602/-32603). Localhost-only like agent_events; also honor Bearer token
  when `Config.REQUIRE_AUTH` is on (accept either localhost or valid token).
- Tools (each maps to existing machinery — nothing new invented):
  `deck_info`, `list_scenes` + `list_buttons` (read profile JSONs via
  `Config.DATA_DIR/profiles`), `press_button` (`{button_id}` or
  `{scene,label}` → execute that button's action through the injected
  executor), `run_action` (`{action:{type,config}}`), `switch_scene`
  (`{scene}` → emit `navigate_scene`), `show_notification`
  (`{title,message}` → emit `panel_notification`), `get_volume`/`set_volume`
  (reuse `actions.cross_platform_action` helpers), `get_now_playing`
  (read `services.now_playing` latest snapshot if present — tolerate its
  absence), `get_agent_states` (`integrations.agent_state.snapshot()`).
  Executor + emitter injected via `set_executor`/`set_emitter` (same pattern
  as job_runner) so app.py wires them later.
- `docs/mcp.md`: how to point Claude Desktop / Cursor at
  `http://127.0.0.1:5000/api/mcp`.
- `backend/tests/test_mcp.py`: protocol lifecycle, tools/list schema shape,
  press_button resolution (seed a temp profile dir), error codes, localhost
  guard.

### W7 — Timer buttons + conditional UI — DL-122

Timer/stopwatch buttons (Pomodoro-grade glanceable timers on a 7" panel):

- Catalog: add `time_timer` entries in `backend/actions/catalog.py` under the
  `time` category (e.g. "Timer / Stopwatch", "Countdown") as
  `runs_on=RUNS_FRONTEND` with config fields: `mode` (`countdown`|
  `stopwatch`), `duration_s` (countdown), `auto_start` (bool),
  `on_finish` (optional nested action executed on expiry), `alarm` (bool —
  flash + toast). `ActionType.TIME_TIMER`/`TIME_COUNTDOWN` already exist in
  `models/button.py`; frontend `types/index.ts` needs the union entries.
- `frontend/src/services/timerButtons.ts`: per-button-id timer engine
  (start/pause/reset/tick via `setInterval`, expiry → optional nested action
  through `dashboardStore.executeButtonAction` or socket `executeAction`,
  toast + face flash). Survives scene switches (module-level map).
- `frontend/src/components/TimerButtonFace.vue`: button face — MM:SS (HH:MM:SS
  over an hour), progress ring or bar, running/paused affordance, expired
  flash; sized to a normal deck button (read `DeckButton.vue`/
  `MetricButton.vue` for face conventions).
- `stores/dashboard.ts`: add a `time_timer`/`time_countdown`/`time_stopwatch`
  branch in `executeButtonAction` that toggles the timer (tap = start/pause;
  reset via long-press or a `reset` sub-action in config — pick the simplest
  consistent UX and document it). You own dashboard.ts; keep edits additive.

Conditional UI (the "if X then style Y" layer competitors call dynamic
states):

- `frontend/src/services/conditionalState.ts`: reactive view of socket-fed
  state for rule evaluation: `system_volume` (existing event — subscribe
  directly), `now_playing`, `agent_state`, `audio_spectrum` (per
  `contracts/socket-events.md`), plus `time` (local clock) and `timer`
  (your own engine). Evaluate lazily per button at render time.
- `models/button.py`: add `rules: List[Dict[str,Any]]` field to `Button`
  (roundtrip in `to_dict`/`from_dict`; tolerate absent). Rule shape:
  `{when: {source:'volume.muted'|'volume.level'|'now_playing.playing'|
  'agent.<src>.state'|'timer.running'|'time.hour', op:'eq'|'neq'|'lt'|'lte'|
  'gt'|'gte'|'truthy', value?:any}, then:{tone?:'warning'|'critical'|'success'
  |'accent', icon?:[str,str], sublabel?:string, dim?:bool}}` — first matching
  rule wins.
- `frontend/src/services/buttonRules.ts`: pure evaluator
  `evaluate(button, state) -> RulePatch|null`.
- `DeckButton.vue`: apply the patch — tone → ring/tint class, icon/sublabel
  overrides, dim. Keep it cheap (computed per button).
- `ButtonEditor.vue`: a "Conditional style" sub-section — add/remove rule
  rows (source select, op select, value, then-style fields), following the
  file's existing sub-section patterns.
- Tests: `backend/tests/test_catalog.py` asserts enum↔catalog agreement —
  keep it green; add `frontend/src/tests/timer-buttons.test.ts` +
  `button-rules.test.ts`.

## Contract summary (details in `contracts/`)

- Socket events: `now_playing`, `audio_spectrum`, `panel_notification`,
  `trigger_fired`, `navigate_scene`, `agent_alert` (extended).
- REST: `GET /api/now-playing`, `GET /api/now-playing/art`,
  `/api/triggers*`, `POST /api/mcp`.
- Screensaver widgets are standalone components in
  `frontend/src/components/screensaver/` — the orchestrator mounts them in
  ScreenSaver.vue and adds the settings toggles.
