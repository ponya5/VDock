# DL-143 - Agent auto-focus, Codex hook, saver widget remove (x), 8+ button templates

## Problem

A batch of related requests, grouped because they share the agent / scene /
screensaver surfaces:

1. Prove the MCP server end to end with a real Claude Code session.
2. Exercise the agent status bar (waiting banner, Snooze, scene pill cues).
3. Screensaver layout editor: a per-widget "x" that disables the widget
   (the Settings toggle must follow) - a second way to turn a widget off.
4. AI-coding templates (except Claude Code / Cursor, which are final) must
   expose the proper action buttons.
5. Every app template should carry at least 8 common functional buttons.
6. / 9. Audit the agent hook mechanism; give every agent that *can* be hooked
   a hook (and test it).
7. "What is Trigger - a scheduler? If so remove it."
8. Auto-focus: when an agent goes idle / asks for permission, the deck must
   put that agent's scene in front.
10. / 11. Test auto scene switching and app scanning (Spotify integration + a
   scene linked to it).
12. Upgrade `Vdock-final.mp4` (spectrum visualizer, no visible jumps at
   screen changes, LinkedIn-ready).
13. Research developer-facing features worth adding.

## Findings before coding

- **Triggers is not a scheduler.** `services/triggers.py` is the
  event -> action engine: events `time | app_foreground | agent_state |
  webhook`, actions `execute_action | switch_scene | show_notification`.
  It is how "when Cursor goes idle, switch to the Cursor scene" can be done
  declaratively, and how webhooks/CI can poke the deck. Decision: keep it.
- Hooks existed for Claude Code, Cursor and Antigravity only. Codex has a
  documented single `notify` hook (turn complete) in `~/.codex/config.toml`.
  Cline / Kilo Code / Copilot / OpenClaw expose no stable, documented
  user-level lifecycle hook, so they are not hooked (see results).
- Waiting cues (pill ring, banner + Snooze, dock chip) existed, but nothing
  moved focus; only a manual chip tap navigated.
- `ScreenSaver.vue` hid widgets only via the Settings toggles
  (`screensaverWidgets[]` + `screensaverClockEnabled`).

## Design

- **Saver "x"**: in layout-edit mode every widget gets a red corner button.
  It writes the same flags the Settings switches use, so the toggle follows
  immediately. Visibility is a setting, not part of the layout, so it applies
  at once rather than on Save.
- **Auto-focus**: `triggerEvents.ts` listens to `agent_state`. A source that
  *newly* starts waiting (state `permission`, or `ready` on a prompted
  session - identical to the glow/pill definition) navigates to the scene
  whose name contains the source. Guards: first broadcast after load only
  primes, edit mode never navigates, `agentAlertsEnabled` must be on, and a
  new persisted `agentAutoFocusScene` (default on) can switch it off.
