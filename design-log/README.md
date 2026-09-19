# Design Log

One entry per non-trivial change, created **before** coding starts and appended
to as work progresses.

Entries are named `DL-<NNN>-<short-slug>.md`. Sections above
`## Implementation Results` are frozen once implementation begins — corrections
go in the results or deviations sections, so the record shows what was actually
believed at decision time rather than a tidied-up version of it.

## Index

| Entry | Feature | Status |
|---|---|---|
| [DL-001](DL-001-unified-background.md) | Unified background setting | In progress — merged to `feat/unified-background`; manual browser verification outstanding |
| [DL-002](DL-002-integrations-config.md) | Integrations configuration surface | Planned |
| [DL-003](DL-003-screensaver.md) | Screensaver rework | In progress — Tasks 1–5 done (news feeds+rotation, market tickers, world-clock cities, widget text size, Test Screensaver); Task 6 manual verification pending |
| [DL-004](DL-004-ide-agent-control.md) | IDE & AI agent control | In progress — session-host window resolution + VS Code/JetBrains/Visual Studio/Devin packs shipped; Phase 3 hooks & context scene pending |
| [DL-005](DL-005-screensaver-weather-size.md) | Screensaver weather widget size | Complete |
| [DL-006](DL-006-dev-first-app-list.md) | Dev-first running-apps list + smart filter | Complete |
| [DL-007](DL-007-port-configuration.md) | Port selection in Server settings | Complete |
| [DL-008](DL-008-reactbits-backgrounds.md) | React Bits background import + scrollable picker | In progress — WebGPU pair needs hardware verification |
| [DL-009](DL-009-small-panel-touch-chrome.md) | Touch-mode scaling for header & action sidebar | Complete |

**Status values:** Planned → In progress → Complete.

## Where the artifacts live

Each entry links to a spec and one or more plans:

- **Specs** — `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`
- **Plans** — `docs/superpowers/plans/YYYY-MM-DD-<topic>.md`

Both directories are gitignored (see `.gitignore:184`, set in commit `b3209d5`,
which stopped tracking internal design docs ahead of the public release), so
those files exist only in the working tree. The design log itself **is**
tracked — it is the durable record. An entry should therefore carry enough
context to stand on its own if the spec and plan files are ever lost.

## Current work

All four entries below were designed together on 2026-09-19 and share a branch:

**Branch:** `upgrade/upgrade--keypad`

**Dependency order:**

```
DL-002 (integrations config) ──┬──> DL-003 (screensaver)
                               └──> DL-004 (IDE control)

DL-001 (background) ──────────── independent
```

DL-002 must land before DL-003 or DL-004 can start, because both take their
credentials and paths from the settings surface it creates.

**Branch note (2026-09-20):** the branches have since been joined —
`upgrade/upgrade--keypad` was merged into `feat/unified-background`
(commit `79eedbf`), which is the tree the running app serves
(`.worktrees/unified-background`). New work lands there and flows back on
the eventual merge into the main line.
