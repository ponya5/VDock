# DL-066: IDE agent parity — Cursor, VS Code Copilot, Visual Studio

**Date:** 2026-09-24
**Depends on:** DL-064 (state-aware actions, live typing), DL-065 (mobile
console, `prompt_command`)

## Background

Claude Code has these capabilities:

- a state-aware action bar;
- scene buttons that type real prompts into the live session (Review,
  Commit, Explain, Write Tests, Fix Tests);
- a phone composer (`prompt_command`).

The IDE profiles only have fixed shortcuts. Cursor's scene opens panels
(Composer, Chat, Palette) but can't ask the agent anything. VS Code has four
Copilot slash commands and no free-text prompt. Visual Studio and JetBrains
have no AI chat commands at all.

## Problem

1. **No free-text prompt command for any IDE.** Scene prompt buttons and
   the phone composer need a command that focuses the IDE's chat input,
   types text and submits it.
2. **Unsafe focus keys.** Live probes on Cursor 3.21 showed that Ctrl+L and
   Ctrl+I toggle the agent panel: pressed while the input has focus, they
   close it. Typing after a toggle key can land in the editor.
3. **Enter-only Submit.** `cursor_submit` is a bare Enter. In an IDE,
   focus may be in a file, so Enter would edit code.
4. **Thin Cursor state.** Only three hook events are installed
   (beforeSubmitPrompt, afterAgentResponse, stop). A long agent run
   reports nothing in between.

## Design

### Focus keys verified from the IDE bundles (not guessed)

| IDE | Action | Key | Source |
|---|---|---|---|
| Cursor 3.21 | Open New Agent Chat (focus a fresh input, not a toggle) | Ctrl+Shift+L | `workbench.desktop.main.js`: "Open New Agent Chat", primary `CtrlCmd+Shift+L` |
| Cursor 3.21 | Focus the current chat's follow-up input | tested live | "Focus Chat Followup" |
| VS Code 1.11x | Open Chat (focus the input) | Ctrl+Alt+I | `primary:2599` |
| VS Code | Submit / Keep all / Cancel | Enter / Ctrl+Enter / Alt+Backspace | `chat.submit` 3, `acceptAllFiles` 2051, `chat.cancel` win 513 |
| Visual Studio 2022 | Copilot Chat | Ctrl+\, Ctrl+C | documented default; not installed here, unverified |

### Commands

- **Cursor:**
  - `cursor_prompt`: Ctrl+Shift+L, then type, then Enter. It starts a new
    agent chat, which suits one-shot tasks from scene buttons.
  - `cursor_followup`: focus the follow-up input, type, Enter. It continues
    the current chat and is the profile's `prompt_command` (the phone
    composer).
  - `cursor_submit`: focus the follow-up input, then Enter, instead of a
    bare Enter.
  - Chat inputs take Shift+Enter as a newline (`newline_keys`).
- **VS Code / Copilot:**
  - `copilot_prompt`: Ctrl+Alt+I, then type, then Enter (the
    `prompt_command`).
  - `copilot_submit`: Ctrl+Alt+I, then Enter.
  - `copilot_stop`: Alt+Backspace.
  - `copilot_keep`: Ctrl+Alt+I, then Ctrl+Enter.
  - `state_actions`: `unknown` only, because Copilot has no hook.
- **Visual Studio:** `vs_copilot_chat` and `vs_copilot_prompt` (the
  Ctrl+\ Ctrl+C chord through `after_keys`), plus `unknown`
  `state_actions`.
- **JetBrains:** skipped. AI Assistant has no default chat shortcut, so any
  key would be a guess.

### Cursor state

Add the observational hook events `afterFileEdit` and
`afterShellExecution`, both mapped to working. The permission-gating
events stay excluded (see DL-064).

### Cursor scene

The scene follows the Claude layout (2×4 grid): New Agent, Review, Commit,
Inline Edit, Explain, Write Tests, Fix Tests, Terminal. The prompt buttons
use `cursor_prompt` with the same texts as Claude's. State-dependent
actions (Submit, Stop, Accept, Reject) stay in the agent bar. The user's
stored profile gets the same scene through a migration script (backup
first).

## Verification Criteria

- Unit: the new commands produce the expected macro steps (focus chord,
  typed text, Shift+Enter newlines, one Enter); every `prompt_command`
  types text; the IDE profiles expose `state_actions`; the Cursor hook maps
  the new events; the default Cursor scene has no state-dependent buttons.
- ~~Live on Cursor: a scene prompt opens a new agent chat...~~ **Dropped —
  see Implementation Results.** This chat *is* the active Cursor window, so
  `cursor_prompt` (Ctrl+Shift+L) or `cursor_submit`/`cursor_followup`
  (Ctrl+Shift+Y) would open a tab or send a message inside this very
  session instead of a disposable one. Verification stayed at the
  macro-step level; no keystroke was sent to the live window.

