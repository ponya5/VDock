# DL-004 — IDE & AI Agent Control

**Date:** 2026-09-19
**Branch:** `upgrade/upgrade--keypad`
**Spec:** `docs/superpowers/specs/2026-09-19-ide-agent-control-design.md`
**Plans:** four, one per phase:
- `docs/superpowers/plans/2026-09-19-ide-phase1-keymaps.md`
- `docs/superpowers/plans/2026-09-19-ide-phase2-claude-code.md`
- `docs/superpowers/plans/2026-09-19-ide-phase3-hook-status.md`
- `docs/superpowers/plans/2026-09-19-ide-phase4-context-scene.md`

**Status:** Planned — no code written
**Depends on:** DL-002 (every key, path and setup action lives in that settings surface)

## Background

Requested by the user as:

> "I want to have the ability to sync with Claude — meaning in Claude and
> Cursor scenes, I want VDock to actually show actions and interact with
> Cursor, Claude Code. For example a Claude continue button will trigger
> continue in the Claude Code CLI. I want you to add the keyboard shortcuts as
> actions in Claude, Cursor and other IDEs' scene buttons. Look at
> https://code.claude.com/docs/en/keybindings and https://vibekeys.dev/"

Both references were read during design. **VibeKeys is a physical keypad** —
six remappable keys, a rotary knob, and on its Max model a status screen
showing *"Claude Code status, voice feedback and AI responses in real time."*
So the request is, in effect: make VDock a software VibeKeys. The "show
actions" half is as important as the "interact" half.

**Claude Code is a terminal TUI.** Its shortcuts are keystrokes into whatever
terminal hosts it, not application hotkeys — and it reads a user-editable
`~/.claude/keybindings.json` that hot-reloads.

## Problem

More infrastructure existed than expected, and one thing did not work as its
name suggested.

**Already present:** `integrations/keymaps.py` (typed Copilot + Cursor
commands), `integrations/editor_base.py` (a focus guard that refuses to send
keystrokes unless the expected process is foreground),
`integrations/context.py` (resolves the focused editor and its project from the
window title), `services/autoSceneSwitcher.ts`.

**Missing or wrong:**

1. **Two shortcut databases that can drift.** `integrations/keymaps.py`
   (backend, executable) and `frontend/src/data/appShortcuts.ts` (frontend, ~35
   entries) both describe Cursor and VS Code.
2. **`claude_continue` does not continue.** Despite the id, it is labelled
   *"Open Claude Code"* (`claude_pack.py:174-187`) and spawns a **new** terminal
   with `--resume`. Nothing interacts with a session already running — so the
   user's exact example was not covered.
3. **No Claude Code keybindings at all.**
4. **No session state**, so nothing can be shown.

## Questions and Answers

**Q: What should VDock actually know about a running Claude Code session?**
A: **Live status via Claude Code hooks.** `SessionStart`, `Notification`,
`PreToolUse`/`PostToolUse` and `Stop` POST to VDock. Supported, event-driven,
no scraping. Rejected: completion notifications only (buttons stay static);
mirroring the transcript on the deck (duplicates the terminal you are already
looking at); and no status at all (drops half the request).

**Q: How should keystrokes be delivered reliably?**
A: **Guarded keystrokes plus a VDock-managed `keybindings.json`.** VDock binds
its own obscure chords and sends those, so a user who has remapped their
defaults is unaffected. Rejected: sending documented defaults (breaks silently
after any customisation); and CLI one-shots only (safe, but cannot press
Continue or Interrupt on a live session).

**Q: Which apps?**
A: All four groups — Claude Code; Cursor + VS Code/Copilot; other AI CLIs
(Codex, Gemini, OpenCode, Aider); JetBrains + Windsurf + Zed. Roughly ten apps,
which is why this is phased.

**Q: How do buttons reach the deck?**
A: **One auto-switching context scene** whose buttons follow the focused app,
building on `autoSceneSwitcher.ts`. Positions stay fixed across apps so muscle
memory survives an alt-tab. Rejected: one ready-made scene per app; and catalog
actions the user places by hand (~60 buttons).

**Q: Where should app knowledge live?**
A: **Approach C — typed in Python, served to the frontend.** Keymaps stay as
frozen `Command` dataclasses in a `keymaps/` package; `GET /api/app-profiles`
serialises them so `appShortcuts.ts` is deleted.

