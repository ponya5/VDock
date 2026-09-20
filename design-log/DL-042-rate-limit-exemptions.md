# DL-042: Rate-limit exemptions for local read routes

## Problem

User reported "too many requests" errors while browsing settings.
`backend/.env` sets `RATELIMIT_DEFAULT=200 per day, 50 per hour`.
Most API blueprints were already exempt (DL-023), but `upload_bp` —
which serves every user image through `/api/uploads/<path>` — was not.
Each `<img>` on the dashboard (avatars, backgrounds, button icons) and
every picker thumbnail grid is a request; opening the Background
picker alone fires ~10-20 GETs, draining 50/hr in minutes. Non-exempt
read blueprints (`assets_bp`, `system_bp`, `templates_bp`,
`app_profiles_bp`) added steady background usage. Once exhausted, every
non-exempt route returns 429 until the window resets.

## Design

Exempt all local read surface; keep limits only on abuse vectors:

- `serve_uploaded_file` — per-view exemption (`limiter.exempt(fn)`), so
  the upload POST write path in the same blueprint stays limited.
- `assets_bp`, `system_bp`, `templates_bp`, `app_profiles_bp` — local
  reads with no abuse surface.
- `auth_bp` stays limited (5/min login brute-force guard), and
  `upload_bp`'s POST stays limited — writes remain the gated surface.

## Implementation Results

- `app.py`: five new `limiter.exempt` calls + `serve_uploaded_file`
  import. Frontend polling (`/app-monitor`, session logs, profiles) was
  already on exempt blueprints, so no client changes were needed.
- Verified: `import app` clean; 757/757 backend tests pass.
