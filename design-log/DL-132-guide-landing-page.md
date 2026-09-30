# DL-132 — Dedicated guide landing page

## Problem

The user guide lives inside Settings as an embedded tab panel — cramped,
modal-ish, and easy to miss. It deserves a real standalone page: roomy
enough for screenshots and search, openable in a fresh browser window so
the deck and the guide can sit side by side.

## Design

- **`/guide` route → `GuideView.vue`** — a landing page, not a settings
  tab. Hero (wordmark, tagline, search field), feature sections laid out
  as alternating rows with real screenshots, and the same site footer the
  Settings page ships (`Created by Daniel S. · v…` + LinkedIn / GitHub /
  personal site).
- **Settings nav "Guide"** now opens `/guide` in a new browser window
  (`window.open`) instead of switching tabs. The embedded `UserGuide.vue`
  panel and the `guide` tab are removed; the sidebar entry keeps its icon
  + gains an external-link hint.
- **Smart search** — a search box filters feature sections live by
  title/keywords/body text (token match), reports a match count, and
  `Enter` scrolls to the first hit. `?q=` is honoured on load so a link
  can deep-search.
- **Screenshots** — real captures of the running deck in
  `frontend/public/guide/` (deck, media/now-playing, header pill,
  settings sub-tabs, MCP modal, triggers, agent bar, scene editor,
  tour, screensaver, auth gate).
- **Footer** — extracted to `components/SiteFooter.vue`, shared by
  `SettingsView` and `GuideView` so the credit/links stay identical.
- `standalone=1` guard learns `canBeStandalone` for `/guide`.

## Implementation Results

- `views/GuideView.vue` — landing page with hero (brand mark, version,
  "Back to the deck"), `/`-focusable smart search (AND-token match over
  title/tagline/body/keywords, live match count, Enter scrolls to first
  hit, `?q=` honoured), chip jump-nav, and 12 feature sections with
  real screenshots in `frontend/public/guide/` (deck, scenes editor,
  media/now-playing, header pill, agents bar, MCP modal, integrations,
  screensaver settings, settings tabs, tour).
- `components/SiteFooter.vue` — the settings credit bar extracted and
  shared; SettingsView mounts it with the `settings-dock` layout class.
- `router/index.ts` — `/guide` route (lazy), `canBeStandalone` meta;
  the standalone guard now consults meta instead of hardcoding
  `/settings`.
- `SettingsView.vue` — Guide nav item opens `/guide` via `window.open`
  (external-link icon affordance, `data-tour` anchor kept); `guide` tab,
  `UserGuide.vue`, PAGE_META entry, `.guide-page` CSS removed.
  `jumpToSearchResult` and `?tab=guide` deep links open the window.
- Verified live: `/guide` serves 12 sections + 10 images; settings nav
  opens the popup window; search filters correctly.
- `UserGuide.vue` deleted — superseded entirely.
- Font-size property test compliance: all literal sizes use clamp()/var.
