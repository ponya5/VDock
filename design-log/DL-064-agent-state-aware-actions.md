# DL-064: Agent state-aware actions — drive the live CLI, show what fits now

**Date:** 2026-09-24
**Depends on:** DL-004 (keymaps, focus-first delivery, session resolution),
DL-045 (agent hook + `/api/agent-events`)

## Background

Reported by the user:

> "open claude cli and i insert a prompt and theres no button to submit …
> i click open claude > opens cli > with claude / i insert a prompt and none
> of the other buttons did anything … make sure that vdock identify the state
> of claude (or cursor or other ide) and present the relevant action buttons"

## Problem

1. **The scene's buttons don't talk to the CLI the user opened.** The seeded
   Claude Code scene (`defaultProfile.ts`, `dev-claude-code.json`) mixes one
   live action (`claude_continue` opens a console) with headless jobs —
   `claude_slash` / `claude_prompt` spawn a *separate* `claude -p` process
   that runs 30 s–4 min and reports via toast. Nothing is typed into the open
   session, so from the user's seat the buttons are dead.
2. **No Submit.** After typing a prompt by hand (or with a text button that
   doesn't submit) there is no button that sends Enter to the session.
3. **Multi-line prompts submit early.** `Command.to_macro_steps` types text
   verbatim; every `\n` is an Enter in a TUI, so a clipboard snippet is
   submitted at its first line.
4. **No agent state.** DL-045 only knows one bit — "an alert is pending".
   VDock can't tell *ready for a prompt* from *working* from *waiting on a
   permission prompt*, so it can't offer the buttons that fit the moment.

## Design

### Agent state model

One state per agent source (`claude`, `cursor`, `devin`, `generic`):

| State        | Meaning                                   | Claude Code hook                     | Cursor hook          |
|--------------|-------------------------------------------|--------------------------------------|----------------------|
| `ready`      | idle, waiting for the user's next prompt  | `SessionStart`, `Stop`, `Notification` (idle) | `stop`       |
| `working`    | processing a turn / running tools         | `UserPromptSubmit`, `PreToolUse`, `PostToolUse` | `beforeSubmitPrompt`, `afterAgentResponse` |
| `permission` | blocked on an approve/deny dialog         | `Notification` (permission)          | —                    |
| *(removed)*  | session ended                             | `SessionEnd`                         | —                    |

`Notification` is split by its `notification_type`
(`permission_prompt` / `idle_prompt` …) when present, else by the message
text ("permission"). States expire after 30 min like alerts do.

With no hook data for an agent, the state is `unknown` and the frontend
falls back to process detection (DL-033 live dot): session running → show
the generic set.

**Backend:** new `integrations/agent_state.py` — a small thread-safe registry
(`record`, `clear_source`, `snapshot`), independent of Flask. The
`/api/agent-events` POST accepts the new `state` field; legacy
`event: waiting|clear` keeps working (mapped to `permission`/`ready`) so an
already-installed DL-045 hook doesn't break. Broadcast `agent_state` over
Socket.IO; `GET /api/agent-events/states` for load/reconnect sync. The DL-045
alert still fires on `Notification` and clears on anything else.

**Hook script:** maps the table above for `--source claude` and
`--source cursor`. Cursor's `beforeSubmitPrompt` requires a JSON reply, so the
script prints `{"continue": true}` for it — the hook must never block the
user's prompt. No Cursor hook that gates a permission (`beforeShellExecution`,
`beforeMCPExecution`) is installed: answering those would bypass Cursor's own
approval.

**Installers:** moved out of the route into `integrations/agent_hooks.py`.
Claude: merges the six events into `~/.claude/settings.json`, and *upgrades*
a DL-045 install that only has `Notification` + `Stop`. Cursor: merges into
`~/.cursor/hooks.json` (`version: 1`). Both keep a `.vdock-backup` copy and
never touch entries they don't own (marker `vdock_agent_hook`).

### State-aware actions

`AppProfile` gains `state_actions: {state: (command ids…)}`, served in
`/api/app-profiles`. Knowledge stays in Python (DL-004 approach C).

- **claude-code** — `ready`: Submit, Continue, Newline, Mode, Clear, Compact;
  `working`: Interrupt, Queue, Background, To-dos; `permission`: Approve
  (Enter on the highlighted option), Option ↑/↓, Deny (Esc);
  `unknown`: Submit, Continue, Interrupt, Approve.
- **cursor** — `ready`: Submit, New Chat, Accept, Reject; `working`: Cancel
  generation, Accept, Reject; `unknown`: Submit, Accept, Reject, Chat.
- **devin** — no hooks, `unknown` only: Submit, Send Prompt, Interrupt.

New commands: `cc_submit` (Enter, session-gated), `cursor_submit` (Enter),
`cursor_cancel` (Ctrl+Shift+Backspace), `devin_submit` (Enter).

**Frontend:** `services/agentState.ts` (reactive per-source state, socket +
REST sync). `AgentActionBar.vue` mounts on the dashboard above the grid when
the current scene resolves to an agent profile (reusing `appDetection`
resolution): a state pill ("Ready for your prompt" / "Working…" /
"Needs your permission" / "Session running") plus the state's actions, each
executed through `dashboardStore.executeAction` with button-state feedback.
Hidden when the scene isn't an agent scene or the agent isn't running.

### Scene buttons drive the live session

- Seeded Claude scene (`defaultProfile.ts`, `dev-claude-code.json`,
  `appTemplates.ts`): Review / Commit / Explain / Write Tests / Fix Tests /
  Continue become `cc_prompt` with the same text — typed into the live
  session. A **Submit** button is added. "Open Claude" stays.