## Implementation Results

- Added `cursor_prompt`, `cursor_followup` and a refocusing `cursor_submit`
  to `backend/integrations/keymaps/cursor.py`, using the workbench-verified
  Ctrl+Shift+L / Ctrl+Shift+Y chords and `Shift+Enter` newlines; set
  `prompt_command='cursor_followup'` and rebuilt `state_actions` (no
  `permission` row — Cursor's hooks can't report one).
- Added `test_cursor_prompt_opens_a_new_agent_chat_and_types_into_it`,
  `test_cursor_followup_focuses_the_current_chat_before_typing` and
  `test_cursor_submit_focuses_the_chat_before_pressing_enter` to
  `backend/tests/test_keymaps_package.py`; fixed the stale
  `PROFILES_BY_ID['cursor'].to_dict()['prompt_command'] is None` assertion
  in `test_agent_state_events.py` to expect `'cursor_followup'`.
- **Deviation:** live keystroke verification against the real Cursor
  window was dropped mid-implementation at the user's explicit instruction
  — this session's own Cursor window is the only one available, and every
  Cursor macro targets whichever window is focused. Full backend suite
  (854 tests) passes; no live send was attempted. The VS Code Copilot and
  Visual Studio prompt commands, the Cursor hook installation are still
  pending. The Claude-style Cursor scene rebuild and the "existing profile"
  migration path shipped as a follow-up on 2026-09-25 — see below.

## Follow-up: Cursor scene rebuild + reset-to-default path (2026-09-25)

### Problem

