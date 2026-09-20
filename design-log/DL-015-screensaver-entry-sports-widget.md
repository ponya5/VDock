# DL-015 — Screensaver entry points, market chip feedback, sports widget

## Background

Three user-reported gaps on the 7" touch panel:

1. "Customize Layout" (Settings → Screensaver) appears to do nothing.
2. Adding a stock ticker (SECZ) appears to do nothing; the user does not want
   to configure an API key.
3. No sports news widget exists.

## Problem

**Customize Layout.** `handleCustomizeScreensaverLayout` sends the
`screensaver_layout_edit` ui_command and toasts "opened on the deck window".
When Settings lives in the same tab (`openSettingsInNewTab=false`, the
default), the dashboard is unmounted — the command sits in the pending queue
until the user manually navigates back, so from the user's seat nothing
happens. Same bug for "Test Screensaver".

**Ticker.** SECZ is valid and the backend already resolves it ($10.86 via the
keyless Yahoo chart endpoint — no API key exists or is needed). The dead
`marketApiKey` field (DL-002: "read by nothing") implies a key is required,
and the chip has no empty/error state — a failed or empty fetch renders a
blank `.ss-chip`, invisible. The chip also only renders inside the
screensaver, which the settings copy never says.

**Sports.** No sports feeds/widget. The existing `/api/news` proxy already
accepts arbitrary RSS feeds, so a sports widget is a second `useNews`
instance pointed at sports feeds.

## Design

### SettingsView.vue

- `handleTestScreensaver` / `handleCustomizeScreensaverLayout`: when
  `!isStandaloneSettings`, `router.push('/')` after `sendUiCommand` — the
  pending queue drains on dashboard mount and the screensaver/editor opens
  immediately. Standalone windows keep the toast-only path (command reaches
  the deck window via socket/broadcast).
- Remove the dead `marketApiKey` input; help copy now states quotes are free
  (Yahoo + CoinGecko, no key) and that the chip shows inside the screensaver.
- Fix stale widget descriptions: news "(requires free API key)" and market
  "stocks optional" are both wrong — neither needs a key.
- New 'sports' widget option + conditional section with a `sportsFeeds`
  textarea and a Test Feeds button (defaults to built-in sports feeds).

### Market chip (ScreenSaver.vue + useMarket.ts)

- `useMarket.refresh`: an empty quote list with configured tickers sets
  `error` instead of silently leaving `prices` empty.
- Chip mirrors `.ss-news-empty`: `marketError || 'Loading prices…'` when the
  list is empty so the widget is never invisible.

### Sports widget ('sports')

- `screensaverLayout.ts`: add 'sports' to `ScreensaverWidgetId`, ids, labels;
  default `{x: 20, y: 42}` (free space below-left of the clock — the bottom
  row is already occupied by news/market/worldclock).
  `normalizeScreensaverLayout` fills missing ids, so old persisted layouts
  are safe.
- `newsService.ts`: `DEFAULT_SPORTS_FEEDS` (ESPN Top, BBC Sport, Sky Sports —
  all verified live RSS, no key).
- `useNews(feedsSource?)`: optional feed getter; default keeps `newsFeeds`
  behaviour so `useNews()` callers/tests are unaffected.
- `ScreenSaver.vue`: sports card reuses `.ss-news` row markup (tappable
  headlines, trophy icon) with its own `useNews` instance and pause;
  `openArticle(item, pauseFn)` pauses the instance that was tapped.
- `settings.ts`: `sportsFeeds` string mirroring `newsFeeds`
  (interface/ref/payload/apply/default/expose).
- `user_settings.py`: allowlist `'sportsFeeds'` — without it the field is
  dropped on save (same bug class as the screensaverWidgets note in that
  file).
- Widget text-size section condition gains 'sports'.

## Scope change — visual redesign (user-supplied mockup)

