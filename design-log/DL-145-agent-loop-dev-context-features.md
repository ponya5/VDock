# DL-145 - Agent loop, usage meter, dev context buttons, general extras

Follows DL-143 (developer-feature research) and DL-144 (CI/PR widgets,
Mission Control, approval inbox). Five phases, one user review stop after
each. Plan: `docs/superpowers/plans/2026-10-02-dl145-developer-features.md`.

## Problem

VDock can already *see* agent sessions (DL-064/071/144) and type into a
specific one (`editor_base.send(..., cwd=...)`), but the everyday loop
around an agent still happens on the keyboard:

- re-typing the same instructions ("write tests for this", "commit with a
  good message", "explain this error");
- copying an error out of a terminal and pasting it into the agent;
- working out what the agent actually changed when it says "done";
- running the tests to check it;
- noticing too late that a session has burnt through tokens or is about to
  overflow its context;
- checking branch / dirty / ahead-behind state, whether the dev server or
  the compose stack is up.

There is also a set of general requests (window layouts, audio devices,
true mic mute, next meeting, push-to-talk) whose value to a *developer*
deck is uneven and has to be weighed against the complexity they add.

## Simplicity guardrails (binding for every phase)

The user's direction: *intuitive, don't overload VDock, focus on added value
for tech/dev roles.* Concretely:

1. **Zero or one visible config field per action.** Everything else is
   auto-detected: target session (pinned → ready → most recent), repo
   (focused editor → last-known editor repo → most recent agent cwd →
   default), test command (from `package.json` / pytest config / `go.mod` /
   `Cargo.toml`), dev ports (listening sockets + process cwd).
2. **Advanced options are hidden.** `ConfigField.advanced=True` fields render
   inside a collapsed "Advanced" section (existing `Collapse.vue`).
3. **No new top-level settings pages.** The only settings UI added is one
   card for Google Calendar (Phase 5, if kept) inside the existing
   Integrations tab.
4. **Reuse existing surfaces**: Mission Control rows (DL-144), button
   badge/tone/sublabel (`buttonState.markFinished`), widget polling
   (`useWidgetPolling`, generalised not duplicated), the action picker's
   existing `ai` / `dev` / `system` categories, `useConfirm` for gated ops.
5. **Fewer, smarter actions.** One "Agent Prompt" action with a preset
   dropdown instead of N prompt actions (error → agent is a preset). Git,
   Docker and dev-server state are each *one* live button whose press opens
   a small menu, not a row of buttons. Target new user-visible action ids:

   | Phase | New action ids | Count |
   |---|---|---|
   | 1 Agent loop | `agent_prompt`, `agent_review_changes`, `dev_run_tests` | 3 |
   | 2 Usage meter | `agent_usage` | 1 |
   | 3 Dev context | `git_context`, `dev_servers`, `docker_status` | 3 |
   | 4 General | `mic_mute` (+ `window_layout`, `audio_device` only if kept) | 1 (3) |
   | 5 General | `agent_dictate` (+ `calendar_next_meeting` only if kept) | 1 (2) |

   **Recommended total: 9 new ids (12 if every deferred item is kept).**
6. **Every phase's acceptance includes:** a first-time user can add the
   feature from the action picker and use it in under 30 seconds without
   reading docs, and every empty/first-run state has plain, actionable copy
   (no blank faces, no raw errors).

### Value check per feature (and recommendations)

| Feature | Developer value (one line) | Verdict |
|---|---|---|
| Agent Prompt presets | One tap sends a saved instruction to the right session: removes the most repeated typing. | **Build** |
| Error → agent | Clipboard error or last failing test run goes to the agent with a fix instruction. | **Build** (as presets) |
| Review what it did | See files / +/- the agent changed this turn; tap a file to open its diff. | **Build** |
| Test runner | One tap runs the repo's tests; the button face stays red/green. | **Build** (watch mode Advanced, off) |
| Usage / context meter | Spend/tokens today and per session, plus "context 82%, compact soon". | **Build** |
| Git context | Branch, dirty, ahead/behind at a glance; pull/push/stash/PR one tap away. | **Build** |
| Dev-server ports | Which dev servers are up, open/restart them without hunting for the terminal. | **Build** |
| Docker / Compose | Stack status + up/stop + log tail without leaving the editor. | **Build, lowest in Phase 3** (only useful to compose users; zero cost when Docker absent) |
| True mic mute | Real mute state that matches Teams/hardware keys; fixes today's broken WMI path. | **Build** |
| Window layout presets | Arrange editor/browser/terminal in one tap. | **Defer/Cut - recommend.** Windows Snap Layouts / FancyZones already do this; multi-monitor + DPI + maximised-state edge cases make it a large, flaky surface for small gain. |
| Audio device switching | Switch headset/speakers. | **Defer/Cut - recommend.** Needs the undocumented `IPolicyConfig` COM interface on the fragile audio thread (DL-058 history); general-user, not dev value. |
| Google Calendar countdown + Join | Next meeting countdown and one-tap join. | **Defer - recommend.** Real value, but the user must create a Google Cloud OAuth client and VDock must hold a refresh token; highest setup cost of the set for a non-dev feature. Full design kept below in case the user keeps it. |
| Push-to-talk to agent | Hold, speak, text appears in the agent session. | **Build tier A only (Windows voice typing, zero deps); Defer tier B (local Whisper, ~250 MB).** |

**Recommended phase order** (highest developer value first) matches the
user's order with trimming: 1 Agent loop → 2 Usage meter → 3 Git / ports /
Docker → 4 mic mute (layouts + audio devices deferred) → 5 dictate tier A
(calendar + Whisper deferred). The user decides at each review stop. The plan
contains full tasks for every item so a "keep" decision needs no re-planning.

## Shared infrastructure (Phase 1, used by every later phase)

Verified while planning: `ButtonEditor.vue` has hand-written config blocks
per core action type and **does not render catalog `config_fields` for plugin
actions at all** (`config_fields` is referenced only in
`stores/actionCatalog.ts`), so a plugin action's fields (e.g. `cc_prompt`'s
"Text to send") silently keep their defaults. Every new feature here is a
plugin action, so this must be fixed first.

