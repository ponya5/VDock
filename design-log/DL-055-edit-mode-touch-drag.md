# DL-055 — Edit-mode touch drag & atomic button swap

**Date**: 2026-09-21
**Status**: Implemented

## Background

On the 1024×600 touch panel, entering edit mode and trying to move a
button did nothing — "during edit mode the touch doesn't work."
HTML5 drag-and-drop (`draggable`/`dragstart`) never fires on touch, and
the existing touch path (`DeckGrid.startTouchDrag`) was only reachable
through a long-press emit that `DeckButton` gated behind
`!isEditMode` — once edit mode was on, the gesture had no source.

Separately, the drop handler had two latent defects even when the
gesture did fire:

- **Swap was impossible**: it emitted two sequential `buttonMove`s, but
  `moveButton`'s collision check rejects a move onto a cell whose
  occupant hasn't left yet — both emits failed silently.
- **Placeholder drops were dead**: a drop on `.button-placeholder`
  produced `targetId = "placeholder-r-c"`, which never matches a real
  button, so no event was emitted at all.

## Changes

- **`DeckButton.vue`** — the grab emit (`longPress`) is no longer gated
  on `!isEditMode`. In edit mode it fires two ways: the 500ms hold
  (unchanged long-press path) *and* press-and-move >12px via a window
  `pointermove` watcher — users who drag immediately are the common
  case, and cancelling on early movement was the visible "touch doesn't
  work" symptom. Overlay controls (delete/edit/copy) are excluded as
  grab sources. No `setPointerCapture` — capture would retarget click
  events and break the overlay buttons.
- **`useButtonActions.handleDeckButtonLongPress`** — early-returns when
  already in edit mode. In view mode a long-press still enters edit
  mode and opens the button editor; in edit mode the same emit is the
  drag grab and must not pop a modal under the user's finger.
- **`SliderButtonFace.onPointerDown`** — returns early in edit mode.
  Previously pressing a slider while rearranging dispatched a real
  `volume_set`/`brightness_set` and `setPointerCapture` stole the
  gesture from the parent.
- **`dashboardStore.swapButtons(id1, id2)`** — new atomic store action.
  Validates both swapped footprints against grid bounds, each other,
  and all third buttons; single `addToHistory` + `saveProfile`.
- **`DeckGrid.onTouchEndDrag`** — drop on an occupied cell emits the new
  `buttonSwap` event (wired through `DashboardView` →
  `handleButtonSwap`); drop on a placeholder parses `placeholder-r-c`
  and emits `buttonMove` into the empty cell. `startTouchDrag` now also
  guards a double-start and plays a 50ms grab haptic.
- **`useGestures.useDoubleTap`** — a `pointerup` only counts as a tap if
  the press started on the same element and stayed under 10px.
  Prevents a drag landing on a button from being counted toward a
  double-tap action execution.

## Implementation Results

- Live-verified at 1024×600 with synthetic PointerEvent+TouchEvent
  sequences: press-and-move drag grabbed instantly (ghost + drop-target
  highlight), button↔button swap exchanged positions, button→placeholder
  drop moved the button, and a slider button dragged to an empty cell
  without firing `volume_set`. No editor modal during drags; view-mode
  slider still applies values on touch.
- `edit-mode-touch-drag.test.ts` (7 assertions) pins the ungated emit,
  move-grab path, overlay exclusion, editor early-return, slider gate,
  drop routing, and the double-tap distance guard.
- `vue-tsc` clean (0 errors); 238/238 tests pass.
