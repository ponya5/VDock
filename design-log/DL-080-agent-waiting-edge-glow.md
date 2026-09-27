# DL-080: Edge-glow + bar highlight when an agent session is waiting

## Background

Agent scenes already report state (`ready | working | permission | unknown`)
in the action bar, and `permission` pops the `AgentAlertOverlay` banner. But
when a session goes `ready` — idle, waiting for the user's next command —
nothing ambient signals it: the user has to read the small state pill.

Requested: while on an IDE scene whose agent session is waiting, glow the
screen boundaries with an animation; highlight which session is idle inside
the interactive bar; gate it behind a setting that defaults to enabled.

## Design

### Edge glow — `AgentWaitingGlow.vue` (new, mounted in DashboardView)

- Mounted next to `AgentActionBar`/`MobileAgentConsole` so it covers desktop
  and mobile layouts (each already shares `useAgentSession`).
- Teleported `<div>` to `body`: `position: fixed; inset: 0;
  pointer-events: none`, animated inset `box-shadow` in the `ready` accent
  (#22c55e), fade-in on entry, gentle breathing pulse while waiting.
- Visible when: `isAgentPossiblyRunning && currentState === 'ready' &&
  !isEditMode && settingsStore.agentWaitingGlowEnabled`.
- `prefers-reduced-motion` and `animationsEnabled` → static edge, no pulse.

### Session highlight — `AgentActionBar.vue`

- `effectiveSession.state === 'ready'` → `.agent-target-chip.waiting` gets a
  pulsing green ring; picker rows with `s.state === 'ready'` get a `waiting`
  tag/ring so the idle session stands out in the list.
- Applies to marker'd agents only (Claude, Devin — Cursor exposes no
  `session_marker`, so no per-session rows; it still gets the edge glow).

### Setting — `agentWaitingGlowEnabled`, default `true`

Mirrors `agentAlertsEnabled` at every lifecycle spot in `settings.ts`
(defaults map, `PersistedUserSettings`, ref, payload, apply, remote merge,
exports). Toggle row added to the existing **Agent attention alerts** panel
in `SettingsView`: "Glow when an agent is waiting".

## Implementation Results

Landed as designed:

- `components/AgentWaitingGlow.vue` (new) — teleported fixed edge-glow,
  breathing green pulse while `ready`, static under `prefers-reduced-motion`
  and `animationsEnabled: false`, hidden in edit mode.
- `views/DashboardView.vue` — glow mounted beside the bar/console so desktop
  and mobile layouts share it.
- `components/AgentActionBar.vue` — `waiting` pulse on the target chip when
  the effective session is `ready`; `waiting` tag + row tint on idle rows in
  the session picker; both gated by the same setting.
- `stores/settings.ts` — `agentWaitingGlowEnabled` at all eight lifecycle
  spots, default `true`.
- `views/SettingsView.vue` — "Glow when an agent is waiting" toggle in the
  Agent attention alerts panel.

### Verification

- `agent-waiting-glow.test.ts` (new, 9 tests): glow on `ready` only, hidden
  by setting/edit-mode/not-running, `no-anim` class, default-on, chip pulse,
  picker-row highlight. Full suite: 60 files / 269 tests green;
  `vue-tsc --noEmit` clean.
- Live (dev servers + Chrome DevTools): POSTed `ready` to `/api/agent-events`
  → green edge glow around the viewport on the Claude scene, bar pill "Ready
  for your prompt"; settings toggle unchecked → glow gone, bar unchanged;
  re-enabled + `ended` state POSTed to clean up. Screenshot captured.
