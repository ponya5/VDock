# DL-119: Notification-to-panel — multi-agent "who needs you" surface

## Background

The DL-045 attention alert keeps ONE `_current_alert` in
`backend/routes/agent_events.py`: a second agent waiting on a permission
prompt overwrites the first, dismissing forgets who was waiting, and nothing
persistent on the panel says *which* agent needs the user. With Claude Code,
Cursor, Devin and Antigravity all able to hook in, a single-slot alert is
wrong the moment two agents block at once.

Related surfaces already exist and are not replaced here:

- DL-045 — the amber `AgentAlertOverlay` banner + `agent_alert` socket event.
- DL-080 — the waiting edge-glow + snooze for idle (`ready`) sessions.
- DL-105 — the `prompted` gate so fresh sessions don't alert.

This change extends that system from one alert to a per-source set, and adds
a persistent corner dock so a dismissed banner still leaves a "who" marker.

## Problem

1. `_current_alert` is single-slot — source B's alert silently erases
   source A's.
2. `DELETE /api/agent-events/current` clears everything; there is no
   per-source dismiss, so the overlay can't offer per-card dismiss.
3. After dismissal nothing remains on screen — on a glanceable 7" panel the
   user has no reminder that an agent still waits.
4. `panel_notification` (W5 triggers / W6 MCP push) has no consumer yet.

## Design

### Backend — `routes/agent_events.py` (edit)

- `_current_alert` → `_alerts: Dict[source, alert-dict]` (insertion-ordered,
  one live alert per source — a new alert for the same source replaces it).
- `_alerts_list()` drops expired entries lazily (same TTL as before) and
  returns survivors sorted newest-first by `ts`.
- `_broadcast_alert()` emits `agent_alert` with
  `{alert: newest-or-null, alerts: [all newest-first]}` per the socket
  contract — legacy `alert` preserved for back-compat.
- `_update_alert()`: raise → set `_alerts[source]`; clear → drop only
  `_alerts[source]`, and only when that source's combined state is no longer
  `permission` (the existing "another session may still be blocked" guard).
  Source-scoped clearing is preserved: an event for source A never touches
  source B's alert.
- `GET /api/agent-events/current` → `{success, alert, alerts}`.
- `DELETE /api/agent-events/current` — `?source=<s>` clears that one source
  (normalised like POST sources); no param clears all. Both broadcast.
- Kept untouched: localhost-only POST, the DL-105 prompted gate, TTL,
  legacy `event`→state mapping, `_broadcast_states`, hook routes.

### Frontend — `services/agentAlerts.ts` (edit)

- State: `{alert, alerts, receivedAt}` — `alerts` newest-first, `alert` the
  newest (legacy). A legacy payload with only `alert` maps to a 1-item list.
- `dismiss(source?)` — with a source: optimistically drop that entry +
  `DELETE ?source=<s>`; without: clear all + plain DELETE.
- `sourceLabelFor(source)` — `SOURCE_LABELS` gains `antigravity`; unknown
  sources fall back to a capitalised raw name, empty → 'Agent'.
- `panel_notification` socket subscription (payload `{source,title,message,
  ts}`) → `useNotificationsStore().warning(title, message, {details: source
  label})` so MCP/trigger pushes land in the bell history + toast queue.
  `warning` (not `important`): these are deliberate user-facing notices, but
  they must not pierce an `errors-only` toast level — the store's own rules
  decide visibility. The store is fetched lazily inside the handler so the
  module never touches Pinia at import time.

### `AgentAlertOverlay.vue` (edit)

- Up to 2 stacked cards (newest first) inside one fixed top-center stack
  container; each card = icon + "<label> needs you" + message + project +
  its own dismiss (per-source DELETE).
- `>2` visible alerts collapse into a single "N agents need you" rollup card
  listing the source labels, with a dismiss-all button.
- The DL-080 "covered by an action bar" stand-down becomes per-card: alerts
  whose source has a visible `AgentActionBar` are filtered out of the stack
  (the bar already shows state + Approve/Deny on a small panel).
- Renders `<AgentWaitingDock />` from its template so no shared file
  (App.vue) needs to change.

### `AgentWaitingDock.vue` (new)

