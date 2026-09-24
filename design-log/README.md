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
| [DL-003](DL-003-screensaver.md) | Screensaver rework | In progress — Tasks 1–5 done (tappable headlines, touch-mode auto-scale); Task 6 manual verification pending |
| [DL-004](DL-004-ide-agent-control.md) | IDE & AI agent control | In progress — session-host window resolution + VS Code/JetBrains/Visual Studio/Devin packs shipped; Phase 3 hooks & context scene pending |
| [DL-005](DL-005-screensaver-weather-size.md) | Screensaver weather widget size | Complete |
| [DL-006](DL-006-dev-first-app-list.md) | Dev-first running-apps list + smart filter | Complete |
| [DL-007](DL-007-port-configuration.md) | Port selection in Server settings | Complete |
| [DL-008](DL-008-reactbits-backgrounds.md) | React Bits background import + scrollable picker | In progress — WebGPU pair needs hardware verification |
| [DL-009](DL-009-small-panel-touch-chrome.md) | Touch-mode scaling for header & action sidebars | In progress — EditSidebar coverage added; manual 800×480 verification pending |
| [DL-010](DL-010-app-scene-backgrounds.md) | Per-app default scene backgrounds | In progress |
| [DL-011](DL-011-animated-avatars.md) | Animated GIF avatars | Implemented — tests green, manual upload check pending |
| [DL-012](DL-012-edit-mode-wiggle.md) | Edit-mode wiggle opt-in | Implemented — default off, tests green |
| [DL-013](DL-013-screensaver-layout.md) | Screensaver layout, background & editor | Implemented — side-by-side default, drag/resize editor, own background; backend restart needed for server sync |
| [DL-052](DL-052-mergeable-slider-buttons.md) | Mergeable slider buttons + Sliders action category | Implemented — seam merge chips, Ctrl+Z/Y undo wiring, Sliders catalog category |
| [DL-053](DL-053-settings-accordion-animation.md) | Settings accordion expand/collapse animation | Implemented — reusable Collapse component, Templates + widget cards + picker |
| [DL-054](DL-054-settings-sidebar-redesign.md) | Settings shell redesign: sidebar nav, row-based panels, preview rail | Implemented — mockup ported, all pages re-skinned, 231 tests green |
| [DL-055](DL-055-edit-mode-touch-drag.md) | Edit-mode touch drag + atomic button swap | Implemented — grab via hold-or-move, swapButtons store op, slider/double-tap guards |
| [DL-056](DL-056-lan-device-connection.md) | LAN device connection fix (QR → black screen) | Implemented — config.json toggles applied at boot, socket URL derives from page host, socket CORS origins cover backend/dev/LAN |
| [DL-057](DL-057-mobile-deck-fit-connect-page.md) | Mobile deck fit + dedicated Connect page | Implemented — square-cell compact grid on narrow/tall viewports, app scanning off by default, Connect-a-device nav page with auto-QR |
| [DL-058](DL-058-backend-crash-com-apartment.md) | Backend silent crash — COM apartment violation + 500 toast spam | Implemented — dedicated COM thread for Core Audio, 5xx toast throttle, 400 guard |
| [DL-059](DL-059-settings-polish-slider-flex-mobile-fit.md) | Settings previews, smaller design picker, slider flex, mobile fit | Implemented — mock-dash CSS, real component bg preview, app_volume slider target, expand/shrink chips, fit-to-screen grid + short-viewport header auto-hide |
| [DL-060](DL-060-landscape-only-mobile.md) | Landscape-only mobile gate | Implemented — portrait phones get a rotate-prompt overlay on the dashboard; tablets/desktops unaffected |
| [DL-061](DL-061-mobile-control-surface.md) | Mobile = control surface only | Implemented — edit mode blocked, config buttons hidden, long-press edit gestures gated on phone viewports |
| [DL-062](DL-062-mobile-layout-fit.md) | Mobile dashboard layout fit | Implemented — docked sidebar hidden, header overlay + slim, reveal pill off the buttons, slim footer |
| [DL-063](DL-063-mobile-dedicated-surfaces.md) | Dedicated mobile chrome + screensaver | Implemented — MobileDeckChrome (scene rail, page steppers, ⋯ menu), screensaver = clock + world clock only |
| [DL-064](DL-064-agent-state-aware-actions.md) | Agent state-aware actions | Implemented — hook-driven agent state (ready/working/permission), state-aware action bar, scene buttons type into the live CLI, Submit |

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