1. **Catalog field metadata** (`backend/actions/catalog.py`):
   `ConfigField.advanced: bool = False`, `ConfigField.show_when:
   Optional[Dict[str, Any]] = None` (render only when another field has that
   value, e.g. `text` only when `preset == 'custom'`). Serialized by `to_dict`
   only when set.
2. **Live-action metadata** on `ActionSpec`: `poll_seconds: int = 0` (>0 makes
   the button a live widget the frontend polls), `poll_config: Mapping = {}`
   (merged into the config on polls, e.g. `{'op': 'status'}` so a poll never
   runs the tests), `press: 'run' | 'menu' = 'run'`.
3. **`CatalogConfigFields.vue`**: generic form for a spec's `config_fields`
   (text, textarea, number, select, boolean, path, url), Advanced collapse,
   `show_when`. Mounted in `ButtonEditor.vue` for action types with no
   hand-written block.
4. **`useWidgetPolling` generalised**: polls any on-screen button whose
   catalog spec has `poll_seconds > 0` (plus the existing `gh_widget_*`
   prefix), merging `poll_config`. One poller, no duplicate.
5. **Press menu** (`LiveActionMenu.vue` + `services/liveActionMenu.ts`): a
   result's `data.menu = [{id, label, icon?, confirm?, danger?}]` and
   optional `data.panel_text` (log tail, failure excerpt) are stored on the
   button's live state. Pressing a `press: 'menu'` button opens a teleported
   sheet with those items (running one `status` poll first if none are
   cached); choosing one dispatches the same action with `config.op =
   item.id`, through `confirmDialog` when `confirm` is set.