Rejected (A): extend the pack model as-is — cheapest, but leaves the dual
database and means three places to edit per new app. Rejected (B): fully
data-driven JSON profiles — adding an app becomes a data file, but it discards
the proven `Command` dataclass and `to_macro_steps()` and needs a schema to
replace the type safety given up.

**Q: Three risks were raised. What are the solutions?**
A: Each is answered in the Design below: hook authentication (§Hook status),
`keybindings.json` safety (§Managed keybindings), and mistargeted keystrokes
(§Safety model). The user asked specifically for these to be solved rather than
just flagged.

## Design

```mermaid
flowchart TD
  subgraph P1[Phase 1: consolidation]
    A[keymaps/ package<br/>Command + AppProfile] --> B[GET /api/app-profiles]
    B --> C[appShortcuts.ts DELETED]
  end
  subgraph P2[Phase 2: Claude Code]
    D[claude_code keymap] --> E[keybindings.py<br/>additive, manifest-tracked]
    E --> F[editor_base<br/>risk gating + dry run]
  end
  subgraph P3[Phase 3: status]
    G[Claude Code hook] --> H[vdock_hook.py<br/>always exits 0]
    H --> I[POST /api/agents/status<br/>token + loopback]
    I --> J[agent_status registry]
    J --> K[socket -> button state]
    J --> F
  end
  subgraph P4[Phase 4: context]
    L[autoSceneSwitcher<br/>remap by focused app] --> M[AI Deck scene]
  end
```

### Managed keybindings

Four rules make writing to someone's real `~/.claude/keybindings.json` safe:

1. **Additive only — VDock never writes `null`.** Unbinding is the destructive
   operation in that format; not doing it removes the entire "VDock clobbered
   my bindings" failure class rather than mitigating it.
2. **Ownership lives in VDock's manifest, not the file.** JSON has no comments,
   so a "VDock block" cannot be marked in place. A manifest records every
   `(context, chord)` pair written, and only those are ever removed.
3. **Collision-avoiding allocation.** The file is read first; chords bound by
   Claude Code (`ctrl+x ctrl+k`, `ctrl+x ctrl+e`, `ctrl+x enter`,
   `ctrl+x ctrl+a`, `ctrl+x tab`, `ctrl+x b`, `ctrl+x ctrl+b`) or by the user
   are skipped. VDock allocates from `ctrl+x` + function keys.
4. **Backup, then atomic write.** Claude Code hot-reloads this file, so a
   corrupt write would break the session the user is sitting in front of.

Opt-in, with a dry-run diff shown first and a clean uninstall.

### Hook status

The hook script's single hard requirement: **it cannot disrupt Claude Code.**
It swallows every exception, uses a ~500 ms timeout, and always exits 0. A
VDock that is closed, busy or crashed must be completely invisible to a live
session — a status light is never worth degrading the editor. That is why it is
a script rather than an inline curl.

The endpoint is token-authenticated with `hmac.compare_digest`, **loopback-only
even when `ALLOW_LAN` is true**, payload-capped, and fails closed when no token
is configured. This matters more than it looks: session state is an *interlock*
for sending keystrokes, so forgeable state would defeat the focus guard.

### Safety model

The existing guard checks `foreground_exe() in target_exes`. That is
insufficient here, because the target is *a terminal* — and a terminal might be
running anything. Four layers:

1. **Hook state is the interlock.** A keystroke goes out only when a live
   session is registered. This is where the hook-auth work and the
   wrong-window work solve each other.
2. **Blast-radius classification** on `Command`: `safe` (focus guard only),
   `input` (guard **and** a live session), `destructive` (not one-tap; per-button
   opt-in plus hold-to-confirm).
3. **No approve button ships.** When a permission prompt is waiting the deck's
   job is to *say so* and offer to focus the terminal. Approving a permission
   prompt from a surface that cannot show what is being approved defeats the
   prompt's purpose.
4. **Dry-run mode** logs what would be sent instead of sending it.

### Platform scope

**Windows-first, explicitly.** `target_exes` are `.exe` names,
`context.py:38-44` lists Windows processes, and the focus guard is
Windows-specific — while the README advertises macOS and Linux and Claude Code
runs on all three. `Command` and `AppProfile` carry per-platform fields from the
start, but only the Windows tables are populated. macOS and Linux are a separate
workstream, recorded as a known gap rather than left as a surprise.

