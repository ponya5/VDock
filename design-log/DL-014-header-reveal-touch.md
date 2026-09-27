# DL-014 — Touch-friendly header reveal affordances

## Background

VDock targets a 7" touch panel (see DL-009). When `showHeader` is false the
app header collapses and two reveal affordances remain:

- `DockedSidebar.vue` — a small "Docked Buttons" pill
  (`.header-toggle-button`, ~90×26 px) in the sidebar header.
- `DeckHeader.vue` — `.header-reveal-trigger`, a full-width 84 px invisible
  hit area whose only visible part is a 96×10 px grey bar (`.reveal-handle`).

## Problem

On a touchscreen both visible affordances are too small and neither says what
it does: "Docked Buttons" labels the column rather than the action, and the
centre bar is a thin line with no icon or label. Users can't tell that
tapping reveals the top header.

## Design

Follow the DL-009 pattern — consume `--touch-multiplier`,
`--min-touch-target`, `--spacing-touch-*` instead of inventing new scaling.

### DockedSidebar.vue

- `.header-toggle-button` div → real `<button type="button">` with
  `@click.stop` (parent `.sidebar-header` keeps its click handler so the
  padding strip still toggles; `.stop` prevents a double emit).
- Relabel to "Show Header" + `chevron-down` icon (the header slides down
  from the top edge). Full-width, `min-height` floored at
  `max(--min-touch-target, 44px × multiplier)` with the plain `44px`
  baseline kept for the Property-22 regex, `touch-action: manipulation`,
  font scaled by `--touch-multiplier`, text allowed to wrap on the 100 px
  compact sidebar.
- `.sidebar-header` padding → `--spacing-touch-md` fallback chain.
- `.add-btn` (edit-mode "+" in the same header) gets the same 44 px touch
  floor — it was a 24 px target.

### DeckHeader.vue

- Keep the 84 px full-width invisible hit area and swipe-down gesture.
- Replace the trigger's `.reveal-handle` bar with `.reveal-pill`: a ~40 px
  glassy pill containing `chevron-down` + "Show Header" — an obvious,
  labelled tap target. `.reveal-handle` stays as-is for the separate
  collapse handle inside the open header.

## Implementation Plan

- [x] Phase 1: DockedSidebar toggle button + add-btn touch floor
- [x] Phase 2: DeckHeader reveal pill

## Trade-offs

The sidebar pill loses the "Docked Buttons" column title while collapsed;
action clarity was judged more valuable than the label. The centre affordance
becomes more visually prominent (a labelled pill vs a barely-visible bar) —
acceptable since it only renders while the header is hidden.

## Verification Criteria

- `vue-tsc` clean, vitest suite passes.
- Toggle button and reveal pill both ≥44 px tall at normal mode and scale in
  tablet mode; both reveal the header on tap.

## Implementation Results

- Phase 1 (DockedSidebar): `.header-toggle-button` is now a real full-width
  `<button>` labelled "Show Header" with a `chevron-down` icon, 44 px →
  `max(--min-touch-target, 44px × multiplier)` min-height, touch padding and
  `touch-action: manipulation`; `@click.stop` emits `toggleHeader` while the
  surrounding `.sidebar-header` strip stays clickable. `.add-btn` floored at
  the same 44 px touch target (was 24 px). Header padding/icon/font consume
  `--spacing-touch-*` / `--touch-multiplier`.
- Phase 2 (DeckHeader): the trigger's 96×10 px `.reveal-handle` bar was
  replaced by `.reveal-pill` — a frosted pill with `chevron-down` + "Show
  Header" text (40 px → 60 px capped scale). The 84 px full-width invisible
  hit area and swipe-down gesture are unchanged; `.reveal-handle` still
  serves the collapse handle inside the open header.
- Tests: vitest 175 pass (49 files), `vue-tsc --noEmit` clean.
- Manual verification on the 7" panel outstanding.

## Follow-up (2026-09-27): reveal button relocated to bottom-left

### Problem

The reveal trigger is a `position: fixed` 84 px fully-transparent strip
spanning the entire top edge, with the visible "Show Header" pill centered
in it. On small panels it sits on top of the mobile scene rail / agent
console action row — visually covering the "Continue"-type buttons and
intercepting taps across the top 84 px. The DL-062 reserved-strip fix was
lost in later refactors, and the strip itself is the overlap: any
top-anchored hit area collides with the scene rail that now lives at the
top edge.

### Design

Move the trigger off the top edge entirely: it becomes a compact floating
button pinned to the **bottom-left** corner
(`bottom/left: 10px + safe-area insets`), sized to the pill itself — no
more invisible full-width strip. Consequences:

