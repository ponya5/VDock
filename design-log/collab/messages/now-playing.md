# W1 — now-playing notes

## For the orchestrator (app.py wiring)

Mirror the `volume_monitor` block exactly:

```python
from services import now_playing
from routes.now_playing import now_playing_bp

now_playing.set_emitter(lambda event, payload: socketio.emit(event, payload))
now_playing.set_spawner(socketio.start_background_task)
app.register_blueprint(now_playing_bp)
# in main(): now_playing.start()   # next to volume_monitor.start()
```

- `start()` is safe to call unconditionally: without winsdk / off Windows it
  spawns a loop that idles (a cached False probe, no work per tick) and
  `GET /api/now-playing` reports `{available:false}`.
- `requirements.txt`: add `winsdk` (Windows-only; the module lazy-imports —
  nothing breaks if the platform marker excludes it).
- Frontend mount: widget id `nowplaying`, component
  `frontend/src/components/screensaver/NowPlayingWidget.vue`, label
  "Now Playing" (per widget-contract). No service init call needed —
  `useNowPlaying()` self-initializes inside the component.

## For W6 (mcp `get_now_playing`)

`services.now_playing` exposes:
- `snapshot()` → last emitted payload dict (may be the "nothing plays"
  empty payload) or `None` before the first poll.
- `latest_track()` → payload or `None` when nothing plays (same mapping as
  `GET /api/now-playing`'s `track` field).
- `available()` → bool. All tolerate winsdk being absent.

## For W7 (conditional rules)

The `now_playing` socket payload is exactly the contract shape
(`playing`, `title`, `artist`, `album`, `source_app`, optional
`position_s`/`duration_s`, `has_art`, `ts`). `now_playing.playing` is the
boolean rule source. Emits happen on track/play-state change, seeks, and
the nothing-playing transition — not on position ticks.

## Flags

- `backend/tests/test_mcp.py::test_set_volume` failed during my full-suite
  run (1016 passed, 1 failed) — that's W6's in-flight file, unrelated to
  W1. Recheck at integration.
- winsdk art-read path (`read_bytes(size) → list`) targets current winsdk;
  a fallback for the legacy `winsdk.system.Array` signature is in place but
  untested on the real API — verify once against real SMTC.