6. **`context.focused_repo()`** (`integrations/context.py`): focused editor
   cwd → last editor cwd seen in the last 30 min (VDock's own window and the
   panel browser don't count) → most recent agent session cwd → existing
   `resolve_cwd` fallbacks. Fixes "the repo is whatever VDock's window is"
   when the deck itself has focus.

## Phase 1 - Agent loop

### 1a. Agent Prompt (`agent_prompt`, category `ai`)
- **One visible field:** `preset` (select). Built-ins (backend constant
  `PROMPT_PRESETS`, labels short enough for a button):
  `continue` "Continue", `write_tests` "Write tests for the code you just
  changed.", `explain_error` "Explain this error and fix it:\n{clipboard}",
  `fix_tests` "These tests are failing. Fix them:\n{last_failure}",
  `review` "Review your last change for bugs, edge cases and missing tests.",
  `commit` "Commit the current changes with a clear conventional commit
  message.", `custom` (reveals `text` via `show_when`).
- **Advanced:** `agent` (auto | claude | cursor | devin | antigravity),
  `cwd` (session directory), `submit` (default true).
- **Targeting** (`services/agent_prompt.py resolve_target`): hooked sessions
  from `agent_state.session_entries` for sources that have a
  `prompt_command` in `keymaps.ALL_PROFILES` (claude → `cc_prompt`, cursor
  → `cursor_followup`, devin → `devin_prompt`, antigravity →
  `antigravity_followup`); filter by `agent`/`cwd`; prefer the session whose
  host pid is pinned (DL-071), then `ready` newest, then newest. No hooked
  session → fall back to today's behaviour (`send()` with the focused
  project), which keeps the existing session-alive + foreground guards.
- **Safety:** refuse when the target is in `permission` (typed text would
  answer the prompt) - 409 "waiting for approval, answer it first"; refuse
  when `working` - 409 "busy, try when it's ready". Placeholders expand with
  the *session's* cwd. Text capped at 1,500 chars (keystroke typing is
  ~10 ms/char; stack traces keep their **tail**). Empty clipboard /
  no failure → friendly refusal, nothing typed.
- **Mission Control:** each `ready` row gets a "Prompt" menu with the
  built-in presets → `POST /api/agent-mission/prompt {source, session_id,
  preset | text}` → same service, explicit session, same re-check.

