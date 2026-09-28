# DL-089 — "Request a feature" + settings credit footer

## Problem / ask

About tab needed a "Request a feature" flow that emails the maintainer
(with optional pasted screenshot, size-capped, address never shown),
the version badge had to sit next to the VDock title, and Settings
needed a credit footer with LinkedIn/GitHub/website links.

## Changes

- `backend/routes/feedback.py` — `POST /api/feedback` (multipart):
  message required ≤4000 chars, optional image (png/jpg/gif/webp
  ≤2MB), 3MB total cap, 30s per-IP throttle. Always stores a copy in
  `data/feedback/` then relays via FormSubmit multipart
  (`formsubmit.co/<addr>`) — the address is built server-side from
  `VDOCK_FEEDBACK_EMAIL` env or a split-string default, so the UI
  never contains it. Returns `{success, emailed}` — `emailed:false`
  means "stored locally, relay unavailable".
- `FeatureRequestModal.vue` — text area (char counter, 4000 cap),
  paste-to-attach (clipboard image) + file picker, preview chip with
  size, Send/Cancel; iOS-safe 16px input rule kept.
- `SettingsView.vue` — About hero gains "Request a feature";
  `.about-title-row` now flexes so `v<ver>` hugs the title (the shared
  `.nav-ver` auto-margin had pushed it to the row edge); nav rail
  gains a `nav-credit` footer: "Created by Daniel S. · v2.1.0" +
  LinkedIn/GitHub FA icons + the DS logo image linking to
  daniel-shalom.com.
- `backend/app.py` — blueprint registered.
- `frontend/public/assets/branding/daniel-shalom-logo.jpg` — added.

## Implementation Results

- Live end-to-end: POST → `{success, emailed:true}`, JSON + relay
  accepted; stored copy verified in `data/feedback/`.
- Modal verified: opens from About, counter/enabled states correct,
  address absent from DOM.
- Footer verified live: credit line + 3 icon links render in the nav
  rail at desktop and 390px (logo image bound via `:src` — a static
  `src` tripped Vitest's asset resolver).
- 6 new backend tests (validation, throttle, relay, local store);
  frontend suite 306/306 (one known Vitest teardown race), `vue-tsc`
  clean, `dist` rebuilt.
- **Ops note:** FormSubmit requires one-time activation — the first
  real submission triggers a confirm email to the target address;
  relay only flows after it's clicked. Until then (or on relay
  failure) requests still land in `data/feedback/`.
- Refs: `design-log/refs/about-request-feature-*.png`.
