# DL-087 — Settings chrome: apply actions in the topbar, savebar removed

## Problem

A persistent bottom bar duplicated what the topbar already offers: a
status dot ("All changes save automatically") plus an Apply button
(or Revert + Save & Apply on the Buttons page). It consumed vertical
space on small panels for a message that is always true.

## Changes

- `SettingsView.vue` topbar — "Reset section" is now followed by the
  apply actions:
  - Buttons page (`appearance → buttons`): "Draft not applied" hint
    (only while `buttonPageDirty`), Revert, Save & Apply to all keys.
  - Other tabs except About/Logs: "Apply" (save + dashboard refresh).
- Bottom `.savebar` removed entirely — markup, `savebarVisible`,
  `savebarMessage`, all `.savebar` CSS (incl. the reduced-motion and
  short-viewport rules), and the stale "sticky savebar" comment.

## Implementation Results

- Live: appearance/buttons topbar shows Reset · Revert · Save & Apply;
  Templates shows Apply only; About/Logs show neither — same
  visibility as the old bar.
- 390px: `.topbar-actions` wraps (added `flex-wrap`), no horizontal
  overflow; topbar grows to fit.
- `.content` keeps `padding-bottom: 32px` so cards don't sit flush.
- Tests: `button-behaviour-subtabs`, `property6_settings`,
  `app-paths` green; `vue-tsc` clean; `dist` rebuilt.
- Ref: `design-log/refs/settings-topbar-apply-*.png`.
