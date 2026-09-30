# DL-128 — State-split Play/Stop media button

## Problem

A media scene spends two cells on Play/Pause and Stop — and the Stop key
is a dead cell while nothing is playing. One button should do the right
thing for the current transport state: **Stop while media plays, Play
when it doesn't.**

## Design

`media_play_stop` — a new `cross_platform` sub-action that resolves the
keypress at dispatch time against the SMTC snapshot the now-playing
service already polls:

- `snapshot().playing === true` → sends `media_stop`
- otherwise → `media_play_pause` (resumes a paused session; a no-op when
  nothing ever played)

The split lives **in the backend**, not the frontend press path — so the
same button works when fired by the panel, a trigger, or an MCP
`run_action` call. On non-Windows hosts or before the first snapshot,
`playing` is absent → it plays. `now_playing` is imported lazily inside
the method so the action module keeps zero service coupling at import.

**Face** (`DeckButton.resolvedVisual`): for `media_play_stop` buttons the
icon swaps on the live `conditionalState.nowPlaying.playing` feed —
`fas:stop` while playing, `fas:play` otherwise — and the secondary label
reads the pending action (`Stop`/`Play`), same convention toggle buttons
use for their on/off side. Explicit `rules` still win the icon slot
(rulePatch applies after, unchanged precedence).

**Discoverable:** `Play / Stop` entries in the action catalog, the Media
button-template group, and the system preset list.

**Migration:** the user's Media scene keeps the Play/Pause cell (now the
merged button, labelled "Play / Stop") and drops the separate Stop cell —
one free slot, per the ask. Profile file backed up before edit.

## Trade-offs

- Play and Stop mean different transports (stop kills position; pause
  keeps it) — the merged button *stops* when playing. Pause-only control
  stays available as the separate Play/Pause action.
- The face reads the same feed the rules engine reads, so a rule
  override on the same button can still restyle the swapped state.

## Implementation Results

Shipped as designed:

- `cross_platform_action.py`: `media_play_stop` in `VALID_ACTIONS` +
  dispatch; `_media_play_stop()` lazily reads `services.now_playing
  .snapshot()` — `playing is True` → `_media_stop()`, else
  `_media_play_pause()` (paused, empty, or unreadable snapshot all
  resolve to play).
- `catalog.py`: `Play / Stop` action spec — pickers list it everywhere
  (deck press, triggers, MCP `run_action` all reach the same handler).
- `DeckButton.vue` `resolvedVisual`: `media_play_stop` buttons swap
  icon (`fas:stop` playing / `fas:play` otherwise) and secondary label
  (`Stop`/`Play`) on `conditionalState.nowPlaying.playing`; rule patches
  still take precedence.
- `buttonTemplates.ts` + `presets/system.ts`: `Play / Stop` entries.
- Profile migration: the Media scene's Play/Pause cell is now the merged
  button (`Play / Stop`); the standalone Stop cell was removed — backup
  at `data/backups/profile-dl128-*.json`.

**Live-verified end-to-end** on the running backend: Spotify playing →
`POST /actions/execute` `media_play_stop` → `playing:false` in 2 s;
fired again → `playing:true`. Playwright screenshot shows the merged
"Play / Stop" cell rendering the stop icon + "Stop" sublabel mid-track.

Tests: 5 backend dispatch cases + catalog auto-coverage
(`test_media_play_stop.py`), 6 frontend face tests incl. live feed flip
(`play-stop-button.test.ts`). Suites: **1099 backend**, **496 frontend**,
vue-tsc clean, dist rebuilt.

Deviation: the separate `media_stop`/`media_play_pause` actions and the
preset entries stay — merged cell is additive, pause still exists as its
own transport when wanted.