### 1b. Error → agent - decision
Presets `explain_error` (clipboard) and `fix_tests` (`{last_failure}` =
last failed run of VDock's own test runner for that repo). **No terminal
scraping:** Windows Terminal exposes no buffer API, UI Automation text reads
of conhost/WT are fragile, slow and would read arbitrary (possibly secret)
terminal content. The test runner already captures output VDock produced
itself, which is the reliable "last error" source.

### 1c. Review what it did (`agent_review_changes` + Mission Control chip)
- **Baseline decision: per-turn baseline, HEAD fallback.** Diffing vs HEAD
  would count the user's pre-existing uncommitted edits as the agent's and
  miss commits the agent made. On a hook event that carries a *new prompt*
  (turn start), `services/turn_baseline.capture(source, session_id, cwd)`
  runs off-thread: `git rev-parse --show-toplevel`, `git stash create`
  (non-mutating: writes a commit object of index + worktree, no stash entry,
  no file changes; empty output when clean → `git rev-parse HEAD`), and the
  untracked list `git ls-files --others --exclude-standard` (capped 2,000).
  In-memory, keyed `(source, session_id)`. Lost on backend restart → HEAD
  fallback, labelled "since last commit".
- **Changes:** `git diff --numstat <base>` (base vs worktree) + untracked
  files not in the baseline list (lines counted, files >1 MB counted as
  binary). `GET /api/agent-mission/changes?source=&session_id=` →
  `{success, base: {sha, kind: 'turn'|'head'}, repo, files: [{path, added,
  removed, status: 'M'|'A'|'D'|'?'}], totals: {files, added, removed}}`.
- **Open diff:** `POST /api/agent-mission/open-diff {source, session_id,
  path}` → `git show <base>:<path>` to `DATA_DIR/diff-base/<sha12>/<path>`,
  then `<editor> --diff <base copy> <worktree file>` where editor = `cursor`
  when the source is cursor or only Cursor's CLI exists, else `code`
  (`sr.find_binary`); new files open plainly. Paths are validated to stay
  inside the repo root.
- **UI:** Mission Control `ready` rows show "4 files +120 −8"; tapping lists
  files, tapping a file opens its diff. Deck button `agent_review_changes`
  (live, `press: 'menu'`, poll 20 s): badge = files, sublabel "+120 −8",
  menu = files (`op: open:<path>`, max 12) for the most recent `ready`
  session; empty state "No changes this turn".

### 1d. Test runner (`dev_run_tests`, category `dev`)
- **Zero fields.** Detection at the focused repo root, else its immediate
  subdirectories (monorepos like VDock: `frontend/`, `backend/`):
  `package.json` with a real `scripts.test` → `npm test --silent` with
  `CI=1` (forces vitest/jest run mode); pytest markers (`pytest.ini`,
  `[tool.pytest` in `pyproject.toml`, `setup.cfg [tool:pytest]`, `conftest.py`,
  `tests/test_*.py`) → `<dir>/venv|.venv/Scripts/python.exe -m pytest -q`,
  else `python -m pytest -q`; `go.mod` → `go test ./...`; `Cargo.toml` →
  `cargo test`. Advanced: `command` (argv split, never a shell), `watch`
  (bool, default off).
- **Run:** `long_running=True` (job runner), one run per repo at a time,
  15-minute timeout, plans run sequentially. Result `data`: `badge` "✓ 1794"
  / "✕ 3" / "…", `status` success|critical|running, `sublabel` per plan
  ("backend 1163 · frontend 631"), `panel_text` = failure excerpt (tail
  2,000 chars, redacted). Counts are best-effort regex parses (pytest,
  vitest, jest, go, cargo); the exit code is the authority.
- **Live badge without re-running:** `poll_seconds=15`,
  `poll_config={'op': 'status'}` returns the cached last result. Watch mode:
  the status poll fingerprints `git status --porcelain=v1 -z` + changed files'
  mtimes and starts a run when it changed (debounced 5 s) - no new file
  watcher dependency.
- Press = run. Last failure feeds `{last_failure}`.

## Phase 2 - Agent usage / cost meter (`agent_usage`)

**On-disk format, verified on this machine (2026-10-02, Claude Code
2.1.284):** transcripts at `~/.claude/projects/<cwd-slug>/<sessionId>.jsonl`
(slug = cwd with `:` `\` `/` → `-`, e.g. `C--Users-Daniel-CursorRepo-VDock2`),
subagent transcripts at `<cwd-slug>/<sessionId>/subagents/agent-*.jsonl`
(71 such files). 129 files / 117 MB total - full rescans are not acceptable.
- `type: "assistant"` records: `message.id`, `message.model` (e.g.
  `claude-sonnet-5-5`), `message.usage.{input_tokens, output_tokens,
  cache_creation_input_tokens, cache_read_input_tokens,
  cache_creation.{ephemeral_5m_input_tokens, ephemeral_1h_input_tokens}}`,
  `timestamp` (ISO UTC), `sessionId`, `cwd`, `isSidechain`. **The same
  `message.id` is repeated once per content block with identical usage**
  (228 of 299 ids in one file) → dedupe by `message.id`.
- `type: "cost-state"`: `totalCostUSD`, `totalLinesAdded/Removed`,
  `modelUsage.<model>.{inputTokens, outputTokens, cacheReadInputTokens,
  cacheCreationInputTokens, costUSD}`, `hasUnknownModelCost`. Written
  **once, at the end of the file** (session close); present in 38 of the 40
  most recent files, absent in some large ones. So it is authoritative for
  finished sessions only.
- `~/.claude/stats-cache.json` exists but was last computed 2026-02-15 -
  stale, not used.

**Design** (`services/claude_usage.py`):
- Incremental reader: per file cache `(size, mtime, offset, aggregates,
  seen_ids)`; only appended bytes are parsed; partial last line deferred.
  "Today" scans only files with mtime ≥ local midnight; a record counts for
  today by its `timestamp` in local time.
- Session totals = own file + its `subagents/*.jsonl`. Cost = `cost-state`
  when present (exact), else **estimate** from a small per-family price
  table (`opus` / `sonnet` / `haiku`, input / output / cache-write-5m /
  cache-write-1h / cache-read per MTok) flagged `estimate: true` and shown
  as "≈$". Unknown family → tokens only. The executor must re-check current
  list prices at implementation time; subscription users see notional
  spend, which the UI labels "API-equivalent".
- **Context meter** (the high-value bit): last assistant record's
  `input + cache_read + cache_creation` tokens ÷ context window (200k
  default; 1M when the model id says so or the count already exceeds 200k)
  → `context_pct`. ≥80 % warning ("compact soon"), ≥95 % critical.
- Session mapping: the Claude hook posts Claude's own `session_id`, which is
  the JSONL file stem; the file is found by `glob(projects/*/<id>.jsonl)`.
  No hook change.
- `GET /api/agent-usage` → `{success, today: {tokens: {input, output,
  cache_read, cache_write, total}, cost_usd, estimate, sessions},
  sessions: [{session_id, project, model, tokens, cost_usd, estimate,
  context_tokens, context_pct}], limit_usd, status}`.
- **Button `agent_usage`** (live, poll 60 s): badge "$4.20" (or "1.2M"),
  sublabel "today", tone warning ≥80 % / critical ≥100 % of the one visible
  field `daily_limit_usd` (0 = no limit). Advanced: `metric` (cost | tokens).
  Press opens Mission Control. Empty state: "No Claude Code usage today".
- **Mission Control:** Claude rows get "≈$1.24 · ctx 72%" (amber/red at the
  thresholds); a red context chip offers the existing `cc_compact`.
- Claude Code only. Cursor/Devin/Antigravity keep no comparable local
  usage; Codex (`~/.codex/sessions`) is future work.

## Phase 3 - Dev context buttons

All three: live, `press: 'menu'`, repo = `context.focused_repo()`, Advanced
`cwd` override, gated ops use `confirm`, subprocess via `sr.run` (argv, no
shell, timeouts), output `secrets.redact`ed.

### 3a. Git context (`git_context`, poll 30 s)
- One call: `git status --porcelain=v2 --branch` → branch, upstream,
  ahead/behind (`# branch.ab +A -B`), dirty count, conflict entries (`u`
  lines); `.git/MERGE_HEAD` / `rebase-merge` → in-progress.
