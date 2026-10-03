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

**Status:** implemented and verified. **Env vars added: none** (`backend/.env.example` unchanged; `CLAUDE_CONFIG_DIR` support was tried and dropped because it would be a new documented variable and the hook installer ignores it too).

**New action:** `agent_usage` (AI Assistants) - live button, polled every 60 s. Face: today's estimated spend ("≈$4.20", or tokens such as "850k" via Advanced "Show"), sublabel "today". One visible field, "Daily budget (USD)" (0 = no colour); amber at 80 %, red at 100 %. Tapping it opens Mission Control. Empty state: "No Claude Code usage today" with a `$0` face.

**Built**
- `services/claude_usage.py`: incremental transcript reader (per-file offset/size/mtime cache, partial last line deferred, a final complete line without `\n` accepted, re-read from 0 when a file shrinks or the day changes), cost estimate, context %, per-session and today totals. In-memory only, so no persisted cache and no atomic-write use.
- `routes/agent_usage.py`: `GET /api/agent-usage?limit_usd=` (today, live Claude sessions, limit status). `GET /api/agent-mission` rows gained `usage {cost_usd, estimate, context_pct, status}` for Claude rows (guarded - a bad transcript yields `null`, never a 500).
- `POST /api/agent-mission/compact {source, session_id}`: types only `/compact`, Claude only, via `send_prompt` so a `permission`/`working` session is refused (409) and nothing is typed.
- Frontend: Mission Control usage chip ("≈$1.24 · ctx 72%", amber/red from the server status, tooltip states estimate vs reported), a Compact button shown only when context is warning/critical, and `useButtonActions` opens Mission Control when a result carries `open_mission_control`.

**Verified on-disk format (Claude Code 2.1.x, this machine, read-only)** - matches the design: `assistant.message.{id, model, usage.{input,output,cache_read_input,cache_creation_input}_tokens}` plus `usage.cache_creation.{ephemeral_5m,ephemeral_1h}_input_tokens`, UTC `timestamp`, `sessionId` == file stem; repeated `message.id` (dedupe confirmed: 512 unique of 1026 records in one file); `cost-state.totalCostUSD` once at file end; subagent files under `<slug>/<id>/subagents/`. Differences found: `<synthetic>` assistant records exist (ignored); transcripts record plain `claude-opus-5` while `cost-state.modelUsage` names `claude-opus-5[1m]` (so the `[1m]` window hint never reaches the reader - only the "> 200k tokens" rule can detect a 1M window); `cost-state` can sit mid-file in resumed sessions.

**Deviations from the plan**
- Prices are matched by ordered substring per model version, not by family: Opus 5.5 ($4/$20), Opus 5/4.5-4.8 ($5/$25), Opus 4/4.1 ($15/$75), Sonnet 5 and 5.5 ($2/$10), Sonnet 4.x ($3/$15), Haiku ($1/$5); a single "opus" row would misprice by up to 25 %. Source: platform.claude.com pricing page, checked 2026-10-03. The 5-minute vs 1-hour cache-write split from the transcript is used (not a flat 5m rate).
- A `cost-state` counts as exact only while it is still the last usage record in the file (a resumed session keeps writing after an old one).
- The Compact verb is its own route (`/compact`), not a generic `/command` with an allowlist: it can only ever type `/compact`.
- Pack action `agent_usage` shares the `agent_loop_pack` (pack requires pynput like its siblings, although this action does not type).

**Tests (before -> after)**: backend 1354 -> 1414 passed (new: `test_claude_usage`, `test_agent_usage_route`, usage cases in `test_agent_loop_pack`); frontend 666 -> 674 (usage chip/compact in `mission-control`, press-opens-Mission-Control in `widget-press-opens-url`). `vue-tsc` clean, `npm run build` ok, `scripts/check.ps1` all PASS.

