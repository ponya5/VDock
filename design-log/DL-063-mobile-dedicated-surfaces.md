# DL-063: Dedicated mobile surfaces — deck chrome + screensaver

The DL-061/062 mobile treatment is still a *shrunken desktop*: the scene
selector hides behind a reveal pill (the primary mobile action — switching
scenes — is two taps away), page dots live in a separate footer strip, and
the screensaver renders the full desktop widget set (weather, headlines,
markets, sports) crammed into a phone screen. The ask: purpose-built
mobile surfaces — an intuitive one-tap control surface (e.g. carrying the
phone to drive Claude Code), and a screensaver showing only clock + world
clock.

## Design

### MobileDeckChrome (new component)

A persistent ~52px top bar replaces DeckHeader + DeckFooter entirely on
mobile (`isMobileViewport`). Three elements, nothing configurable:

- **Scene rail** — the centerpiece. Horizontally scrollable segmented
  control; one tap switches scene. Unlike the desktop pill (glider sized
  `100/N%` + `translateX`, which misaligns once segments overflow into
  scroll), the mobile rail uses a **measured indicator**: the glider's
  width/offset are read from the active segment's real box, so it stays
  aligned under scroll, and the active segment is `scrollIntoView`ed when
  the scene changes by any path (rail tap, page swipe). Live app dots
  preserved — a green dot on the Claude scene means its session is
  actually running, the key signal for the carry-the-phone use case.
  Segments: min 72px wide, 44px tall, icon + ellipsized label.
- **Page nav** — `‹ 1/2 ›` compact steppers, rendered only when the scene
  has >1 page. Swipe navigation still works.
- **Overflow menu** — single ⋯ button → Fullscreen / Refresh / Exit
  (app controls, not configuration; DL-061's guarantee intact). Exit
  keeps the confirm dialog.

DeckHeader and DeckFooter don't mount on mobile; their `.mobile`
overrides added in DL-062 (reveal pill, overlay header, slim footer) are
dead code and get removed. The `padding-top: 34px` pill reservation in
DashboardView goes too — the chrome is in-flow.

### Screensaver mobile variant

`.screensaver.ss-mobile` via the shared flag:

- Feed widgets (weather, news, sports, market) return `false` from their
  `show*Widget` computeds on mobile — hidden regardless of settings, and
  their composables don't start (also fixes `startWeather()` running
  unconditionally).
- World clock is force-shown on mobile (explicitly requested content).
- `.ss-pos` flattened (`position: static !important`, transform/left/top
  cleared) → clock + world clock become a centered flex column instead of
  absolute-positioned desktop coordinates.
- Clock scales to the landscape height (`~26vh`), date line compact,
  world clock becomes a wrapped row of zone chips (label over time,
  hairline separators) instead of a vertical list — readable density, no
  scroll.
- Layout-edit machinery can't trigger on mobile; drift/resize flatten
  harmlessly.

## Implementation Results

Verified live on a real device emulation (Galaxy S9+ landscape, 658×320
CSS px, native touch) and on the LAN URL `http://192.168.1.173:5000`:

- **MobileDeckChrome** replaces DeckHeader + DeckFooter on phones:
  56px bar, 4 scene segments (44px touch targets), measured glider
  tracks the active segment pixel-perfect (verified: segment box
  {x:104,w:143} == glider box after switching Media → Claude Code).
- **Scene switching is one tap** — the rail is always visible, no
  reveal step. Live app dots and `scrollIntoView` keep the active
  scene reachable under rail scroll.
- **Page steppers** `‹ 1/2 ›` render only when the scene has >1 page.
- **⋯ overflow** opens Fullscreen / Refresh / Exit VDock; Exit keeps
  the confirm dialog. No configuration affordances anywhere (DL-061).
- **Screensaver on mobile**: clock (26vh serif) + date + world-clock
  chip row only; weather/news/market/sports hidden AND their
  composables no longer start (the previously unconditional
  `startWeather()` is now gated too). `.ss-pos` flattened into a
  centered column — verified visually, reads cleanly.
- Portrait still shows the rotate gate; Settings/profiles unaffected.
- Dead DL-062 mobile overrides removed from DeckHeader/DeckFooter and
  the 34px pill reservation from DashboardView.

Caught during verification: the first LAN check showed an empty rail —
`dist` had been built before the `scenes` prop fix (`currentProfile.scenes`,
not `dashboardStore.scenes`). Rebuilt; LAN now renders all 4 segments.

Checks: `vue-tsc` clean, production build clean, 239/239 frontend tests.
