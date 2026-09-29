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

## Follow-up — cached endpoint pinned to a stale output device (2026-09-29)

**Symptom:** volume slider drags "succeeded" (badge updated, `volume_set`
returned success) but no audible change.

**Root cause:** the worker's `endpoint_box` latched the
`IAudioEndpointVolume` pointer for the process lifetime — resolved once
on first use and never re-queried. On a machine where the default output
changes (wireless headset docked, HDMI/panel audio, manual device
switch), the slider kept controlling whatever was default at first touch.
Verified live: backend `volume_get` returned 56 — the exact level of the
Lenovo H600 headset — while the active Realtek output sat at 34, proving
the running worker was pinned to the headset endpoint.

**Fix:** `get_endpoint()` now resolves `AudioUtilities.GetSpeakers()`
(the eMultimedia default, matching the Windows volume UI) fresh on every
job instead of caching. The DL-058 invariant is preserved — the pointer
is created inside the job on the COM thread and released there when the
job's reference drops; per-call errors (device unplugged) now recover
instead of latching permanently.

**Verification:** standalone script through the backend venv — get → 52,
set 30 → get 30, set 25 → get 25 (each call a fresh endpoint resolve).
936/936 backend tests pass. Requires a backend restart to reach the
running process.

## Follow-up 2 — the real crash mechanism: `cast()` aliasing, not just thread affinity (2026-09-29)

The previous follow-up's per-call re-resolution made the backend crash *worse* —
the process died under sustained volume traffic. The investigation found the
actual fault beneath both crashes:

**Root cause:** `cast(interface, POINTER(IAudioEndpointVolume))` does not AddRef —
the cast wrapper and `interface` alias the **same** native COM reference. The
original code leaked `interface` forever, which accidentally kept the endpoint
alive. Once cleanup released `interface` (or tracebacks carried wrappers to a
foreign GC), the COM object was freed while `endpoint` still pointed at it —
`GetMasterVolumeLevelScalar` then read a vtable at `0xFFFFFFFFFFFFFFFF`.
"Pointer churn" blamed earlier was mostly this use-after-free plus off-thread
`__del__`→Release from comtypes' self-cycled wrappers (bound-method caches mean
refcounting never frees them — only cyclic GC does, on whatever thread runs it).

**Fix (now in `cross_platform_action.py`):**

- `endpoint = interface.QueryInterface(IAudioEndpointVolume)` — a real second
  reference; `interface`/`devices` can be released independently.
- `_compointer_base.__del__` is patched once (`_install_com_gc_guard`):
  finalization on a foreign thread is deferred onto the audio worker's job
  queue instead of releasing in place — covers pycaw-internal leaks too.
- `_release_com` marks wrappers `_vdock_released` so no release fires twice.
- Endpoint lifetime is **cache + invalidate** (re-resolve on op failure, an
  `IMMNotificationClient` default-device-change callback on an MTA thread, or
  a 60 s TTL) with a 3 s resolve rate-limit so a flapping device cannot
  amplify churn.
- `gc.collect(0)` on the worker after each job sweeps wrapper cycles on the
  safe thread.

**Verification:** 300 reads + 50 sets across 3 threads with forced caller GC —
0 errors, process survived (previously exit 139 within seconds). Sustained
monitor polling + 25 rapid `volume_get` HTTP calls on the live backend —
stable. 936/936 tests.

This supersedes the "resolve per call" approach above: correctness (follows
device switches) now comes from invalidation signals, not churn.
