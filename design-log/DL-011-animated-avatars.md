# DL-011 — Animated GIF Avatars

**Date:** 2026-09-20
**Status:** In progress

## Background

User request: "add the ability to add Gif as avatar image -- like a nice
animated gif". Profile avatars render as plain `<img>` in `DeckHeader` and
`ProfilesView`, so a GIF animates for free once it is stored and served
unchanged.

## Problem

`AvatarPicker.vue` nominally accepts GIF (`accept`, regex, help text all list
it), but posts to `POST /api/upload/icon` — **a route that does not exist in
the backend** (only `/api/upload` and `/api/assets/upload` do; the README
documents `/api/upload/icon` but no handler implements it). Custom avatar
upload therefore 404s for every file type, not just GIF. The picker also only
offers 18 static PNG presets.

## Questions and Answers

**Q: Does GIF animation survive the pipeline?**
A: Yes, once the right endpoint is used. `/api/upload` saves raw bytes
(`file.save`, no PIL re-encode) and `send_file` returns `image/gif`, so frames
stay intact; `<img>` animates natively in every surface that shows avatars.

**Q: New endpoint or fix the existing call?**
A: Fix the call. `/api/upload` already does everything needed (type allowlist
includes `gif`, uuid filenames, size cap). Add an `avatar` type →
`data/uploads/avatars/` so avatars stop landing in `uploads/backgrounds/`.

**Q: Bundled animated presets?**
A: Yes — generate a few procedural looping GIFs (Pillow is already a backend
dependency) into `frontend/public/avatars/` and append them to the picker
list. Keeps the feature discoverable without requiring the user to have a GIF
handy.

## Design

- `backend/routes/upload.py`: `AVATARS_DIR = UPLOADS_DIR/'avatars'`;
  `get_target_dir` maps `avatar`/`avatars` to it.
- `AvatarPicker.vue`: post to `/api/upload` (form already sends
  `type: 'avatar'`); preset list gains animated entries
  (`/avatars/animated-*.gif`).
- Generator script: `backend/tools/make_animated_avatars.py` (Pillow) →
  writes 128×128 looping GIFs to `frontend/public/avatars/`.

## Implementation Plan

- [x] Task 1: backend `avatar` upload type + picker endpoint fix
- [x] Task 2: animated GIF presets + picker list
- [x] Task 3: tests + log results

## Trade-offs

- **Chose** reusing `/api/upload` over adding `/api/upload/icon`: one upload
  pipeline, one allowlist. Cost: none — the old route never existed.
- **Chose** procedural presets over shipping third-party GIFs: no licensing
  or fetching needed; they are simple but demonstrably animated.

## Verification Criteria

1. Uploading a `.gif` through Choose Avatar succeeds and the returned URL
   renders animated in the header avatar.
2. Animated presets appear in the picker and animate in the preview.
3. Existing PNG upload path unchanged.

## Implementation Results

- **Task 1.** `routes/upload.py`: added `AVATARS_DIR` (`data/uploads/avatars/`,
  created on import) and mapped `avatar`/`avatars` types to it.
  `AvatarPicker.vue` now posts to `/api/upload` — the old `/upload/icon` call
  404'd because that route never existed; the stale `backend/README.md` entry
  documenting it was corrected.
- **Task 2.** `backend/tools/make_animated_avatars.py` (Pillow) generates
  three looping 128×128, 24-frame GIFs into `frontend/public/avatars/`:
  `animated-orbit`, `animated-pulse`, `animated-spin`. The picker lists them
  first with a "GIF" badge on the preview; uploaded GIF previews animate
  natively via `<img>`.
- **Task 3.** New `backend/tests/test_upload_avatars.py` (4 tests: type→dir
  mapping, gif allowlist, verbatim-byte storage) and
  `src/tests/avatar-upload.test.ts` (5 tests: endpoint, avatar type field,
  badge, presets-on-disk are looping GIFs). **vitest 47 files / 158 tests,
  pytest 739, `vue-tsc` clean.**
- **Deviations:** none from the design. Test learned two things: the route's
  `relative_to(UPLOADS_DIR)` means tests must monkeypatch `Config.UPLOADS_DIR`
  and `AVATARS_DIR` together; and the picker source comment mentioning the
  dead route false-positives a naive `not.toContain`, so the assertion matches
  the call expression instead.
- **Manual check outstanding:** upload a real animated GIF through Choose
  Avatar and confirm it animates in the header avatar on the deck.
