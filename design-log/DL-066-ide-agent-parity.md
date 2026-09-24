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
  Visual Studio prompt commands, the Claude-style Cursor scene rebuild, the
  user-profile migration, and the Cursor hook installation are still
  pending — tracked as follow-up work in this same entry.