- **Codex hook**: `vdock_agent_hook.py --source codex` reads the payload from
  the last argv (Codex's notify convention), maps `agent-turn-complete` ->
  `ready` and carries prompt/reply. `agent_hooks.install_hook('codex')` does a
  text-level TOML merge: prepend a top-level `notify`, never replace a
  foreign one, leave tables untouched, idempotent, backup written.
- **Templates**: append real, verifiable buttons (deep-link URLs, documented
  CLI commands, documented single-chord shortcuts) to every template under
  8 buttons; top up with generic browser actions only when still short.
  `cursor`, `claude-code`, `antigravity` are skipped.

## Implementation Results

**Verified live**

- *MCP + Claude Code*: a real `claude -p` session using a temporary
  `--mcp-config` (global Claude config untouched) discovered the `vdock`
  server, called `get_agent_states`, `list_scenes` and `show_notification`
  (`delivered: true`). Its own hook-reported session showed up as `working`.
- *Hooks*: payloads piped through the real hook script for Claude Code,
  Cursor and Antigravity produced the right states (`working` -> `ready` /
  `permission`) and the permission alert; `hook-status` reports Claude
  installed.
- *Status bar / cues* (browser against the built bundle): Cursor scene bar
  shows the project and "Waiting for your prompt"; off-scene, the Cursor pill
  rings and the "Cursor is waiting for input" bar with Snooze appears.
- *Auto-focus*: posting `working` then `ready` for `cursor` while on the
  Media scene moved the deck to the Cursor scene on its own.
- *Saver x*: clicking the world-clock and clock x buttons removed
  `worldclock` from `screensaverWidgets` and set `screensaverClockEnabled`
  false (values restored afterwards).
- *Spotify*: with app scanning on, `Spotify.exe` appears in Running
  applications; enabling "Integrate" stored `{appExe: spotify.exe, enabled}`,
  "Create Scene" produced a linked "Spotify" scene, which was then filled with
  the transport / volume / now-playing buttons. MCP `get_now_playing` reads
  the Spotify session (title, artist, source app).

**Code changes**

- `ScreenSaver.vue`: `removeWidget()`, `.ss-remove` x on all 7 widgets.
- `SettingsView.vue`: layout editor `<Teleport to="body">` (it rendered inside
  a 3000px-tall ancestor so widgets landed off-screen); Codex hook target;
  "Jump to the agent's scene" switch.
- `services/triggerEvents.ts`: `agent_state` auto-focus.
  `stores/settings.ts` + `routes/user_settings.py` allowlist +
  `test_user_settings_payload_keys.py`: `agentAutoFocusScene`.
- `scripts/vdock_agent_hook.py`, `integrations/agent_hooks.py`,
  `agent_state.py`, `services/triggers.py`, `TriggersPanel.vue`,
  `agentAlerts.ts`: Codex source + installer.
- `data/appTemplates.ts`: every template now has >= 8 buttons (Cline 10,
  Copilot 10, Kilo Code 8, Codex 9, OpenClaw 8, ...); Cursor / Claude Code /
  Antigravity untouched.
- `api/client.ts`: the auto-switch poller's 404 ("no foreground window") no
  longer raises a "Not Found" toast.
- Tests: `agent-auto-focus`, `auto-scene-switcher` (frontend); Codex hook +
  installer cases in `test_agent_state_events.py`. Full suites green
  (frontend 585+ tests, backend 1124+).

**Not verified / limits (be honest)**

- *Live foreground-based auto scene switching* could not be exercised: this
  session has no foreground window (`GetForegroundWindow()` = 0, lock screen
  running), so `/app-monitor/current-app` correctly 404s. The switch logic is
  covered by a unit test only. Please retest once at the desk.
- The running backend process was not restarted, so the new Codex hook
  endpoint / `agentAutoFocusScene` persistence need a backend restart to take
  effect (frontend `dist` is rebuilt).
- Cline, Kilo Code, GitHub Copilot, OpenClaw: no documented hook surface, so
  no hook. Their "waiting" state can still be reached by a webhook trigger.
- Multi-chord shortcuts are avoided in templates (the hotkey action sends one
  chord); the Kilo Code "Add Context" chord was dropped for that reason.
- Mobile / narrow viewports force clock + weather + world-clock on, so the x
  there flips the setting without hiding the widget.
- The agent Install-hook text under Settings still describes JSON files;
  Codex's TOML is covered by the path shown next to the dropdown.

**Video (`Downloads`)**: `Vdock-final-v2.mp4` (1920x1080, 64.4 s, same
audio) - the 9 hard cuts (4, 9.4, 16.6, 21.8, 28, 33.2, 39, 47, 53.6 s) are
now 0.5 s dissolves that hold the outgoing frame, so nothing shifts against
the soundtrack; scene-detection finds no remaining cuts. An audio-reactive
CQT spectrum band runs along the bottom. `Vdock-linkedin-4x5.mp4`
(1080x1350): blurred full-bleed backdrop, headline "Your spare screen, a
developer control deck.", framed video, large spectrum band, URL footer.
The original is untouched.

## Research: what would make VDock more useful to developers

Existing research (`FEATURE-RESEARCH.html`, `competitive-analysis.md`) already
shipped now-playing, notifications, timers, system stats, scene scheduling,
MCP and triggers. External survey of what developer Stream Deck setups use
(GitHub Utilities: Actions run status, PR/issue counters, review queue,
workflow dispatch; Docker: container/stack start-stop with live status;
Home Assistant: live entity state with templated labels) shows the gap is
**live status buttons**, not more launchers. Ranked by value / fit with the
existing `metric_action`, `http_request`, `buttonState`, triggers and
agent-state plumbing:

1. **CI / PR status buttons** (GitHub Actions run state, open PR count,
   review-requested count). A button whose colour is the build state and that
   opens the failing run on press. Feeds the waiting glow when CI fails.
   Mostly an `http_request` poller + `buttonState` badge.
2. **Multi-agent mission control**: one scene listing every hooked session
   (project, state, last reply snippet, time idle), tap to focus that
   session's window. Builds directly on `agent_state` + `agent-sessions`.
3. **Docker / Compose status + start/stop** with live state and a log-tail
   popover (CLI based, no new dependency).
4. **Git context buttons** that follow the focused repo: branch name, ahead /
   behind, dirty count; one-tap stash / pull / push / open PR.
5. **Port & dev-server panel**: detect listening dev ports, show up/down,
   one-tap restart or open in browser.
6. **Agent approval inbox**: queue of pending permission prompts across
   agents with Approve / Deny; optional auto-approve rules per project.
7. **Focus / meeting mode**: one button mutes notifications, starts a
   timer, switches the scene, sets Slack/Teams status (via webhook).
8. **Pomodoro tied to agent runs**: nudge a break while a long agent run is
   `working`; alert when it finishes.
9. **Env / cloud shortcuts**: AWS profile / kube-context switcher with a
   visible "prod" warning colour.
10. **Shareable scene packs** (JSON import / export + community gallery) so
    teams can distribute a standard "repo cockpit" scene.

Recommended order: 1, 2, 6 (they reinforce the agent-control story that
differentiates VDock), then 3-5.

### Follow-up: auto-switch case mismatch

User retest with Spotify focused did not switch scenes. Cause: the integration stored `spotify.exe` while the foreground-window API reports the exe with its on-disk casing (`Spotify.exe`), and `autoSceneSwitcher` compared with `===`. Fix: case-insensitive exe match in `handleAppChange` and `findSceneForApp`; regression test added. My earlier unit test only used lowercase names, which is why it passed.

### Follow-up: integrations + auto-switch now sync via server settings

Second retest still failed. Root cause: `appIntegrations` and `autoSceneSwitching` lived only in each window's localStorage; I had configured them in the Cursor test browser, so the Electron panel had nothing to match. No other frontend code overrides scene selection (checked `setScene` / app-monitor consumers). Fix: both values are now part of the persisted user settings (`appIntegrations`, `autoSceneSwitching` in the backend allowlist and the settings store payload/apply path); `composables/useAppIntegrations.ts` gained `useAutoSceneSwitching` / `setAutoSceneSwitching`; `App.vue` watches both and enables/disables the switcher live. A server list is only adopted when non-empty so a fresh window never wipes local links. The running backend was restarted and the Spotify link seeded server-side. Still unverified live: an actual foreground change to Spotify in the Electron panel.
