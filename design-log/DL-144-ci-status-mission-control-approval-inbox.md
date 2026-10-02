# DL-144 - Live CI/PR buttons, Agent Mission Control, Approval Inbox

Implements the top three items of the DL-143 developer-feature research
(recommended order 1, 2, 6).

## Problem

1. **CI / PR status buttons.** `github_pack.py` already ships `gh_widget_ci`,
   `gh_widget_prs` and `gh_widget_notifications`, but in practice they are
   dead weight: they need a `GITHUB_TOKEN` in `backend/.env` even though the
   user is already logged in with `gh`, nothing ever *refreshes* them (the
   `refresh_interval` field is configured but no poller reads it - a widget
   only updates when pressed), and pressing one does not take you to the
   failing run.
2. **Multi-agent mission control.** With several agents/sessions running
   (Claude Code x2, Cursor, Codex...) the deck shows one chip per *source*.
   There is no single place that lists every session with its project, state,
   how long it has been idle and what it last said, and no one-tap "go to that
   session".
3. **Approval inbox.** A blocked permission prompt can only be answered from
   the Claude Code scene (Approve/Deny buttons target "the" session). With two
   sessions blocked you cannot answer a specific one from anywhere else.

## Design

### 1. CI / PR widgets that actually work
- Token resolution: `GITHUB_TOKEN` env first, otherwise the token from
  `gh auth token` (cached in-process; registered with `secrets.redact` so it
  never leaks into messages/logs). Availability + reason strings follow.
- Polling: a `useWidgetPolling` composable in the dashboard re-runs every
  *visible* `gh_widget_*` button at its `refresh_interval` (floor 30 s),
  writing the result into `buttonStateStore` (badge / tone / sublabel) without
  a toast. Polls pause while the tab is hidden and in edit mode.
- Press: runs the widget once (visible feedback) then opens `data.url` (the
  latest run, or the PRs page) through the existing `url` action, so a red
  build is one tap from its log.
- Failure notification: a CI widget flipping from non-critical to `critical`
  raises one notification ("CI failed on <branch>"). This stands in for the
  research idea "feeds the waiting glow" - the glow is agent-state-only today
  and wiring a second source into it is out of scope.
- PR widget also returns the PRs URL; `only_mine` (review requests) is
  already supported and is surfaced in the docs.

### 2. Mission Control
- `GET /api/agent-mission` flattens `agent_state` into one row per session:
  source, session id, project, cwd, state, message, last prompt, last reply
  excerpt, `ts`, `needs_you`, `can_decide`. Sorted needs-you first (permission
  oldest-first, then ready-prompted), then working, then the rest.
- `POST /api/agent-mission/focus` raises the session's host window
  (`window_focus.find_session_host_window` by cwd).
- Frontend `AgentMissionControl.vue`: teleported modal. Live via the existing
  `agent_state` socket event + a 1 s ticker for "idle 4m". Opened by the
  `vdock:mission-control` window event, by a new frontend deck action
  `agent_mission_control`, and by an "Inbox" chip that the waiting dock shows
  whenever something needs the user.

### 3. Approval inbox
- Lives at the top of Mission Control: "Needs your approval (n)".
- `POST /api/agent-mission/decide {source, session_id, decision}` sends the
  existing keymap command (`cc_approve` -> `y`, `cc_deny` -> `n`) to *that*
  session's window via `editor_base.send(..., cwd=session.cwd)`.
- Safety: the server re-checks that the targeted session is **still in
  `permission`** (409 otherwise) and that the source supports decisions
  (today: Claude Code only - it is the only agent with confirm keymaps). A
  stale tap can never type `y` into a session that moved on.
- Per-project auto-approve rules from the research are deliberately **not**
  built: silently answering "yes" to permission prompts is a security
  decision that deserves its own design and opt-in review.

## Out of scope
- Auto-approve rules; Approve/Deny for Cursor/Codex/Antigravity (no confirm
  keymaps exist for them); PR/CI widgets for non-GitHub hosts.

## Implementation Results

Implemented as designed.

- **Live CI / PR buttons:** `github_pack` resolves a token from `GITHUB_TOKEN`
  or `gh auth token` (cached 10 min, registered with the redactor), so no .env
  setup is needed. Widget results carry a `url`; pressing a `gh_widget_*`
  button opens it. `only_mine` filters the pulls list by requested reviewer
  (the search API 422'd on private repos). `useWidgetPolling` refreshes
  on-screen widgets silently (min 30 s, default 120 s; paused when hidden or
  editing) and raises one "CI failed" notification on a transition to critical.
- **Mission Control:** `routes/agent_mission.py` (list / focus / decide),
  `services/missionControl.ts`, `AgentMissionControl.vue`, a dock button and a
  `agent_mission_control` deck action (`ui_control: open_mission_control`).
- **Approval inbox:** Approve/Deny inside Mission Control, Claude Code only
  (`cc_approve`/`cc_deny`). The server re-checks the session is still in
  `permission` and returns 409 otherwise; keystrokes target that session's window.

**Verification:** backend 1144 + 19 new GitHub widget tests and 15 mission tests
pass; `vue-tsc` clean; vitest 631/631 (41 new); production build done; backend
restarted. Live: three simulated sessions rendered grouped and ordered,
stale-approve returned 409, Open on a nonexistent window showed the error toast,
test sessions cleaned up.

**Limits:** the real `y`/`n` keystroke into a live Claude Code window was only
unit-tested (mocked), not fired live. No auto-approve rules (deliberate).
Approve/Deny is unavailable for Cursor/Codex/Antigravity.