- Zero overlap: nothing covers the scene rail or console rows, visually
  or for touches; the pill only overlays empty deck corner space.
- The bottom-left corner is free on both chromes — the waiting-alert
  snooze chip is bottom-center, mobile has no bottom nav.
- The swipe-down-to-reveal gesture previously caught by the top strip now
  applies to the button itself (`useSwipe` stays bound to the trigger);
  the "swipe down from anywhere along the top edge" affordance is
  retired — it was the source of the overlap. Tap-to-reveal on the pill
  is unchanged, as is swipe-up-to-dismiss on the header.

### Implementation Results (follow-up, 2026-09-27)

- `DeckHeader.vue`: `.header-reveal-trigger` now `bottom/left: 10px +
  env(safe-area-inset-*)` with `width/height: auto` — the hit box is
  exactly the pill. `.reveal-pill` lost the now-pointless `margin-top`.
- Verified live (1280×800, desktop chrome): trigger rect x:10 y:730
  205×60 — the AgentActionBar row (session chip, Submit/Mode/etc.) fully
  unobstructed at top. Real click reveals the header; the 5 s autohide
  re-hides it (earlier "still hidden" reads were post-autohide, not a
  regression).
- The pill stays under the screensaver (z 110 < 500) — first tap dismisses
  the saver, then the pill is reachable; matches its previous layering.
- Screenshot: `design-log/refs/header-reveal-bottom-left.png`.

### Addendum #2 (2026-09-27): Uiverse ripple-button restyle

Per user request the reveal pill now uses the Uiverse "mi-series" ripple
button look: solid `#40B3A2` teal, `border-radius: 4px`, uppercase label
(`letter-spacing: 1.2px`), flanked by two `.reveal-ripple` dots emitting
expanding box-shadow rings (0.6s loop, clipped inside the pill by
`overflow: hidden`). Touch scaling kept: `min-width` 200px and padding/
font multiply by `min(--touch-multiplier, 1.6)` — 320×83px at tm=2.
Hover is `opacity: .92 + scale(1.04)`; reduced-motion freezes the ripple.
Chevron-down icon kept inside the label for the expand affordance.
Verified live at 1280×900 (tm=2): `bg rgb(64,179,162)`, radius 4px,
font 19.2px, 2 ripple dots animating. Screenshot:
`design-log/refs/header-reveal-teal-ripple2-*.png`. `npm run build`
(vue-tsc + vite) clean; dist rebuilt for the panel.

### Addendum #3 design (2026-09-27): shared-direction slide choreography

Reveal: header slides **down** into place while the Show Header button
slides **down** off the bottom edge. Collapse: header slides **up** away
while the button rises **up** back into place — both elements always move
in the same direction, so the motion reads as one handoff. Implemented as
a single `<Transition name="hdr-reveal">` wrapping the trigger/header
v-if/v-else pair (simultaneous enter+leave); 0.55s `--ease-io`; the
leaving header relies on `.header-hidden`'s `height:0; overflow:visible`
so the grid reclaims space immediately with no end-of-leave jump.
Reduced-motion disables the transition.

### Implementation Results (addendum #3, 2026-09-27)

- `DeckHeader.vue`: trigger + header wrapped in
  `<Transition name="hdr-reveal">` (default simultaneous mode — both
  elements animate together; no `mode="out-in"` gap). New classes:
  `hdr-reveal-enter-active/-leave-active` apply
  `transform 0.55s var(--ease-io)`; `.deck-header` goes `translateY(-102%)`
  at enter-from/leave-to, `.header-reveal-trigger` `translateY(140%)` at
  enter-from/leave-to — so both travel the same direction per gesture.
- `.deck-header.hdr-reveal-leave-active { z-index: 100 }` — during
  collapse `.header-hidden` zeroes the wrapper immediately, so the
  sliding header needs to paint above the grid reclaiming its space.
- Transform composition: the pill's hover/active `scale(1.04)` lives on
  `.reveal-pill` (inner), the transition transform sits on
  `.header-reveal-trigger` (outer) — no conflict; ripple animation
  untouched.
- Verified live (Playwright, 1280×900): open = header `-164px → 0` while
  button `0 → +113px` (down off-screen); close = header `0 → -159px`
  while button `+116 → 0` (rises into bottom-left). Autohide collapse
  exercises the same path; trigger settles at x:10, bottom:10, 320×83.
- Reduced-motion: `hdr-reveal-*` classes collapse to `transition:none`,
  restoring the previous instant swap.
- `vue-tsc --noEmit` clean; 37/37 focused vitest green; `npm run build`
  clean — dist rebuilt for the panel.
