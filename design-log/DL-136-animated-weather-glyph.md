# DL-136 — Animated, day/night-aware weather glyph

## Problem

The screensaver weather pill shows a static FontAwesome icon that knows
nothing about day/night and never moves: a clear night still shows the
same `cloud-sun` glyph as a July noon. Feedback: "weather widget should
be interactive — moon at night, sun by day, sun+cloud when cloudy,
animated rays slowly orbiting the sun, moon slowly spinning, rain when
it rains, wind, etc."

## Design

### Data: real WMO code + day flag

`WeatherResult` currently exposes a pre-resolved `icon` tuple — the
glyph component needs the raw condition instead. `fetchCurrentWeather`
adds `is_day` to the Open-Meteo `current=` list and returns
`code: number` (the WMO weather code) and `isDay: boolean`. `icon` is
kept for compatibility; WEATHER_CODE_MAP gains 77/85/86 (snow grains,
snow showers) which were unmapped.

### Component: `components/screensaver/WeatherGlyph.vue`

A pure-SVG 64×64 scene, props `{ code, isDay, windy, unavailable }`:

| Scene | Trigger | Motion |
|---|---|---|
| Sun | 0/1 + day | Disc + 8-ray ring, rays orbit ~32 s linear |
| Moon | 0/1 + night | Crescent slowly rotating (~40 s) + 3 twinkling stars |
| Sun+cloud | 2 + day | Sun peeking top-left, small cloud drifting in front |
| Moon+cloud | 2 + night | Same with moon |
| Overcast | 3 | Two-layer cloud, slow side drift |
| Fog | 45/48 | Cloud silhouette + 3 mist lines sliding alternately |
| Drizzle | 51/53/55 | Cloud + 2 thin short drops |
| Rain | 61/63/65/80/81/82 | Cloud + 3-4 drops falling, staggered delays |
| Snow | 71/73/75/77/85/86 | Cloud + flakes falling with sway |
| Storm | 95/96/99 | Cloud + bolt that flashes every ~3 s |

`windy` (windSpeed ≥ 30 km/h) overlays two curved streaks sweeping
across whatever scene is active — wind rides over rain or clear alike.

`unavailable` renders a dimmed static cloud — the pill's slot must stay
draggable in layout-edit mode even with no reading.

All motion is CSS keyframes on SVG groups; `prefers-reduced-motion`
freezes everything (each scene stays legible statically). Colors ride
the existing widget palette — sun warm amber, moon pale, clouds
translucent white — so it sits inside the current `.ss-weather` pill
unchanged in size: the glyph box reuses the icon's font-size clamp via
`1em` sizing on the SVG root.

### Wiring

`ScreenSaver.vue` swaps `FontAwesomeIcon :icon="weatherIcon"` for
`<WeatherGlyph :code :isDay :windy :unavailable>`. `weatherIcon` computed
is removed (no other consumer — `weather.value.icon` is only read here).

## Implementation Results

- `weatherService.ts`: `current=` now fetches `is_day`; `WeatherResult`
  gained `code` (raw WMO) + `isDay`; codes 77/85/86 mapped (Snow
  Grains / Snow Showers) which previously fell through to "Unknown".
- `components/screensaver/WeatherGlyph.vue`: new pure-SVG scene
  component (64×64 viewBox). Sun disc + 8-ray ring orbiting at 32 s;
  swaying crescent moon + 3 twinkling stars; sun/moon peeking behind a
  bobbing cloud for partly-cloudy; two-layer overcast; drifting mist
  lines for fog; 2-drop drizzle / 4-drop rain; swaying snowflakes;
  storm cloud + bolt that flashes in a double-blink every 3 s. Wind
  (≥30 km/h) overlays two gusting streaks on any scene. `unavailable`
  renders a desaturated static cloud so the pill's edit slot survives.
  Transform-vs-attribute conflict handled: positioning transforms sit
  on wrapper `<g>`s so CSS keyframes can't clobber `<use>` offsets.
  `prefers-reduced-motion` freezes every animation.
- `ScreenSaver.vue`: `FontAwesomeIcon` swapped for `WeatherGlyph`;
  sizing reuses `.ss-weather-icon`'s clamp via `1em` on the SVG root.
- Tests: `weather-glyph.test.ts` — 10 cases covering every scene
  branch, the wind overlay, and the unavailable fallback.
  15/15 weather tests green; `vue-tsc` clean; `dist` rebuilt.
- Verified live: it's 01:36 in Modiin — the saver correctly shows the
  night scene (spinning crescent + stars) beside 19°C
  (`refs/saver-weather-glyph-moon-2026-10-01T22-36-09-432Z.png`,
  `refs/saver-weather-glyph-closeup-2026-10-01T22-36-22-376Z.png`).
