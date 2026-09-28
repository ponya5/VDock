# DL-095 — Settings topbar action polish + panel-head presence

## Problem / ask

The Appearance → Buttons topbar action cluster looks ugly (user report +
screenshot): "Draft not applied" is naked orange text wedged between two
identical ghost buttons; "Reset section" (section utility) and "Revert"
(draft undo) read as interchangeable; panel heads are thin — the ~11px
muted uppercase h2 crowds the inline hint; `.preview-head` is a third,
slightly different header idiom (11px/14px padding vs 13px/18px).

## Design

Full polish of the header area, approved scope:

1. **Draft state → chip.** `draft-hint` becomes `.draft-chip`: amber dot
   + "Draft not applied" inside a warn-tinted pill
   (`rgba(245,181,71,0.10)` bg, 0.35-alpha warn border, 999px radius,
   `--fs-xs` semibold). Renders as a status badge, not a control.
2. **Action grouping.** Hairline `.topbar-divider` (1px × 20px,
   `var(--line)`) inside the `isButtonsPage` template, separating the
   `Reset section` utility from the draft lifecycle group
   `[chip] [Revert] [Save & Apply]`.
3. **Panel-head presence.** `.panel-head h2`: `--fs-xs → --fs-sm`,
   `--text-2 → --text` — still an uppercase eyebrow but readable as a
   section header; hint keeps `--fs-sm`/`--text-3` (now differentiated
   by weight + color rather than size).
4. **One header idiom.** `.preview-head` padding aligns to
   `.panel-head` (`13px 18px 11px`).

## Implementation Results

- `.draft-hint` replaced by `.draft-chip` — amber dot (`.draft-dot`,
  6px) + label inside a warn-tinted pill; renders inside the
  `isButtonsPage` template only while `buttonPageDirty`.
- `.topbar-divider` (1px × 20px `var(--line)`) renders at the top of the
  `isButtonsPage` template, so `[Reset section] │ [chip] [Revert]
  [Save & Apply]` — divider only appears on the Buttons page, never
  dangles before the generic Apply button on other tabs.
- `.panel-head h2` bumped `--fs-xs → --fs-sm`, `--text-2 → --text`;
  `.preview-head` padding aligned to `13px 18px 11px` + same type
  treatment — one header idiom across panels and preview cards.
- Verified live (chrome-devtools MCP, 1400×800): chip pill + divider
  visible once a motion draft field changed (select → pulse); Revert
  enabled. Headers read clearly at panel size.
- `vue-tsc --noEmit` clean; `npm run build` green — `dist/` rebuilt.

## Follow-up — warn note → toast (2026-09-28)

The permanent `.note.warn` block under the Buttons column ("drafts until
Save & Apply, which rewrites every existing key") was removed on request;
the same warning now fires as a toast once per dirty episode:

- `watch(buttonPageDirty)` — on false→true fires
  `notificationsStore.warning('Draft changes', …, { duration: 7000,
  important: true })`; the flag resets when the draft is reverted/applied
  so a new episode warns again.
- `Notification.important` added to the store type: `toasts` under
  `toastLevel: 'errors-only'` now returns `error` OR `important` —
  this warning guards an irreversible per-key rewrite, so it pierces
  the errors-only filter (user decision). `'off'` still silences it.
- Verified live: `errors-only` instance shows the amber toast top-center
  when a motion/design field changes; `ns.toasts` includes the flagged
  warning, unflagged warnings stay filtered. `vue-tsc` clean, `dist`
  rebuilt.

## Follow-up — Revert button removed (2026-09-28)

The user found `Reset section` and `Revert` read as duplication and asked
for Revert's removal. The topbar button was deleted; the draft group is
now `[Reset section] │ [chip] [Save & Apply]`. `revertButtonDefaults()`
remains as a helper — `resetAppearanceSection` still calls it so a
section reset also syncs the draft previews. With no discard control,
an applied-or-reset section is now the only way out of a dirty draft
(deliberate: drafts only exist until Save & Apply or Reset).
