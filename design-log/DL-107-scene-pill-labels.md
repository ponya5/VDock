# DL-107: Scene-pill labels always readable (stop the squeeze)

## Problem

On the 7" header the scene rail truncates names to "M…", "Cl…",
"Web…". Cause: `.header-left` is space-starved (avatar + title vs the
~310px right button cluster), the pill container shrinks, and each
`.segment` flex-shrinks to its `min-width:96px` floor — where
padding(32px) + logo(26px) + gap(8px) leave ~30px for the label, so the
`text-overflow:ellipsis` label shows 1–3 characters. The container's
`overflow-x:auto` never engages because segments compress before they
overflow.

## Design

- `.segment` gets `flex-shrink: 0` — a pill always keeps its natural
  content width; when the row overflows, the existing scroll-on-the-rail
  behavior takes over (scrollbar hidden, `measureGlider` already
  `scrollIntoView`s the active pill on every switch).
- `.segment-label` `max-width` 112px → 200px — full names read; only
  genuinely long names still ellipsize (the cap also keeps the
  edit-mode badge lane sane).
- Narrow-header slimming (`max-width: 1100px`): padding 16px→10px
  horizontal, gap 8px→6px, logo 26px→22px, font cap 18px→16px — most
  4–5 scene sets then fit on the panel without scrolling; overflow
  still scrolls when it doesn't.

The label keeps `min-width:0` + ellipsis for the cap case; the edit
badge lane (`pill-edit .is-active` min-width) is unaffected — it widens
the pill instead of eating the label now.

## Implementation Plan

- [ ] `.segment` `flex-shrink:0`; label cap 200px; narrow-viewport slim
      rules
- [ ] Test pin: segment doesn't shrink, label cap raised
- [ ] vitest, vue-tsc, build

## Implementation Results

Landed as designed:

- `.segment` → `flex-shrink: 0`: pills always render at natural content
  width; when the row outgrows the rail the container's existing
  `overflow-x:auto` (hidden scrollbar) takes over, and `measureGlider`'s
  `scrollIntoView` keeps the active pill visible on every scene switch.
- `.segment-label` cap 112px → 200px — "Claude Code", "Websites" etc.
  read in full; the cap only catches genuinely long custom names.
- `@media (max-width: 1100px)` slim block: padding 16→10px horizontal,
  gap 8→6px, logo 26→22px, font cap 18→16px — a typical 4–5 scene set
  fits the 1024px header without scrolling.
- The 768px label cap (84px, mobile/narrow windows) unchanged; the
  edit-mode badge lane still widens the active pill rather than eating
  its label.

**Tests:** +2 source pins in `scene-app-live-dot.test.ts` (no segment
shrink; 200px label cap + narrow slim block). 16/16 in that file,
`vue-tsc` clean, `npm run build` clean, `dist/` rebuilt.