- `Command.newline_keys`: when set, typed text is split on newlines and each
  break is sent as that chord (Claude Code: Ctrl+J) instead of Enter, so a
  multi-line prompt arrives as one prompt.
- The user's existing profile is migrated through the profiles API (same
  approach as DL-004's rewiring), preserving ids, positions and styles.

## Trade-offs

- **Hooks over screen scraping** — reading the console buffer would work
  without setup but is brittle across terminals/hosts; hooks are the
  supported interface. Fallback is process detection, so an un-hooked agent
  still gets a useful bar.
- **Bar over rewriting the grid** — auto-swapping the user's buttons on
  state change would fight muscle memory and their own layouts; a fixed bar
  keeps the grid stable and still surfaces the right actions.
- **Approve = Enter, Deny = Esc** rather than `y`/`n`: Claude Code's current
  permission dialog is an option list; Enter on the default option and Esc
  are correct across versions, typed letters are not.

## Verification Criteria

- Hook script maps every table row; exits 0 with backend down; prints
  `{"continue": true}` for Cursor `beforeSubmitPrompt`.
- Installer upgrades a DL-045 install, is idempotent, preserves foreign
  hooks, writes a backup; Cursor installer creates `version: 1`.
- `/api/agent-events` accepts `state`, keeps legacy `event`, broadcasts
  `agent_state`; states expire.
- Multi-line `cc_prompt` emits Ctrl+J between lines, one Enter at the end.
- Live: open Claude → type a prompt by hand → **Submit** on the bar sends it;
  state flips `ready → working → ready`; a permission prompt shows
  Approve/Deny and Approve answers it. No console/network errors.

## Implementation Results

**Status:** Implemented. Everything is verified except the final keystroke
delivery into a live terminal, which was blocked because the PC sat on the
Windows screensaver desktop for the whole session.

### Deviations from the design

- **Per-session state.** State is keyed by `(source, session_id)`, using Claude's
  `session_id` or Cursor's `conversation_id`, and then combined per source:
  a pending permission prompt in any session wins, otherwise the newest event
  wins. A single slot per source failed in practice, because a headless
  `claude -p` run ending (`SessionEnd`) wiped the state of the interactive
  session. `GET /api/agent-events/states` exposes the combined snapshot, which
  includes `session_count`.
- **Explicit `attention` flag.** The hook sets `attention: true` only for
  `Notification` events. The first draft inferred attention from the word
  "waiting", which made every `Stop` pop the alert overlay.
- **Root cause of "no server push ever arrives".** `python app.py` runs the
  file as `__main__`, and routes that lazily `from app import action_executor`
  then imported a second copy as module `app`. That copy built a second,
  unserved SocketIO and re-pointed every broadcaster at it. After the first
  button press, no socket event reached any client: not agent state, not
  alerts, and not background-job results, which had silently failed since
  that pattern was introduced. Fixed by aliasing `sys.modules['app']` to
  `__main__` in `app.py`. `test_app_main_module_alias.py` guards the fix.
- **Focus escalation and lock detection.** `focus_hwnd` now escalates from a
  plain `SetForegroundWindow`, to an Alt tap, to minimise/restore.
  `interactive_desktop_blocked()` detects the lock screen or screensaver, and
  delivery fails with "The PC is locked or its screensaver is on" instead of
  a generic "Windows would not bring it forward".
- **Bar fallback when app scanning is off.** With scanning disabled,
  "not detected" only means "not looked for". In that case the bar still shows
  the `unknown` actions, labelled "Status unavailable", instead of hiding.
  Without this, the Cursor scene showed nothing when its hook wasn't installed.
- **Cursor hook not installed in the live IDE.** It is available as one click
  in Settings → Agent hooks. The Claude hook was installed into
  `~/.claude/settings.json`, with a backup at `settings.vdock-backup.json`.
- **Collateral fixes:** `ScreenSaver.vue` was calling `nextTick` without
  importing it (a `ReferenceError` on every news-fit pass). The default Cursor
  scene used the Font Awesome Pro icon `square-terminal`; it now uses the free
  `terminal` icon.

### Known limitations

- `chrome-native-host.exe`, which ships with the Claude desktop app, matches
  the Claude session marker. It can be picked as a session host when no
  terminal session is running.
- Cursor has no hook for its own permission prompts, so Cursor never reports
  the `permission` state. Accept and Reject are always offered instead.

### Verification

- Backend: 828 passed, including about 40 new tests in
  `test_agent_state_events.py` and the `__main__` alias regression test.
  Frontend: 240 passed.
- Real Claude hooks: `claude_continue` opened a session that reported
  `ready`. A real `claude -p` run went `working → ready → ended`.
- Browser, with real hook payloads piped through `vdock_agent_hook.py`: the bar
  switched live over the socket from ready (Submit / Continue / Newline /
  Mode / New Session / Compact), to working (Interrupt / Queue / Background /
  To-dos), to permission (Approve / Option ↑ / Option ↓ / Deny, with the
  attention alert overlay), and back to ready. The Cursor scene shows
  Submit / Accept / Reject / Chat. Media and Websites show no bar. There
  were no console errors or warnings across all scenes after the fixes.
- Pressing Approve while the screensaver was on returned a clear error toast
  naming the lock screen or screensaver.
- **Not verified:** keystroke delivery (Submit typing Enter into the focused
  Claude terminal). It needs an unlocked desktop.
