# DL-116 — Now Playing (SMTC) monitor + screensaver widget

## Background

Windows exposes what is playing system-wide through SMTC (`GlobalSystem
MediaTransportControlsSessionManager`) — the same data the OS media flyout
shows: track title/artist/album, album art, play/pause state, position, and
the source app. On a 7" panel whose job is to mirror the machine, "what's
playing" is the most glanceable ambient signal there is. The screensaver
already shows weather, markets, headlines — this adds the media card.

## Problem

Nothing in VDock reads SMTC today. Media controls exist (`media_play_pause`
etc.) but are write-only: the deck can command playback yet can never *show*
it. To display now-playing we need:

- a backend poller that turns SMTC's pull-model API into a push channel
  (socket event on change only),
- a REST snapshot + album-art endpoint so a freshly loaded or reconnected
  client re-syncs without waiting for the next change,
- a frontend reactive service + a screensaver widget matching the
  `.ss-section` visual language, with honest unavailable states when SMTC
  isn't there (non-Windows host, `winsdk` not installed).

`winsdk` is an optional dependency: the module must import and idle
gracefully without it, and the REST endpoint then reports
`available: false` so the widget shows its honest "not supported" state.

## Design

### `backend/services/now_playing.py`

Mirrors `services/volume_monitor.py` exactly in shape: `set_emitter` /
`set_spawner` / `start(interval)` driving a daemon poll loop at ~1.5 s
(`socketio.start_background_task` in app.py — threading-mode Socket.IO drops
emits from foreign threads, DL-052).

- The SMTC fetch is one replaceable module function,
  `_fetch_snapshot(previous_key)`, so tests inject a fake reader without
  touching Windows APIs. It lazily imports
  `winsdk.windows.media.control`; on ImportError or a non-Windows platform
  the module marks `available = False` and the loop idles.
- winsdk APIs are async; the worker thread runs them on a private
  thread-local `asyncio` loop (`run_until_complete`) — one loop reused per
  poll, never `asyncio.run` churn, and no asyncio objects shared across
  threads.
- Per poll: `request_async()` → `get_current_session()` →
  `try_get_media_properties_async()` + `get_playback_info()` +
  `get_timeline_properties()`. Every call is wrapped defensively; a failed
  poll keeps the last state and emits nothing (volume-monitor semantics).
- Emits socket event `now_playing` per `contracts/socket-events.md` —
  `{playing, title, artist, album, source_app, position_s?, duration_s?,
  has_art, ts}` — only when the *identity key*
  `(title, artist, album, source_app, playing, has_art)` changes. Position
  ticks do not emit; the widget extrapolates locally. First successful read
  always emits; a "nothing playing" transition emits the empty payload.
- Album art is fetched once per track change (thumbnail →
  `open_read_async()` → `DataReader.load_async` + `read_bytes`), written to
  `Config.DATA_DIR / 'now_playing_art.bin'`, content-type remembered in
  module state. A track change to no-art (or nothing playing) deletes the
  stale file so `has_art:false` and the 404 agree.
- Latest snapshot kept in module state for the route:
  `available()`, `latest_track()` (None when nothing plays),
  `art_path()`, `art_mime()` (falls back to JPEG/PNG magic-byte sniffing so
  a backend restart still serves the cached file).

### `backend/routes/now_playing.py`

Blueprint `now_playing_bp` (url_prefix `/api`), `@require_auth` like other
client-facing reads:

- `GET /api/now-playing` → `{success, available, track|null}`.
- `GET /api/now-playing/art` → image bytes via `send_file`, 404 when none.

### `frontend/src/services/nowPlaying.ts`

Reactive singleton like `services/agentState.ts`: subscribes
`socketClient.on('now_playing')` (any event implies `available`), re-syncs
via `GET /api/now-playing` on socket connect, self-initializes on first
`useNowPlaying()` call so no orchestrator wiring is needed. Exposes
`{ track, playing, available, artUrl }`; `artUrl` is
`/api/now-playing/art?ts=<track ts>` when `has_art` (the `ts` cache-buster
makes art swap atomically with the track payload).

### `frontend/src/components/screensaver/NowPlayingWidget.vue`

`.ss-section` visual language: small-caps "Now Playing" head + hairline,
album art square (FontAwesome music-icon fallback), title (ellipsis),
artist, source-app tag (`.exe` stripped), play/pause glyph, thin progress
bar from `position_s`/`duration_s` that ticks forward locally at 1 Hz while
playing. States: loading → data; `available === false` → muted "Not
supported on this system"; supported-but-silent → dim "Nothing playing".
`layoutEdit` prop accepted and ignored per the widget contract.

## Implementation Plan

1. `services/now_playing.py` — lazy winsdk import, async fetch helper,
   identity-key change detection, art cache, snapshot getters.
