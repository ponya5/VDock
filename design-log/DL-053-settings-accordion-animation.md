# DL-053 — Settings accordion expand/collapse animation

## Context

Settings accordions (App Templates categories, Screen Saver → Widgets config
cards) toggle via `v-if`/`display:none` — content teleports in and out. The
user asked for a proper expand/collapse animation (example: App Templates).

## Design

New reusable `Collapse.vue` component (`components/Collapse.vue`):

- `grid-template-rows: 0fr → 1fr` trick — pure CSS height animation without
  JS measuring, interruptible mid-flight (transitions retarget).
- Inner content also fades `opacity` + `translateY(-6px)` → 0 for a softer
  reveal; `visibility: hidden` when closed so collapsed content stays out of
  tab order and the a11y tree.
- Duration 250ms, easing `var(--ease-out)` (existing token,
  `cubic-bezier(0.22, 1, 0.36, 1)`).
- `prefers-reduced-motion`: keeps the opacity crossfade, drops the height and
  transform motion.

Applied to:

- **App Templates** — `.template-grid` wrapped in `<Collapse :open>`; the
  `v-if` is removed so content stays mounted for the animation.
- **Widget cards** (Screen Saver → Widgets) — each card body wrapped in
  `Collapse`; the `column-width` masonry moves from `.widget-card.is-open`
  onto `.collapse-inner` so the flat-child masonry layout is preserved
  inside the wrapper. The old `display:none` sibling rules are removed —
  Collapse now owns body visibility.
- **Chevrons** — both accordions switch from swapping `chevron-up`/`chevron-down`
  to a single `chevron-down` that rotates 180° when open (200ms ease-out).

## Implementation Results

Implemented as designed:

- `frontend/src/components/Collapse.vue` — reusable accordion wrapper.
- `SettingsView.vue` — wrapped the Templates grid, all 6 widget-card bodies,
  and the widget picker toggle list (which now folds/unfolds smoothly when a
  config card opens instead of `display:none` teleporting). The
  `picker-collapsed` CSS kill-switch was removed; Collapse owns visibility.
- Widget-card `column-width` masonry moved inside `.collapse-inner`
  (`:deep()`) so the 300px column flow survives inside the animated body.
- Chevrons on both accordions now rotate `chevron-down` 180° instead of
  swapping to `chevron-up`.

Verified live at 1280×800:

- Templates: open animates `grid-template-rows` 0 → 297px with opacity
  0 → 1 mid-flight (measured 114px/0.87 at ~110ms); closes the same way.
- Widget card: open measured mid-flight (114px, opacity 0.87), settled at
  126px; picker folded to 0px while open and re-expanded on close.
- `vue-tsc` clean; 231/231 vitest tests pass.

Note: the card frame itself jumps to `grid-column: 1 / -1` instantly
(grid-column isn't animatable) — only the body slides open. Acceptable per
the accordion recipe; a true FLIP resize would be a bigger refactor.
