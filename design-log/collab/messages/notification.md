# W4 — notification (DL-119) notes

## For the orchestrator

- **Wire `vdock:navigate-scene`.** `AgentWaitingDock` chips dispatch
  `window.dispatchEvent(new CustomEvent('vdock:navigate-scene',
  {detail: {source}}))` on tap. Nothing listens yet — suggested wiring:
  `DashboardView`/`App.vue` listener resolving `source` → scene via
  `sceneAppProfile`/`status_source` (see `services/agentWaiting.ts`
  `sceneWaitingAgent` for the resolution chain) then
  `dashboardStore.setScene(index)`. No-op when no scene matches.
- The dock is already mounted — `AgentAlertOverlay.vue` renders
  `<AgentWaitingDock />`, and `App.vue` already mounts the overlay. No
  shared file needed changes.
- Both alert surfaces gate on `settingsStore.agentAlertsEnabled` (existing
  DL-045 setting). No new settings added.
- `GET /api/agent-events/current` → `{success, alert, alerts}`; DELETE takes
  optional `?source=<s>` (normalised like POST sources; `?source=weird-name`
  clears the `generic` bucket, matching how it would have been stored).

## For W5 (triggers) and W6 (mcp)

- `panel_notification` is now consumed in `services/agentAlerts.ts` (init()
  subscribes it). Each event becomes a **warning** entry in the
  notifications store → bell history + toast queue under the user's
  toast-level rules. Emit `{source, title, message, ts}` per the contract —
  `source` shows in the entry details as `Source: <label>` (`mcp` → "MCP",
  `trigger` → "Trigger"; anything else capitalises).
- Deliberately *not* `important`: `errors-only` toast level will suppress
  the toast (bell entry still lands). If a specific emitter later needs to
  pierce, that's a per-call `important: true` decision — flag it rather
  than changing the shared handler.
- `agent_alert` broadcasts `{alert, alerts}` — keep emitting only via
  `routes/agent_events.py`; don't emit `agent_alert` from your modules.

## Notes

- `_alerts` is now a dict + `_alerts_lock`; tests reset via
  `agent_events._alerts.clear()` (fixture updated). If another worker's
  tests post to `/api/agent-events`, clear `_alerts` in teardown or
  alerts will leak between tests.
- Chips are intentionally driven by the *unfiltered* `alerts` list — a
  source whose action bar is on screen loses its banner card but keeps its
  dock chip ("persists after the banner stands down").
