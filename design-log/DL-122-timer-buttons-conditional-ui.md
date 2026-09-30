# DL-122 — Timer/stopwatch buttons + conditional button UI (W7)

## Intent

Two related deliverables for the 7" panel:

1. **Glanceable timers on deck keys** — a button that runs a countdown
   ("tea timer", "Pomodoro") or a stopwatch, showing the remaining/elapsed
   time on its face. Tap toggles start/pause. On expiry: optional alarm
   (flash + toast) and an optional nested `on_finish` action.
2. **Conditional button UI** — per-button "when X then style Y" rules
   (e.g. `volume.muted eq true → tone critical + sublabel "Muted"`), the
   dynamic-state layer stream-deck-alikes ship.

## Background / Problem

- `time_timer` already exists in the catalog but as `RUNS_WIDGET` — the
  face (`TimeOptionsButton`) keeps a *local*, per-mount `setInterval`
  timer that resets on every scene switch and is lost on remount.
  `useButtonActions.handleButtonClick` refuses to dispatch display-only
  types, so pressing a timer button can never reach the store.
- No conditional styling exists: a Mute button looks identical whether or
  not the system is muted.

## Design

### Part A — timers

- **Catalog** (`backend/actions/catalog.py`, additive):
  - The existing `time_timer` entry is converted `RUNS_WIDGET →
    RUNS_FRONTEND` (pressing it must dispatch) with new config fields:
    `mode` (`countdown`|`stopwatch`), `duration_s`, `auto_start`,
    `alarm`, `on_finish` (nested action, `steps` field type — same type
    the toggle entry uses for `on_action`/`off_action` nested actions).
  - New `time_stopwatch` entry: its own `action_type='time_stopwatch'`
    (added to `ActionType` + the TS union), `RUNS_FRONTEND`, default
    `mode: 'stopwatch'`.
  - `time_countdown` (count-to-a-datetime widget) stays `RUNS_WIDGET`.
- **Engine** (`frontend/src/services/timerButtons.ts`): module-level
  `reactive` map `buttonId → TimerState` so timers survive scene switches
  and unmounts. One shared 250 ms `setInterval` while any timer exists;
  elapsed time is computed from `Date.now()` (tick-counting drifts).
  API: `toggle/start/pause/reset/acknowledge/getTimer/isRunning` +
  `ensureMounted` (honours `auto_start`). Expiry → `expired` +
  `flashing` (auto-clears ~10 s), `alarm` → notifications toast,
  `on_finish` → `socketClient.executeAction` (fire-and-forget; socket
  path keeps it working regardless of which store/view is mounted).
  Legacy `timer_duration` configs normalise (`>0 → countdown`, else
  stopwatch).
- **Face** (`frontend/src/components/TimerButtonFace.vue`): display-only
  face (tap handled by the normal press path) — label, MM:SS or H:MM:SS,
  run/pause glyph, thin progress bar, expired flash. Mounted in
  `DeckButton.vue` for `time_timer`/`time_stopwatch` in place of
  `TimeOptionsButton`.
- **Dispatch** (`stores/dashboard.ts`, append-only): `executeButtonAction`
  gains a branch for `time_timer`/`time_stopwatch`/`time_countdown` →
  `timerButtons.toggle(button.id, config)` → `{success,message}`.
  (`time_countdown` stays display-only upstream, so the branch is a
  defensive no-op for it.)
- **UX**: tap = start/pause; tap on an *expired* countdown =
  acknowledge + re-arm. Reset lives in the editor/on the face as a
  re-arm via `reset()` — long-press is reserved for edit-mode drag.
- **Editor**: `time_timer`/`time_stopwatch` config block (mode, duration,
  auto-start, alarm, `on_finish` SubActionEditor).

### Part B — conditional rules

- **Model** (`backend/models/button.py`): `Button.rules:
  List[Dict[str,Any]] = []`, round-tripped through `to_dict`/`from_dict`.
- **State** (`services/conditionalState.ts`): one reactive object fed by
  `system_volume`, `now_playing`, `agent_state`, `audio_spectrum` socket
  events (module-level `socketClient.on` — the pending-listener queue
  makes it connect-safe) + a local 30 s clock tick for `time.hour`.
- **Evaluator** (`services/buttonRules.ts`): pure
  `evaluateRules(rules, state) → RulePatch|null`, first match wins.
  Sources: `volume.muted`, `volume.level`, `now_playing.playing`,
  `now_playing.source_app`, `now_playing.title`, `agent.<src>.state`,
  `spectrum.live`, `spectrum.level`, `timer.running`, `time.hour`,
  `time.minute`. Ops: `eq neq lt lte gt gte truthy`.
  `timer.running` = *this* button's own timer (false for non-timers).
- **DeckButton**: `rulePatch` computed per button; `tone` → ring/tint
  classes on the root, `icon` → overrides the rendered FA icon,
  `sublabel` → replaces the secondary label, `dim` → dims the face.
  No rules → `null` → zero extra render cost.
- **ButtonEditor**: "Conditional style" sub-section — rule rows
  (source select + agent-source input, op, value; then tone/icon/
  sublabel/dim) with add/remove, saved to `button.rules`.

## Implementation Plan

1. DL + STATUS. 2. Backend: catalog entries, `Button.rules`, enum.
3. `types/index.ts`. 4. `timerButtons.ts`. 5. `conditionalState.ts` +
   `buttonRules.ts`. 6. `TimerButtonFace.vue`. 7. `dashboard.ts` branch.
