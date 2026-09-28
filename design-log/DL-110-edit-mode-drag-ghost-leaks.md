# DL-110: Edit-mode drag ghosts leak + reveal FAB overlaps edit footer

**Date:** 2026-10-02

## Problem

Screenshots of edit mode show deck-button **duplicates frozen over the
grid** (a detached "Previous" card + a stray icon glyph floating over the
empty cells). These are drag-ghost clones that never got cleaned up.

Two independent leak paths:

1. **`DeckGrid.vue` `startTouchDrag`** creates a `position:fixed`
   `cloneNode` ghost and binds only `touchmove`/`touchend` on `document`.
   No `touchcancel`, `pointerup`, `pointercancel`, `blur`, or unmount
   cleanup. The grab can be triggered by **pointer** events
   (`useLongPress` + the >12px `pointermove` watcher are
   pointerType-agnostic), so a *mouse* long-press/press-drag creates a
   ghost that can never receive a `touchend` — permanently frozen. A
   touch drag cancelled mid-flight (scroll takeover, gesture conflict,
   second finger) leaks the same way. (On desktop, mouse reorder is
   already served by the native HTML5 `draggable` path — the ghost is
   the touch-only substitute and should never arm for mouse.)
2. **`useTouchActionDrag.ts`** (sidebar action drags) has the same hole:
   document-level `touchend` only, no `touchcancel`; the source's own
   `touchcancel` handler only resets the long-press flag and never calls
   `cancelTouchDrag` while a drag is active.

Also visible: the floating "Header ⌄" reveal FAB overlaps the footer's
**Delete Page** button in edit mode — `.above-footer` lifts it by one
strip height, but the edit-mode footer is two rows (Grid/Add/Delete +
Save Profile), so the FAB lands mid-controls over a destructive button.

## Fix

- **`DeckButton.vue`** — `handlePointerDown` captures
  `downPointerType = event.pointerType` (all modes); `emitGrab` passes it
  as a second `longPress` arg; `handleEditModeMove` bails for
  `pointerType === 'mouse'`.
- **`DeckGrid.vue`** — `handleButtonLongPress(button, pointerType)`:
  emits `longPress` unchanged (view-mode long-press → enter-edit+editor
  is a feature), but only calls `startTouchDrag` when `isEditMode` and
  `pointerType !== 'mouse'`. `onTouchEndDrag` body extracted into
  `finishDrag(executeDrop)`; binds `touchend`/`pointerup` → drop,
  `touchcancel`/`pointercancel`/`window blur` → cancel without drop;
  `onUnmounted` reuses it. All listeners removed via
  `removeTouchDragListeners()`.
- **`useTouchActionDrag.ts`** — document-level `touchcancel` +
  `pointercancel` + `window blur` → `cancelTouchDrag()` (no drop on
  cancel); removed alongside the other drag listeners.
- **`DashboardView.vue`** — reveal FAB hidden while `isEditMode` (the
  two-row edit footer overflows the `.above-footer` lift; the FAB would
  sit on Delete Page). Swipe-down reveal still works.

## Implementation Results

Implemented as described; verified live in the running app via Chrome
DevTools synthetic input:

- **Mouse long-press + drag on a deck button in edit mode** → **no
  ghost created** (`strayGhosts: 0`). Previously this left a frozen
  `position:fixed` clone — the exact "floating Previous button" defect
  in the screenshots. Mouse reorder is served by the existing native
  HTML5 `draggable` path, which was untouched.
- **Touch long-press** → ghost created (`ghostDuringPress: 1`), then:
  - `pointerup`/`touchend` → drop executed, ghost removed
    (`ghostAfterRelease: 0`)
  - `touchcancel` → ghost removed with no drop (`ghostAfterCancel: 0`)
    — the previously-leaking path on the touch panel.
- **Reveal FAB** no longer renders in edit mode — the two-row edit
  footer overflows the `.above-footer` lift, so it was landing on
  **Delete Page**. Swipe-down reveal still works while editing.
- App state left clean after verification (edit mode exited, header
  re-hidden).

Regression pins appended to
`frontend/src/tests/edit-mode-touch-drag.test.ts` (source assertions on
the pointer-type gate, the full cancel/listener set, unmount reuse, and
the edit-mode FAB guard) — **11/11 green**, `vue-tsc --noEmit` clean,
`npm run build` clean.
