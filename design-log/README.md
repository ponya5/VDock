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
| [DL-001](DL-001-unified-background.md) | Unified background setting | Planned |
| [DL-002](DL-002-integrations-config.md) | Integrations configuration surface | Planned |
| [DL-003](DL-003-screensaver.md) | Screensaver rework | Planned |
| [DL-004](DL-004-ide-agent-control.md) | IDE & AI agent control | Planned |

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
