# DL-079: De-densify the README — tables to prose/bullets, general trim

## Background

The README had accumulated a table in nearly every section (Settings,
Screensaver widgets, Quick start installers, Requirements, Features/deck,
Integrations, Look and feel, Troubleshooting, plus the genuinely-tabular
competitor comparison) on top of already-detailed prose under each heading.
The user's feedback was direct: too dense, too long, too many tables.

## Design

Docs-only change, no code:

- Converted every table that was really a list of "label → one-line
  description" pairs into a compact bullet list (`- **Label** — detail`)
  or an inline bold-lead sentence — a table's header row and border
  overhead cost more vertical space than the content did for anything
  under ~6 rows of short text.
- Kept the **Why VDock** comparison table as an actual table (4 competitors
  × 6 criteria is genuinely tabular data a table communicates faster than
  prose would) but trimmed it from 7 rows to 6, dropping the "Account
  required" row as the least load-bearing one.
- Collapsed the "Real use cases" six `###` subheadings into bold-lead
  inline paragraphs (still six distinct, skimmable items, just without a
  heading each) and moved the touchscreen-second-monitor tip (DL-077) into
  a `<details>` disclosure so it doesn't cost vertical space for readers
  who don't need it.
- Trimmed prose throughout — cut restating-the-obvious sentences, merged
  short adjacent sentences, removed a few "Two details that make this
  actually usable"-style sub-explanations down to inline clauses.
- Left every image, every anchor link, and the Contents list untouched —
  this is a formatting/length pass, not a content or navigation change.
  Fixed one incidentally-broken link along the way: the Platform badge
  pointed at `#requirements`, a heading that never existed (it was inside
  a `<details>` summary, which markdown doesn't anchor) — repointed to
  `#quick-start`.

## Implementation Results

517 lines → 234 lines (down 55%), 227 lines of table/prose removed against
72 lines of replacement bullets/prose added. No tables removed entirely
except by conversion — the Why VDock comparison and the two image-grid
`<table>`s (mobile screenshots, key-design screenshots) are the only
`<table>` elements left, both genuinely needing tabular/grid layout.

### Verification

- Read through the full rewritten file top to bottom for broken anchors,
  dangling references, and orphaned links — all resolve to real headings.
- Not run through a markdown linter (none configured in this repo); this
  is a prose/structure edit with no build step to verify against.