The frontend's actual default-profile Cursor scene (`frontend/src/utils/
defaultProfile.ts`, `createCursorScene`) still shipped the pre-DL-066
Composer/Chat/Inline Edit/Palette/Accept/Reject/Terminal/Quick Open button
set, and — separately — never passed a `grid_config` override, so it fell
back to the shared `DEFAULT_SCENE_GRID` of `{ rows: 3, cols: 5 }` while only
using an 8-button 2×4 area. On mobile this made the Cursor scene's buttons
render visibly smaller than Claude Code's (which does set `{ rows: 2, cols:
4 }`), with dead space filling the unused rows/columns — reported by the
user directly from side-by-side phone screenshots.

Separately, the design's "user's stored profile gets the same scene through
a migration script" point could not be done as a one-off backend migration:
this workspace's `data/profiles/` is empty (a fresh checkout, not the
user's live server), so there is no profile file here to touch.

### Fix

- `createCursorScene` now builds the design's intended 2×4 layout — New
  Agent (`cursor_new_chat`), Review, Commit, Inline Edit (`cursor_
  inline_edit`) / Explain, Write Tests, Fix Tests, Terminal (`cursor_
  toggle_terminal`) — with `grid_config: { rows: 2, cols: 4 }` explicitly
  set, matching Claude Code's. The five prompt buttons (Review, Commit,
  Explain, Write Tests, Fix Tests) use `cursor_prompt` and reuse the exact
  same prompt text as Claude's for the three prompts that are agent-
  agnostic (Commit/Explain/Write Tests/Fix Tests now share
  `COMMIT_PROMPT`/`EXPLAIN_PROMPT`/`WRITE_TESTS_PROMPT`/`FIX_TESTS_PROMPT`
  module constants); Review's text was adapted to a plain instruction
  instead of Claude's `/code-review` slash command, since that's a Claude
  CLI plugin command with no Cursor equivalent — typing it verbatim into
  Cursor's chat would just be a literal, meaningless message there.
  `Submit`/`Continue`/`Stop`/`Accept`/`Reject` are left out of the grid
  entirely, same as Claude — they're already driven by the `cursor`
  profile's `state_actions` (`backend/integrations/keymaps/cursor.py`,
  shipped in the original DL-066 work) via the agent action bar.
- **In place of a backend data migration** (not possible from this
  workspace — see above): `createClaudeCodeScene`/`createCursorScene` are
  now exported, plus `isFactoryIdeSceneName`/`createFactoryIdeScene`, a
  small name-keyed registry. `dashboard.ts`'s `resetScene` — previously
  only able to restore the single `isDefault` Media scene — now also
  restores a scene identified by name as "Claude Code" or "Cursor" to its
  current factory layout, preserving the scene's id/isActive. `SceneEditor.
  vue`'s "Reset to Default" button now shows for these scenes too. This
  gives any user on the old Cursor layout (including the one who reported
  this) a one-tap, in-app fix: open the Cursor scene in edit mode → Reset
  to Default — no server-side migration script needed, and it's the same
  mechanism a future layout fix can reuse.

### Verification

- `default-profile.test.ts`: updated the allowed-action-types list for the
  new Cursor button set; added a test pinning Cursor's `grid_config` to
  `{ rows: 2, cols: 4 }` (matching Claude) and asserting Cursor's own
  state-bar-owned action types (`cursor_submit`, `cursor_followup`,
  `cursor_cancel`, `cursor_accept`, `cursor_reject`) are absent from the
  grid.
- Full frontend suite: 59 files / 251 tests green; `vue-tsc --noEmit`
  clean.
- Not yet verified live in the running app (no access to the user's
  device) — the user should confirm the rebuilt layout via "Reset to
  Default" on their existing Cursor scene.

## Follow-up 2: automatic upgrade instead of a manual reset (2026-09-25)

### Problem

The manual "Reset to Default" path above still requires the user to find
and press it — the user's next report was from the *desktop* view, still
showing the pre-fix Cursor layout, asking for it to just be fixed rather
than telling them where to click.

### Fix

`isUntouchedLegacyCursorScene(scene)` (`defaultProfile.ts`) fingerprints a
"Cursor" scene by its buttons' action types: true only when the set is
*exactly* the eight pre-fix types (`cursor_composer`, `cursor_chat`,
`cursor_inline_edit`, `cursor_command_palette`, `cursor_accept`, `cursor_
reject`, `cursor_toggle_terminal`, `cursor_quick_open`) with nothing added
or removed. `dashboard.ts`'s `setProfile()` now runs this check on every
profile load (right after the existing default-scene reconciliation) and
silently replaces the scene's `pages`/`icon`/`color` with the fresh
factory build when it matches, preserving the scene's `id` — so it slots
back into whatever position/isActive state it already had. Per the
existing "in-memory only" migration convention (`migrateProfileToScenes`
above), this doesn't force an immediate save; it rides along with the
next real edit's auto-save, same as the other migration this function
already runs.

The fingerprint is deliberately exact-match, not "contains any legacy
type": a user who kept some of the old buttons but added or removed even
one has customised the scene, and this must never silently overwrite that
— per the same rule `resetScene` already follows. A customised Cursor
scene still only gets fixed through the explicit "Reset to Default" button
in SceneEditor.

### Verification

- `default-scene.test.ts`: `setProfile auto-upgrades an untouched legacy
  Cursor scene to the current layout` (id preserved, grid/action types
  updated) and `setProfile leaves a customised Cursor scene alone` (one
  substituted button action is enough to opt out).
- Full frontend suite: 59 files / 253 tests green; `vue-tsc --noEmit`
  clean.

## Follow-up 3: the Quick Templates gallery deck was still on the old design (2026-09-25)

### Problem

The user's "all IDEs, same layout, based on Claude" directive applies
beyond the profile-bootstrap scenes above: `backend/scripts/
generate_dev_templates.py`'s `cursor_deck()` — the "Cursor AI" entry in the
in-app Quick Templates gallery (`/api/templates`, unrelated to
`defaultProfile.ts`) — still built the pre-fix layout (Composer, Chat, Full
Composer, Palette, Quick Open, Find in Files, Sidebar), completely
independent of the frontend fix. Anyone importing that gallery template
would land back on an inconsistent Cursor deck regardless of the
`isUntouchedLegacyCursorScene` migration above.

Regenerating also surfaced an unrelated, pre-existing drift: the checked-in
`dev-claude-code.json` still referenced `cc_prompt`/`cc_submit`, action
types that no longer exist in the backend catalog (renamed to
`claude_prompt`/`claude_slash` at some point without re-running the
generator) — that gallery template was silently stale/broken before this
change, independent of anything in this design log entry.

### Fix

Rebuilt `cursor_deck()` to mirror `claude_code_deck()`'s row structure —
row 0 and 1 are agent-prompt actions (New Agent, Review, Commit, Explain,
Write Tests, Ask, Continue, Fix Tests) plus Accept/Reject, row 2 is
utility (Terminal, Inline Edit, Copy, CPU, Memory), row 3 is page nav +
Clock — using the same 4x5 grid and button count (18) as the Claude deck,
so the two read as one family in the gallery. Ran `python scripts/
generate_dev_templates.py` to rewrite both `dev-cursor-ai.json` (new
layout) and `dev-claude-code.json` (incidentally resynced to its current
source, fixing the stale `cc_prompt`/`cc_submit` action types).

### Verification

- `generate_dev_templates.py`'s own catalog validation: `6 decks written,
  all action types valid.`
- Full backend suite: `854 passed`.
