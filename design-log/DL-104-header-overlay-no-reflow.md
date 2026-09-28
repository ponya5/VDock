# DL-104: Header as overlay (no grid reflow) + window-glyph reveal button

## Problem

Two complaints on the hidden-header flow (DL-102 follow-up):

1. **Grid reflows when the header toggles.** `.deck-header-wrapper` is
   in-flow; `.header-hidden` collapses it to `height:0`, so the deck
   grows/shrinks ~header-height on every toggle and every button
   resizes. The user wants the grid pinned: *"the size and layout should
   be intact even when the header is opened."*
2. **The reveal control reads as a bare arrow.** The DL-102 circle FAB
   carries only a chevron — it doesn't communicate "this summons the
   header." User supplied a reference: a window/form shape with a
   contrasting header band, and asked for a unique, self-explanatory
   design.

## Design

### Header overlays instead of pushing

`.deck-header-wrapper` becomes `position: absolute; top/left/right: 0`
anchored to `.dashboard-view` (already `position: relative` — the mobile
header already overlays the same way, so this aligns desktop with the
existing mobile model). The wrapper's in-flow height is then permanently
zero — whether hidden or shown — so `.deck-main` and the grid never
reflow.

Trade-off, accepted by the user requirement: the open header covers the
top of the deck (top grid row + docked sidebar top) like a notification
shade. The DL-014 slide choreography is unchanged — it just slides over
the grid now instead of into reclaimed space. `.header-hidden`'s
`height:0` becomes harmless redundancy; the leave transition's
z-index/overflow handling still applies.

### Reveal button: mini-window glyph

The FAB becomes a miniature window, matching the supplied reference
(rounded frame + header band): a dark glass rounded rect (~56x48px,
still ≥44px touch floor) containing

- `fab-window-head` — an accent-colored band across the top of the mini
  window (the "header" being summoned);
- a chevron-down caret centered in the body below — "pull it down".

A slow `fab-head-drop` keyframe slides the band down 2px and back — a
tactile "the header drops" hint legible on touchscreens where hover
never fires (breathing ring from DL-102 retained). Same gesture contract:
tap or swipe-down reveals, `aria-label="Show header"`, reduced-motion
strips animation.

## Implementation Plan

- [ ] `DeckHeader.vue`: wrapper → absolute overlay; verify transition
      still clean
- [ ] `DashboardView.vue`: FAB markup → mini-window glyph (head band +
      caret); restyle; keep ref/swipe/class contract
- [ ] Update `header-reveal-dock.test.ts` (no more `border-radius: 50%`
      circle pin; assert window-glyph structure + compactness)
- [ ] Build + panel check

## Implementation Results

Landed as designed:

- `DeckHeader.vue` — `.deck-header-wrapper` is now `position: absolute;
  top/left/right: 0; z-index: 100`, anchored to `.dashboard-view`
  (`position: relative` was already there for the mobile overlay header —
  desktop now follows the same model). The wrapper has zero flow height
  whether the header is shown or hidden → `.deck-main`/grid never reflow
  and buttons keep their size. `.header-hidden`'s `height:0` retained as
  documented redundancy for the leave choreography. Verified no
  height-compensation elsewhere: `mainStyle` only paints backgrounds.
- `DashboardView.vue` — the FAB is now a mini window glyph: 56×46px
  rounded-rect glass frame (`overflow:hidden`, ≥44px both axes), an
  accent teal gradient `fab-head` band across the top 40% (the "header"
  it summons, bobbing 2px on a 2.6s loop), and a `fab-caret` chevron in
  the body. Breathing ring, `.above-footer` lift, swipe-down, and
  reduced-motion handling all preserved (`.fab-head` added to the
  reduced-motion rule).
- `header-reveal-dock.test.ts` — circle pin replaced with window-glyph
  assertions: no `border-radius:50%`, clipped frame, `fab-head`/`fab-caret`
  markup, accent band rule, compact footprint, touch floor.

**Tests:** header-reveal + edit-sidebar suites green (9/9); `vue-tsc`
clean; `npm run build` clean, `dist/` rebuilt. The one visual trade-off
worth a device pass: the open header now *covers* the top grid row +
sidebar top (shade behavior) instead of pushing them — that's what keeps
the layout pinned.

## Follow-up: header painted under the docked sidebar

The overlay's `z-index:100` tied the `.docked-sidebar`'s `z-index:100` —
`.deck-main` sits later in DOM order, so the sidebar painted *over* the
open header's left strip. Wrapper bumped to `z-index:200`: above the
sidebar, still below the narrow-mode drawer (999), toasts (1000) and
modals (2000). header-reveal tests green, build clean.

## Follow-up 2026-09-28 (b): button carries the word "Header"

User asked the reveal button to name what it opens. The word sits in a
`.fab-body` row under the band (`.fab-label` + caret inline), so it's on
the button itself — more prominent than inside the thin band. Button
widened 56→68px; height, band, and overlay behavior unchanged. Test pin
added (`fab-label` + label content); header-reveal tests green, build
clean.

## Follow-up 2026-09-28 (c): header starts closed at launch

`showHeader` is ephemeral per-window state (never persisted/synced); it
initialised `true`, so every launch opened the header until a manual
hide. Now `ref(false)` — the deck launches full-grid with the labelled
FAB visible; revealing still arms the 5s auto-hide, short-viewport
auto-hide logic unchanged.
