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

### Follow-up (2026-09-28): reveal pill docked into the footer strip

#### Problem

Live screenshot on the 7" panel (1024×552): the bottom-left floating pill
straddles the chrome seam — it covers the left end of `DeckFooter` and its
top edge + shadow graze the bottom border of the grid's bottom-left tile
(the "+" placeholder). Pixel-measured: footer band y512–552, tile bottom
y511, pill y≈508–546. Two consequences:

- **Visual overlap:** the pill clips the tile's bottom edge instead of
  sitting on clean chrome.
- **Touch conflict (latent):** `footer-left` is where `.page-dots` render
  when `totalPages > 1` — the fixed pill would sit on top of them and
  intercept their taps.

Root cause: a `position: fixed` pill can never be overlap-free here. The
pill's min-height (`max(--min-touch-target, 52px × min(tm,1.6))` ≈ 52–104px
outer under border-box) exceeds the footer's `max(44px, 56px × tm)` at low
multipliers, so at `bottom: 10px` it always pokes above the footer band
into the grid — up to ~18px at tm=1. And every corner of the footer strip
except the right end is spoken for (dots left, snooze chip center). This
is the same class of bug the top-edge strip had: floating chrome colliding
with live content, relocated rather than eliminated.

#### Design

Stop floating — dock the pill **inside** `.deck-footer` as an in-flow flex
item (first child of `.footer-left`, ahead of the page dots). In-flow
placement makes overlap with grid tiles and page dots structurally
impossible at every touch multiplier, and it reuses reserved chrome space
instead of hovering over content.

- `DeckFooter.vue` gains the trigger markup (same `.header-reveal-trigger`
  → `.reveal-pill` → ripple/label structure and class names, so the
  editorial/mono font theming in `main.css` keeps applying), `v-if`ed on
  `!settingsStore.showHeader`, tap → `settingsStore.showHeader = true`,
  `useSwipe` DOWN → same reveal. Trigger becomes a plain flex item:
  `position: static`, vertically centered by the footer's `align-items`.
  If the pill is taller than the footer's minimum the footer simply grows
  (≤ ~8px at tm=1, nothing at higher multipliers) — a fair trade while
  the grid is already gaining the whole header's height.
- Shared-direction choreography preserved via the pill's own
  `<Transition name="hdr-pill">` in the footer: on hide the pill rises up
  into its slot while the header slides up away; on reveal it slides down
  off the bottom edge while the header slides down in. `leave-active`
  takes the pill out of flow (`position: absolute` on the now-`relative`
  footer, same left offset / vertical centre) so the footer reclaims its
  height at the *start* of the leave — inside the header's 0.55s motion,
  invisible — instead of snapping after it.
- `DeckHeader.vue` drops the trigger div, `triggerRef`, `revealHeader()`,
  its `useSwipe`, and the trigger/pill/ripple styles (moved verbatim to
  the footer). The `hdr-reveal` Transition stays, now wrapping only the
  header (single `v-if` child — slide animation unchanged).
- `userRevealedOnShort` is now set inside the `showHeader` watcher,
  guarded by `innerHeight < SHORT_VIEWPORT_PX` — any reveal path (footer
  pill, future callers) marks the flag, and a reveal on a tall viewport
  no longer leaves the flag stuck true forever (matching the flag's
  name/intent: it only suppresses auto-hide *on short viewports*).
- Mobile unchanged: `DeckFooter` and `DeckHeader` are both
  `v-if="!isMobileViewport"`, so the pill still never renders on phones —
  same as today.

#### Trade-offs

The reveal affordance is now coupled to the footer existing (always true
on the dashboard desktop chrome). Footer grows ≤ ~8px at tm=1 while the
header is hidden; dots shift left at leave-start as the pill exits flow —
both masked by the simultaneous header slide.

#### Implementation Results (follow-up, 2026-09-28)

- `DeckFooter.vue`: `.header-reveal-trigger` + `.reveal-pill` (markup,
  styles, ripple keyframes, hover/active, reduced-motion) moved here
  verbatim, rendered in-flow as the first child of `.footer-left` ahead
  of `.page-dots` inside `<Transition name="hdr-pill">`. Tap →
  `settingsStore.showHeader = true`; `useSwipe` DOWN → same.
  `.deck-footer` gains `position: relative`; `.hdr-pill-leave-active`
  goes `position: absolute` at the same left offset / vertical centre so
  the footer reclaims height at leave-start (inside the header slide).
- `DeckHeader.vue`: trigger markup, `triggerRef`, `revealHeader()`, its
  `useSwipe`, and the fixed-position/pill/ripple styles removed.
  `hdr-reveal` Transition now wraps only the header; slide unchanged.
- `userRevealedOnShort` moved into the `showHeader` watcher guarded by
  `innerHeight < SHORT_VIEWPORT_PX` — every reveal path marks it; a
  tall-viewport reveal no longer pins the flag.
- New regression guard `src/tests/header-reveal-dock.test.ts`: trigger
  absent from DeckHeader, present + non-`fixed` in DeckFooter, pill
  keeps its `min-height: 44px` baseline (plain line added ahead of the
  `max()` form, matching the codebase's baseline-then-enhanced
  convention).
- Verified live (Chrome DevTools MCP, backend serving fresh `dist`,
  viewport ~1343×677): pill settles in-flow inside `.footer-left`
  (`position: static`, rect 32,406 320×83 — inside footer band
  391–503; grid bottom = footer top = 391 → zero overlap). Click →
  header enters ~550ms while pill slides down out; autohide re-hide →
  pill re-enters. Screenshot: `design-log/refs/header-reveal-footer-docked.png`.
- `vue-tsc --noEmit` clean; vitest 308/309 (sole failure =
  `news-carousel` `beforeEach` hook timeout flake under full-suite load —
  passes in isolation, unrelated); `npm run build` clean, `dist/` rebuilt
  for the panel.
