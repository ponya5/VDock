# DL-092 — Generic agent hooks + install dropdown

## Problem / ask

Integrations screen hardcodes "Claude Code hook" / "Cursor hook" rows
and Claude-specific alert copy. User wants hook install generalized to
a dropdown over supported agents, and the alert language made generic.
Machine has Claude Code, Cursor, Antigravity.

## Design

**Antigravity support** (new `_TARGETS` entry): writes named hook
`vdock-agent-state` into `~/.gemini/config/hooks.json` (documented
global path). Events: PreInvocation/PreToolUse/PostToolUse/
PostInvocation → working; Stop → ready. Command embeds
`--event <Name>` so the state mapping doesn't depend on Antigravity's
stdin field names (they differ from Claude's `hook_event_name`).
Ownership recognized by HOOK_MARKER in commands; same merge/backup/
idempotent rules as the other targets.

**Hook script**: new `--event` arg; when present it supplies the event
name instead of the stdin payload. Antigravity state map added.

**API**: `hook-status?agent=all` returns every agent's status in one
call for the dropdown.

**UI**: one "Agent hooks" row — select lists each supported agent with
its install state (installed / partial / not installed); button reads
Install or Reinstall from the selected agent's status; a compact chip
per selection shows the settings file state. Header chip becomes
"N/M agents hooked". Alert copy generalized ("an agent"), Claude's row
still names its settings path.

## Implementation Results

- `agent_hooks.py`: `antigravity` target — writes a named
  `vdock-agent-state` entry into `~/.gemini/config/hooks.json`; loop
  events get bare command entries, tool events get matcher+hooks shape
  (mirrors Antigravity's documented schema); every command carries
  `--event <Name>` + `--source antigravity` + `--port`.
- `vdock_agent_hook.py`: `--event` flag; when set it seeds
  `hook_event_name`/`event` so `map_event` doesn't depend on the
  agent's stdin shape. `AGY_STATE_BY_EVENT`: PreInvocation/PostInvocation/
  PreToolUse/PostToolUse → working, Stop → ready.
- `hook-status?agent=all` returns all three agents' states in one call
  — the dropdown renders from it.
- Settings → Integrations: per-agent rows replaced by an "Agent hooks"
  row — select annotates each option (hooked / partial / not hooked),
  the description shows the selected agent's settings path, button
  reads Install/Update/Reinstall per state; header chip →
  "N of 3 agents hooked". Alert copy now says "a hooked agent".
- **Live on this machine**: Claude (already), Cursor
  (`~/.cursor/hooks.json`), Antigravity (`~/.gemini/config/hooks.json`)
  all installed — options show "— hooked", chip reads "3 of 3".
  Simulated antigravity POST accepted → `states` shows
  `antigravity: ready` — and the real "Agent needs you" banner +
  frame glow fired from the pipeline during testing.
- Also fixed: `feedback.py` used `X | Y` syntax which the
  min-Python-3.9 test rejects → dropped the annotation. 917 backend /
  306 frontend green, `vue-tsc` clean, `dist` rebuilt.
- Refs: `design-log/refs/agent-hooks-dropdown-*.png`.
