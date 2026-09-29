# DL-114 — Screensaver weather chip unavailable state

## Background

The screensaver weather pill (top-left) reads from `useWeather()`, which
resolves coordinates via browser geolocation (or a manual city) and then
fetches Open-Meteo. On the 7" panel geolocation is frequently denied or
absent, so `weather` stays `null` and the chip renders a gold `cloud-sun`
icon, an em-dash location, and a literal `--°C` — looking permanently
broken rather than temporarily unavailable. The Markets widget next to it
handles the same situation gracefully (`marketError || 'Loading prices…'`
in `.ss-empty`), so the inconsistency is also visually obvious.

## Problem

When weather data was never fetched successfully, the chip shows a dead
`--°C` placeholder with no hint of why, or how to fix it (the actionable
hint "set a city in Settings" produced by the composable is thrown away —
`ScreenSaver.vue` destructures only `weather` from `useWeather()`).

## Design

Mirror the Markets widget's "unavailable" treatment inside the pill's own
format (icon + kicker + display value):

- Consume `error`/`loading` from `useWeather()` in `ScreenSaver.vue`.
- **Error + no data:** icon swaps to `cloud-slash` and loses the gold
  accent; the kicker (`.ss-weather-loc`) shows the composable's error text
  (e.g. `Location unavailable — set a city in Settings`,
  `Couldn't find "X"`), ellipsized with a `title` tooltip; `--°C` is dimmed
  so it reads as a placeholder, not a reading.
- **Loading, no data yet:** kicker shows `Locating…` (same label
  `WidgetColumn` uses), matching the existing `--°C` + `—` placeholder.
- **Stale data + later error:** keep showing the last good reading —
  `useWeather` intentionally does not clear `weather` on failure, so the
  error visual only appears when there is nothing to show. No staleness
  badge (overkill for a glanceable chip).

Hiding the pill on error was rejected: the widget is user-positionable in
the layout editor (it must stay visible to drag), it recovers on the next
15-minute refresh, and the other feed widgets all stay mounted with empty
states.

## Implementation Plan

- [ ] `ScreenSaver.vue`: destructure `error`/`loading`, update `weatherIcon`,
      `location`, `tempStr` computeds and add `.is-unavailable` styling.
- [ ] Rebuild `frontend/dist` (the panel serves the built bundle).
- [ ] Verify live via Playwright with geolocation denied.

## Trade-offs

Showing the raw error sentence in the kicker is long for tracked-caps, but
it carries the fix ("set a city in Settings") — capped with ellipsis +
tooltip rather than replaced by a vague "Unavailable".

## Verification Criteria

- With geolocation denied and no manual city: chip shows muted
  `cloud-slash`, reason text, dimmed `--°C`.
- With data present: unchanged gold icon + temp.
- `WidgetColumn` weather card already has an error block — untouched.

## Implementation Results

- Implemented in `ScreenSaver.vue`: `useWeather()` now contributes
  `loading`/`error`; `weatherUnavailable` (`!weather && !!error`) drives a
  `.is-unavailable` class, a muted `cloud` icon, the error text in the
  kicker (ellipsized, `--ss-weather-scale`-aware `max-width`, `title`
  attribute), and `--°C` at 0.4 opacity. `Locating…` shows during the
  first fetch.
- **Deviation:** `cloud-slash` → `cloud`. `faCloudSlash` is a Pro-only
  icon — absent from `free-solid-svg-icons@6.5.1`, so the component
  rendered an empty comment node. Plain `cloud` muted keeps the weather
  family without claiming a condition.
- Verified live on the dev server (:4444) via Playwright with geolocation
  denied and `open-meteo`/`bigdatacloud` fetches blocked: chip shows
  `is-unavailable`, `fa-cloud` at `rgba(255,255,255,0.4)`, kicker
  `LOCATION UNAVAILABLE — SET A CI…`, `--°C` at 0.4 opacity (screenshot
  captured).
- `vue-tsc` clean; `frontend/dist` rebuilt for the panel. Vitest suite:
  364/365 pass — the single failure is the randomized `property8`
  clamp() sampler catching a pre-existing `font-size: 19px` in
  `SettingsView.vue` (untouched by this change).