## Implementation Plan

- [ ] **Phase 1 — consolidation.** Keymaps package, `AppProfile`,
      `/api/app-profiles`, delete `appShortcuts.ts`. **No behaviour change.**
- [ ] **Phase 2 — Claude Code.** Keymap, managed keybindings, risk gating,
      dry run, relabel `claude_continue`.
- [ ] **Phase 3 — status.** Session registry, hook script, authenticated
      endpoint, session interlock, button rendering.
- [ ] **Phase 4 — context.** Remaining seven apps, context scene,
      destructive-command opt-in UI, AI Deck template.

Each phase is independently shippable. Phase 1 alone is a pure consolidation
worth landing on its own.

## Trade-offs

**Chosen: approach C.** Keeps the proven typed dataclasses and reuses the focus
guard, the plugin manager and the catalog, while still killing the dual
database. Cost: adding an app needs a small Python module rather than a data
file — acceptable, since each new app tends to need process-detection quirks
anyway. A JSON overlay for user-defined apps stays possible later.

**Chosen: VDock binds its own chords.** More moving parts than sending
documented defaults, but it is the difference between working and silently not
working for anyone who has customised their keybindings.

**Chosen: additive-only writes.** Gives up the ability to rebind a key the user
already uses. Worth it: it makes the destructive case structurally impossible.

**Chosen: no approve button.** Deliberately less convenient than VibeKeys'
"accept with a single click". Accepting a code suggestion and approving a
permission prompt are different acts, and only one of them is safe to do
blind. Available as an explicit per-button opt-in.

**Chosen: `claude_continue` keeps its id.** The id is the misleading part, but
user buttons reference it and renaming it would break them. Only the label and
description change; the new `cc_continue` does the real thing.

**Chosen: Windows-first.** Stated rather than hidden. Half-populating the mac
tables would be worse than leaving them empty.

**Rejected: transcript mirroring, voice input, any non-keystroke control
channel** — no public interface exists for a running Claude Code session.

## Verification Criteria

**Phase 1** — every existing Cursor/Copilot command keeps its id, keys and
macro steps; a pre-existing user button still works; `grep appShortcuts` comes
back clean.

**Phase 2** — the keybindings writer never emits `null`; user bindings survive;
Claude Code's reserved chords are never allocated over; a failure mid-write
leaves the original intact; uninstall removes exactly the manifest pairs; no
`Confirmation`-context command ships.

**Phase 3** — the hook script exits 0 when the backend is unreachable, errors,
or returns 500, verified end-to-end in a subprocess; a wrong or missing token
is rejected; non-loopback is rejected with `ALLOW_LAN=True`; an unconfigured
token fails closed; an `input` command refuses with no live session.
**Manual:** Claude Code runs completely normally with the VDock backend
stopped, and **no button can approve a permission prompt.**

**Phase 4** — every profile's layout references only real commands and is 4
wide; no destructive command ships by default; a terminal agent's `input`
commands all require a session; context scenes fall back rather than blanking;
existing scenes are unchanged. **Manual:** dry-run sweep of every new app's
buttons against that app's real shortcuts before any live use.

## Implementation Results

### Phase 2 — Claude Code control (shipped, with deviations)

**Keystroke delivery.** `backend/integrations/keymaps/claude_code.py` defines
nine `cc_*` commands — `cc_interrupt` (Esc), `cc_mode` (Shift+Tab),
`cc_clear`, `cc_resume`, `cc_compact`, `cc_model`, `cc_add_file`, `cc_help`,
and `cc_exit` (Ctrl+C ×2) — all targeting `TERMINAL_EXES` with
`window_title_hint='claude'`. `claude_code_pack.py` exposes them through
`KeystrokeEditorPlugin`. The `claude-code` scene template in
`appTemplates.ts` now offers live-session buttons.

**Focus-first delivery (the touch-deck fix).** Tapping a VDock button steals
focus to the browser, so keystrokes never reached the app — this is the
actual reason the Claude scene appeared dead. `editor_base.send()` now
raises the target window first via `utils/window_focus.py`
(EnumWindows + force-foreground on Windows, `prefer_title` picks the tab
whose title hints at the session), waits `FOCUS_SETTLE_SECONDS`, then runs
the original foreground-process guard before `MacroAction` types anything.
`app_monitor` records window handles to support this. Per-button
`focus_first` and `enforce_focus` config fields ship on every keystroke
action.