8. `DeckButton.vue` mount + patch application. 9. `ButtonEditor.vue`
   timer config + rules section. 10. Tests + suites green.

## Implementation Results

**Status: complete.** Everything in the plan above landed.

### Delivered

- **Catalog** (`backend/actions/catalog.py:512-562`): `time_timer`
  converted `RUNS_WIDGET → RUNS_FRONTEND` with `mode`, `duration_s`,
  `auto_start`, `alarm`, `on_finish` (`steps` field — same nested-action
  type `toggle` uses). New `time_stopwatch` entry (`RUNS_FRONTEND`,
  icon `fas:stopwatch-20`). `time_countdown` deliberately stays
  `RUNS_WIDGET` — it remains the count-to-a-datetime widget.
- **Model** (`backend/models/button.py`): `ActionType.TIME_STOPWATCH`
  added; `Button.rules: List[Dict[str,Any]]` round-trips via `to_dict` /
  `from_dict` (`data.get('rules') or []`).
- **Types** (`frontend/src/types/index.ts`): `'time_stopwatch'` in the
  action union; `ButtonRule` interface; `Button.rules?: ButtonRule[]`.
- **Engine** (`frontend/src/services/timerButtons.ts`): module-level
  reactive `Map<buttonId, TimerState>`, one shared 250 ms interval,
  `Date.now()`-derived elapsed (no tick drift). `toggle` contract: tap
  pauses/resumes; tap on an *expired* countdown acknowledges and re-arms
  (still stopped). `ensureMounted` honours `auto_start` exactly once —
  the first-mount guard (`hasBeenStarted`) fixed a bug where every
  remount re-autostarted. Expiry sets `expired`+`flashing` (auto-clears
  after 10 s), toasts via `useNotificationsStore().warning` when
  `alarm` (default on), and dispatches `on_finish` through
  `socketClient.executeAction` — fire-and-forget, works from any scene.
  Legacy `timer_duration` / `countdown_target` configs normalise.
- **Face** (`frontend/src/components/TimerButtonFace.vue`): display-only
  — label, mode glyph, tabular-nums `MM:SS`/`H:MM:SS`, run/pause/bell
  state icon, 4 px progress bar (countdown drains; stopwatch fills
  per-minute so the face visibly moves), expiry flash with
  `prefers-reduced-motion` fallback. Mounted in `DeckButton.vue` for
  `time_timer`/`time_stopwatch`; the enclosing button keeps the press.
- **Dispatch** (`frontend/src/stores/dashboard.ts:622-636`): append-only
  branch → `timerButtons.toggle(id, config, label, type)`.
- **Rules**: `services/conditionalState.ts` (socket-fed
  volume/now-playing/agent/spectrum + 15 s local clock),
  `services/buttonRules.ts` (pure first-match evaluator; loose value
  coercion so the editor's text input `'true'`/`'300'` matches real
  types), applied in `DeckButton.vue` — tone → `rule-tone-*` classes,
  icon → overrides `resolvedVisual.icon`, sublabel → replaces the
  secondary label, dim → `rule-dim`. `ButtonEditor.vue` gained the
  "Conditional style" rows + serialisation to `button.rules`, and the
  timer config block replaced the legacy `timer_duration` fields.

### Verification

- `vitest run timer-buttons.test.ts button-rules.test.ts` — **27/27**
  (11 engine: tick/pause/resume/expiry/stopwatch/legacy-normalise/
  auto-start-once/alarm-off/reset/isolation/no-pinia; 16 evaluator).
- `pytest tests/test_catalog.py tests/test_profile_roundtrip.py` — green;
  full backend suite **1057 passed**.
- Focused existing frontend tests (default-profile, socket-correlation,
  button-state, action-catalog, default-scene, background-jobs):
  61 passed.
- `npx vue-tsc --noEmit -p tsconfig.app.json` reports only **pre-existing
  baseline diagnostics** — none on lines added here (verified per file).
  Note: `npm run type-check` is a no-op (`tsconfig.json` has
  `"files": []`), so the strict pass above is the meaningful check.
- `npm run build` intentionally NOT run (parallel-work rule) — and it
  would currently fail on the same pre-existing `vue-tsc` baseline.

### Deviations / decisions

- `on_finish` uses the `steps` config-field type rather than a new type
  — the editor renders it with the existing `SubActionEditor`.
- Expired countdown tap semantics: acknowledge + re-arm (not restart) —
  a second tap starts the next round. Documented on the face's sublabel
  ("Done — tap to re-arm").
- `alarm` defaults to **on** (`cfg.alarm !== false`) — a countdown that
  silently expires is rarely what a user wants on a glanceable panel.
- Legacy `timer_duration` keys are stripped on editor save
  (`delete cfg.timer_duration`) so the engine sees one canonical schema.

### Known limitations (for the orchestrator)

- `useButtonActions` falls back to `time_`-prefix display-only when the
  catalog hasn't loaded — timer taps are no-ops until the catalog
  arrives (graceful; `actionCatalog.ts` is orchestrator-owned).
- Rule `icon`/`sublabel` patches don't render on special faces
  (`time_*`, `metric_*`, `weather`, `slider`) — those faces own their
  content. `tone`/`dim` still apply.
- `DashboardView`'s compact-mode heuristic lists `time_timer` but not
  `time_stopwatch` (orchestrator file) — cosmetic only.
