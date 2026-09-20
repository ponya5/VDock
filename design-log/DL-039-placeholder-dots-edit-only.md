# DL-039: Hide empty-slot dots outside edit mode

## Problem

Empty grid slots rendered faint translucent circles in normal (non-edit)
mode — the "+" icon's `background: rgba(255,255,255,0.12)` was applied
unconditionally while `color: transparent` only hid the glyph. Users saw
mystery dots scattered across the dashboard.

## Design

Keep the placeholder elements mounted (they're the hit targets for
long-press-to-enter-edit-mode and click-to-add/paste), but scope the
visible circle to `.is-edit-mode`. The tile's hover affordance is
unchanged — mouse users still see the add tile on hover.

## Implementation Results

- `frontend/src/components/DeckGrid.vue`: `.button-placeholder > svg`
  background `transparent`; the `rgba(255,255,255,0.12)` circle moved to
  `.button-placeholder.is-edit-mode > svg`.
- Verified live at 1024×600: 56 placeholders mounted, zero visible dots
  in normal mode; entering edit mode restores the dashed tiles + circled
  plus icons.