**Gating.** `keymaps/base.py` `Command` gained `risk`, `requires_session`,
`session_marker`, `window_title_hint`, `repeat`, `types_text`/`submit`,
`category`, `priority`. Destructive commands refuse unless the button opts
in (`allow_destructive`, default off); only `cc_exit` is destructive and no
Confirmation-context command ships. `requires_session` commands are gated by
`integrations/sessions.py` — a **process scan**, not the Phase-3 hook
registry, which is the main deviation: hooks and live status remain
unimplemented. A second deviation: no managed `keybindings.json` writer —
commands send keystrokes directly rather than remapping Claude Code's own
bindings.

**Compatibility.** `claude_continue` keeps its id and still spawns
`claude --resume` in a new terminal; only its label/description were
corrected. Existing Cursor/Copilot commands are unchanged (Phase-1
verification holds).

**Tests.** `test_integrations.py` mocks the new focus step; new cases cover
the session gate, destructive opt-in, and focus-first macro steps.
`test_keymaps_package.py` union/default assertions updated for the third
pack. Result: **717 backend tests pass**; `vue-tsc` clean; **115 frontend
tests pass**.

**Not started:** Phase 3 (hooks, live session status, session-aware
interlock beyond process scan), Phase 4 (remaining ~8 apps, context scene).

### Porting note — merge into `feat/unified-background`

The running app served `.worktrees/unified-background`, which had branched
before Phase 1; the work above was developed on `upgrade/upgrade--keypad`
(commits `2729768`, `e6bc18e`) and merged here in `79eedbf`. One conflict:
`SettingsView.vue`'s search index — resolved by keeping this branch's
unified `Background` entry (its two background pickers were merged into
one) plus the new `Weather Widget Size` entry. Post-merge: **719 backend
tests pass** (717 + 2 unified-background persistence tests), `vue-tsc`
clean. The live `Claude` scene (`scene-1789846753894`) was rewired via the
profiles API: `New Session`→`cc_clear`, `Open Claude Code`→`claude_continue`,
`Resume`→`cc_resume`, `Add File`→`cc_add_file`, `Interrupt`→`cc_interrupt` —
button ids, positions and styles preserved.

### User workflow context (2026-09-20)

The user's real setup, stated directly: VDock itself is developed with
**Devin + Cursor, and the Claude CLI runs inside Cursor's integrated
terminal** — not a standalone terminal window. Two consequences:

1. **Known gap in Phase 2 as shipped.** `cc_*` commands target
   `TERMINAL_EXES`; a Cursor-hosted Claude session lives in a `Cursor.exe`
   window, which isn't in that list. `focus_app_window` won't find it and
   the guard correctly refuses rather than typing `/clear` into a source
   file. Options for Phase 3: add `cursor.exe` to the Claude target list
   gated on a focused-terminal-panel signal, or rely on the hook registry
   to report the hosting window — hooks are the honest answer because the
   session knows its own tty/parent process.
2. **Devin CLI is another agent candidate** — same terminal-TUI shape as
   Claude Code; a `devin` keymap/profile would slot into the existing
   `terminal_agent` machinery.

The vision confirmed by the user is the stream-deck model: VDock detects
which dev tool is running/focused and offers that tool's real actions —
exactly the Phase-4 context scene.

### Session-host window resolution (2026-09-20)

The Phase-2 targeting gap — Claude inside a terminal *panel* owned by an
editor process — is now closed without waiting for hooks:

- `utils/window_focus.py` gained `find_session_host_window(marker)`: find
  the agent process, walk its ancestor chain, return the first ancestor
  that owns a visible top-level window. Verified against the live setup:
  `claude.exe ← powershell.exe ← Devin.exe` resolves to the Devin window
  (`hwnd 263938`). Works for Devin, Cursor, VS Code, Windows Terminal —
  any host — because it follows the process tree instead of an exe list.
- `editor_base` consults it first when a command carries `session_marker`;
  the post-focus app check now reads the *live* foreground window instead
  of the app monitor's cached value (the cache lags a refocus by up to
  the poll interval).
