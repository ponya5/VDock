# DL-103: About action row trim + tour swipe/copy fixes

## Problem

The About hero's action row duplicates other surfaces and buries the most
useful action:

- **Help & guide** button → the Guide tab already sits in the settings side
  nav (DL-088); duplicate entry point.
- **GitHub** link → the same repo link is in the Build card's Repository row
  and in the dock footer's credit links; duplicate.
- **Launch tutorial** — the action a returning user most likely wants — sits
  mid-row styled identically to everything else.
- Tour copy: the "Scenes & Pages" step should explicitly call out
  left/right swipe on the dashboard, and the final step still points at
  "Settings → About" for the guide (the Guide tab is the real home now).

## Design

- `SettingsView.vue` about-actions becomes:
  `[Launch tutorial (btn primary — leftmost, distinct accent)]`
  `[Request a feature]` `[Report an issue]` `[Star the repo]`.
  `data-tour="about-help"` goes away with the removed button (no tour step
  or test references it).
- `tutorial.ts`: Scenes & Pages text explicitly says swiping left/right on
  the dashboard switches scenes; final step copy points re-launchers at
  Settings → Guide instead of About.

## Implementation Plan

- [ ] `SettingsView.vue`: reorder/retint/remove buttons
- [ ] `tutorial.ts`: copy updates
- [ ] Visual check at 1024×600 + desktop widths

## Implementation Results

Landed as designed:

- `SettingsView.vue` About — the action row is now: **Launch tutorial**
  (leftmost, `btn primary` accent — the one action that changes app
  state), Request a feature, Report an issue, Star the repo. The Help &
  guide button is gone (Guide already sits in the side nav — the removed
  button's only behavior was `activeTab = 'guide'`); the standalone
  GitHub button is gone (the repo link survives on the Build card and the
  author credit). `data-tour="about-help"` removed with the button.
- `tutorial.ts` — Scenes & Pages step now says "swipe right/left anywhere
  on the dashboard to move between scenes" (explicit per request; the
  swipe handler itself already mapped left→next / right→previous).
  Final step re-pointed: "The full Guide lives in Settings → Guide —
  re-run this tour anytime from Settings → About" (the old copy sent the
  reader to a Help & Guide button that no longer exists).

**Tests:** vitest **325/325**, `vue-tsc` clean, `npm run build` clean.
No dedicated test added — the row is plain template; the behavior it
drops was a tab switch already covered by the Guide nav item.
