# DL-054 — Settings shell redesign: sidebar nav, row-based panels, preview rail

## Background

The user supplied a static HTML/CSS redesign mockup
(`settings screenshots/redesign/`) describing a new information architecture
for the Settings view. The existing settings UI grew organically: a top header
with search, a left icon rail, then two more nested tab rows inside Appearance
(Appearance → sub-tab → Buttons/Screensaver sub-sub-tab), plus large card
sections that left most of the right side of the window empty on wide displays.

## Problem

- Three levels of navigation (rail → appearance sub-tabs → button/screensaver
  sub-sub-tabs) made settings hard to find and hard to reach on a touchscreen.
- Card layouts waste horizontal space; there is no live preview beside the
  controls being edited.
- Header search occupies prime header space and is visually disconnected from
  the navigation it routes to.

## Design

Port the mockup's shell into `SettingsView.vue` while preserving every real
binding and handler:

```
.settings-app
├── aside.nav           brand · search · nav-groups(+nav-subs) · footer
└── main.main
    ├── header.topbar   breadcrumb · page title · blurb · actions
    ├── div.content     .col (panels/rows) + optional sticky .rail preview
    └── div.savebar     autosave status + Apply-to-dashboard
```

Key mappings:

- **Navigation**: `tabs` becomes sidebar groups. Appearance becomes an
  expandable group whose sub-links drive the existing `appearanceSubTab` ref
  (`buttons` | `layout` | `background` | `screensaver`). `buttonsSubTab` and
  `screensaverSubTab` stop being page switchers; their contents merge into
  single pages, with search/deep-links scrolling to anchored panels.
- **Rows**: `.row` (label+desc left, control right, hairline separators) and
  `.row.stack` (slider/picker/wide controls) replace the card+toggle-grid
  language on Appearance/Server. `.row-reset` hover affordance wraps
  `SettingResetButton`.
- **Rail**: the four Appearance pages get `.content.has-rail` with a sticky
  `.rail` preview; collapses under/beside content below ~1180px, hidden under
  ~760px where it becomes a top block.
- **Savebar**: settings autosave via the store deep watch — there is no dirty
  state. The savebar is the honest "clean" variant: green dot + "Changes save
  automatically" + a real **Apply to dashboard** action
  (`requestVdockRefresh()`), which broadcasts live settings to the deck
  window. No fake dirty counter or dead Revert button.
- **Search**: same index, moved into `.nav-search`; results dropdown anchored
  to the sidebar. `jumpToSearchResult` gains anchor scrolling.
- **Tokens**: mockup's `--bg/--panel/--line/--accent/--r-*` palette and
  `--nav-w/--rail-w/--gutter` are scoped under `.settings-app` so they never
  leak; motion uses existing `--ease-out` + 150–250ms.

Pages: Appearance×4 (rails), Templates, Server (sub-anchors to
Startup/Connection/Device), Integrations, Logs, About (hero+features+build).
Templates/Integrations/Logs keep their existing internal markup, re-skinned to
`.panel` shells. Widget settings (weather/location/text-size/news/sports/
market/worldclock) become expandable `.row` detail regions inside the Screen
Saver → Widgets panel, keeping the DL-053 `Collapse` animation.

## Implementation Plan

- [x] New shell template (nav/topbar/content/savebar) + script nav model
- [x] Appearance×4 pages with rows + sticky rails
- [x] Templates/Server/Integrations/Logs/About panels
- [x] Scoped design-system CSS; retire old header/nav/tab styles
- [x] Update tests pinned to removed sub-tab markup; typecheck + full suite
- [x] Live verify at 1024×600 and large viewport

## Trade-offs

- **No fake save model**: the mockup's dirty-count/Revert bar was rejected —
  the store autosaves; pretending otherwise would lie to the user.
- **Single-file rewrite over splitting into page components**: dozens of
  handlers and store bindings stay co-located; page split can come later.
- **Sub-refs kept internally**: `appearanceSubTab` remains the Appearance
  page model so existing tests/search routing keep working with minimal churn.

## Verification Criteria

- All existing settings controls still bound and mutating the store.
- `vue-tsc` clean; full Vitest suite green.
- Live: sidebar nav/subs, sidebar search routing, rail stickiness/responsive
  collapse, savebar, widget accordions, 1024×600 usability.

## Implementation Results

