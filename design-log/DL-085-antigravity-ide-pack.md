# DL-085 — Antigravity IDE pack + AI Coding template

## Problem

Antigravity (Google's agentic IDE, Code-OSS based) exists in the template
gallery only as a URL card under "AI Platforms" — a single "Open
Antigravity" button pointing at antigravity.ai. It belongs in "AI Coding"
with real actions, like the Cursor pack: keystrokes routed to the running
IDE, an AppProfile so scene detection/agent-bar work, and an app-path
override so "can't find antigravity.exe" is fixable the same way
cursor.exe was (DL-084).

## Keybindings (verified against Antigravity docs)

- `Ctrl+Shift+I` — open/focus the agent panel (idempotent — safe to
  prefix typing)
- `Ctrl+L` — toggle the agent panel
- `Ctrl+Shift+L` — new conversation thread on the agent surface
- `Ctrl+E` — toggle Editor ↔ Agent Manager
- `Ctrl+I` — inline AI command (editor or terminal)
- `Enter` submits the agent input; `Shift+Enter` is the newline
- `Esc` halts the active stream
- Editor/navigation chords are inherited VS Code: `Ctrl+Shift+P`,
  `Ctrl+P`, ``Ctrl+` ``, `Ctrl+B`, `Ctrl+Shift+F`, `Ctrl+,`

## Changes

- `keymaps/base.py`: `ANTIGRAVITY_EXES = ('antigravity.exe',)` + export.
- `keymaps/antigravity.py` (new): `ANTIGRAVITY_COMMANDS` +
  `ANTIGRAVITY_PROFILE` — prompt/followup/submit/stop, agent panel,
  new thread, Agent Manager, inline command, and the inherited VS Code
  nav set. Follow the Cursor pattern: never prefix typing with a
  *toggle* chord, focus with the idempotent `Ctrl+Shift+I` first.
- `keymaps/__init__.py`: register the commands + profile.
- `integrations/antigravity_pack.py` (new): `KeystrokeEditorPlugin`
  subclass, `plugin_id='antigravity'`.
- `integrations/context.py`: `'antigravity.exe': 'Antigravity'` in
  `EDITOR_EXECUTABLES` (project-name window-title parsing).
- `integrations/agent_state.py`: add `'antigravity'` to
  `ALLOWED_SOURCES` + `_LIVENESS_SOURCES` so a future Antigravity hook
  is accepted and liveness-pruned (`session_alive('antigravity')`
  matches antigravity.exe). No hook ships yet, so the profile's
  `unknown` state row only appears if a user wires one up.
- `appTemplates.ts`: move the `antigravity` card from `aiPlatforms`
  into `aiCoding`, buttons wired to the new `antigravity_*` action ids.
  The old aiPlatforms URL card is removed — one Antigravity entry.
- `appPaths.ts`: add `antigravity` to `launchApps` (card gear already
  derives `antigravity` from the template id; the panel row covers
  users without the card installed). Probe candidates need no change —
  the generic paths cover `Programs\antigravity\Antigravity.exe`,
  `/Applications/Antigravity.app`, `/usr/bin/antigravity`.

## Risks

- `Ctrl+Shift+I` colliding with devtools on a Code-OSS build — it is
  Antigravity's documented agent-panel binding.
- `Esc` as "stop" is deliberately bound to a named command only (not
  auto-fired) so it never interrupts a user mid-keystroke.
- No `permission` state row — Antigravity has no shipped hook, mirroring
  the Cursor comment.

## Implementation Results

Implemented as designed:

- **Backend**: `ANTIGRAVITY_EXES` in `base.py`; new
  `keymaps/antigravity.py` (14 commands — prompt/followup/submit/stop,
  agent panel, new thread, Agent Manager, inline command, palette,
  quick open, terminal, sidebar, find-in-files, settings) and
  `ANTIGRAVITY_PROFILE` (`status_source='antigravity'`,
  `prompt_command='antigravity_followup'`, 2×4 default layout);
  `antigravity_pack.py` plugin; `context.py` window-title name;
  `agent_state.py` accepts + liveness-prunes an `antigravity` source.
- **Frontend**: the `antigravity` card moved from AI Platforms to AI
  Coding (10 buttons wired to `antigravity_*` action ids + an
  `open_app` launcher); the old URL-only card removed so exactly one
  Antigravity entry exists; `antigravity` added to `launchApps` for the
  path-override panel (the card gear also derives `antigravity` via
  `templateAppKey`'s open_app stem).
- **Verification**: `plugin_manager.load_builtin_packs()` loads
  `antigravity`; `profile_for_exe('Antigravity.exe')` resolves;
  `GET /api/app-profiles` serves the profile live; probe endpoint
  returned the real install
  `…\AppData\Local\Programs\antigravity\Antigravity.exe` on the dev
  machine — Antigravity is installed there and the generic candidate
  paths cover it, so no vendor_dir was needed.
- **Tests**: 3 new keymap assertions (union membership, submit focuses
  before Enter, typing commands never lead with the Ctrl+L toggle) +
  3 new frontend tests (category placement/single entry, real action
  ids, path-key derivation). Suites: 900 backend, 301 frontend green,
  `vue-tsc` clean, `dist` rebuilt.
- **Deviation**: Property 8 flagged the pre-existing bare
  `font-size: 16px` iOS anti-zoom override in `AppPathEditor.vue`;
  rewritten as `clamp(16px, 1rem, 18px)` (same ≥16px floor).


### Addendum: Cursor card + category order

- `cursor` template added to `aiCoding` — 11 buttons wired to the
  existing `cursor_*` pack (prompt/followup/submit/cancel/chat/
  composer/inline/accept/reject/terminal) + an `open_app` launcher so
  the card gear derives the `cursor` path key. No `logo` (no
  cursor.png asset ships) — the `i-cursor` FA icon renders instead.
- `templateCategories` reordered: `ai-coding` now precedes
  `ai-assistants` — AI Coding leads the gallery.
- Tests: cursor-in-ai-coding + category order assertions in
  `app-paths.test.ts`. Verified live (AI Coding first, 8 templates,
  Cursor card present); `vue-tsc` clean, `dist` rebuilt.