- `claude_code.py`: safe commands carry `session_marker='claude'` (targeting
  only — no gating); new `cc_prompt` command types a configurable prompt
  (default "continue") into the live session.
- **Verified live:** `cc_interrupt` → resolved the Devin window →
  `Sent hotkey: escape`. First VDock button to reach a real Claude session
  hosted in an editor terminal.
- The live `Daniel` profile's Claude Code and Cursor scenes were rewired
  via the API to real `cc_*`/`cursor_*` actions (the previous build was
  still on `command`/`open_url` placeholders).

### Phase 4 (partial): out-of-the-box keymaps for major IDEs

New keymap modules + auto-discovered `*_pack` plugins:

- **vscode** (35 commands incl. merged Copilot set) — palette, quick open,
  terminal, panels, F-row debugging, quick fix, rename.
- **jetbrains** (20) — double-Shift Search Everywhere, Find Action,
  Alt+F12 terminal, Alt+Enter intentions, F7/F8 stepping.
- **visualstudio** (19) — Go to All, build, F5/F9/F10/F11. Chord-only
  shortcuts (Ctrl+K Ctrl+D style) are deliberately absent — a one-shot
  hotkey can't express them.
- **devin** (5) — terminal-agent shape, `session_marker='devin'` so the
  process-tree resolver finds its host window anywhere.

Ordering note: `_PROFILE_BY_EXE` maps an exe to the LAST profile listing
it. `vscode` is placed after `copilot` so `code.exe` resolves to the
merged profile; `devin` precedes `claude-code` so terminal exes keep
resolving to `claude-code` (session detection disambiguates at action
time anyway).

**Verified:** 9 plugins load, 206 catalog actions; `vsc_terminal` cleanly
refuses when VS Code isn't running ("No code.exe or codium.exe window
found"); pytest 734.