The user provided a bundled HTML mockup (`Screensaver.html`) defining a new
editorial look: JetBrains Mono meta text + Instrument Serif display type, a
gold accent (#f2b040), weather top-left, ticker top-right, giant serif clock
with accent colon, date flanked by hairlines, and a bottom band of numbered
"Headlines" articles + "World time" serif rows. The redesign re-skins every
widget while keeping the `.ss-pos` free-position + layout-editor machinery —
widget ids are unchanged, only internals and default positions move.
'Sports' becomes a fifth section styled like Headlines. Fonts load from
Google Fonts (already in the PWA runtime-cache allowlist) with Georgia /
ui-monospace fallbacks for offline panels.

## Implementation Plan

- [x] Phase 1: same-tab navigate-back for Test/Customize buttons
- [x] Phase 2: market key field removal + chip empty state + copy fixes
- [x] Phase 3: sports widget (layout id, settings field, composable param,
        chip markup, settings section, backend allowlist)
- [x] Phase 4: screensaver redesign per mockup (fonts, accent, per-widget
        restyle, new default positions)

## Trade-offs

- Sports defaults to a mid-left position rather than squeezing a fifth slot
  into the bottom row — four widgets across would overlap on 800px panels.
- The sports chip duplicates the news card markup rather than abstracting a
  shared component — the file already specialises each widget's wrapper for
  layout-edit drag/resize, and the duplication is ~50 lines of template.
- `marketApiKey` stays in the store/allowlist (harmless persisted key);
  only the misleading UI field is removed.

## Verification Criteria

- Same-tab: Customize Layout opens the editor immediately; standalone keeps
  working.
- `SECZ` shows a price on the chip; an unreachable symbol shows text, not a
  blank chip.
- Sports widget toggles on, fetches headlines, survives save/reload.
- `vue-tsc` clean; vitest suite passes.

## Implementation Results

- **Phase 1** (`SettingsView.vue`): both `handleTestScreensaver` and
  `handleCustomizeScreensaverLayout` call `sendUiCommand` then
  `router.push('/')` when Settings is embedded in the dashboard tab
  (`!isStandaloneSettings`); the pending queue drains on dashboard mount, so
  the screensaver/editor opens immediately instead of appearing to do nothing.
- **Phase 2** (`useMarket.ts` + `ScreenSaver.vue`): configured-ticker fetch
  returning an empty list now sets `error = 'No quotes for <symbols>'`; the
  market region renders `marketError || 'Loading prices…'` in `.ss-empty`
  when `marketPrices` is empty — SECZ ($10.86 via keyless Yahoo) or an
  explicit message is always visible. No API key field in the UI; stale
  option descriptions corrected.
- **Phase 3**: `'sports'` added to `ScreensaverWidgetId`/ids/labels
  (`screensaverLayout.ts`); `DEFAULT_SPORTS_FEEDS` (ESPN, BBC Sport, Sky
  Sports) in `newsService.ts`; `useNews(feedsSource?)` parameterized so the
  sports instance reads `sportsFeeds` → built-in defaults; `sportsFeeds`
  plumbed through `settings.ts` (interface/ref/payload/apply/default/watch/
  expose — the watch entry was missed initially and added on review) and
  `user_settings.py` allowlist; Settings gains a Sports widget toggle +
  conditional feeds section with its own Test Feeds button (`testFeeds`
  helper shared with news).
- **Phase 4** (`ScreenSaver.vue` + `index.html`): editorial redesign per
  mockup — JetBrains Mono + Instrument Serif loaded in `index.html`; giant
  serif clock with gold accent colon (`hourStr`/`minuteStr` split +
  `.ss-time-colon`), hairline-flanked date, top-left weather glance, top-right
  serif market rows, bottom sections "Headlines" (2-col numbered grid),
  "Sports" (numbered list), "World time" (serif rows). All sections keep
  `.ss-pos` + `.ss-resize` edit machinery; `sports` default position
  `{x:60, y:78}` sits between news and worldclock. `index.html` now loads
  the two Google fonts.
- Fresh-install `screensaverWidgets` default is now all five widgets
  (persisted choices unaffected); `.ss-news`/`.ss-sports`/`.ss-worldclock`
  section widths clamp for the 800px panel.
- **Deviations**: the `.ss-news-row`/`.ss-chip` markup was replaced by
  `.ss-article`/`.ss-section` markup; `news-carousel.test.ts` source-grep
  assertions were updated to the new class names. `property8.test.ts`
  (font-size clamp property) intermittently fails on a pre-existing
  `font-size: 10px` in `.app-badge` — committed before this work, out of
  scope.
- **Verification**: `vue-tsc --noEmit` clean; vitest 175/175 pass.
- **Follow-up (world clock + section headers)**: the market chip gained a
  "MARKETS" `.ss-section-head` to match the "HEADLINES"/"SPORTS"/"WORLD
  TIME" headers. An analog-face world-clock variant (SVG face + offset
  subtitle) was tried, then **reverted** when the user confirmed the target
  design: plain serif rows — mono-caps city label left, big serif time
  right — per the supplied mockup. Saved `screensaverLayout` was reset to
  defaults via the app's own Reset/Save toolbar so widget positions match
  the mockup (weather top-left, market top-right, headlines bottom-left,
  world time bottom-right). Verified live at 1024×600.
