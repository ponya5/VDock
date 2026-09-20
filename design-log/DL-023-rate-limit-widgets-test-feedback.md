# DL-023 — Rate limit starving data widgets + invisible test feedback

## Problem

1. **Stocks/sports dead on the 7" panel** — MARKETS showed "Market data
   unavailable", SPORTS hung on "Loading sports…", while news/weather looked
   fine (they render their last good fetch — the widgets that had not yet
   loaded when the quota ran out were the ones that looked broken).
2. **Test Feeds / Test Connection gave zero visual feedback.**

## Root causes

- `backend/.env` sets `RATELIMIT_ENABLED=True` + `200 per day, 50 per hour` —
  a DoS-protection default for exposed deployments. The self-refreshing
  widgets (weather/news/market/sports), metrics polls and settings sync burn
  through 50/hour in normal operation; once exhausted every data endpoint
  returns 429. `profiles`/`actions`/`user_settings` were already exempt —
  the data blueprints were not.
- `App.vue` gated the whole toast layer behind `!isStandaloneSettings` —
  the standalone settings window (which is where the Test buttons live)
  rendered no toasts at all, so the success/error notifications the test
  handlers already fired went nowhere.

## Changes

- `app.py`: exempt `news_bp`, `market_bp`, `weather_bp`,
  `system_metrics_bp`, `app_monitor_bp`, `config_bp` — internal data reads,
  not abuse surface. `auth`/`upload`/`system` remain limited (brute-force
  and upload-flood protection is the limiter's actual job).
- `App.vue`: `NotificationCenter` now mounts in standalone settings too.
- `SettingsView.vue`: persistent inline result under each Test button —
  green "N headlines fetched" / red failure text (`describeTestError` maps
  429 → "rate limit reached", network failure → "server unreachable"),
  surviving until the next run; toasts still fire on top.
- `useNews(feedsSource, label)` — sports instance now reports "Sports
  unavailable" instead of "News unavailable".

## Verification

- `curl /api/market?symbols=SECZ` on the production backend → **429 "200 per
  1 day"** — confirmed the quota wall before the fix.
- Live in dev: Test Feeds → inline green "40 headlines fetched" + toast.
- `vue-tsc` clean; 49 files / 176 tests pass.

## Note

The rate-limit exemption takes effect on **backend restart**; the panel
serves `frontend/dist`, which was rebuilt with this fix.