2. `routes/now_playing.py` — the two endpoints.
3. `tests/test_now_playing.py` — fake-reader emit-on-change, art cache
   write/delete, route shapes via a local Flask app, art 404/200.
4. `services/nowPlaying.ts` + `NowPlayingWidget.vue`.
5. Orchestrator wires `app.py` (emitter/spawner/start + blueprint) — noted
   in `collab/messages/now-playing.md`.

## Trade-offs

- **Poll vs. SMTC events**: SMTC has `SessionsChanged`/`MediaPropertiesChanged`
  callbacks, but winsdk event subscriptions need a living asyncio loop and
  COM-agile handler plumbing; a 1.5 s poll matches volume_monitor's proven
  pattern and is effectively free. Lag ≤ ~1.5 s — fine for a screensaver.
- **Art on disk vs. memory**: the file survives the request cycle and a
  restart, and lets `send_file` stream; a `.bin` name + sniffed mimetype
  avoids extension churn.
- **Emit-on-change key excludes position**: emitting every poll just to move
  a progress bar would churn the socket; the widget extrapolates between
  emits and re-anchors on the next change.

## Verification Criteria

- `pytest tests/test_now_playing.py -q` green: first read emits, identical
  reads don't, track/play-state/nothing-playing transitions emit the exact
  contract payloads, art written on change / deleted on no-art track,
  `{available:false, track:null}` without winsdk, art 404 then 200.
- `import services.now_playing` never raises without winsdk; `start()` idles.
- Widget renders the three honest states; progress bar advances while
  `playing` and freezes on pause.

## Implementation Results

Implemented as designed; all deliverables verified by tests.

**Built**

- `backend/services/now_playing.py` — `set_emitter`/`set_spawner`/`start`
  identical to `volume_monitor`; ~1.5 s daemon loop gated on a cached
  `_smtc_supported()` probe (Windows + lazy winsdk import). The SMTC read is
  one replaceable seam, `_fetch_snapshot(previous_track_key)`, run on a
  thread-local asyncio loop (`_run_on_worker_loop` — asyncio objects never
  cross threads). Emits `now_playing` on identity change
  `(title, artist, album, source_app, playing)`, first read, and detected
  seeks (`|Δposition − interval| > 2 s` — an extension so the widget's
  progress bar re-anchors after scrubbing). Album art extracted once per
  track change (`open_read_async` → `DataReader.load_async` → `read_bytes`,
  with the old winsdk fill-array signature as fallback), written
  atomically to `DATA_DIR/now_playing_art.bin`; deleted when the new track
  has none or nothing plays. `available()` / `latest_track()` /
  `snapshot()` / `art_path()` / `art_mime()` (magic-byte sniff fallback)
  exposed for the route and for W6's `get_now_playing`.
- `backend/routes/now_playing.py` — `now_playing_bp` (`url_prefix='/api'`):
  `GET /api/now-playing` → `{success, available, track|null}`;
  `GET /api/now-playing/art` → `send_file` with stored/sniffed mimetype,
  404 when absent. Both `@require_auth`.
- `backend/tests/test_now_playing.py` — 12 tests, fake reader injected at
  the module seam; routes tested on a fresh Flask app (no app.py coupling).
- `frontend/src/services/nowPlaying.ts` — reactive singleton; subscribes
  `now_playing`, re-syncs `GET /api/now-playing` on `connect`, self-inits on
  first `useNowPlaying()`. `available` is tri-state (`null` = loading).
- `frontend/src/components/screensaver/NowPlayingWidget.vue` — `.ss-section`
  language, art + FA fallback, ellipsis title, source tag (`.exe`/AUMID
  stripped), play/pause badge, 1 Hz local progress extrapolation clamped to
  `duration_s`, img `@error` icon fallback; three honest states.
- `frontend/src/tests/now-playing.test.ts` — 10 tests: service socket/REST
  behavior + widget mount (compile + render states).

**Verified**

- `cd backend && ./venv/Scripts/python.exe -m pytest tests/test_now_playing.py -q`
  → 12 passed.
- `cd frontend && npx vitest run src/tests/now-playing.test.ts` → 10 passed.
- Full backend suite: 1016 passed; 1 unrelated failure in W6's
  `test_mcp.py::test_set_volume` (parallel work-in-progress, not mine).
- `import services.now_playing` + `start()` smoke-tested without winsdk:
  idles, `available() → False`, no exceptions.

**Known limits / deviations**

- Seek emits are an addition beyond the minimal spec — same "emit on
  change" contract, more useful widget. Position ticks still never emit.
- Replaying the *identical* track (same title/artist/album/app while
  playing) produces no emit — the seek heuristic catches most real cases;
  a paused→replay edge can leave the local bar clamped at 100 %.
