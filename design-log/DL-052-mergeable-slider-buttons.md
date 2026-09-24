# DL-052 — Mergeable slider buttons + Sliders action category

**Date**: 2026-09-21
**Status**: In progress

## Background

User asked for two related things:

1. Sliders should be a first-class member of Button Actions — today the
   three slider specs (`slider_volume`, `slider_brightness`,
   `slider_ui_brightness`) sit in the backend catalog's `custom`
   category, surfacing in the sidebar under "Custom Media" where they
   are easy to miss.
2. Adjacent slider buttons should be mergeable into one wide slider:
   in edit mode, when two sliders sit side by side, a merge button on
   their shared edge merges them into a single button spanning both
   cells.

## Analysis

- `Button.size = { rows, cols }` already exists and is honored
  everywhere it matters: `DeckButton` places itself with
  `gridRow/gridColumn` spans, `emptySlots` marks all covered cells
  occupied, `checkButtonCollision` treats buttons as rectangles, and
  `addButton`/`moveButton` reject overlaps. A merged slider is just a
  button with `size.cols > 1` — no model changes needed.
- `SliderButtonFace` is width-agnostic (track stretches to 100%).
- Store mutations (`addButton`, `removeButton`, `updateButton`) each
  push a history entry; merging must be a single store method so undo
  restores both buttons in one step.
- Edit-mode chrome lives in `DeckButton.edit-overlay`, but a seam
  affordance spans two buttons — `DeckGrid` is the component that knows
  both geometries, so the merge chip belongs there.

## Design

- **Catalog**: new backend category `sliders` ("Sliders",
  `fas:sliders-h`); the three slider specs move from `custom` to it.
  `catalogCategories` appends it automatically — no frontend alias
  needed.
- **Merge store method**: `mergeSliderButtons(leftId, rightId)` —
  validates both are enabled sliders on the same row with equal height
  and `right.col === left.col + left.size.cols`, then
  `left.size.cols += right.size.cols`, removes `right`, single
  `addToHistory` + `saveProfile`. Left button keeps its config
  (target/min/max/step), label, and styling; undo restores both.
