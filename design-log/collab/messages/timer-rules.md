# W7 — timer-rules notes

## For the orchestrator

**No app.py / backend wiring needed.** `time_timer` and `time_stopwatch`
are `RUNS_FRONTEND` — the engine (`frontend/src/services/timerButtons.ts`)
is self-contained and module-level, so nothing needs starting in `main()`.
`time_countdown` stays `RUNS_WIDGET` (unchanged behaviour).

Integration items worth a look:

- **Offline press no-op**: `actionCatalog.ts` (orchestrator-owned)
  falls back to the `time_` prefix as display-only when the catalog
  hasn't loaded, so a timer tap before catalog load / with the backend
  down does nothing instead of toggling. If that matters, the fallback
  set could whitelist `time_timer`/`time_stopwatch` — I didn't touch the
  file.
- **`on_finish` dispatch** goes through `socketClient.executeAction`
  → the `execute_action` socket handler (exists, app.py:317). It only
  works while the socket is connected; a missed dispatch just logs a
  console warning. Backend-only action types should be used for
  `on_finish` — a frontend-only nested action would be rejected by the
  backend executor.
- **Compact-mode heuristic**: `DashboardView.vue`'s
  `shouldUseCompactMode` includes `time_timer` but not `time_stopwatch`
  (orchestrator file) — cosmetic.
- **`requirements.txt`**: no new backend deps.

## Contract notes for other workers

- `Button.rules` persists verbatim through `button.to_dict()/from_dict`
  — any dict shape is stored; only the frontend interprets it.
- New catalog types: `time_stopwatch` added to `ActionType` +
  TS union. `time_timer` is no longer `display_only` — anything that
  assumed "every `time_*` type never dispatches" (e.g. editor
  `isExecutableType`, `isSpecialActionType`) still treats it as a
  special face, which is correct.
- Rule sources now readable: `volume.muted`, `volume.level`,
  `now_playing.playing`, `now_playing.source_app`, `now_playing.title`,
  `agent.<src>.state`, `spectrum.live`, `spectrum.level`,
  `timer.running`, `time.hour`, `time.minute`. `agent.<src>.state`
  reads W4's `agentState` payload shape (`states[src].state`).

## Flags

- **`src/tests/property8.test.ts` fails at HEAD**, unrelated to W7:
  counterexample `font-size: 19px` is committed code in
  `views/SettingsView.vue:4277` (`.dock-credit-link`, orchestrator-owned,
  unmodified by me). The property scans all `src/**/*.vue|.css` for px
  font-sizes without `clamp()` — the CSS predates the test or vice versa.
  Someone should either clamp() it or exempt icon-size declarations.
- Full frontend suite: 74/75 files, 432/433 tests — that single
  property8 failure. `property6_settings.test.ts` also left an
  `EnvironmentTeardownError` (pending console log at worker shutdown);
  smells like fast-check worker noise rather than a real failure.
- `vue-tsc -p tsconfig.app.json` has ~60 pre-existing errors across the
  tree (union-type drift in `buttonVisual.ts`, `defaultProfile.ts`,
  `DeckButton`, `ButtonEditor`, `dashboard.ts:171`, views). None on my
  added lines — verified per line range. `npm run type-check` is a
  no-op (`files: []`), so don't rely on it; `npm run build` currently
  fails on that baseline regardless of my change.
- Rule `icon`/`sublabel` patches intentionally don't render on special
  faces (`time_*`, `metric_*`, `weather`, `slider`); `tone`/`dim` do.