- Face: badge = dirty count or "✓"; sublabel "main ↑2 ↓1"; tone warning when
  behind or dirty+ahead, critical on conflicts / merge or rebase in progress.
  Ahead/behind reflect the last fetch (no network on polls).
- Menu: Pull (`git pull --ff-only`), Push (confirm; `git push`, or
  `git push -u origin HEAD` with no upstream), Stash (confirm; `git stash
  push -u -m "VDock <time>"`), Pop stash (only when a stash exists), Open PR
  (`gh pr view --web`, else `gh pr create --web`; hidden without gh). No
  force-push, no reset - ever.
- Empty state: "Not a git repository - focus a project in your editor".

### 3b. Dev servers (`dev_servers`, poll 10 s)
- `psutil.net_connections('inet')` LISTEN sockets on loopback / any, port
  ≥1024, owned by a dev runtime (`node`, `python`, `bun`, `deno`, `java`,
  `dotnet`, `ruby`, `php`, `go`-built binaries in the repo, `uvicorn`...),
  excluding VDock's own backend and dev-server ports. `Process.cwd()` /
  `cmdline()` map each to a repo; focused-repo servers listed first.
- **Known servers:** the first sighting records `(port, cmdline, cwd)` per
  repo in memory, so a server that dies shows as **down** with Start.
- Face: badge = running count, sublabel ":5173 :8000", tone warning when a
  known server is down. Menu per server: Open (browser via the existing
  `url` action), Restart (confirm; kill tree then `sr.spawn(cmdline, cwd)`),
  Stop (confirm), Start (down + known). Empty state: "No dev servers
  running".
- Access-denied processes (other users/services) are skipped silently.

### 3c. Docker / Compose (`docker_status`, poll 20 s)
- CLI only (`docker` on PATH - present on this machine). Compose file in the
  focused repo (`compose.y[a]ml`, `docker-compose.y[a]ml`) → `docker compose
  ps --all --format json` (JSON array or one object per line - parse both);
  otherwise `docker ps --format json` (running containers).
- Face: badge "3/4", tone warning when partially up; daemon down (`docker
  info` fails) → badge "–", sublabel "Docker not running" (normal tone, not
  an error). Not installed → `unavailable_reason` in the picker.
- Menu: Up (`docker compose up -d`), Stop (confirm; `docker compose stop` -
  never `down`/`rm`/volume removal), Restart <service>, Logs <service> →
  `docker compose logs --tail 80 --no-color <svc>` into `panel_text`.

## Phase 4 - General

### 4a. True mic mute (`mic_mute`, category `system`, poll 3 s) - Build
- Default capture endpoint via `pycaw.AudioUtilities.GetMicrophone()` →
  `IAudioEndpointVolume.GetMute/SetMute`, **on the existing audio COM
  thread** (`cross_platform_action._run_on_audio_thread`), QueryInterface
  ownership as DL-058 requires. Tap toggles; poll reflects mutes made by
  Teams/Zoom/hardware keys. Face: "MUTED" red (critical) / "LIVE" normal.
