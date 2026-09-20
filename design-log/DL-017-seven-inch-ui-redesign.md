# DL-017 — 7-inch UI redesign (user-supplied Claude mockups)

## Background

The user generated three reference mockups for the 1024×600 touch panel and
asked to "upgrade the design":

- `Dashboard, 7-inch-html.zip` (`Dock.dc.html`)
- `Edit mode, 7-inch-html.zip` (`Dock-Edit.dc.html`)
- `Settings, 7-inch-html.zip` (`Settings.dc.html`)

All values below are extracted from the mockups' inline styles.

## Design tokens (from mockups)

- **Font**: Heebo (UI) + Instrument Serif (weather temp). Accent `#1f6fd1`
  (default), blue tint `#4aa3ff`, text `#eef2fa` / secondary `#a9b6cc`.
- **Dashboard bg**: `#4a3f9a` + radial pink `rgba(232,53,140,.85)` @0% 52%
  + radial purple `rgba(120,70,190,.9)` @85% 100% + linear `160deg #6f7be6 →
  #5b4fb5 45% → #3a2f78`, dim overlay `rgba(10,8,30,.22)` (`.3` edit mode).
- **Header**: h84, `rgba(10,8,32,.66)`, border-b `rgba(255,255,255,.12)`;
  56px circle buttons (`rgba(255,255,255,.1)`, border `.18`); nav pill
  `rgba(255,255,255,.08)` r18 p4; tabs h48 px14 r14 fs18/500, active accent
  + `0 4px 12px rgba(31,111,209,.45)`; page pills 48px r14 fs20/600; hide
  handle 120×18 hit area, 48×5 bar `rgba(255,255,255,.5)`.
- **Content**: p12 gap12; sidebar 132px + 1px divider `rgba(255,255,255,.14)`;
  grid 5×156 rows gap12.
- **Card** (deck button + weather): r24, `rgba(20,16,50,.4)`, border
  `rgba(255,255,255,.18)`, shadow `inset 0 1px 0 rgba(255,255,255,.18),
  0 10px 24px rgba(8,6,30,.28)`; icon tile 64×64 r18 brand bg fs26/700
  + `inset 0 0 0 1px rgba(255,255,255,.14), 0 6px 12px rgba(0,0,0,.25)`;
  label fs20/500. Add button: `rgba(255,255,255,.05)` + 2px dashed `.34`,
  plus-circle `rgba(255,255,255,.12)`.
- **Edit mode**: card border → `.3`, rotate ±0.8° wiggle; red minus 44px
  `#d92d20` + 2px white border + `0 6px 14px rgba(0,0,0,.35)` at −10,−10;
  grip dots top-right `rgba(255,255,255,.7)`; Done pill h56 accent fs20/600;
  Add button brighter `rgba(255,255,255,.16)` + dashed `.7`, plus-circle
  accent; hint "Drag to reorder. Tap the red minus to remove." 16px/1.35
  `rgba(255,255,255,.86)`.
- **Settings**: bg `#0f1726`, header h72 `#121d31` border `.09`; search pill
  h48 r24 `rgba(255,255,255,.06)` border `.14`; Close pill `#eef2fa`/`#0f1726`;
  left nav w216, rows min-h56 r14 fs19, active `rgba(74,163,255,.16)` +
  border `.45` + `#7dbcff`; sub-tab pill `rgba(255,255,255,.06)` r18, tabs
  h48 px18 r14 fs18, active accent; section titles 16px/600 ls .14em
  uppercase `#a9b6cc`; cards `#17233a` r20 border `.09` / rows
  `rgba(255,255,255,.05)` r14-16; option rows h72 r16 p16, selected
  `rgba(74,163,255,.14)` + 2px `#4aa3ff` + 30px check circle `#4aa3ff`/
  `#0f1726`; toggle 60×34 r17 `#1f6fd1`, knob 28px white; slider 8px track
  `rgba(255,255,255,.16)` + `#4aa3ff` progress, 32px white thumb; preview
  card w300 r20, stage `#1a2740` + conic checker; preview button tile 92×88
  r20 `rgba(20,16,50,.7)` border `.22`; bottom fade `→ #0f1726`.

## Plan

- [x] Phase 1: tokens — Heebo in index.html; `.theme-dark` accent vars;
      mockup purple gradient added to background catalog as default.
      *(implemented via dedicated `--app-backdrop` — see deviation note)*
- [x] Phase 2: DeckButton card restyle (r24 translucent card, icon tile,
      label) + edit-mode minus/grip/rotate.
- [x] Phase 3: DeckHeader (dark bar, pill nav, round buttons, page pills).
- [x] Phase 4: DockedSidebar weather card + grid gaps + Add button.
- [x] Phase 5: SettingsView dark restyle (nav, tabs, option rows, toggle,
      slider, cards, preview).
- [x] Verify: vue-tsc, vitest, live screenshots at 1024×600.

## Trade-offs

- Keep per-button fills/effects machinery — the new card style is the
  *default* look; explicit per-button styles still override.
- Edit overlay keeps edit/copy/delete actions but restyled to the mockup's
  minus + grip vocabulary (mockup only shows minus; copy/edit remain needed).
- Settings restructure is style-level, not DOM-level, where possible.

## Implementation Results

### Global tokens (`main.css`, `index.html`, `App.vue`)