- **Seam chips** in `DeckGrid` (edit mode only): for each pair of
  horizontally adjacent equal-height sliders, render a small circular
  chip centered on their shared edge — a grid item anchored to the
  right cell's first column with `justify-self: start;
  translateX(-50% - half-gap)`, vertically centered on the shared
  rows. Click emits `buttonMerge(left, right)` →
  `useButtonActions.handleButtonMerge` → store method + toast.
- Chains work naturally: a 2-wide slider adjacent to another slider
  shows the chip again and merges to 3-wide.
- **ButtonEditor**: bump the size Columns input `max` from 3 to 12 so
  merged sliders stay editable without the spinner clamping them.
- Vertical merging is out of scope (sliders are horizontal controls).

## Implementation Results

Implemented and verified live at 1280×800 in edit mode:

- **Sliders category** — backend catalog now has `sliders` ("Sliders",
  `sliders-h` icon) holding Volume Slider, Brightness Slider and UI
  Dimmer Slider; the sidebar shows them as their own group instead of
  buried under Custom Media. Backend restarted to load it.
- **Merge chips** — `DeckGrid` computes `sliderSeams` (adjacent,
  same-row, same-height sliders) and renders a circular link-icon chip
  centred on the shared edge in edit mode. Clicking merged two volume
  sliders into one 330px (2-cell) slider; the track stretched and a
  drag to ~20% applied the real OS volume. Chains generalise (the chip
  reappears beside an already-wide slider).
- **Undo** — `mergeSliderButtons` is one store mutation = one history
  entry. Wired the existing-but-unreachable history: Ctrl+Z / Ctrl+Y
  (and Ctrl+Shift+Z) now call `undo()`/`redo()` + `saveProfile` in edit
  mode. Verified: merge → Ctrl+Z splits back to two 1-cell sliders →
  Ctrl+Y re-merges.
- `ButtonEditor` Columns cap raised 3 → 12 so merged sliders stay
  editable.
- Test fix during CI: `property8` requires `clamp()`/`var()` font
  sizes — chip icon uses `calc(12px * min(var(--touch-multiplier), 1.25))`.

`vue-tsc` clean, 231/231 tests pass (1 pre-existing jsdom network
error unrelated to this change).

**Note:** the docked sidebar (`DockedSidebar`) renders `DeckButton`s in
its own column — merge chips are `DeckGrid`-only, so docked sliders
don't offer merging (vertical column, horizontal control — correct to
skip).

## Follow-up (2026-09-22) — wheel scrolling + merge failure feedback

Two defects from live use:

- **Wheel did nothing.** `SliderButtonFace` only handled pointer-drag and
  arrow keys — scrolling over a volume slider was dead input. The face
  root now handles `@wheel.prevent`: each notch nudges `max(step, 5)%`
  (a notch should be audible even at fine configured steps), and a 160ms
  trailing timer force-dispatches the resting value so the 120ms dispatch
  throttle can't leave the system level short of the face.
- **Merge failed silently.** `mergeSliderButtons` returns false when the
  pair isn't side-by-side/same-height, and the caller showed no feedback —
  a click that does nothing reads as broken. `handleButtonMerge` now
  surfaces an error toast on refusal. (Verified the chip path itself
  works: clicking it merged two volume sliders into one 2-col slider,
  persisted to the profile.)

## Follow-up 2 (2026-09-22) — settings savebar pinned mid-page

`SettingsView`'s `.savebar` was `position: sticky; bottom: 0` as a direct
child of `.main` — the scroll container itself. A sticky element is
clamped to its containing block, and a scroll container's box is only the
scrollport, not the scrolled content: the bar was pinned at content-y
≈ viewport height and scrolled off upward on any scroll (verified:
scrollTop 800 → rect top −259). It only looked right at scrollTop 0.
Fix: `.content` is now the scroller (`overflow-y: auto`) and the savebar
is a static flex footer beneath it — always at the bottom, never
overlapping cards. Verified live at 1024×560: bar rect stays
top=541/bottom=600 at scrollTop 0, 800 and end.

## Follow-up 3 (2026-09-24) — comtypes crash silenced every real volume set,
## quick-jump preset chips

Reported as "the scroller is not fully responsive (not affecting the sound
level)".

### The volume level bug

`_volume_set`/`_volume_get` route through `_run_on_audio_thread`, a
dedicated COM apartment thread that owns the pycaw `IAudioEndpointVolume`
pointer for its whole life. On this machine that thread died on its first
line: `comtypes==1.4.0` raises `NameError: name '_compointer_base' is not
defined` on `import comtypes` under Python 3.13 — a known comtypes/3.13
ordering bug, fixed upstream in 1.4.17. The thread's exception handler in
`_audio_worker_loop` never ran (the crash was in the `import` above the
`try`), so `done.set()` was never called and every request silently timed
out after 5s with `"Audio worker did not respond"`. The slider's own UI
(fill/thumb/value label) updates unconditionally in `apply()`, so the face
looked responsive while every real `volume_set`/`volume_get` failed —
matching the report exactly.

Fixed by upgrading `comtypes` to `>=1.4.17` and pinning it explicitly in
`backend/requirements.txt` (it was previously an unpinned transitive
dependency of `pycaw`, so a bare `pip install -r requirements.txt` could
still land on the broken 1.4.0 depending on resolver luck). Verified live:
`volume_get` → 16%, `volume_set 37` → real Windows volume moved to 37%
(confirmed by a second `volume_get`), then restored to 16%.

### Quick-jump preset chips

Added a row of five chips under the slider track — 0/25/50/75/100% of the
configured `min`/`max` range, with the 0% chip showing a mute icon instead
of "0" when `target === 'volume'`. Tapping a chip calls the same `apply(v,
true)` the drag/wheel paths use (forced dispatch, real haptic tick). The
active chip highlights when the current value matches it. A new
`config.show_presets` (default `true`, `!== false` fallback) hides the row
for buttons too small to fit it — exposed as a checkbox in `ButtonEditor`'s
slider section, backed by a `showSliderPresets` computed so the box reads
correctly checked even though an unset config field means "on".

`backend/tests/test_keymaps_package.py` and friends untouched (this fix is
in `cross_platform_action.py`/`requirements.txt`, no test coverage exists
for the live COM path — it can't run in CI without a real Windows audio
device). Full backend suite: 854 passed. Frontend: `vue-tsc` shows no new
errors from `SliderButtonFace.vue`/`ButtonEditor.vue`; the four touched
test files (44 tests) pass.