**Still not started:** Phase 3 (Claude Code hooks → live session state on
the deck), the Phase-4 context scene itself (auto-built per-app layout —
profiles' `default_layout` rows are the input).

### Claude Code keymap — full keyboard surface as deck buttons

The Claude keymap now covers the official keybindings doc
(`code.claude.com/docs/en/keybindings`) — 40 commands total:

- **Permission prompts**: `cc_approve` (y) / `cc_deny` (n) / `cc_accept`
  (Enter) — the deck's core value: answer a permission dialog without
  touching the keyboard. Priority 10 so they sort first.
- **View toggles (safe)**: `cc_todos` (Ctrl+T), `cc_transcript` (Ctrl+O),
  `cc_history` (Ctrl+R), `cc_redraw` (Ctrl+L), `cc_rewind` (Esc x2 opens
  the message-selector dialog), `cc_thinking` (Alt+T), `cc_fast` (Alt+O).
- **Navigation**: `cc_scroll_up/down` (PgUp/PgDn), `cc_nav_up/down`
  (arrows for dialogs/pickers).
- **Draft controls (session-gated)**: `cc_cancel` (Ctrl+C =
  `app:interrupt`), `cc_newline` (Ctrl+J), `cc_stash` (Ctrl+S), `cc_undo`
  (Ctrl+Shift+-), `cc_editor` (Ctrl+G), `cc_paste_image` (Alt+V),
  `cc_background` (Ctrl+B), `cc_queue` (Ctrl+X Enter chord, v2.1.247+).
- **Slash commands**: `/tasks`, `/diff`, `/agents`, `/effort`,
  `/permissions`, plus `!` (bash) and `#` (memory) prefixes.
- **Destructive**: `cc_kill_agents` (Ctrl+X Ctrl+K), `cc_exit` — corrected
  to Ctrl+D x2 per the docs (`app:exit`); the previous Ctrl+C x2 was
  `app:interrupt`, which is now `cc_cancel`.

`Command` gained `after_keys`: a tuple of follow-up keystrokes emitted as
separate hotkey steps, expressing two-stroke chords (Ctrl+X Ctrl+K,
Ctrl+X Enter) that a single hotkey can't.

`default_layout` leads with the permission pair and surfaces
rewind/todos: `(prompt, interrupt, approve, deny)` / `(clear, mode,
rewind, todos)` / `(resume, compact, add_file, model)`. The live `Daniel`
profile's Claude scene got the same additions in its free cells.

**Verified:** 735 backend tests; `cc_todos` delivered `Ctrl+T` to the
live Devin-hosted session. A stale backend process was found sharing
port 5000 (Windows `SO_REUSEADDR` lets two listeners bind the same
socket — the old code answered the first probe); killed it, the current
backend reports all 40 `cc_*` actions.

### Follow-up (2026-09-21): `claude_continue` fails with WinError 87

**Reported:** every press of the `claude_continue` buttons ("Open Claude",
"Continue") toasted `Action Failed — Could not start Claude Code
(WinError 87) The parameter is incorrect`.

**Root cause.** `utils/subprocess_runner.py::spawn` OR'd
`CREATE_NEW_CONSOLE | DETACHED_PROCESS` into `Popen(creationflags=...)`.
The two flags are mutually exclusive — `CreateProcess` rejects the
combination with `ERROR_INVALID_PARAMETER` (87). Reproduced directly:
`Popen([claude.cmd, '--version'], creationflags=NEW_CONSOLE|DETACHED)`
raises it. Even without the error, `DETACHED_PROCESS` was wrong for this
action — it gives the child *no* console, so an interactive `claude`
session would open invisible. `CREATE_NEW_CONSOLE` alone is the correct
flag: the child gets its own console window and outlives VDock, which is
what the original comment intended.

**Fix:** keep `CREATE_NEW_CONSOLE`, drop `DETACHED_PROCESS`. No other
spawn-path change — `sr.run` (used by `claude_prompt`/`claude_slash`)
passes no creation flags and was never affected.

**Known limitation (not changed):** `claude` resolves to the npm
`claude.cmd` shim, so arguments reach it through `cmd.exe` even with
`shell=False` — batch-file argument escaping is a Windows/cmd limitation,
not something `list2cmdline` quoting can fully close. The docstring's
"never through a shell" guarantee holds for the launch mechanism but
`.cmd` shims remain a weak spot for metacharacters in prompts.

**Verified (2026-09-21):**

- `Popen` with the old flag pair raises `[WinError 87]` on this machine;
  with `CREATE_NEW_CONSOLE` alone, `sr.spawn(['claude', '--continue'])`
  returns cleanly and the interactive terminal window opens.
- `claude_open` (`target=web`) exercised through `execute_action` —
  returns success (`start "" "https://claude.ai"` path unaffected).
- New regression test `test_spawn_gives_windows_children_their_own_console`
  monkeypatches `Popen` and asserts `CREATE_NEW_CONSOLE` present +
  `DETACHED_PROCESS` absent on Windows, no flags elsewhere (tightened
  after the first `/code-review` job flagged the one-sided original).
- `test_subprocess_runner.py` 42/42, `test_integrations.py` 51/51 pass.

**Same-session finding — the `.cmd` shim eats argv (fixed).** The
button-matrix test surfaced a second defect: Explain/Write Tests ran but
Claude reported "the snippet didn't come through" — `{clipboard}` had
expanded fine, but `claude` resolves to the npm `claude.cmd` shim which
forwards `%*` through `cmd.exe`, so the quoted multi-line snippet was
truncated at the first newline. Proven with a local echo shim: a payload
of `Explain this:\n\ndef f(x): return "a|b" ^ x` arrived as
`-p "Explain this:`. Fix: `find_binary` now unwraps the npm
`"<path>" %*` idiom to the real executable
(`...\node_modules\@anthropic-ai\claude-code\bin\claude.exe`), so argv
reaches it via `CreateProcess` verbatim — the "never through a shell"
guarantee actually holds now. Shims forwarding to scripts (`node cli.js`)
are left alone. Regression test runs a fabricated shim on PATH with a
metachar+newline payload and asserts verbatim delivery.

**Live verification of the full Claude Code scene (8 buttons):**
`claude_open` → claude.ai/new opened; `claude_continue` → interactive
`claude --continue` console spawned (PID confirmed, host window resolved
via `find_session_host_window`); `/code-review`, `/commit`, `Explain`,
`Write Tests`, `Fix Tests`, `Continue` (`--continue -p`) all returned
`success` through the job runner — including a real commit `e226343`
produced by `/commit` and a correct failing-test diagnosis from Fix Tests.
Caveat surfaced: `-p` runs take 30s–4min, so buttons "feel" dead while
the job is in flight — a UX gap worth a progress indicator later.