- Heebo loaded in `index.html` alongside Instrument Serif + JetBrains Mono.
- `.theme-dark` moved to the mockup palette: surface `#0f1726`, primary
  `#1f6fd1`, accent `#4aa3ff`, text `#eef2fa`/`#a9b6cc`, glass
  `rgba(20,16,50,.4)` + `rgba(255,255,255,.18)` borders.
- **Deviation from plan**: `--color-background` was left as the flat navy
  surface. ~40 existing usages treat it as a card/modal/control background —
  making it the mockup's gradient painted purple over every Settings card.
  The page gradient moved to a dedicated `--app-backdrop` var; `App.vue`
  layers `background: var(--color-background)` + `background-image:
  var(--app-backdrop)` on the themed root. `.bg-animated` stays transparent
  so animated/scene backgrounds keep working.
- `.btn`, `.btn-icon-circle`, `.input` restyled to glass circles/pills with
  accent focus states (replacing the metallic Uiverse treatment).

### Dashboard

- `DeckHeader.vue`: 84px translucent dark bar (`rgba(10,8,32,.66)` +
  blur), 56px glass circle actions, accent active states, avatar with
  status dot, hide-handle bar per mockup.
- `GlassPillSceneSelector.vue` / `PageNavigation.vue`: dark pill
  `rgba(255,255,255,.08)` r18, blue accent glider
  (`#1f6fd1` + `0 4px 12px rgba(31,111,209,.45)`), 48px touch segments.
- `DeckButton.vue`: editorial card — r24 `rgba(20,16,50,.4)` glass,
  `inset 0 1px 0 rgba(255,255,255,.18) + 0 10px 24px rgba(8,6,30,.28)`,
  64px r18 brand icon tile, 20px/500 label. Removed the dome/gloss/mask
  Uiverse layers. Labels clamp to 2 lines (`-webkit-line-clamp`) so long
  labels ellipsize instead of clipping mid-glyph.
- `DeckGrid.vue`: 12px gap/padding, dashed `rgba(255,255,255,.34)`
  placeholder cells with plus-circle affordance.
- `DockedSidebar.vue`: transparent column + `rgba(255,255,255,.14)`
  divider, vertical compact weather card (icon tile + Instrument Serif
  temp) sized for the 100–132px rail.

### Settings (`SettingsView.vue`)

- Flat `#0f1726` page, 72px `#121d31` header, search pill (r24,
  `rgba(255,255,255,.06)`), white "Back" pill.
- 216px left nav rail: min-h56 r14 rows, active `rgba(74,163,255,.16)` +
  `#7dbcff` text.
- Sub-tab pill bar with accent active tab; section titles 16px/600 ls .14em
  uppercase `#a9b6cc`; cards `#17233a` r20.
- Toggles 60×34 `#1f6fd1` w/ 28px knob; sliders 8px track + `#4aa3ff`
  progress + 32px thumb; option rows with selected accent ring.
- Button preview stage uses a conic checkerboard so the DL-016
  transparency slider is visually meaningful.

### Edit mode

- Always-visible affordances per mockup: 44px `#d92d20` minus badge
  (top-left, −10/−10, 2px white border), edit/copy glass circles top-right,
  grip/drag indicator, ±0.8° wiggle, brighter dashed add-slot.
- Hint text "Drag to reorder. Tap the red minus to remove." in sidebar.
- `DeckFooter`/`EditSidebar` moved to the same navy/accent language;
  footer controls (grid size, Add/Delete Page, Save Profile) unchanged
  functionally.

### Header overflow fix (found in browser verification)

At `--touch-multiplier` ≥1.5 the right action group measured ~671px and
starved the scene pill to a 10px sliver; a pill `.segment` also intercepted
clicks on the edit-mode toggle. Fixes in `DeckHeader.vue` /
`GlassPillSceneSelector.vue`:

- `.header-left` `flex: 1 1 auto; min-width: 0` (selector can shrink/scroll).
- `.header-center` `flex: 0 1 auto` — claims no space when empty.
- `.header-right` `flex: none` + `z-index` — actions never overlap, never
  compress.
- Pill container `overflow-x: auto` so scenes scroll inside their share.

Result at 1024×600 / mult 2: right group ~633px, pill ~248px scrollable
with truncated segment labels; all header buttons hit-test clean.

### Verification

- `vue-tsc --noEmit`: clean.
- `vitest run`: 175/175 pass (incl. `vdock-ui-redesign-property*` scans).
  Literal-px font-sizes flagged by property8 (15/16/28px new + pre-existing
  10px) converted to rem.
- `npm run build`: succeeds (PWA precache warning is pre-existing).
- Browser at 1024×600 and 800×480: dashboard, settings, edit mode
  screenshotted and checked; edit-mode toggle, scene pill scroll, settings
  nav, minus/edit/copy badges, empty-slot plus all exercised.
- `openSettingsInNewTab` respected — header Settings click opens the
  standalone settings window rather than navigating in place.

### Follow-up: masonry packing for Appearance card grids

User flagged dead space on the Screen Saver tab — implicit grid rows set
each row's height to the tallest card, stranding gaps under short ones.
All four Appearance sub-tab grids now carry `.settings-grid-masonry`
(`display:block` + `column-width:340px`, cards `break-inside:avoid` +
`margin-bottom`): cards pack column-wise with no row alignment, and the
column count self-adjusts (2 columns at 1024px where `minmax(380px)` only
fit 1 — strictly denser). Verified live: Screensaver tab packs 8 cards in
2 columns, Buttons tab shows Display+Preview | Touch Mode side by side
with the transparency slider above the fold. 176/176 tests pass.