- Persistent corner dock (fixed bottom-right, z-index 29000 — just under the
  overlay's 30000): one chip per alert with a pulsing amber dot, source
  label, project. Chips read the same `alerts` list as the overlay, so a
  chip lives exactly as long as its backend alert (per-source dismiss, state
  clear, or TTL).
- Chip tap dispatches
  `new CustomEvent('vdock:navigate-scene', {detail: {source}})` on `window` —
  the orchestrator wires the listener; the dock imports no stores besides
  settings/notifications it needs for its own visibility.
- Each chip carries a small × that per-source-dismisses (same as the card's
  Got it) — otherwise a dismissed banner would leave an alert the user can
  no longer clear without answering the agent.
- Same amber palette + `clamp()` sizing as the overlay; honours
  `agentAlertsEnabled` (part of the same alert surface) and
  `prefers-reduced-motion` for the pulse.

## Implementation Plan

- [ ] `routes/agent_events.py`: `_alerts` map, `_alerts_list`, broadcast
      `{alert, alerts}`, GET gains `alerts`, DELETE `?source=`
- [ ] `test_agent_state_events.py`: fixture reset update + multi-source
      coverage (ordering, per-source delete, cross-source clearing, replace)
- [ ] `agentAlerts.ts`: alerts list, `sourceLabelFor`, `dismiss(source?)`,
      `panel_notification` → notifications store
- [ ] `AgentAlertOverlay.vue`: stacked cards + rollup + dock mount
- [ ] `AgentWaitingDock.vue`: chips + navigate CustomEvent + per-chip ×
- [ ] `frontend/src/tests/notification-panel.test.ts`: ordering, dismiss,
      panel_notification, overlay/dock rendering
- [ ] `pytest tests/test_agent_state_events.py` + `vitest` notification-panel
      / agent-waiting / agent-waiting-glow

## Implementation Results

Landed as designed, plus one hardening detail:

- `backend/routes/agent_events.py` — `_current_alert` replaced by
  `_alerts: Dict[source, alert]` guarded by a `_alerts_lock` (hook POSTs
  arrive on request threads; the single-slot assignment never needed one,
  but dict iteration in `_alerts_list` does — same reason
  `integrations/agent_state.py` locks). `_alerts_list()` expires lazily and
  sorts newest-first; `agent_alert` broadcasts `{alert: newest|None,
  alerts: [...]}`; GET `/current` returns both; DELETE honours
  `?source=<normalised>` vs clear-all. Prompted gate, TTL, legacy event
  mapping, localhost guard, `_broadcast_states` all untouched.
- `agentAlerts.ts` — state is `{alert, alerts, receivedAt}`; `alerts` is
  re-sorted newest-first defensively (a misordered payload still lands
  right); legacy `{alert}`-only payloads map to a 1-item list.
  `dismiss(source?)` is optimistic + `DELETE ?source=`/plain. New
  `sourceLabelFor()` (+ `antigravity`, `mcp`, `trigger` labels; unknown
  sources capitalise). `panel_notification` → `notificationsStore.warning`
  with `details: "Source: <label>"` — deliberately *not* `important`, so
  `errors-only` toast levels still silence them. The store is resolved
  lazily inside the handler (Pinia isn't guaranteed at socket-listen time).
- `AgentAlertOverlay.vue` — `TransitionGroup` stack renders ≤2 cards
  (newest first) or a single "N agents need you" rollup listing the source
  labels with a Dismiss-all button. The action-bar stand-down is now
  per-card (`visibleAlerts` filters `isAgentBarVisible(source)`). The group
  stays mounted (no v-if) so the last card's leave transition still plays.
  `<AgentWaitingDock />` mounts from the overlay template — App.vue
  unchanged.
- `AgentWaitingDock.vue` (new) — bottom-right fixed dock at z-29000, one
  pulsing amber chip per alert (dot + source label + project), reading the
  same `alerts` list as the overlay so chips live exactly as long as their
  backend alert. Tap dispatches `vdock:navigate-scene` `{detail:{source}}`;
  per-chip × calls `dismiss(source)`. Gated on `agentAlertsEnabled`;
  `prefers-reduced-motion` freezes the pulse. Note: chips intentionally use
  the *raw* `alerts` list — a bar-covered source still gets its chip, which
  is the "persists after the banner stands down" case.

### Verification

- `pytest tests/test_agent_state_events.py` — **72 passed** (66 prior + 6
  new: coexistence/ordering, same-source replace, `?source=` delete,
  clear-all, cross-source state clearing, per-alert TTL).
- `vitest run notification-panel.test.ts agent-waiting.test.ts
  agent-waiting-glow.test.ts` — **48 passed** (16 new: ordering, legacy
  payload compat, GET re-sync, per-source/all dismiss, sourceLabelFor,
  panel_notification → warning entry + fallback title, overlay 2-card and
  rollup rendering, dock chips/navigate/per-chip dismiss).
- `vue-tsc --noEmit` clean. No `npm run build` (orchestrator builds).

### For the orchestrator

- `vdock:navigate-scene` (`window` CustomEvent, `detail.source`) needs its
  listener wired — resolve `source → scene` (e.g. via
  `sceneAppProfile`/`status_source` against the active profile) and call
  `dashboardStore.setScene`.
- W5/W6 emitters: `panel_notification` is consumed — `{source,title,
  message,ts}` lands in the bell as a warning entry; keep title ≤80,
  message ≤300.
- `GET /api/agent-events/current` now also returns `alerts`; DELETE accepts
  `?source=`. Contract files already describe both.

### Follow-up — Settings configurability pass

The waiting dock gained its own persisted switch, `agentWaitingDockEnabled`
(default on, user-settings file), exposed as "Pin waiting agents on the deck"
in Settings → Integrations → Agent attention alerts, gated on the master
`agentAlertsEnabled`. `AgentWaitingDock.vue` ANDs both flags. A new
"Agent Attention Alerts" entry was added to the Settings search index.
