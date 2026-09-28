# DL-091 — Log files card spacing + smart log search

## Problem / ask

The Logs left card renders flush to the panel edge — the "Log Files"
heading + folder icon sit at the border (icon visually clipped), rows
touch the card edge. Also: no way to find a specific log entry inside
a loaded tail.

## Design

**Files card**: real card chrome — own border + subtle background +
inner padding so header/rows/footer sit clear of the edges. Same
treatment language as `.logs-viewer-card` (which already has padding).

**Smart search**: an input row between the toolbar and the log viewer.
- Case-insensitive substring filter over the loaded tail.
- `level:` prefix — `level:error`, `level:warn`, `level:info`,
  `level:critical` — filters by the same classification `logLineClass`
  uses; text after the prefix still substring-matches
  (`level:error upload` → error lines containing "upload").
- Matched text highlighted via segmented spans (no v-html — no XSS
  surface on arbitrary log text).
- Statusbar reports "N of M lines match" while filtering; empty-match
  state tells the user to widen the tail (the search is over the
  loaded tail — 100/300/1000 lines — not the whole file).
- Esc in the input or the × button clears.

## Implementation Results

- `.logs-files-card` gained real chrome — padding 12px, subtle bg,
  border, radius — plus a `> h2` rule (flex + gap + small caps
  styling). Heading/folder icon now sit 13px clear of the card edge;
  was 0/0 (clipped look).
- Search row between toolbar and viewer: magnifier icon + input +
  inline match count + × clear; Esc clears. Filter covers the loaded
  tail; `level:` prefix maps onto `logLineClass` (error includes
  CRITICAL — same as the row coloring).
- Highlighting via segment spans (no v-html). `.log-hit` accent tint.
- Live: "plugin" → 139/300 + 139 hit spans; `level:error` → 3/300,
  all .log-error; no-match state guides to widen tail. Statusbar
  switches to "N of M lines match".
- 390px: zero horizontal overflow; search 300px, card 352px.
- `vue-tsc` clean, property6 green, `dist` rebuilt.
- Refs: `design-log/refs/logs-full-after-wide-*.png`.
