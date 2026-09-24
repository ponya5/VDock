# DL-067: Mobile fullscreen — promoted button + best-effort auto-trigger

**Date:** 2026-09-25
**Depends on:** DL-063 (mobile chrome — introduced the `⋮` overflow menu
that originally held Fullscreen)

## Background

On phones, `MobileDeckChrome`'s Fullscreen action lived inside the `⋮`
overflow menu alongside Refresh and Exit VDock. Landing on the dashboard for
the first time (e.g. right after scanning the Connect page's QR code) still
shows the browser chrome (address bar, tab strip) until the user happens to
open that menu and tap Fullscreen — not obvious, and easy to miss entirely.

## Problem

The user asked, for a phone launching the dashboard in landscape: highlight
the fullscreen control so it's immediately obvious, and auto-trigger
fullscreen automatically if at all possible.

Auto-triggering is only partly possible: the Fullscreen API's
`requestFullscreen()` requires a recent user gesture in essentially every
mobile browser (Chrome, Safari) unless the page already holds fullscreen
permission (e.g. an installed PWA that was granted it previously, or the
Electron shell, which uses a native window call instead of the DOM API).
An unattended call from `onMounted` will silently reject on a fresh mobile
browser tab — there is no way around that from web content.

## Design

- **Promote, don't hide:** move Fullscreen out of the `⋮` menu into its own
  always-visible 44×44 icon button in the main chrome bar, next to the page
  steppers and the `⋮` button. Refresh and Exit VDock stay in the overflow
  menu — they're not needed on first load the way Fullscreen is.
- **Pulsing highlight:** while not yet fullscreen, the button carries a
  `mc-suggest` class — a soft blue glow/border plus a `box-shadow` pulse
  animation (same visual language as the scene rail's active-segment blue,
  `#1f6fd1`) — so it reads as "tap me" without needing a tooltip or copy.
  The pulse stops the moment the user taps the button (success or not) or
  fullscreen is entered through any means (including the auto-attempt
  below), tracked by a local `suggestFullscreen` ref that starts `true` and
  flips permanently `false` on first tap. It does not reappear if the user
  later exits fullscreen — one suggestion per visit, not a nag.
- **Best-effort auto-attempt:** `MobileDeckChrome`'s `onMounted` calls the
  existing `toggleElectronFullscreen()` (from `useElectron`) once, guarded
  on `!isFullscreen`, and swallows a rejection silently. This is a genuine
  no-op on most phone browsers, but costs nothing there and actually lands
  in the contexts that do allow it (Electron's native fullscreen call,
  or a PWA/browser that already granted the permission from a previous
  visit) — "automatic where possible" without pretending the API can be
  forced on every platform.
- `prefers-reduced-motion: reduce` disables the pulse animation, matching
  the rest of the mobile chrome's motion handling.

## Trade-offs

- The auto-attempt is unverifiable from this session (no physical phone
  browser available) — it is expected to no-op on a stock Chrome/Safari tab
  and is not the primary fix; the promoted, pulsing button is the part that
  reliably solves the user's ask on every platform.
- No setting to disable the pulse — it's single-shot per visit, low-risk to
  leave unconditional.

## Verification Criteria

- `MobileDeckChrome.vue`: Fullscreen button renders in the main bar (not
  inside `mc-menu`), toggles the icon between expand/compress, and its
  `mc-suggest` class is present only while not fullscreen and before the
  first tap.
- The overflow menu still opens/closes and contains exactly Refresh and
  Exit VDock.
- Frontend suite green; `vue-tsc --noEmit` clean.

## Implementation Results

- Moved the Fullscreen button from `.mc-menu` to a new `.mc-fullscreen-btn`
  in `MobileDeckChrome.vue`'s main bar; added `suggestFullscreen` ref and
  the `mc-suggest` pulse animation (`prefers-reduced-motion` respected).
- Added a best-effort `toggleElectronFullscreen()` call in `onMounted`,
  guarded on `!isFullscreen`, with a swallowed catch for the expected
  rejection on unprivileged mobile browser tabs.
- Verified: full frontend suite (59 files / 250 tests) green, `vue-tsc
  --noEmit` clean. Not verified live on a physical phone browser from this
  session — flagged for the user to confirm the promoted button (and,
  opportunistically, the auto-trigger) on their device.
