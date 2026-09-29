# DL-115 — Volume slider live sync with the OS

## Intent

The `volume` slider is a two-way control, but today it is only two-way in one
direction: dragging writes to the OS, yet the displayed value is read once at
mount and never again. Change the level anywhere else — keyboard volume keys,
Windows Quick Settings, another app, a headset reconnect — and the deck keeps
showing the stale number until the view remounts. On a panel whose whole job
is to mirror the machine, a volume control that drifts out of truth reads as
broken (observed: OS at 56%, deck thumb at 0%).

The slider should sit in sync continuously, like the Windows volume flyout
itself: wherever the level is changed, every surface agrees within a moment.

## Frictions

- **Display staleness.** `SliderButtonFace` fetches `volume_get` once in
  `onMounted` and stays there. OS-side changes are invisible.
- **No push channel exists.** The OS has no HTTP route to call; the only way
  the deck learns about external changes is a backend-originated socket
  event. Flask-SocketIO in threading mode drops emits from threads the
  server did not spawn (DL-052 measured this), so any monitor must run
  under `socketio.start_background_task` like `job_runner`.
- **Push must not fight a drag.** While the user's finger is on the track,
  an inbound echo of the level would snap the thumb mid-gesture. The
  gesture is authoritative until pointer-up.
- **COM safety.** Volume reads on Windows must stay on the dedicated COM
  apartment worker (DL-058). A monitor thread cannot touch COM directly.

## Mechanical Translation

- `cross_platform_action` gains a module-level `read_output_volume()`
  returning `(percent|None, muted|None, err)` per platform:
  - **Windows** — scalar + `GetMute()` on the *current* default endpoint,
    executed on the audio worker (inherits the DL-058 threading invariant
    and the per-call endpoint resolution from the stale-endpoint fix).
  - **macOS** — one `osascript -e "get volume settings"` call, parsing both
    `output volume:` and `output muted:`.
  - **Linux** — `amixer get Master`, parsing `[NN%]` and `[on|off]`.
  `_volume_get` refactors to share it — one source of truth.
- New `services/volume_monitor.py` mirrors `job_runner`'s injected
  emitter + spawner pattern. `start()` spawns a loop (via
  `socketio.start_background_task` in `app.py`) that polls ~1.5 s and emits
  `system_volume { value, muted }` only when the tuple changes — first
  successful read always emits, failed reads emit nothing.
- `SliderButtonFace` (target `volume` only) subscribes to `system_volume`
  on mount, unsubscribes on unmount. On event: update `value` (clamped)
  and a new `muted` ref; skip the `value` write while `dragging` so the
  thumb is never yanked mid-drag. The badge follows reality — an external
  OS change updates it like a successful set does.
- `muted` joins the icon choice: muted at 56% shows the mute icon over the
  real level (Windows' own flyout semantics — the scalar survives mute).
- Poll-over-callback is deliberate: `IAudioEndpointVolumeCallback` would
  need an STA message pump the queue-based worker doesn't run. A ~1.5 s
  read is effectively free on Windows and a tiny subprocess elsewhere.
- `app_volume` sliders are untouched — session-level polling across process
  churn is a different problem.

## Core Loop

Change volume anywhere (keys, flyout, deck, headset dial) → next monitor
tick sees the new tuple → `system_volume` broadcasts → every connected
surface's volume slider moves to match. The deck is no longer a
write-only mirror.

## Design Proof

- Set volume via keyboard/OS flyout → the deck slider follows without a
  remount.
- Drag the deck slider → OS follows (unchanged), and any *other* connected
  surface's slider follows via broadcast.
- Dragging while an echo arrives → thumb stays under the finger; on release
  the next tick confirms the same value.
- No audio device / device unplugged → reads fail, nothing emitted, loop
  keeps polling; replug or default-device change resumes sync.
- Two `volume` sliders on the same deck stay in agreement through the same
  event.

## Implementation Results

Implemented and verified live end-to-end.

**Built**

- `read_output_volume()` in `cross_platform_action` returns
  `(percent|None, muted|None, err)` per platform; `_volume_get` shares it.
- `services/volume_monitor.py` polls ~1.5 s and emits
  `system_volume {value, muted}` only on change, spawned via
  `socketio.start_background_task` in `app.py` under `__main__` (imports
  never spawn it).
- `SliderButtonFace` (`target === 'volume'` only) subscribes on mount,
  unsubscribes on unmount; inbound values are clamped, `muted` drives the
  icon, and the badge follows. Updates are skipped while `dragging`.
- `dist` rebuilt; `system_volume` confirmed in the bundle.

**Deviations from the plan (COM section)** — the plan assumed per-call
endpoint resolution inside the worker was safe. It was not, and the
resulting crash investigation rewrote the endpoint model:

- `cast(interface, POINTER(IAudioEndpointVolume))` aliases Activate's
  *single* COM reference. Releasing `interface` afterwards freed the object
  out from under the endpoint — every later call read a vtable at
  `0xFFFFFFFFFFFFFFFF`. All previous "clean" runs leaked `interface` and
  were stable for that reason alone. Fixed by `QueryInterface` (a real
  second reference).
- comtypes wrappers are self-cycled via bound-method caches, so only
  cyclic GC frees them — on whatever thread collects. `_compointer_base.__del__`
  is now patched once so off-worker finalization is *deferred onto the
  worker's job queue* instead of releasing in place; `_release_com` marks
  wrappers (`_vdock_released`) so no release fires twice.
- Endpoint lifetime is now: **cache + invalidate**, never per-call churn.
  Re-resolution happens on (a) an op failure, (b) an
  `IMMNotificationClient` default-device-change callback (registered on a
  separate MTA thread — no pump needed), or (c) a 60 s TTL hedge. A 3 s
  resolve rate-limit stops a flapping device from amplifying churn.
- Stress: 300 reads + 50 sets across three threads with forced caller GC —
  zero errors, zero process faults (previously died at exit 139).
  936/936 backend tests pass.

**Verified live** (built bundle on :5000, Playwright):

- External pycaw set 40→62% → slider head + `aria-valuenow` showed 62%
  within one poll cycle.
- Synthetic drag on the track → OS endpoint measured 30% externally.
- External `SetMute(1)` → icon flipped to `fa-volume-xmark`; unmute + 34%
  propagated back (`fa-volume-low`, 34%).
- Slider started at the true OS level on load (40%), not stale config.
- Backend survived sustained monitor polling + 25 rapid `volume_get` HTTP
  hits; log clean.

**Known limits:** poll interval means up to ~1.5 s lag (deliberate — COM
value callbacks need an STA pump); `app_volume` sliders do not subscribe —
per-app sessions are a different lifecycle.
