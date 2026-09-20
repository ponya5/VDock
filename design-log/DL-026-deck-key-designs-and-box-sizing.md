# DL-026 — Deck-Key Button Designs, Design Picker & Real Box Sizing

## Background
The dashboard has ~22 visual effects selectable per button (Button Editor →
"Visual Effects" dropdown) plus a global "apply to all" control in Settings →
Buttons. The user reports three problems on the 7-inch touchscreen:

1. "There is only one type of button design" — the effect choice is a plain
   text dropdown buried in the Button Editor; nothing advertises the designs.
2. "Button size option only changes the icon and text, not the actual button
   box" — `settings.buttonSize` is passed to `DeckButton` and only scales
   `iconStyle`/`labelStyle`/`mediaStyle`; the `.deck-button` grid item always
   fills its cell (see DeckGrid.vue's comment explaining why a whole-grid
   transform was rejected).
3. Two new Claude mockups were supplied as design references:
   `Buttons-Rich.dc.html` (already implemented in DL-019: glowglass/gem/
   neonrim/watermark) and `Buttons-Deck.dc.html` (new: J. Deck key,
   K. Status key, L. Full-art key, M. Folder key).

## Problem
- No discoverable/visual way to pick a button design.
- Button Size slider does not change the rendered button box dimensions.
- The deck-style mockup styles (deckkey/statuskey/fullart/folder) don't exist.

## Design

### New effect types
Extend `EffectType` with `'deckkey' | 'statuskey' | 'fullart' | 'folder'`.
CSS lives in `main.css` next to the DL-019 rich styles, brand-parametric via
`var(--btn-brand)` with `color-mix()`, `!important` beating inline defaults —
same convention as `.deck-button-glowglass` etc.

- **deckkey** — physical keycap: `.deck-button` becomes the dark bezel
  (padding ~7px, `linear-gradient(145deg,#34343e,#0a0a0e)`, hard drop shadow +
  1px black ring). `.button-content` becomes the recessed screen: `#050507` +
  radial brand glow from the top + diagonal sheen + `inset 0 0 0 1px` ring.
  Pressed = darker bezel + brand-lit inner ring.
- **statuskey** — dark card (`#1b1b24→#0b0b10`) + ambient brand glow shadow +
  a glowing LED bar (`button-content::after`, absolute, bottom-centred, brand
  colour + glow). Pressed = LED brightens, card dips.
- **fullart** — brand gradient fills the whole key (colour-mixed 3-stop),
  two concentric ring decorations via `closest-side` radial-gradient bands,
  icon rendered ~2.1× without the capsule tile, label pinned to a bottom scrim
  band (`position:absolute` + `linear-gradient(0deg, rgba(0,0,0,.62), 0)`).
- **folder** — glass card where `.button-icon` becomes a 2×2 mini-cell capsule.
  If the button's action is `goto_page`, cells show the target page's first
  enabled buttons (icon or logo img, brand-tinted cell background) and a count
  badge (`.folder-badge`, top-right accent circle) shows the target page's
  button count. Non-goto_page buttons get the button's own icon in cell 0 +
  empty cells. Grid cells without children render as dimmed empty tiles.

### Button Size → real box size
`DeckButton.buttonStyle` gains, when `buttonSize ≠ 1`:
`width/height = boxScale%` + `placeSelf: 'center'`, where
`boxScale = s<=1 ? clamp(s,0.5,1) : min(s,1.12)`.
Percentage width/height on a grid item resolves against its grid area, so the
box literally shrinks (0.5 → half the cell) or grows (+12% max, absorbed by the
12px grid gap — ~7px per side on a ~160px cell, no neighbour overlap). Icon/
label keep their existing `scale = buttonSize` px math, so net content scale is
unchanged; only the box is new. `min-width/height: 60px` still floors the box.
No `transform` is used on the button itself — it would fight the `:active`
press scale and wiggle/pulse keyframe animations.

### Design picker
New `ButtonDesignPicker.vue` — a touch-friendly swatch grid. Each swatch is a
mini `deck-button deck-button-<effect>` DOM stub (`.button-content >
.button-icon > icon`), so the real card CSS renders each preview for free.
Selection = accent ring + check. Two tiers:
- **Design** swatches: none, glass, glowglass, gem, neonrim, watermark,
  deckkey, statuskey, fullart, folder.
