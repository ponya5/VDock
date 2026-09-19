# DL-005 — Screensaver Weather Widget Size

**Date:** 2026-09-19
**Status:** Planned — no code written
**Related:** DL-003 (screensaver rework — pending, does not cover widget sizing)

## Background

VDock runs on a dedicated 7-inch touch panel (~1024×600). The screensaver's
weather widget is a small pill pinned to the top-right corner; its font sizes
are `vw`-clamped (`ScreenSaver.vue`), so on a small viewport they resolve to
~18 px for the temperature and ~10 px for the location — not glanceable at
arm's length.

## Problem

No way to make the weather widget bigger. Sizes are hardcoded clamps tuned
for desktop windows.

## Questions and Answers

**Q: Scale just the weather widget, or all screensaver widgets?**
A: Weather only, for now — it is the widget the user flagged. News and chips
have their own layout constraints; a global scale can come later under the
same pattern if needed.

**Q: Discrete sizes or a continuous scale?**
A: Continuous slider (50–300 %), matching the existing "Screensaver Delay"
slider pattern. Dedicated panels vary, so fixed steps would guess wrong.

**Q: How is the scale applied?**
A: A `--ss-weather-scale` CSS variable set on `.ss-weather-corner` from
`settingsStore.screensaverWeatherSize`, multiplied into the existing clamps
and the pill's padding/gap. Keeps placement and clamps unchanged.

## Design

- `screensaverWeatherSize` (number, percent, default 100) joins the persisted
  settings pipeline: `PersistedUserSettings` interface, store ref, payload /
  apply / load defaults, watch list, store export, and
  `ALLOWED_USER_SETTING_KEYS` in `routes/user_settings.py`.
- Settings UI: a "Weather Widget" section with a percentage slider, shown
  only when the weather widget is enabled — same conditional-section pattern
  as News and Stocks already use. Added to the settings search index.
- `ScreenSaver.vue`: bind `--ss-weather-scale` on `.ss-weather-corner` and
  multiply it into icon, temp, location, gap and padding declarations.

## Implementation Plan

- [x] Task 1: `screensaverWeatherSize` through the settings store + allowlist
- [x] Task 2: Slider section + search-index entry in `SettingsView.vue`
- [x] Task 3: Scale application in `ScreenSaver.vue`

## Trade-offs

**Chosen: a setting rather than a blanket size increase.** A larger default
would fix the 7" panel but make the pill intrusive on desktop windows. A
slider lets each install find its own size.

## Verification Criteria

1. Slider at 200 % visibly doubles the weather pill; 100 % matches today's
   rendering.
2. Value persists across reload (localStorage + `/api/user-settings`).
3. `vue-tsc --noEmit` clean.

## Implementation Results

- **Task 1:** `screensaverWeatherSize` (number, %, default 100) added to
  `PersistedUserSettings`, store ref, `buildSettingsPayload`,
  `applySettingsObject`, `loadSettings` defaults, the watch list and the store
  export in `stores/settings.ts`; allowlisted in
  `routes/user_settings.py`.
- **Task 2:** "Weather Widget" slider section (50–300 %, step 10) in the
  screensaver sub-tab, shown only when the weather widget is enabled; added to
  the settings search index.
- **Task 3:** `ScreenSaver.vue` binds `--ss-weather-scale` on
  `.ss-weather-corner` and multiplies it into icon/temp/location font sizes
  plus gap and padding, so the whole pill scales proportionally.
- **Tests:** `vue-tsc --noEmit` clean; vitest 41 files / 115 tests pass.
- **Deviations:** none.
