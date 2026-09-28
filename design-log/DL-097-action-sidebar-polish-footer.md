# DL-097: Action sidebar polish + conditional animated footer

Two related pieces of chrome polish from live screenshots on the 7" panel.

## Problem

1. **Edit-mode action sidebar truncates every category name.** Each row
   carries a pair of `^`/`v` buttons — a session-only, never-persisted
   category *reorder* feature that reads visually as expand/collapse
   controls and consumes ~90–176px of row width, leaving ~100px for the
   name: "Quick Lau...", "Window M...", "Audio & V...". Rows are flat and
   undifferentiated — "looks very very simple".
2. **The footer bar is dead space outside edit mode.** It renders
   unconditionally; with a single-page scene and the header visible it is
   an empty 44–112px strip eating grid height the 7" panel needs.

## Design

### Action sidebar (`EditSidebar.vue`)

Adopt the settings accordion's visual language (DL-053 `panel-head` +
icon + hint + rotating chevron + `Collapse`):

- **Reorder buttons removed** (`moveCategoryUp`/`Down` + emits deleted in
  DashboardView too) — clicking the row already toggles; the freed width
  fits every category name (longest: "Window Management", 17ch) at every
  touch multiplier, so no renames.
- Row becomes `[icon chip] [full name] ......... [count pill] [chevron]`:
  - Per-category accent hue via a `CATEGORY_ACCENTS` map keyed by id
    (`--cat-accent` inline style); chip = rounded square, tinted bg
    (color-mix 18% over white overlay fallback) + accent icon.
  - Hardcoded categories gain an `icon` field in `actionCategories`;
    catalog-appended categories pass through the backend `CategorySpec.icon`
    (robot/code/sliders-h already defined); fallback `puzzle-piece`.
  - Single `chevron-down` icon rotated `-90°` when collapsed — transform
    transition instead of icon swap (same as `chevron-open` in Settings).
  - Count pill `(n)` muted at right before the chevron.
  - Expanded state: accent-tinted border + bg, chip brightens.
- Actions list wrapped in `<Collapse :open>` (grid-rows 250ms + fade).
  Crucially `Collapse` keeps children *mounted* (`visibility`, not v-if)
  so the touch-drag bindings registered at mount stay live — a v-if or
  v-show swap would strand them.
- `.category-actions` gets a thin left accent rail + indent so items read
  as belonging to the category.
- Search input gains a leading icon + focus glow.

### Conditional footer (`DashboardView.vue` + `DeckFooter.vue`)

Footer mounts only when it has content:
`!isMobileViewport && (isEditMode || !showHeader || totalPages > 1)`.

- Non-edit + visible header + single page → no footer → the ~44–112px
  goes back to the grid (the complaint).
- Header hidden → footer exists to host the docked reveal pill (DL-014
  follow-up — in-flow dock means "no footer = homeless pill" without this).
- Multi-page non-edit → footer exists for the page dots — removing it
  would orphan page navigation (the header's PageNavigation auto-hides).
- Wrapped in `<Transition name="footer-slide">`: enter slides up from
  below the viewport edge (dashboard `overflow:hidden` clips it), leave
  slides down off it; `leave-active` goes `position: absolute` anchored
  to `.dashboard-view` (relative) so the grid reclaims height at the
  start of the slide — inside the motion, not a snap after.
- User's described flow: header hidden → footer (pill) → click pill →
  header in, footer slides away → toggle edit → footer slides up with
  controls. Matches.

## Trade-offs

- Conditional mount means the footer appears/disappears with header
  autohide — a 44px layout shift at that moment; masked by the slide and
  net-positive space (header ≈90–164px freed vs footer ≈44–112px added).
- Reorder feature deleted outright: session-only on a mostly-hardcoded
  catalog; near-zero value, and it was the truncation culprit.
- property22 test scans `EditSidebar.vue` for `.btn-control` — updated to
  scan `.category-header` (keeps its `min-height: 44px` baseline).

## Implementation Plan

- [ ] DL entry (this file) + README index row
- [ ] Failing tests: `edit-sidebar-categories.test.ts` (no controls/
      reorder refs; icon chip, count, chevron classes; 44px floor),
      footer conditional + footer-slide assertions
- [ ] EditSidebar rework; DashboardView category icons + catalog icon
      passthrough + drop reorder; footer v-if + Transition; DeckFooter
      slide styles
- [ ] property22 test update; vue-tsc; vitest; npm build; live verify

## Implementation Results

**Implemented as designed.** Deviation: "Window Management" (17ch) still
ellipsized at touch-multiplier 2 — 21px over — so it was renamed to
"Windows" (the one sanctioned rename; id `window-management` unchanged,
no category-merge or alias targets depend on the label).

- `EditSidebar.vue` — reorder controls block + emits deleted; rows are
  `role="button"` + `tabindex` + `aria-expanded` with icon chip (per-category
  `--cat-accent`), full name, count pill, single rotating `chevron-down`;
  actions wrapped in `<Collapse>` (grid-rows + fade, children stay mounted
  so touch-drag bindings persist); `.category-actions` indents under an
  accent rail; search gains leading icon + focus glow; `color-mix` tints
  carry rgba fallbacks on every declaration.
- `DashboardView.vue` — `icon` on all 13 hardcoded categories (rocket,
  desktop, volume-high, music, window-restore, globe, keyboard,
  chart-line, clock, cloud-sun, compass, video, puzzle-piece); catalog
  merge passes `CategorySpec.icon` through so AI Assistants/Developer/
  Sliders keep their backend icons; `moveCategoryUp/Down` handlers + emit
  bindings removed; footer mounts only when
  `isEditMode || !showHeader || totalPages > 1` inside a `footer-slide`
  Transition.
- `DeckFooter.vue` — `footer-slide` styles; `leave-active` goes
  `position: absolute` anchored to `.dashboard-view` so the grid reclaims
  the strip inside the slide, not after it.

**Verified live on :5000 (built dist), tm=2, 1343×727:**

- Non-edit + header visible + 1 page → footer absent, grid fills to the
  viewport bottom (727).
- Header hidden → footer present (615–727), pill docked in-flow
  (630–713, `position: static`) — zero overlap, unchanged from DL-014 fix.
- `showHeader=true` → header mounts +200ms, footer slides out and
  unmounts +400ms; autohide at 5s → footer slides back in hosting the
  pill, header exits +5.6s. Both directions exercised.
- Edit toggle → footer mounts with edit controls; leaving edit → footer
  enters `footer-slide-leave-active`/`position: absolute` at +150ms,
  unmounts +450ms.
- All 16 category names fully visible, zero truncation at tm=2 — includes
  catalog groups AI Assistants (57), Developer (108), Sliders (4).
- Click toggles: System collapsed → `.open` removed, chevron rotated
  -90° (`matrix(0,-1,1,0,0,0)`), collapse closed, and its 20 action items
  remained mounted (drag bindings live).
- a11y snapshot: rows expose `button "Name n" expandable expanded`.

**Tests:** `edit-sidebar-categories.test.ts` (5) + `property22` updated
(`.btn-control` → `.category-header`, keeps its 44px floor).
`vue-tsc` clean; vitest **314/314** (the news-carousel flake from the
previous session passed this run); `npm run build` clean, `dist/` rebuilt.

Screenshots: `design-log/refs/edit-sidebar-polish.png` (expanded Quick
Launch row + accent-railed action item), `edit-sidebar-header.png`
(row close-up).
