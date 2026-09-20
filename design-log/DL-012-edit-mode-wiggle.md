# DL-012 — Edit-Mode Wiggle Opt-In

**Date:** 2026-09-20
**Status:** Implemented

## Background

User request: "by default remove the dashboard button wobbling animation."
Entering edit mode applied an iOS-style `btn-wiggle` rotate animation to every
deck button (`.deck-grid.is-edit-mode .deck-button` in `DeckGrid.vue`). On the
7" touch panel the constant motion read as jitter, not affordance.

## Problem

The wiggle was unconditional: any edit mode meant every button rotated ±1.5°
at 0.3s forever. No setting gated it — `animationsEnabled` exists but nothing
consumes it.

## Questions and Answers

**Q: Remove entirely or make it opt-in?**
A: Opt-in. "By default remove" keeps the affordance available; edit mode still
shows the `::after` drag-handle dot and the edit sidebar, so the state stays
discoverable without motion.

## Design

- New persisted setting `editModeWiggle`, default `false`
  (`stores/settings.ts` — ref, `PersistedUserSettings`, payload, apply,
  localStorage defaults `=== true`, watch list, store return).
- Backend allowlist `ALLOWED_USER_SETTING_KEYS` += `'editModeWiggle'` so it
  survives server sync (the un-allowlisted `screensaverWidgets` bug showed
  what happens otherwise).
- `DeckGrid.vue`: wiggle CSS gated by a new `wiggle-buttons` class bound to
  `isEditMode && settingsStore.editModeWiggle`; `is-edit-mode` still drives
  the drag-handle dot and placeholder styling.
- `SettingsView.vue`: "Wiggle buttons in edit mode" toggle under "Enable
  animations".
- `types/index.ts` `ProfileSettings` + `defaultProfile.ts` defaults updated.

## Implementation Plan

- [x] Setting plumbing (store, types, backend allowlist, defaults)
- [x] DeckGrid gate + Settings toggle
- [x] Tests + log

## Trade-offs

- **Chose** a dedicated key over reusing `animationsEnabled`: the latter is
  unconsumed today and would silently couple this to a future global
  animation switch.

## Verification Criteria

1. Edit mode shows no wobble with default settings; enabling the toggle
   restores it.
2. The drag-handle dot still appears in edit mode either way.
3. Setting persists across reload and server sync.

## Implementation Results

- All plumbing landed; `edit-mode-wiggle.test.ts` asserts the default, the
  class gate, persistence wiring, the Settings toggle, and the backend
  allowlist. vitest 48 files / 163 tests; `vue-tsc` clean; pytest 739.
- Manual check outstanding: toggle edit mode on the panel and confirm no
  wobble; flip the setting on and confirm it returns.
