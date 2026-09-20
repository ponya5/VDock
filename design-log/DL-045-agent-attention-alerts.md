# DL-045: Agent attention alerts — "agent is waiting" popup

## Problem

When a Claude Code / Cursor session blocks on a permission prompt or
idle-waits for input, nothing surfaces that to the user — especially on
the 7" deck, which is usually showing the screensaver. The user asked
for a popup on both the dashboard and the screensaver.

## Design

Local webhook → socket broadcast → global overlay:

- `POST /api/agent-events` (`backend/routes/agent_events.py`) accepts
  `{source, event: 'waiting'|'clear', message, project, cwd}` —
  localhost-only, unauthenticated (agent hooks are local shell commands
  that can't carry UI tokens; the socket payload is display-only).
  `GET/DELETE /api/agent-events/current` let clients sync/dismiss.
  Alerts auto-expire after 30 min so a killed session can't wedge one.
- `scripts/vdock_agent_hook.py` — stdlib-only helper invoked by Claude
  Code hooks: reads the stdin JSON, maps `Notification`→waiting and
  `Stop`→clear, POSTs to the backend. Always exits 0 — a hook must
  never block the agent.
- `POST /api/agent-events/install-hook` merges the command hook into
  `~/.claude/settings.json` (Notification + Stop), keeping a
  `.vdock-backup.json` beside it; `GET /hook-status` reports install
  state for the Settings card.
- Frontend: `services/agentAlerts.ts` holds reactive state fed by the
  `agent_alert` socket event + `/current` on load (alerts raised while
  the UI was closed still show). `AgentAlertOverlay.vue` teleports a
  pulsing amber card to `body` at z-30000 — above the tutorial (10000)
  and screensaver (500). Settings → Integrations gains an "Agent
  Attention Alerts" card with a persisted `agentAlertsEnabled` toggle,
  hook status pill, and Install button.

## Implementation Results

- Verified end-to-end live: POST → card over the screensaver at
  1024×600 → "Got it" dismisses locally *and* clears the backend alert.
- Hook script verified with real Claude-shaped stdin payloads.
- 757/757 backend tests, 231/231 frontend tests, typecheck clean.
