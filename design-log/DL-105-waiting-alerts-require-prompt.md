# DL-105: "Waiting" alerts only after the session's first prompt

## Problem

Opening a fresh Claude Code session immediately raises the
"Claude Code is waiting for input" surfaces (edge glow, scene-pill ring,
Snooze chip) — and ~60s later the Claude `Notification` (idle) event fires
the DL-045 attention popup too. A brand-new session is *always* idle, so
the alert is noise: the user's requirement is *"only show idle
notification when the agent is waiting after the user's first prompt."*

Root cause: `SessionStart` maps to `state:'ready'`, and every waiting
surface treats any `ready` as alertable. Nothing distinguishes
"fresh session, never prompted" from "finished a response, now waiting".

## Design

Track a per-session **`prompted`** flag in `agent_state` — true once the
session has seen a user prompt (or equivalent work):

- **Hook** (`vdock_agent_hook.py`): `build_body` adds
  `'prompted': event_name not in {'SessionStart', 'Notification'}`. Every
  other event (UserPromptSubmit, Pre/PostToolUse, Stop; all Cursor and
  Antigravity events — they only exist mid-run) implies a prompt
  happened. This covers the edge where the prompt *text* isn't captured.
- **`agent_state.record()`**: new `prompted` kwarg; the entry stores
  `prompted = flag or bool(prompt_text) or previous.prompted` — sticky
  per session, reset naturally by a new `session_id` (a `/resume` reuses
  the id, keeping history → resumed sessions may alert, which is
  correct: they carry a prompt history).
- **Route**: `_update_alert` is gated — `attention` on a `ready` state is
  dropped when the entry is unprompted (fresh-session idle-notification).
  `permission` bypasses the gate: a permission dialog is a real blocker,
  and it preserves the legacy `event:'waiting'` → alert contract.
- **Frontend**: `sceneWaitingAgent` (drives the glow, pill ring, Snooze
  chip, mobile flags) requires `entry.prompted` alongside
  `state === 'ready'`. The state pill still reads "Ready for your
  prompt" on a fresh session — only the *alert* is suppressed.

`_combined` stays "newest wins, permission outranks": with several
sessions the source-level entry reflects the freshest event; the session
picker already shows per-session state.

## Implementation Plan

- [ ] `vdock_agent_hook.py`: `prompted` in `build_body`
- [ ] `agent_state.record()`: persist `prompted` (sticky per session)
- [ ] `agent_events.py`: pass the flag through; gate `ready`-attention
      on `entry.prompted`
- [ ] `agentState.ts`: `prompted?: boolean` on `AgentStateEntry`
- [ ] `agentWaiting.ts`: `sceneWaitingAgent` requires `entry.prompted`
- [ ] Tests: backend (fresh ready+attention → no alert; prompted →
      alert; flag without text; legacy waiting unaffected) + frontend
      (unprompted ready → null; existing snooze tests get
      `prompted: true`)
- [ ] `pytest`, `vitest`, `vue-tsc`, `npm run build`

## Implementation Results

Landed as designed, plus one extra surface found during implementation:

- `vdock_agent_hook.py` — `build_body` emits
  `'prompted': event_name not in ('SessionStart', 'Notification')`
  (resolved via `hook_event_name or event`, matching `map_event`).
- `agent_state.record()` — `prompted` kwarg; the entry stores
  `flag or bool(prompt) or previous.prompted`, sticky per `session_id`.
- `agent_events.py` — passes the flag through; `attention` on a
  non-`permission` state is dropped when `entry.prompted` is false.
  Permission bypasses the gate → legacy `event:'waiting'` unaffected.
- `/api/agent-sessions` rows now carry `prompted` — the desktop picker
  rows/chip (`AgentActionBar`: row ring, "waiting" tag, chip hint,
  other-session nudge) and mobile console session chips
  (`MobileAgentConsole`) all gate on `state === 'ready' &&
  prompted === true`. This was the second surface beyond
  `sceneWaitingAgent` — four raw `s.state === 'ready'` sites existed.
- `agentWaiting.sceneWaitingAgent` requires `entry.prompted`;
  `AgentStateEntry`/`AgentSessionInfo` gained the field. The state pill
  still shows "Ready for your prompt" on fresh sessions — only alerts
  are suppressed.

**Tests:** backend +5 (idle-notify on fresh session → quiet; after prompt
→ alert; flag-without-text counts; permission bypasses; hook flag
matrix incl. cursor/antigravity). Frontend: updated snooze/glow/console
fixtures to `prompted: true`, added unprompted-suppression cases.

**Verified:** `pytest` 922/922, `vitest` 327/327, `vue-tsc` clean,
`npm run build` clean (`dist/` rebuilt). Live end-to-end on the
restarted backend: `ready+attention+prompted:false` → no alert,
`prompted:true` → alert raised.

**Note:** the running backend was again stale (two `app.py` processes
were up; the pre-change one owned :5000). Killed both, relaunched the
venv interpreter — the gate is live as of that restart.