- The existing Windows `microphone_mute` / `microphone_unmute` path
  (nircmd or WMI `Win32_SoundDevice.Disable()`, which disables the device
  and needs admin) is switched to the same endpoint mute; ids unchanged.
- No microphone → "No microphone found".

### 4b. Window layout presets (`window_layout`) - Defer/Cut, recommend
If kept: one action, `press: 'menu'`; menu = saved layouts + "Save current
layout". Capture = visible top-level windows of known dev apps (editors,
browsers, terminals) with monitor-relative rects + maximised flag, stored
in `DATA_DIR/window_layouts.json`; apply = match by exe (+title hint),
restore then `SetWindowPos` (per-monitor-DPI aware). Risks: DPI scaling,
monitor changes, elevated windows refusing moves, UWP frames.

### 4c. Audio device switching (`audio_device`) - Defer/Cut, recommend
If kept: menu lists active render/capture endpoints; select sets default
for all roles via `IPolicyConfig::SetDefaultEndpoint` (undocumented,
declared with comtypes; pycaw 20240210 in the venv has no wrapper -
verified) on the audio thread, then invalidates the cached endpoint
(DL-058) and nudges `volume_monitor`.

## Phase 5 - General

### 5a. Push-to-talk to the agent (`agent_dictate`)
- **Tier A - Build: Windows voice typing.** Hold (existing `trigger:
  'press'` + `release_action` mechanism in `DeckButton.vue`): resolve the
  target session as Agent Prompt does, refuse in `permission`, focus its
  window with the existing guards, send `Win+H`; release sends `Win+H` again
  (stops listening). Text lands in the session's input; **never
  auto-submitted** - the user taps Submit/Continue after reading it. Zero
  dependencies. Requires Windows 11 voice typing (uses Microsoft's online
  speech service unless the user's language pack supports on-device) -
  stated in the action description.
- **Tier B - Defer, recommend: local Whisper.** `faster-whisper` (wheels:
  ctranslate2 ~35 MB, onnxruntime ~12 MB for VAD, av ~30 MB, tokenizers) +
  `base.en` int8 model ~145 MB → roughly **250 MB** total; capture via the
  already-installed `soundcard` + `numpy`; transcribe on release (~1-2 s for
  10 s audio on CPU), type via the agent's prompt command with
  `submit=False`. Lazy import; missing package → falls back to tier A with
  a hint. Fully offline, but large.

### 5b. Google Calendar next meeting (`calendar_next_meeting`) - Defer, recommend
If kept:
- **User prerequisite:** create a Google Cloud project, enable the Calendar
  API, configure the OAuth consent screen (External, Testing, add yourself
  as test user), create an OAuth client of type **Desktop app**, copy client
  id + secret.
- **Auth:** installed-app flow with PKCE and a loopback redirect
  `http://127.0.0.1:<backend port>/api/calendar/google/callback`, scope
  `https://www.googleapis.com/auth/calendar.events.readonly`, `state`
  nonce, `access_type=offline`, `prompt=consent`. Plain `requests` against
  `oauth2.googleapis.com/token` and Calendar v3 - no Google SDK.
- **Storage:** client id/secret in `backend/.env` (`GOOGLE_OAUTH_CLIENT_ID`,
  `GOOGLE_OAUTH_CLIENT_SECRET`) via `config.write_env_keys`, declared as
  `SecretSpec`s in `services/secrets.py` (`ALL_SECRETS` → redacted). Refresh
  token in `DATA_DIR/google_oauth.json` encrypted with Windows DPAPI
  (`win32crypt.CryptProtectData`, pywin32 already a dependency); access
  token memory-only; both registered with `register_runtime_secret`.
  Disconnect deletes the file and calls the revoke endpoint.
- **UI:** one "Google Calendar" card in Integrations > Apps & scenes:
  three numbered steps with a link to the Cloud console, two paste fields,
  Connect (opens the consent URL in the host browser) / Disconnect, status
  line. Button face (poll 60 s): badge "12m", sublabel meeting title, tone
  warning ≤5 min, critical once started; press opens `hangoutLink` /
  `conferenceData.entryPoints[video].uri`, or a Zoom/Teams/Meet URL found in
  location/description; none → opens the event's `htmlLink`. Empty states:
  "Connect Google Calendar in Settings > Integrations", "No more meetings
  today".

## Cross-cutting decisions

- New plugin packs (scanned automatically as `*_pack.py`):
  `integrations/agent_loop_pack.py` (agent_prompt, agent_review_changes,
  agent_usage, agent_dictate) and `integrations/dev_tools_pack.py`
  (dev_run_tests, git_context, dev_servers, docker_status). Logic lives in
  `services/*` modules so routes, packs, MCP and triggers share it. Pack
  action types are not in the `ActionType` enum, like the GitHub pack.
- Mission Control stays the one agent surface: Prompt menu, change chip,
  usage/context chip all go on existing rows.
- No new Python/npm dependencies in Phases 1-4 or 5a. Only deferred 5a tier
  B adds one (faster-whisper).
- All keystroke features route through `editor_base.send` (window resolved,
  focused, foreground verified) after a server-side session-state re-check.
- Polling over pushed socket events for button faces, consistent with
  `job_runner`'s documented finding that background-thread emits do not
  reach clients on this stack.

## Risks / unknowns (executor must re-verify on disk)

- Transcript format can change with Claude Code versions - re-run the
  format probe in the plan before Phase 2; parse defensively (unknown
  record types ignored).
- `cost-state` may stop being end-of-file only; the reader handles any
  position (latest wins).
- `git stash create` ignores untracked files - handled by the untracked
  list; renames show as delete + add.
- Keystroke typing speed caps prompt length (1,500 chars).
- `psutil.net_connections` may hide pids of other users' processes on
  Windows without elevation - those servers are skipped.
- Windows voice typing availability/language varies per machine.
- Socket push from background threads is unreliable (see `job_runner.py`);
  faces poll.

## Out of scope

- **Auto-approve rules** for agent permissions - deliberately rejected for
  safety (as in DL-144). Nothing here answers a permission prompt.
- Terminal-buffer scraping; usage meters for non-Claude agents; Docker
  `down`/prune/volume removal; git force-push/reset; a prompt-library
  settings page (custom prompts live on the button).

## Implementation Results

### User decisions (recorded at Phase 1 start)

- **Deferred, never built in any phase:** window layout presets, audio device switching, Google Calendar, local Whisper STT. Push-to-talk (Phase 5) uses Windows voice typing only.
- **Guideline:** features stay intuitive - one visible config field (or none) per action by default, advanced options collapsed, existing surfaces reused, developer value first.
- **Repo/secrets rule:** keys and tokens an integration needs live only in `backend/.env` (documented in `backend/.env.example`, redacted via `services/secrets.py`), never in `config.json`, user settings, or API responses.

### Phase 1 - Agent loop

**Status:** implemented and verified. **Env vars added: none** (no integration in this phase needs a key; `backend/.env.example` is unchanged).

**New actions**
- `agent_prompt` (AI Assistants) - types a preset or custom prompt into the ready agent session. One visible field, "Prompt" (Continue, Write tests, Fix this error, Fix failing tests, Review your change, Commit, Custom...). "Custom prompt" appears only for Custom; Agent, Session directory and "Press Enter after typing" sit under a collapsed Advanced section.
- `agent_review_changes` (AI Assistants) - live button; the badge shows what the agent changed this turn, press opens a menu of files and tapping a file opens its diff.
- `dev_run_tests` (Developer) - detects npm/pytest/go/cargo (monorepo subfolders included), runs them, face shows pass/fail counts; optional "re-run when files change" and a test command override under Advanced.

**Built**
- Backend: `services/agent_prompt.py` (presets, target resolution, safe send through `editor_base.send`; `submit=False` unless the user opted in), `services/turn_baseline.py` (per-turn non-mutating `git stash create` baseline, numstat diff, open-diff), `services/test_runner.py`, `integrations/live_pack_base.py` (shared live-result helper), `integrations/agent_loop_pack.py`, `integrations/dev_tools_pack.py`; `context.focused_repo()` (configured, focused editor, last editor within 30 min, newest agent session cwd); catalog metadata (`advanced`, `show_when`, `poll_seconds`, `poll_config`, `press`); `status` ops skip the job runner; Mission Control API gained `can_prompt`, `presets`, `POST /api/agent-mission/prompt`, `GET /api/agent-mission/changes`, `POST /api/agent-mission/open-diff`; agent events capture the baseline on a prompt and forget it on `ended`.
- Frontend: `CatalogConfigFields.vue` + `CatalogField.vue` (generic catalog form, mounted in `ButtonEditor.vue`), `liveActionMenu.ts` + `LiveActionMenu.vue` (press menu sheet), generalised `useWidgetPolling` (polls any catalog spec with `poll_seconds`), `buttonState` menu/panel text and success tone, Mission Control Prompt menu (inline presets, errors shown verbatim incl. 409) and "N files +a -r" changes chip with tap-to-diff.

**Deviations from the plan**
- The generic form is two components (`CatalogConfigFields` + `CatalogField`) because scoped styles do not reach a child field and one file would have mixed layout with per-type inputs.
- `ButtonEditor.vue` uses a deny-list of action types that already have hand-written blocks. Static types with no hand-written block (`ui_control`, `goto_page`, `switch_scene`, `http_request`, `obs_*`, `random`) now also get the generated form for their simple field types (text/select/number/boolean/path/url); `keys` and `steps` field types are skipped. Not visually reviewed for those types.
- `focused_repo` learns the foreground editor through the app-monitor singleton and `current_editor()` (the monitor only runs while the frontend polls and only fires on exe change).
- A menu-item run that returns no badge refreshes the button face with a status poll so it does not blank the badge.
- `MissionSession.can_prompt` is required in the TS type (test fixtures updated).

**Tests (before -> after)**
- Backend: 1163 -> 1262 passed (new: catalog live meta, focused repo, agent prompt, turn baseline, mission changes routes, agent-loop pack, test runner, dev-tools pack).
- Frontend: 631 -> 664 passed; `vue-tsc --noEmit` clean. New/extended: `catalog-config-fields`, `live-action-menu`, `widget-polling`, `button-state`, `mission-control`. The 664 also includes a test file added concurrently by another change (`agent-brand`).

**Live verification** (backend restarted on :5000, `npm run build`, browser at http://127.0.0.1:5000, simulated sessions only)
- `/api/actions/catalog` lists `agent_prompt`, `agent_review_changes` (poll 20 s, menu press), `dev_run_tests` (poll 15 s).
- Action picker: searching "agent prompt" shows one entry under AI Assistants; selecting it opens the editor with exactly one visible field ("Prompt"), Advanced collapsed. Choosing Custom shows "Custom prompt" with its variable hint; Advanced expands to Agent, Session directory, Press Enter. Add-and-configure took four interactions (search, tap, ready to save), well under 30 s. Editor cancelled, nothing saved to the profile.
- Mission Control with simulated sessions (fake ids, ended afterwards): Prompt button on ready rows only, preset list renders, changes chip showed "9 files +634 −58" and expanded to a tappable file list.
- Empty states confirmed via the action API: "No agent session yet" (Review Changes), "No tests found in Temp - set a test command under Advanced" (Run Tests).
- Live check found and fixed a real bug: `fetchSessionChanges` passed `{params}` to a client wrapper that already wraps the query object (request 404'd); test now asserts the call shape.
- Screenshots: `C:\Users\Daniel\AppData\Local\Temp\cursor\screenshots\page-2026-10-02T21-37-27-900Z.png` (Mission Control), `...page-2026-10-02T21-39-41-992Z.png` (editor, one field), `...page-2026-10-02T21-39-56-090Z.png` (Custom + Advanced).

**Known limits**
- No keystroke was sent to a real agent window by design; `agent_prompt` send and preset posts were verified by unit tests and mocks only, and not against a real Claude/Cursor session.
- `dev_run_tests` carries `menu` data in its status face but its press is `run`, so that menu is unreachable today.
- Pinned-host sessions get only a basic safety check (`_pinned_risk` in `services/agent_prompt.py`); not exercised live.
- `sr.spawn` may flash a console window when tests start on Windows.
- The press-menu sheet (`LiveActionMenu`) was verified by unit test, not by pressing a placed Review Changes button; the changes chip counts every uncommitted edit in the repo since the turn started, including edits by other tools.
- Browser console was not captured as a log; no errors surfaced during the exercised flows.

### Phase 2 - Agent usage / cost meter
_Not started._

### Phase 3 - Git context, dev servers, Docker
_Not started._

### Phase 4 - Mic mute (+ layouts / audio devices if kept)
_Not started._

### Phase 5 - Push-to-talk (+ Google Calendar if kept)
_Not started._