- **Overlay effect** select (kept for parity): the remaining animated/legacy
  effects (neumorphism, gradient, glow, 3d, neon, metallic, liquid,
  holographic, shadow, emissive, fire, plasma, particles, aurora, scanline,
  rain).

Used in ButtonEditor (per-button `editedButton.style.effect`) and SettingsView
Buttons tab (`previewEffect`, applied to all buttons via the existing
"Save & Apply to All Buttons" path). ButtonEditor's static preview box gains
the 4 new class mappings. SettingsView Button-Size help text updated to say
the box itself resizes.

## Implementation Plan
- [ ] Phase 1: `EffectType` + 4 CSS classes + DeckButton mappings/folder peek
- [ ] Phase 2: box sizing in `buttonStyle`
- [ ] Phase 3: `ButtonDesignPicker` + ButtonEditor/SettingsView wiring
- [ ] Phase 4: typecheck, tests, build, live verify at 1024×600

## Trade-offs
- **Chosen:** width/height% + place-self for box sizing.
  **Rejected:** `transform: scale()` (breaks press/wiggle animations, overflow
  clip risk); grid reflow (can't — grid_config rows/cols is fixed by layout);
  negative margins (% margin quirks vs. area).
- Box growth capped at +12%: more would overlap neighbours on a 12px-gap grid.
  The remaining growth goes to icon/label, which already scaled that way.
- Folder peek uses real `goto_page` data; generic grid fallback for other
  actions keeps the style meaningful on any button.

## Verification Criteria
- Changing Button Size changes `getBoundingClientRect()` of `.deck-button`
  (not just icon/label font-size) at 0.5×, 1×, 1.5×, 2×.
- All 10 designs visibly distinct in the picker and on the dashboard.
- `goto_page` folder shows real child icons + count; other buttons fall back
  gracefully.
- Edit-mode badges, drag/drop, press states, transparency, and docked sidebar
  unaffected. Old buttons with no effect render as before.
- 1024×600: no overlap/clip at max size; picker usable by touch.

## Implementation Results

- Phase 1: `EffectType` extended with `deckkey|statuskey|fullart|folder`;
  four `.deck-button-*` blocks added to `main.css` (bezel+screen, LED bar,
  brand-art + rings + scrim label, 2×2 peek capsule + count badge). DeckButton
  maps the classes, routes them through the rich-card style branch, boosts
  fullart icons ~2.1× in `iconStyle` (skipping the hasLabel cap since the
  label overlays), and renders `folderCells`/`folderBadgeCount` — `goto_page`
  buttons show the target page's first four enabled buttons with real icons
  and its total count badge; others fall back to the button's own icon.
- Phase 2: `buttonStyle` sets `width/height = boxScale%` + `place-self:center`
  when `settingsStore.buttonSize ≠ 1` (clamp 0.5–1.1). Live-verified at
  1024×600: box rect 78×60 → 157×92 → 172×101 for slider 0.5→1→2.
  **Deviation:** box scale reads the RAW slider (`settingsStore.buttonSize`),
  not the `buttonSize` prop — the prop is multiplied by `touchModeMultiplier`
  (tablet = ×2), which would have permanently overflowed every button into
  its neighbours. Icon/label still use the multiplied prop, unchanged.
- Phase 3: `ButtonDesignPicker.vue` — 10 real-preview swatches (mini
  deck-button DOM so global classes render them) + overlay-effects select.
  Wired into ButtonEditor (`buttonDesign` computed proxy writing
  `layers.effect`, clearing `style.effect` — otherwise a stale layers.effect
  silently shadows the picker's choice, which is exactly what the first live
  save attempt revealed) and SettingsView's global preview. New buttons
  inherit `buttonDefaultEffect` via `resolveDefaultEffect()` in
  useButtonActions (previously stored but unused for creation).
- Phase 4: `npm run type-check` clean; `npx vitest run` 50 files / 188 tests
  (12 new in `deck-key-designs.test.ts`); `npm run build` succeeded.
  Verified live at 1024×600: all four designs visually distinct on the grid,
  picker shows in Button Editor (pinned footer intact) and Settings →
  Buttons; pick→save persists; folder badge = "9" on a goto_page button.
