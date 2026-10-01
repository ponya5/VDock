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

## Follow-up — side rail, sub tabs, scroll fix (2026-02-20)

**Request.** "Improve the guide landing page — add sub tabs and easy
navigation, a side navbar. I can't scroll up and down."

**The scroll bug.** `#app` is `height:100dvh; overflow:hidden` — the
body never scrolls; every view must own a scrollport. `.guide-view`
was `min-height:100vh` with no overflow of its own, so everything past
the fold was permanently clipped. Restructured: `.guide-view` is now a
fixed-height flex shell — a static side rail plus `.guide-content`,
the single scrolling column (`overflow-y:auto`).

**Side navbar.** A 264 px left rail carries brand + version, the
search box (moved out of the hero so it never scrolls away), the
section list grouped under four sub-tab headings — *The Deck*, *Media
& Display*, *Agents & Automation*, *System* — and "Back to the deck"
pinned to the bottom.

**Scroll-spy.** A passive scroll handler on `.guide-content` marks the
last section whose top passed a mark ~30 % down the column as active;
the rail highlights it (accent bar + tint). Group lists collapse to
matching items while searching.

**Sub tabs / mobile.** The existing hero chips moved out of the hero
into a dedicated rail. ≤ 980 px the sidebar hides; the hero regains
brand/back/search and the chip rail becomes `position:sticky` at the
content top — horizontally scrollable, active chip highlighted, so
navigation stays one tap away on the panel and phones.

Verified headless (built bundle): 1400×900 shows the rail + active
"Agent Awareness" after scrolling; 600×900 shows the sticky chip bar
pinned while content scrolls; `scrollHeight > clientHeight` on the
content column confirms scrolling works. Guide tests 9/9, Property 8
green, `npm run build` clean → dist.

## Follow-up 2 — section order matches the sidebar groups

**Request.** "Order the guide topics chronologically — scrolling down
mixes topics from different sections."

The `features` array (page order) had drifted from `NAV_GROUPS`
(sidebar order): `media` rendered between `scenes` and `header` —
jumping Media & Display → The Deck — and `screensaver` rendered after
`integrations`, jumping Agents → Media again. Reordered the array to
walk the groups top-to-bottom: deck, scenes, header → media,
screensaver → agents, mcp, integrations → settings, security, tour,
connect. No structural change; the rail, chips and scroll-spy already
read the same list. Guide tests 9/9, `npm run build` clean → dist
rebuilt.
