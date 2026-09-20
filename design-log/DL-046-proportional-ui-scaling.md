# DL-046: Proportional UI scaling for large screens

**Date**: 2026-09-20
**Status**: Implemented

## Problem

The entire Settings UI was sized in fixed pixels tuned for the 1024×600
touchscreen. Opened standalone on a desktop browser (e.g. 1600×900 or
1920×1080) it rendered miniature — small nav rail, tiny controls, dead space —
because nothing grew with the viewport.

## Approach

A single global scale factor `--ui-zoom` applied via CSS `zoom`:

- `App.vue` computes `zoom = clamp(min(vw/1024, vh/600), 1, 1.9)` on
  mount + resize and writes it to `document.documentElement`.
- `.settings-view` applies `zoom: var(--ui-zoom)` and divides its
  `100vh`/`100vw` back out (`calc(100vh / var(--ui-zoom))`) so the view
  still fills the window exactly — zoom multiplies viewport units too.
- `UserGuideModal` gets the same zoom with `max-width/max-height` divided
  by the factor so it can't outgrow the window.

`zoom` was chosen over `transform: scale` because it reflows layout
(correct scroll regions, pointer hit-testing) and over a px→rem refactor
(one knob vs. touching hundreds of declarations). Media queries still see
the real viewport, which is desirable: zoom>1 always wants the wide-screen
rules.

On the 7" panel (1024×600) `min()` yields exactly 1 — zero visual change.

## Implementation Results

- `App.vue`: `updateUiZoom()` on mount + window resize; rounds to 0.05
  steps to avoid sub-pixel churn.
- `SettingsView.vue`: `.settings-view` zoomed with compensated dimensions.
- `UserGuideModal.vue`: zoomed with compensated `max-width`/`max-height`.

### Verified live

| Viewport | Zoom | Result |
|---|---|---|
| 1024×600 | 1.0 | Identical to before — Button Display bottom 581px, no overflow |
| 1600×900 | 1.5 | Fills window exactly, no h/v overflow |
| 1920×1080 | 1.8 | Fills window; guide modal 1710×994 centered under cap |

Frontend: 231/231 tests, `vue-tsc` clean.

### Follow-up: label overflow on short buttons (found in final self-test)

Tablet touch mode scales labels ~1.4x; two-word labels wrapped to two
lines and clipped mid-glyph at the 92px card edge (18px measured
overflow). Fix: `.deck-button` is now a `container-type: size` container;
an `@container (max-height: 115px)` rule drops `.button-label` to a
single ellipsized line. Note: the rule must sit *after* `.button-label`
in source — equal specificity resolves by order. Verified live: worst
overflow 18px → 1px at 1024×600 tablet mode.
