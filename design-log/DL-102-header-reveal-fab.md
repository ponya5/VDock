# DL-102: Header reveal → independent floating button (footer strip reclaimed)

## Problem

Hiding the header leaves a ~52px tall, ≥200px wide "Show Header" pill docked
inside `DeckFooter`, and the footer mounts *solely* to host it
(`DashboardView.vue:134` includes `!settingsStore.showHeader`). So hiding the
header still sacrifices a full-width bottom strip + a large labeled pill —
the opposite of the intent (more room for the deck).

## Design

Revert to a floating control (the original DL-014 approach) but compact
enough that the overlap concerns that docked it don't apply:

- **DashboardView** owns a new `<button class="header-reveal-fab">`:
  `position: fixed; right: 12px; bottom: 12px` — bottom-*right*, not left:
  the docked sidebar occupies the left column, and page dots/edit controls
  occupy the footer's left/center, so the right corner is the only spot that
  never collides. When the footer is mounted (edit mode or multi-page
  scene) the button lifts above it via `bottom: calc(footer min-height + gap)`
  class binding.
- Icon-only chevron-down in a ~44px circle (meets the touch floor), dark
  translucent + backdrop blur, subtle idle ring so it stays discoverable,
  hover/focus raises opacity. Tap reveals; `useSwipe` keeps swipe-down on the
  button working, same gesture direction the header dismisses with.
- `v-if="!isMobileViewport && !settingsStore.showHeader"` — mobile keeps its
  own chrome (DL-062/063).
- **DeckFooter** loses the pill markup, `.reveal-pill`/`.header-reveal-trigger`
  CSS, `hdr-pill` Transition, `revealTriggerRef` and its `useSwipe`; the
  footer's mount condition in DashboardView drops the `!showHeader` term, so
  it only renders for edit controls or page dots and the grid reclaims the
  strip.
- `header-reveal-dock.test.ts` rewritten for the new architecture: footer no
  longer hosts the trigger; the FAB lives in DashboardView, keeps its ≥44px
  floor, and lifts above a mounted footer.

## Implementation Plan

- [ ] `DashboardView.vue`: FAB markup + `useSwipe` down-reveal + styles;
      footer `v-if` updated
- [ ] `DeckFooter.vue`: remove pill template/script/style
- [ ] Rewrite `header-reveal-dock.test.ts`

## Implementation Results

Landed as designed:

- `DashboardView.vue` — new `footerVisible` computed (`!mobile && (edit
  mode || multi-page)`) drives `DeckFooter`'s `v-if`; `!showHeader` no
  longer mounts the strip. The reveal is a `<button class="
  header-reveal-fab">` fixed bottom-right — right edge because the docked
  sidebar owns the left and footer content sits left/center. 44px-minimum
  circle, translucent glass (`rgba(10,8,32,0.66)` + 20px blur), `z-index
  95`, `.above-footer` lifts it above the footer strip's height + 10px
  whenever the footer is mounted. Tap reveals; `useSwipe` on
  `revealFabRef` preserves the swipe-down → reveal gesture. A 3s
  `fab-breathe` ring keeps it discoverable on touchscreens (no hover);
  `prefers-reduced-motion` strips animation/transition.
- `DeckFooter.vue` — pill template, `useSwipe`/`useSettingsStore`/`ref`
  imports, `revealHeader`, and all `.reveal-pill`/`.hdr-pill-*` CSS
  removed; footer keeps dots + edit controls and its own slide-leave
  anchoring.
- Tests — `header-reveal-dock.test.ts` rewritten (4): footer no longer
  hosts the control; DashboardView owns the FAB wired to `!showHeader` +
  `revealFabRef`; base style is a fixed, compact, right-anchored circle
  at the 44px floor with no pill-width footprint; `above-footer` raises
  it with a `calc()` bottom. `edit-sidebar-categories.test.ts` footer
  assertions updated to `footerVisible` and to *reject* `showHeader` in
  the `v-if`.

**Tests:** vitest **325/325**, `vue-tsc` clean, `npm run build` clean.
Visual pass on the 7" panel still owed — the FAB is translucent and
44-62px so the corner tile it grazes stays legible, but a device check is
worth the next panel session.