Shipped in `frontend/src/views/SettingsView.vue` (~4,600 lines). The old
header + icon-rail + nested-tab shell was replaced by the mockup's
`.settings-app` grid: `aside.nav` (brand, `#setting-search`, nav-groups with
`Collapse`-animated `.nav-sub` lists, Reload/Back footer) beside `main.main`
(`.topbar` → `.content` `.col`+`.rail` → `.savebar`).

**Navigation.** `appearanceSubs` (`buttons`/`layout`/`background`/`screensaver`)
and a matching Server group drive the nested links; `selectAppearanceSub` +
`scrollToPanel` route and scroll `mainEl`. `jumpToSearchResult` maps
`deepTab`/anchors onto the new pages. Result crumbs moved to their own line so
labels no longer truncate.

**Pages.** Appearance×4 (each with a sticky `.rail` preview), Templates,
Server (sub-anchors), Integrations, Logs, About. Screen-saver widgets are
`.row`s whose `.row-control` carries an `Options` `aria-expanded` button plus
the enable switch; detail bodies live in `Collapse` `.widget-detail` regions.
Weather location + widget size merged into the Weather detail. The topbar
gains a contextual "Reset section" (`resetAppearanceSection`) on Appearance
pages.

**Savebar.** Honest autosave model: clean state shows "All changes save
automatically" + a working **Apply to dashboard**. On the Buttons page the
three motion/design defaults (`previewAnimation`/`previewIconLoop`/
`previewEffect`) are held as a draft — `buttonPageDirty` flips the bar to
"Design draft not applied — preview only" and enables Revert +
Save & Apply (`revertButtonDefaults` / `saveAndApplyButtonSettings`).

**Fixes during verification.** `profilesStore.currentProfile` (non-existent)
→ `dashboardStore.currentProfile` in `availableScenes` — the scene dropdown
now populates. `SETTINGS_DEFAULTS.minimumTouchTargetSize` reference dropped.
≤880px breakpoint: nav becomes a sticky, `max-height:52vh`, scrollable top
panel instead of pushing all content below the fold.

**Tests.** `logs-and-weather-move.test.ts` and the sub-tab assertions in
`button-behaviour-subtabs.test.ts` updated to the new IA. `vue-tsc`: no
SettingsView errors (remaining errors elsewhere are pre-existing on HEAD).
Vitest: 231/231 green.

**Live-verified** at 1024×600 (all pages + search + widget expand + draft
savebar/revert) and at 1600×900; no horizontal overflow at 820px.

## Follow-up — emil-design-eng polish pass

Ran the `emil-design-eng` checklist over the new shell. Changes, all in
`SettingsView.vue` scoped styles:

- **Press feedback everywhere**: `.btn` `:active` now `scale(0.97)` (was a
  1px nudge); `scale(0.98)` added to `.nav-item`, `.nav-sub button`,
  `.nav-result`, `.pick`, `.seg label`; `:active` tint on
  `.log-file-row`, `.app-item`, `.category-header`.
- **Touchscreen truth**: every `:hover` rule gated behind
  `@media (hover: hover) and (pointer: fine)` — on the 1024×600 panel,
  hover fired on tap and stuck until the next tap. `touch-action:
  manipulation` + `-webkit-tap-highlight-color: transparent` remove the
  double-tap delay and tap flash.
- **Popover origin**: `.nav-results` gets `transform-origin: top` + a
  160ms `scale(0.97)`/`translateY(-4px)`/`opacity` enter — it now scales
  down from the search input instead of popping in cold.
- **Switch tactility**: knob transition moved to a mild spring curve
  (`cubic-bezier(0.34,1.3,0.64,1)`, 220ms) — subtle overshoot on toggle.
- **Missing transitions**: `.seg label` checked state, `.pick`
  border/background, `.select`/`.input` border-color all transitioned
  (were snapping). `.pick` tick gets a `scale(0.3→1)` pop.
- **Slider grab feel**: `::-webkit-slider-thumb` + `-moz-range-thumb`
  `scale(1.2)` on `:active` — thumbs grow under the finger.
- **Page-enter stagger**: `.col > *`/`.rail > *` rise `translateY(10px)`
  + fade at 260ms ease-out, 45/85/120/150ms delays — pages mount via
  `v-if` so it replays per navigation. Occasional interaction → allowed.
- **Savebar**: `data-state="dirty"` slides up once; status dot color
  cross-fades.
- **A11y**: `:focus-visible` outlines added to nav items/results and
  accordion headers; `prefers-reduced-motion` extended to cover every
  new animation and transition.

Verified: `vue-tsc` clean, 231/231 vitest, popover origin + stagger +
switch spring confirmed live at 1024×600.

