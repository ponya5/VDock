# DL-058: Backend silent crash — COM apartment violation + 500 toast spam

## Problem

The user launched VDock, opened Settings, and was hit with a stack of
"Server Error — An internal server error occurred" toasts plus
"Logs unavailable — Request failed with status code 500".

Investigation showed the backend process had **died silently** at 21:37 —
`vdock-backend-launcher.log` stops mid-poll with no traceback. After that,
every `/api/*` request failed: through the Vite dev proxy a dead upstream
surfaces to the browser as HTTP 500, and each failed request raised its own
toast (the client's throttle only covers network errors and 429s).

## Root cause

`vdock-backend-launcher.err.log` is littered with:

```
OSError: exception: access violation writing 0x0000000000000005
  File ".../comtypes/_post_coinit/unknwn.py", line 288, in __del__
    self.Release()
```

`CrossPlatformAction._windows_volume_interface()` calls
`comtypes.CoInitialize()` on whichever Flask worker thread happens to serve
the request, creates an `IAudioEndpointVolume` pointer, and returns it.
When the request finishes the Python object is garbage-collected — on an
arbitrary thread, in an arbitrary COM apartment (or none). `__del__` calls
`Release()` cross-apartment → access violation. These are usually printed
as "Exception ignored in __del__", but an AV raised inside a live
comtypes call bypasses Python exception handling entirely and terminates
the process instantly — matching the log-stops-mid-request signature.

## Design

### Dedicated COM apartment worker (backend)

Confine all Core Audio COM objects to a single long-lived thread:

- `_audio_worker_loop`: daemon thread, `CoInitialize()` once, lazily
  creates and **permanently holds** the `IAudioEndpointVolume` pointer in
  worker-local state — it is never garbage-collected, so `Release()` can
  never run on the wrong apartment. `CoUninitialize()` on shutdown.
- `_run_on_audio_thread(fn, timeout)`: submit a callable to the worker,
  wait on an `Event`, return result or re-raise. 5s timeout so a COM
  stall degrades to an action failure instead of a hung Flask worker.
- `_volume_set` / `_volume_get` run their endpoint calls inside the
  worker. NirCmd fallback for set is unchanged.
- Worker respawns (fresh queue) if it ever dies.

### 5xx toast throttle (frontend)

Extend the client's existing `lastErrorTime`/`errorThrottleMs` dedupe to
500 and 502/503/504 responses so a dead backend produces one toast per
window instead of one per failed request.

## Implementation Results

- `_windows_volume_interface` replaced by `_volume_scalar` + module-level
  `_run_on_audio_thread`/`_audio_worker_loop`: one daemon thread owns
  `CoInitialize`, lazily creates the `IAudioEndpointVolume` and holds it
  for the process lifetime — no GC, no cross-apartment `Release()`.
  Worker auto-respawns on death; jobs time out at 5s.
- Verified live: `volume_set 55 → get 55`, then 12 concurrent
  `volume_get` calls all answered 55 through the single worker — backend
  healthy, **zero access violations** in the log (previously the err log
  accumulated one per volume call).
- Bonus guard: `POST /api/actions/execute` with a non-object `action`
  now returns 400 instead of `AttributeError → 500` (found while testing).
- Frontend: 500/502/503/504 share an 8s toast window (`last5xxTime`) — a
  dead backend yields one toast per window instead of one per request.
- 782/782 backend tests, vue-tsc + production build pass.