**Accuracy: exact vs estimated** - cost is exact only for a finished session whose `cost-state` is last in the file; live sessions and "today" are always estimates (API list prices; subscription plans are not billed per token). Cross-checked against Claude's own `cost-state` on the 8 largest finished sessions: 5 within ~5 % (e.g. 26.82 vs 25.86, 7.28 vs 7.15), 3 not: 61.97 exact vs 157.50 estimated (the transcript holds ~3x the cache-read tokens `cost-state` counted, probably because `cost-state` covers only the last run of a resumed session), 32.31 vs 23.96 and 11.14 vs 10.48 (cost-state larger, e.g. work not persisted in subagent files). So "≈" figures can be far off for resumed or subagent-heavy sessions; the number is a sanity gauge, not an invoice. Today's spend matched an independent probe over the same day (0.10 / 104,251 tokens on 2026-10-02, identical). Context % assumes a 200k window unless the count exceeds 200k, so a 1M-window session below 200k shows an inflated percentage.

**Live verification** (backend restarted, `npm run build`, http://127.0.0.1:5000, simulated sessions with real transcript ids as read-only data sources, all ended afterwards)
- `GET /api/agent-usage` and the catalog respond; `agent_usage` listed (poll 60 s, press run). Cold read of all 147 transcripts (about 117 MB): 0.55 s; warm: 0.011 s; cold `/api/agent-usage` for the empty day: 45 ms.
- Picker: searching "agent usage" lists one entry under AI Assistants; opening it shows exactly one visible field ("Daily budget (USD)") with Advanced collapsed - two interactions from search to a configured button, well under 30 s. Placed button face showed `$0` / "today" (no Claude usage after midnight); pressing it opened Mission Control.
- Mission Control with two simulated Claude rows and one Cursor row: the finished session showed "$0.10 · ctx 18%" (no ≈), the live one "≈$20 · ctx 77%", the Cursor row no chip.
- Budget colouring (synthetic transcript in a temp home, no real data): limit 0/10 -> normal, 4.5 -> warning, 4 -> critical against a ≈$4.00 day. No real session reached 80 % context, so the amber/red chip and the Compact button were verified by unit tests only; Compact was never pressed against a real window.
- Screenshots: `C:\Users\Daniel\AppData\Local\Temp\cursor\screenshots\page-2026-10-02T22-54-33-592Z.png` (editor, one field), `...page-2026-10-02T22-55-32-444Z.png` (button face), `...page-2026-10-02T22-56-46-938Z.png` (Mission Control chips).

**Mistake and cleanup:** clicking a picker entry in edit mode adds the button to the profile immediately and Cancel does not remove it. The live check therefore saved an "Agent Usage" button into the user's real `My VDock` profile; it was removed again by hand (profile JSON re-validated, no `agent_usage` left). The `Agent Prompt` button already in that profile has the same origin (Phase 1 live check) and was left in place.

**Known limits**
- Claude Code only; Cursor/Devin/Antigravity rows have no chip.
- Browser console output was not captured as a log; no errors surfaced during the exercised flows.
- The first scan after a backend restart re-reads transcripts (0.55 s for everything here; scales with transcript size).

### Phase 3 - Git context, dev servers, Docker

**Status:** implemented and verified. **Env vars added: none** (`backend/.env.example` unchanged). **Docker was not available on this machine** (Docker Desktop installed, daemon not running), so the "Docker not running" state was verified live and everything else by mocked unit tests only.

**New actions** (all in the existing `dev_tools_pack`, category Developer, live, `press: 'menu'`, no visible config field; Project directory under Advanced)
- `git_context` "Git Branch" (poll 30 s) - badge = changed-file count or a tick, sublabel `main ↑2 ↓1`; amber when behind or dirty+ahead, red on conflicts or a merge/rebase in progress. Menu: Pull (fast-forward only), Push (asks first; sets upstream when none), Stash changes (asks first, only when dirty), Pop stash (only when a stash exists), Open pull request (only with `gh`). Empty state: "Not a git repository - focus a project in your editor".
- `dev_servers` "Dev Servers" (poll 10 s) - badge = servers running, sublabel `:5173 :8000`; amber when a server seen earlier is gone (it then offers Start). Menu per server: Open, Restart (asks), Stop (asks). Empty state: "No dev servers running".
- `docker_status` "Docker Containers" (poll 20 s) - badge `2/3`, amber when partly up. Compose project: Start stack, Stop stack (asks), Restart and Logs per service; otherwise Logs per running container. Daemon down: badge "–", "Docker isn't running - start Docker Desktop" (normal tone, not an error). Picker greys it out with "Docker CLI not found - install Docker Desktop" when the CLI is missing.

**Built**
- `services/git_context.py`, `services/dev_servers.py`, `services/docker_status.py`; the pack dispatches `config.op` (default `status`) to each service's `status(repo)` / `run_op(repo, op)`. The repo is `context.focused_repo()`; git ops re-resolve `git rev-parse --show-toplevel` so only a real repository is ever acted on.
- Safety: argv lists only; no force/reset/clean/rebase/checkout/`down`/`rm`/`prune`/`-v` can be built (asserted over every argv in tests); Docker service and container names are accepted only if they appear in the CLI's own `ps` output; dev-server ops address a port that must be in a fresh scan (pid and command line never come from the request); command output goes through `secrets.redact`.
- Frontend: no new component. One fix to `openLiveMenu`: an empty cached menu is re-fetched so the backend's plain-language empty state shows in the sheet (previously only "Nothing to show right now."). Test added.

**Deviations from the plan**
- Labels are "Git Branch" and "Docker Containers", not "Git Status" / "Docker": the picker already has a generated "Git Status" template (types `git status` into a terminal) and a "Docker" app launcher, and the live check showed picking by name grabbed the wrong one. Search keywords still include "git status" and "docker".
- Down-server memory is per backend run and never forgets a server the user stopped on purpose; it clears on backend restart.
- Dev-runtime allow-list is process names only (`node`, `python`, `pythonw`, `bun`, `deno`, `java`, `dotnet`, `ruby`, `php`, `uvicorn`, `gunicorn`, with `.exe`); `go`-built binaries are not detected.
- VDock's own ports (backend `Config.PORT`, panel frontend port) are excluded by importing `routes.system._configured_frontend_port`; a service importing a route helper is a small layering compromise, guarded by try/except.
- Restart/Start use `sr.spawn`, which opens the server in its own console window on Windows.
- `docker compose ps --format json` shape could not be sampled (daemon down); the parser accepts both a JSON array and one object per line, and fixtures use Compose v2's field names (`Name`, `Service`, `State`).

**Tests (before -> after)**: backend 1414 -> 1477 passed (new: `test_git_context`, `test_dev_servers`, `test_docker_status`, pack cases in `test_dev_tools_pack`); frontend 674 -> 675 (`live-action-menu`). `vue-tsc` clean, `npm run build` ok, `scripts/check.ps1` all PASS.

**Live verification** (backend restarted on :5000, built bundle, http://127.0.0.1:5000, throwaway profile; read-only commands only)
- Catalog lists the three actions with poll 30/10/20 s and `press: menu`. Status calls against the real repo: git 126 ms (branch `main`, 69 changed files then 71 as work continued, no stash, `gh` menu item present), dev servers 47 ms (none), docker 261 ms ("Docker not running").
- Placed from the picker into a throwaway profile (searching, tapping the entry, Save: three interactions each, well under 30 s). Faces painted by polling: `Git Branch | main | 69`, `Dev Servers | none running | 0`, `Docker Containers | Docker not running | –`. The Git press menu listed Pull, Push, Stash changes, Open pull request; Pull/Push/Stash were not pressed.
- Empty-state sheets after the fix: "No dev servers running", "Docker isn't running - start Docker Desktop". No console errors or unhandled rejections captured during these flows.
- Screenshot: `C:\Users\Daniel\AppData\Local\Temp\cursor\screenshots\page-2026-10-02T23-17-50-765Z.png` (faces plus Git menu).
- Cleanup: the stray "Agent Prompt" button was removed from `My VDock` (single entry, file re-validated, API load fine, no `agent_prompt` left). Live checks used a throwaway profile, since deleted; the active profile was switched to it and restored to `My VDock`. Mistaken picks (a generated "Git Status" and the "Docker" launcher) were only ever in the throwaway profile.

**Not verified live / known limits**
- Docker with a running daemon (compose "2/2", logs panel, Stop confirmation): mocked tests only.
- Dev server Open/Restart/Stop/Start and its non-empty list: no scratch server was started (verification was read-only); covered by mocked psutil tests, including the stop-then-spawn order.
- Pull, Push, Stash, Pop and Open pull request were never run against the real repo. The confirmation text is covered by tests; the confirm dialog itself was not exercised in a browser.
- Focused-repo switching when the editor changes was not exercised.

### Phase 4 - True mic mute

**Status:** implemented and verified. **Env vars added: none.** Window layouts (4b) and audio device switching (4c) stay deferred per the user's decision.

**New action:** `mic_mute` "Mic Mute" (System) - live button, polled every 3 s, no config fields at all. Face: `LIVE` (normal) or `MUTED` (red) with sublabel "Microphone"; tapping toggles. It follows mutes made in Windows Settings, Teams, Zoom or a hardware key. No microphone: the poll paints a `!` face with "No microphone found"; a press shows the same as an error. Off Windows the picker greys it out.

**Changed (no new id):** `microphone_mute` / `microphone_unmute` on Windows now set the capture endpoint's mute flag instead of disabling the sound device through WMI (`Win32_SoundDevice.Disable()`, which needs admin and takes the device offline). nircmd is used only when pycaw is missing. macOS/Linux paths are unchanged.

**Built**
- `actions/cross_platform_action.py`: the playback endpoint cache was extracted into `_make_endpoint_cache(activate, describe_error)` and instantiated twice on the audio worker thread (playback for volume, capture for the mic) - same TTL, flap guard, invalidate-and-retry-once and QueryInterface ownership as before, now not duplicated. The device-change notifier marks the matching cache dirty for `eRender` or `eCapture`. New `read_mic_mute()` / `set_mic_mute(muted|None)` run on the audio thread through `ctx['mic_endpoint_op']` and return the state read back.
- `integrations/system_live_pack.py`: the `mic_mute` spec and face. Kept apart from `dev_tools_pack` because a mic button is not a developer tool.
- Tests: `tests/test_mic_mute.py` (20).

**Deviations from the plan**
- The plan put the endpoint helper "inside the worker context"; the cache is a module-level factory instead so the retry behaviour is unit-testable without COM.
- A status poll with a failure returns `success: true` (polls are silent; the face explains), while a press failure is `success: false`.
- The icon stays the plan's `microphone-slash` for both states (the badge carries the state), so a LIVE button still shows a slashed mic. A state-dependent icon is possible later.

**Tests (before -> after):** backend 1477 -> 1497; frontend 675 -> 675 (no frontend change needed: the generic live-button path already renders it). `vue-tsc` clean, `npm run build` ok, `scripts/check.ps1` all PASS. No "Errors N error" from vitest.

**Live verification** (backend restarted on :5000, built bundle, throwaway profile)
- pycaw 20240210 / comtypes 1.4.17 on Python 3.13.14: `GetMicrophone()` resolves a real capture device on the audio thread; reads return `(False, None)`.
- Real mic state: read-only everywhere except one controlled toggle through `set_mic_mute(None)` in a separate Python process (before `False` -> toggled `True` -> read `True`), restored in a `finally` to `False` and re-read `False`. The mic was left unmuted, as found. Nothing else wrote to the device; the browser button was never pressed.
- 100 consecutive status polls through `POST /api/actions/execute` returned `LIVE` every time; no audio errors in `vdock.log`.
- Picker: searching "mic" lists "Mic Mute" under System (next to the two old actions under Audio & Volume); one tap opens the editor with no config fields; Save + Save Profile placed it, about four interactions. The placed button painted `LIVE` / "Microphone".
- Screenshots: `C:\Users\Daniel\AppData\Local\Temp\cursor\screenshots\page-2026-10-02T23-36-20-532Z.png` (picker), `...page-2026-10-02T23-36-36-685Z.png` (editor, no fields), `...page-2026-10-02T23-37-44-546Z.png` (live face).
- Cleanup: the throwaway profile "Zz Mic Throwaway" was deleted and the active profile restored to My VDock; `My VDock` contains no `agent_*`, `git_context`, `dev_servers`, `docker_status` or `mic_mute` entries.

**Not verified / known limits**
- The `MUTED` face and the 50-rapid-toggles DL-058 regression check were not exercised live (they would flip the user's real mic); covered by mocked tests plus 100 live reads. Muting from Teams/Windows flipping the face within 3 s was not tried.
- "No microphone found" was verified by mocks only (this machine has a microphone). Browser console output was not captured as a log.

### Phase 5 - Push-to-talk to the agent (Windows voice typing)

**Status:** implemented and verified. **Env vars added: none.** Local Whisper (5.2) and Google Calendar (5.3) stay deferred per the user's decision.

**New action:** `agent_dictate` "Dictate to Agent" (AI Assistants, microphone icon). Hold the button, speak, let go. Holding opens Windows voice typing (Win+H) in the agent's terminal/chat; releasing closes it. The text stays in the prompt box - nothing is ever submitted; tap Submit/Continue after reading it. No visible config field; Agent and Session directory sit under the collapsed Advanced section. Not offered off Windows (picker greys it out with the reason).

**Built**
- `services/agent_dictate.py`: `start` / `stop` / `dictate(op)`. It builds a one-off keymap `Command` from the agent's prompt command (so it inherits the terminal exes, title hint and session marker) with only the voice-typing chord - no text, `submit=False`, no Enter possible - and sends it through `editor_base.send` (resolve the session window, focus it, refuse if the foreground window is not it, refuse if the session is dead, refuse on a locked desktop). Target and states reuse Agent Prompt: refuses `permission` and `working` sessions with its messages; Cursor first presses its chat-focus chord so the text has an input to land in.
- `stop` only acts after a start of ours (Win+H toggles, so a stray release would otherwise open the panel). A second start while listening sends nothing and says "Already listening", so a missed release self-heals on the next press/release. A lock serialises start and stop so a quick release waits for the start to finish.
- Unavailable copy: off Windows, or when the registry flag `OnlineSpeechPrivacy\HasAccepted` is explicitly 0, the press fails with "Online speech recognition is off - turn it on in Settings > Privacy & security > Speech. Turn on voice typing in Settings > Time & language > Typing (or press Win+H once in any text box to set it up)." The first successful start per backend run also carries a one-line hint to the same settings.
- `agent_prompt.check_typeable()` and `editor_label()` extracted from `send_prompt` so prompts and dictation share the same state/pinned-host checks (no duplication).
- Frontend: catalog `press: 'hold'` (already reserved in the types) now drives the pointer pipeline. `DeckButton` treats a hold spec like push-to-talk (dispatch on pointerdown, capture the pointer, release on up/cancel); `useButtonActions` sends `op: 'start'` on press and `op: 'stop'` on release (shared `dispatchAction` helper replaces the duplicated release code), and ignores a bare click so keyboard activation can never start dictation with no way to stop it. `ButtonEditor` hides the manual "Fires on / Push-to-talk" controls for hold actions, since they would contradict the built-in behaviour.

**Deviations from the plan**
- Stop re-focuses the session window (`focus_first` stays on) instead of "only if the foreground is still the session". On a touch deck the press itself takes focus, so a no-refocus stop would never close the panel; the focus still goes through the verified-window path.
- A failed stop returns a failure with "Press Win+H in the agent window to close it", not a silent success, because the panel may still be open.
- The registry check only blocks on an explicit "off" value (it is absent on this machine), so a machine that never opened voice typing proceeds and Windows shows its own first-run prompt.
- With no hooked session the target falls back to the legacy "focused project" path exactly like Agent Prompt, guarded by the session-alive and foreground checks.

**Tests (before -> after):** backend 1497 -> 1516 (`test_agent_dictate.py`: sends Win+H to the session's directory, no Enter or text in any built command, Cursor chat-focus chord, permission/working refusals send nothing, stop-without-start sends nothing, stop once, double start, first-use hint once, unavailable copy and registry cases, unknown op, spec shape); frontend 675 -> 680 (`hold-press.test.ts`: down starts, up and cancel stop exactly once, trailing click ignored, bare click never starts, normal buttons unaffected). `vue-tsc` clean, `npm run build` ok, `scripts/check.ps1` all PASS, no vitest "Errors" line.

**Live verification** (backend restarted on :5000, built bundle, http://127.0.0.1:5000, throwaway profile; **no keystroke was sent to any window**)
- Catalog lists `agent_dictate` with `press: hold`; API calls with `op: stop` ("Not listening") and no op ("Hold the button to talk") answered without touching any window. `op: start` was deliberately never sent to the real backend: with no hooked session it targets a running Claude process on this PC.
- Picker: searching "dictate" lists one entry under AI Assistants; one tap opens the editor with no config field, Advanced (collapsed) holds Agent and Session directory, and the "Fires on / Push-to-talk" controls are gone. Search to configured button was two interactions, well under 30 s.
- Placed button, pointer events with the execute request blocked in the browser (captured, never sent): pointerdown -> `op: start`, two pointerups plus a click -> exactly one `op: stop`; pointerdown + pointercancel -> `start`, `stop`.
- Screenshots: `C:\Users\Daniel\AppData\Local\Temp\cursor\screenshots\page-2026-10-02T23-49-14-199Z.png` (picker result), `...page-2026-10-02T23-51-12-703Z.png` (editor, Advanced open), `...page-2026-10-02T23-51-36-267Z.png` (placed button).
- Cleanup: the throwaway profile was deleted and My VDock reloaded; `backend/data/profiles/0027a602-99fa-4a3f-882d-2f32e6bccc9a.json` contains no `agent_dictate`, `agent_prompt`, `agent_usage`, `git_context`, `dev_servers`, `docker_status` or `mic_mute` entries. The edit-mode gate in the browser blocks desktop-less viewports, so edit mode was entered through the store.

**Not verified / known limits**
- The real Win+H path (panel appears in the terminal, speech lands in the prompt, release closes it) was not exercised, by design; covered by mocked `editor_base.send` tests only. Whether the Windows voice typing panel keeps the terminal as the foreground window (needed for the verified stop) is untested.
- The "Online speech recognition is off" and not-Windows messages are covered by unit tests with mocked registry/platform; they were not triggered live.
- Windows voice typing needs a mic, the right language and (unless on-device) internet. If the user closes the panel by hand mid-hold, the release toggles it open again.
- A short stuck-spinner on the button after the blocked requests was seen in the test only because the requests were aborted on purpose.

## Overall summary - DL-145 (Phases 1-5)

**Shipped (9 new action ids, the plan's recommended count; target range 9-12):**
1. `agent_prompt` - preset/custom prompt to the ready agent session.
2. `agent_review_changes` - files the agent changed this turn, tap for diff.
3. `dev_run_tests` - detects and runs the repo's tests, pass/fail face.
4. `agent_usage` - today's Claude Code spend/tokens (API-equivalent estimate).
5. `git_context` - branch/dirty/ahead-behind with a pull/push/stash menu.
6. `dev_servers` - running dev servers with open/restart/stop.
7. `docker_status` - containers/compose status with start/stop/logs.
8. `mic_mute` - real Windows microphone mute, LIVE/MUTED face.
9. `agent_dictate` - hold to dictate to the agent via Windows voice typing.

Plus shared infrastructure: catalog metadata (`advanced`, `show_when`, `poll_seconds`, `press`), generic catalog config form, press-menu sheet, generalised widget polling, `focused_repo()`, Mission Control Prompt/changes/usage/Compact; `microphone_mute` now sets the endpoint mute flag. **Env vars added: none, in any phase.**

**Deferred (not built):** window layout presets, audio device switching, Google Calendar next meeting, local Whisper STT.

**Known limits (see each phase):** no keystroke path was exercised against a real agent window in any phase (mocked/unit only); cost figures are estimates and can be far off for resumed or subagent-heavy sessions; Docker with a running daemon, dev-server start/stop and git write ops were not run live; the MUTED face, DL-058 50-toggle check and real voice typing were not exercised live.

**Try-it checklist**
1. Settings > Time & language > Typing: make sure voice typing works (press Win+H in any text box once; allow Online speech recognition if asked).
2. Start a Claude Code (or Cursor) session and let it reach the ready state.
3. Edit mode > search "dictate" > tap Dictate to Agent > Save. Hold it, speak, release; read the text, then tap Submit yourself.
4. Try Agent Prompt (Continue / Write tests), Review Changes, Run Tests, Agent Usage, Git Branch, Dev Servers, Docker Containers and Mic Mute from the picker; each needs at most one field.
5. Check Mission Control (Prompt menu, change chip, cost/context chip).
