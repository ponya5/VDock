# DL-041: Sub-tab width utilization + About layout

## Problem

Sub-tabs split each settings pane into one narrow masonry column
(~340px) even when a sub-tab holds a single card — Button Display
scrolled ~600px of controls down the left third of a 1024px screen.
About was capped at 720px and stacked everything vertically.
Server/Integrations used a `minmax(380px)` grid that also collapsed
to a single column in the ~760px pane.

## Design

- `.card-span` — `column-span: all` lets a lone card fill the masonry
  width.
- `.slider-pair` — related sliders/inputs sit side by side.
- `.toggle-grid` — toggle rows become compact label-over-switch pills,
  five across on wide panes.
- `.preview-cols` — Live Preview splits into stage | animation selects |
  design picker columns.
- Touch Mode spanning card: mode options as a horizontal row, stat
  pills and Advanced Settings beside them; per-mode descriptions hidden
  (the name + scale chip carry the meaning).
- `.masonry-dense` (≥900px) — `column-width: 220px` adds a third column
  to card-heavy grids; feed textareas shrink to 64px.
- `.about-grid` — three columns: full-width brand header row (logo,
  title, description inline), three side cards (Help / Connect /
  Support), then Key Features spanning the bottom as a 4-up chip grid.
- Non-masonry settings grids dropped from `minmax(380px)` to 300px so
  two columns actually fit the pane; Server/Integrations switched to
  masonry for balanced packing, and the compact card rules
  (12/18px padding, 48px toggle rows, 0.8rem help) apply there too.

## Implementation Results

- `SettingsView.vue`: `card-span`, `slider-pair`, `toggle-grid`,
  `preview-cols`, `sidebar-pair`, `masonry-dense`, `button-row`, and the
  three-column `.about-grid` with `about-brand-row` /
  `about-features-all` spans. Narrow fallbacks: ≤820px → 2 cols,
  ≤560px → 1 col, ≤700px → pairs stack vertically.
- `TouchModeSelector.vue`: options row across the top, preview info +
  advanced settings grouped horizontally beneath.
- `ButtonDesignPicker` scoped to `repeat(4, minmax(0,1fr))` inside the
  preview column — its 5-up grid overflowed the ~240px column.
- Measured card bottoms at 1024×600 (viewport 600): Button Display 581,
  Live Preview 609, Touch Mode 595, Layout 570, Screensaver
  Settings/Backgrounds ~428, About 597, Integrations 594, Server 627
  (was 1057). Screensaver Widgets keeps scrolling (8 config cards ≈
  2.4 viewports of content) but uses a spanning picker + 3 dense
  columns — 1672 → 1450.
- 226/226 frontend tests, vue-tsc clean, production build clean.
- Verified no horizontal overflow at 520px; single-column fallbacks
  engage correctly.
