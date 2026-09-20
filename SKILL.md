---
name: daniels-app-development
description: Build and modify applications the way Daniel expects — touch-friendly UI that fits the target viewport, visible feedback for every action, zero-config/free defaults, root-cause fixes, design-log discipline, and verified-at-real-resolution delivery. Apply to any UI feature, bug fix, or refactor in this project.
---

# How to build for Daniel

These rules come from real review feedback. Follow them on every task —
features, fixes, and styling — not just greenfield work.

## UX non-negotiables

1. **Touch targets ≥44–48px.** If a control is hard to hit on a small
   touchscreen, it's a bug. Affordances must be obvious — no invisible
   hit areas, no unlabeled thin bars.
2. **Every action gives visible feedback.** A button that appears to do
   nothing is broken even if the backend succeeded — show the state
   change, toast, or opened surface.
3. **Content fits the viewport.** No screen-inside-a-screen scrolling.
   When content exceeds the space, adapt the layout (accordion, columns,
   collapse) — don't just scroll a pane.
4. **Use all the space.** A lone column of content with two-thirds of the
   width empty is a defect. Span, balance, or restructure.
5. **Hierarchy is visible.** Different navigation levels look different.
   If two stacked tab bars are styled identically, restyle the deeper one.
6. **Scale proportionally.** A UI tuned for a small panel grows on bigger
   windows — it must not render miniature.
7. **Zero-config defaults.** Features work with no API keys and no paid
   services. Prefer free/public data paths. Ship starter content, not
   empty states.
8. **Polish the details:** no ghost empty-state artifacts, overlays have
   mutual exclusion and z-order discipline, every user-adjustable value
   has a reset-to-default, styled dialogs instead of `confirm()`/`alert()`,
   and prefer visual pickers over text-only dropdowns.

## Engineering rules

- **Fix the root cause.** Reproduce first, trace the real code path, fix
  the invariant — not the symptom.
- **Consume existing systems.** Use the project's design tokens, scaling
  variables, and defaults constants. Never invent a parallel mechanism.
- **Single source of truth** for defaults and factories.
- **State sync:** multi-window/broadcast sync must not flicker or revert —
  guard stale loads and don't echo broadcasts. Batch/debounce persistence
  writes.
- **Environment awareness:** service workers can serve stale bundles
  (auto-reload on update); rate limits must never cover the app's own
  reads/assets; keep limits on auth/write/upload surfaces.
- **Hygiene:** no secrets in commits; ignore local data, logs (incl.
  `*.log.*`), backups, uploads. Back up user config files before
  programmatic edits. Keep the repo publishable (LICENSE, SECURITY.md,
  README assets committed).

## Process

- **Design log:** for non-trivial changes, write a numbered entry
  (`design-log/DL-NNN-slug.md`) before coding — context, root cause,
  approaches considered, decision. Freeze the design sections once
  implementation starts; append an "Implementation Results" section with
  what actually happened.
- **Verify live:** run tests + typecheck + build, then check the real
  target resolution in a browser — measure element bounds, screenshot,
  click the flow. Check the small/narrow fallback too.
- **Report honestly:** real measurements and counts, what still
  overflows/scrolls, what's unverified. Concise, direct — flag bad ideas
  instead of implementing them politely.
