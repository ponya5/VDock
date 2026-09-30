# DL-129 — Now Playing deck button

## Problem

The deck knows what's playing (DL-116 SMTC feed) but nothing on a scene
*shows* it — the Media scene is transport controls only, and the user has
to guess which app owns the session before tapping anything.

## Design

A new action type `now_playing` (`runs_on=RUNS_FRONTEND`): the face
renders the live SMTC track — album art, title, artist, source app, and
a play/pause state glyph — and a tap dispatches `media_play_pause`
(client-orchestrated, same seam timers use), so the 2-cell card is also
a working transport.

- `NowPlayingButtonFace.vue` — the face component in the DeckButton
  `v-else-if` chain (weather/calendar/slider precedent); reads
  `useNowPlaying()`. No track → honest "Nothing playing" state; SMTC
  unavailable → "No media session". Art uses `/api/now-playing/art` with
  the payload's `ts` cache-buster.
- `isSpecialActionType` gains `now_playing` so the stock icon/label don't
  double-render; `ActionType` union + `FALLBACK_DISPLAY_ONLY_EXACT`? No —
  it's not display-only: press toggles. The naming fallback stays as is.
- Catalog `ActionSpec` in `category='media'` so the button-actions list
  offers it under Media controls; `buttonTemplates.ts` entry with
  `size {cols:2,rows:1}` (the established "wide" cell, same as the
  slider).
- Default Media scene: Now Playing at row 1 cols 3–4 beside the
  transport row, and the default swaps Play/Pause+Stop for the DL-128
  merged `media_play_stop` cell.
- The user's existing Media scene gets the same edit: Now Playing fills
  row 1 cols 3–4 (the Stop cell was freed in DL-128).

## Trade-offs

- 2×1 (two cells wide, one tall) — matches the volume slider's span and
  the user's "2X size" wording; a 2×2 card would crowd the 6-col grid.
- Tap = play/pause, not play/stop: pausing keeps position and is the
  least surprising transport for a face that also displays state.
- The face is read-only for position (progress bar only when the app
  reports duration; position ticks on snapshot cadence, ~1.5 s — no
  per-frame interpolation on a button).

## Implementation Results

Shipped and live-verified on the running deck.

- **Catalog**: `ActionSpec id='now_playing'` under `category='media'`,
  `runs_on=RUNS_FRONTEND` (not widget — the tap *does* dispatch, just
  through the client). `NOW_PLAYING = 'now_playing'` added to
  `models/button.py`'s `ActionType` enum — required by the catalog
  consistency test that every catalog type is persistable.
- **Face**: `NowPlayingButtonFace.vue` — art thumb (greyscale-fallback
  music glyph when `has_art` is false), title, `artist · source` (`.exe`
  stripped), PLAYING/PAUSED state line, 3px progress bar when the app
  reports a duration. Empty states: "Nothing playing" (session, no
  track) and "No media session" (`available=false`).
- **DeckButton**: `now_playing` branch in the special-face chain +
  `isSpecialActionType` so the stock icon/label don't double-render.
- **Press**: `executeButtonAction` intercepts `now_playing` before the
  generic dispatch and routes to `cross_platform media_play_pause` —
  the same seam timers use. The widget type itself never reaches the
  backend. (Not added to `FALLBACK_DISPLAY_ONLY_EXACT` — by design,
  it's interactive.)
- **Create paths**: `ButtonTemplate.size?` and `ButtonPreset.size?`
  fields added; `applyTemplate` in ButtonEditor and `presetToButton`
  honor them — every creation path (templates, presets, catalog)
  produces the 2×1 span.
- **Factory scene**: Now Playing at row 1 cols 3–4; Play/Pause + Stop
  replaced by the DL-128 merged `media_play_stop` cell.
- **Live profile**: Now Playing added at row 1 cols 3–4 of the 6×3
  Media scene (backup in `data/backups/profile-dl129-*.json`).

**Verified**: Playwright — card renders on the Media scene at
`grid-column: 4 / span 2`, showing live SMTC data ("Waves Of Silence —
Lynnic · Spotify", PLAYING, progress). Catalog API lists it under Media
Controls. Tests: 10 new frontend (face states, press dispatch, catalog
wiring, default-scene span + collision); the seeded-buttons allowlist
gained `now_playing`. Suites: **1103 backend, 506 frontend**,
`vue-tsc` clean, `dist` rebuilt.
