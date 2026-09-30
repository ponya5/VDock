# Contract — Socket.IO events

FIXED. Emitters and consumers code against these exact names and payload
shapes. All are server→client broadcasts. Frontend subscribes via
`socketClient.on('<event>', cb)` from `frontend/src/api/socket.ts`.

## `now_playing` — W1 emits; W1 widget + W7 conditional rules consume

```json
{
  "playing": true,
  "title": "Song",
  "artist": "Artist",
  "album": "Album",
  "source_app": "spotify.exe",
  "position_s": 42.5,
  "duration_s": 201.0,
  "has_art": true,
  "ts": 1759200000.0
}
```

Emitted only on change (track, play state, or first poll). `position_s` may be
absent; `duration_s` may be 0/unknown. When nothing plays:
`{"playing": false, "title": "", "artist": "", "album": "", "source_app": "", "has_art": false, "ts": ...}`.

Album art is NOT in the payload — fetch `GET /api/now-playing/art?ts=<ts>`.

## `audio_spectrum` — W2 emits; W2 widget + W7 (optional) consume

```json
{ "bands": [0..100 x20], "level": 0, "live": true, "ts": 1759200000.0 }
```

- `bands`: exactly 20 ints 0–100, low→high frequency (30 Hz–16 kHz log-spaced).
- `level`: overall 0–100.
- `live`: true while audio is actually playing; heartbeat
  `{bands:[0…], level:0, live:false, ts}` ~every 2 s when silent.
- Max rate ~14 Hz; emit only when a band moved ≥2 or `live` flipped.

## `panel_notification` — W5 + W6 emit; W4 consumes

```json
{ "source": "mcp|trigger|<free>", "title": "Build done", "message": "…", "ts": 1759200000.0 }
```

Title ≤80 chars, message ≤300. Consumers show a toast + notification-center
entry. `source` labels the origin ('mcp', 'trigger', or a caller tag).

## `navigate_scene` — W5 + W6 emit; orchestrator's frontend listener consumes

```json
{ "scene": "Claude Code" }
```

Scene name (case-insensitive match against the active profile). If the name
doesn't match, receivers do nothing.

## `trigger_fired` — W5 emits; orchestrator + W5 panel consume

```json
{ "id": "trg_x", "label": "Evening scene", "ok": true, "detail": "…", "ts": 1759200000.0 }
```

`ok:false` + `detail` when the trigger's action failed.

## `agent_alert` — W4 emits (extended, back-compatible); W4 consumes

```json
{
  "alert":  { "source": "claude", "message": "…", "project": "…", "cwd": "…", "ts": 0 },
  "alerts": [ { "source": "claude", "message": "…", "project": "…", "cwd": "…", "ts": 0 } ]
}
```

`alert` = newest alert or null (unchanged legacy semantics). `alerts` = all
pending per-source alerts, newest first (new field). Existing fields on the
alert object unchanged.

## Existing events consumers may subscribe to (do NOT re-emit)

- `system_volume {value: 0-100, muted: bool}` — 1.5 s cadence, on change.
- `agent_state {states: {<source>: {source, state, message, cwd, project,
  prompt, reply, prompted, ts, session_count}}}` — on change.
- `toggle_state`, `action_result`, `ui_command`, `user_settings_updated`,
  `background_job` events — unchanged.