- winsdk not installed yet (orchestrator owns requirements); the art-read
  path targets current winsdk (`read_bytes(size) → list`) with a
  best-effort fallback for the legacy fill-array signature — worth a live
  check on real SMTC at integration.
- Live verification on real SMTC still pending winsdk install — the unit
  tests cover contract/logic only.

## Follow-up — poll-thread death on album-art write (fixed)

**Symptom reported:** `/api/now-playing` returned `track: null` while
Spotify was actively playing — the screensaver widget could never show a
track.

**Root cause (live-reproduced):** two stacked defects in the art path.

1. `_read_thumbnail`'s fallback for the winrt-* binding created
   `Array('B')` with **no size** — `read_bytes` filled zero bytes, so the
   coroutine returned `art = (None, mime)`.
2. `_poll_once` calls `_replace_art` *outside* its own `try`. The service
   then called `tmp.write_bytes(None)` → `TypeError: memoryview: a
   bytes-like object is required` — uncaught → **the daemon poll thread
   exited on its first tick that saw a thumbnailed track**. `available()`
   stayed `True` (it's a static binding check), so the route looked
   healthy while never producing a snapshot. Diagnosed via `py-spy` —
   `Thread-5 (_loop)` was absent while volume/spectrum/triggers threads
   were alive.

**Fixes in `services/now_playing.py`:**

- `_read_thumbnail`: `Array('B', size)` — the buffer is allocated to the
  stream length so winrt's out-param `read_bytes(arr)` actually fills it
  (live-verified: 97 KB Spotify PNG decoded).
- `_replace_art`: a tuple with falsy `data` now drops the stale file
  instead of writing it, and the cache write catches `Exception` (art is
  decorative — it must degrade, never propagate).
- `_loop`: last-resort `try/except` around the whole tick logs
  `Now-playing poll tick failed` and keeps polling — no single-tick edge
  can ever kill the thread silently again.

**No new dependencies or hooks:** the fix is entirely inside the existing
native SMTC path. YouTube-in-browser flows through the identical API
(Chrome/Edge/Firefox publish Media Session metadata to SMTC) — no
browser-specific code required.

**Verified**

- Reproduced the crash pre-fix (`_poll_once` → TypeError on poll 0).
- Post-fix, six live polls: snapshot returns real Spotify track
  (`title`/`artist`/`position_s`), 97–223 KB PNG art cached, thread
  survives.
- `pytest tests/test_now_playing.py` → 14 passed (2 new regressions:
  `(None, mime)` art tuple drops stale file without raising; `_loop`
  continues after a tick-level exception).
- Backend restarted; `py-spy` shows `Thread-5 (_loop)` alive at
  `now_playing.py:166`; `GET /api/now-playing` returns the live Spotify
  track and `GET /api/now-playing/art` serves `image/png` (~220 KB).

## Follow-up — source-site branding for the no-art fallback (2026-02-20)

**Motivation.** YouTube videos in Chrome publish SMTC metadata without
album art, so every now-playing surface fell back to the generic music
glyph even though the source was clearly identifiable.

**Backend (`services/now_playing.py`)**

- Payload gains a normalized `site` field (e.g. `youtube`, `spotify`,
  `twitch`; `''` when unknown). `empty_payload()` emits `site: ''`.
- `detect_site(source_app, title)` — app-id substring hints for native
  apps (spotify, yt music, netflix, twitch, prime, jellyfin, plex,
  tidal, deezer, vlc, apple music, disney+…); for **browser** source
  apps (chrome/edge/firefox/opera/brave/vivaldi/arc…) it scans visible
  window titles, requiring the track title to appear in a window title
  that names a known site; a weak fallback matches a known-site window
  when the track title isn't found (SMTC often reformats titles).
- Site is resolved **once per track** and cached on the poll state —
  the window-title scan never runs per-tick.

**Frontend**

- `services/nowPlaying.ts`: `NowPlayingTrack.site`; shared helpers
  `nowPlayingIcon(track)` → `['fab', <brand>]` or `['fas','music']`
  fallback, and `nowPlayingSourceLabel(track)` → friendly site name
  (YouTube, Spotify…) ahead of the raw exe name.
- All three surfaces — `SpectrumStage` media card, `NowPlayingWidget`,
  `NowPlayingButtonFace` — use the helpers for their no-art fallback
  icon and source kicker. Album art still wins whenever it exists.

**Verified**

- `pytest tests/test_now_playing.py` → 20 passed (6 new: app-hint skip,
  browser title match, weak match, no-known-site, non-browser, and
  site-stamped-once-per-track).
- Frontend: spectrum-stage + now-playing-button suites 28/28 green;
  `npm run build` clean → `dist` rebuilt.
