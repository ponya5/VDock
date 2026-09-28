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
| [DL-001](DL-001-unified-background.md) | Unified background setting | Implemented — shipped in product; featured in README screenshots/video |
| [DL-002](DL-002-integrations-config.md) | Integrations configuration surface | Implemented — superseded by the shipped Integrations settings surface |
| [DL-003](DL-003-screensaver.md) | Screensaver rework | Implemented — shipped in product; featured in README screenshots/video |
| [DL-004](DL-004-ide-agent-control.md) | IDE & AI agent control | Implemented — session-host window resolution + all IDE packs ship (9 plugins load at boot); per-IDE hook installation tracked in DL-066 |
| [DL-005](DL-005-screensaver-weather-size.md) | Screensaver weather widget size | Complete |
| [DL-006](DL-006-dev-first-app-list.md) | Dev-first running-apps list + smart filter | Complete |
| [DL-007](DL-007-port-configuration.md) | Port selection in Server settings | Complete |
| [DL-008](DL-008-reactbits-backgrounds.md) | React Bits background import + scrollable picker | Implemented — shipped; WebGPU backgrounds degrade gracefully via `reportFailure` by design |
| [DL-009](DL-009-small-panel-touch-chrome.md) | Touch-mode scaling for header & action sidebars | Implemented — shipped; compact-display auto-fullscreen in electron main.js covers the small-panel case |
| [DL-010](DL-010-app-scene-backgrounds.md) | Per-app default scene backgrounds | Implemented — shipped in product |
| [DL-011](DL-011-animated-avatars.md) | Animated GIF avatars | Implemented — shipped in product |
| [DL-012](DL-012-edit-mode-wiggle.md) | Edit-mode wiggle opt-in | Implemented — default off, tests green |
| [DL-013](DL-013-screensaver-layout.md) | Screensaver layout, background & editor | Implemented — side-by-side default, drag/resize editor, own background; shipped |
| [DL-052](DL-052-mergeable-slider-buttons.md) | Mergeable slider buttons + Sliders action category | Implemented — seam merge chips, Ctrl+Z/Y undo wiring, Sliders catalog category; wheel scroll + merge-failure toast + savebar fix + comtypes/3.13 volume fix + quick-jump preset chips; follow-up: slider dispatch failures now surface an "Action Failed"-style toast instead of failing silently |
| [DL-053](DL-053-settings-accordion-animation.md) | Settings accordion expand/collapse animation | Implemented — reusable Collapse component, Templates + widget cards + picker |
| [DL-054](DL-054-settings-sidebar-redesign.md) | Settings shell redesign: sidebar nav, row-based panels, preview rail | Implemented — mockup ported, all pages re-skinned, 231 tests green |
| [DL-055](DL-055-edit-mode-touch-drag.md) | Edit-mode touch drag + atomic button swap | Implemented — grab via hold-or-move, swapButtons store op, slider/double-tap guards |
| [DL-056](DL-056-lan-device-connection.md) | LAN device connection fix (QR → black screen) | Implemented — config.json toggles applied at boot, socket URL derives from page host, socket CORS origins cover backend/dev/LAN |
| [DL-057](DL-057-mobile-deck-fit-connect-page.md) | Mobile deck fit + dedicated Connect page | Implemented — square-cell compact grid on narrow/tall viewports, app scanning off by default, Connect-a-device nav page with auto-QR; follow-up: fit-to-screen sizing now forced on every mobile viewport (not just the aspect-ratio heuristic), fixing oversized/truncated buttons on landscape phones; follow-up 2: real-phones photo added as a README hero image and a thumbnail beside the Connect page's QR code |
| [DL-058](DL-058-backend-crash-com-apartment.md) | Backend silent crash — COM apartment violation + 500 toast spam | Implemented — dedicated COM thread for Core Audio, 5xx toast throttle, 400 guard |
| [DL-059](DL-059-settings-polish-slider-flex-mobile-fit.md) | Settings previews, smaller design picker, slider flex, mobile fit | Implemented — mock-dash CSS, real component bg preview, app_volume slider target, expand/shrink chips, fit-to-screen grid + short-viewport header auto-hide |
| [DL-060](DL-060-landscape-only-mobile.md) | Landscape-only mobile gate | Implemented — portrait phones get a rotate-prompt overlay on the dashboard; tablets/desktops unaffected |
| [DL-061](DL-061-mobile-control-surface.md) | Mobile = control surface only | Implemented — edit mode blocked, config buttons hidden, long-press edit gestures gated on phone viewports; follow-up: server-persisted `activeProfileId` so a phone's first connection loads the desktop's actual active profile instead of guessing, and the first-run tutorial (which force-navigated to `/profiles`) no longer auto-starts on mobile at all |
| [DL-062](DL-062-mobile-layout-fit.md) | Mobile dashboard layout fit | Implemented — docked sidebar hidden, header overlay + slim, reveal pill off the buttons, slim footer |
| [DL-063](DL-063-mobile-dedicated-surfaces.md) | Dedicated mobile chrome + screensaver | Implemented — MobileDeckChrome (scene rail, page steppers, ⋯ menu), screensaver = clock + world clock only |
| [DL-064](DL-064-agent-state-aware-actions.md) | Agent state-aware actions | Implemented — hook-driven agent state (ready/working/permission), state-aware action bar, scene buttons type into the live CLI, Submit |
| [DL-065](DL-065-mobile-agent-console.md) | Mobile agent console | Implemented — portrait phone console on agent scenes: state card, last prompt/reply from hooks, state actions, shortcut chips. Follow-up 1: fixed a starvation bug where a failed profile fetch (scanning off by default) permanently hid the console/action bar on mobile — retry + eager unconditional load. Follow-up 2: removed the free-text composer entirely (actions/shortcuts only) and shrank the oversized empty-state card. Follow-up 3: dropped the empty-state card entirely and turned the shortcut row into a wrapping grid of bigger tiles so every shortcut is visible without scrolling |
| [DL-066](DL-066-ide-agent-parity.md) | IDE agent parity | In progress — Cursor prompt/follow-up/submit commands done and unit-verified (no live injection, by design); Cursor scene rebuilt to match Claude's 2x4 layout; existing profiles auto-upgrade an untouched legacy Cursor scene on load (customised scenes keep the explicit "Reset to Default" opt-in); VS Code Copilot, Visual Studio and Cursor hook installation pending |
| [DL-067](DL-067-mobile-fullscreen-prominence.md) | Mobile fullscreen — promoted button + best-effort auto-trigger | Implemented — Fullscreen moved out of the `⋮` menu into an always-visible, pulsing chrome-bar button; best-effort auto-attempt on mount; 6-second "Tap for fullscreen" callout bubble for a phone's first visit; follow-up 2 fixed the button silently no-oping on iPhone Safari (no Fullscreen API there at all) by detecting that and swapping in an "Add to Home Screen" callout instead; not yet live-verified on a physical phone |
| [DL-068](DL-068-tutorial-persistence-launch-freshness.md) | Tutorial re-showing every launch + launcher frontend freshness | Implemented — settings-load race fixed (tour now waits for the real `tutorialCompleted` value instead of racing App.vue's fetch), launcher gained `ensure_fresh_frontend()` to detect/restart duplicate dev servers; not yet live-verified end to end |
| [DL-069](DL-069-lan-dev-server-staleness.md) | Mobile/LAN devices frozen on stale code (dev mode) | Implemented — Connect-a-device QR now targets the live Vite dev server (LAN-gated `host`, `strictPort`) instead of the one-time-built backend dist/ in dev; `dist/` rebuilt; found 5 orphaned dev-server processes on the machine the agent cannot terminate — user must close them once via Task Manager |
| [DL-070](DL-070-tray-menu-trim.md) | Tray menu trim | Implemented — Show/Settings/Exit only; Settings routes main window to `/settings` via `navigate-to` IPC; broken Fix Firewall + legacy settings modal deleted; tray verified live in DL-073's packaged-app launch |
| [DL-071](DL-071-agent-session-targeting.md) | Agent session targeting (picker + pin) | Implemented — `prefer_pid` + `list_session_hosts`, pin registry, `/api/agent-sessions` + `/target` routes, action-bar picker; matcher hardened vs `chrome-native-host.exe` and `detected-profiles` aligned to `iter_session_pids` (fixed a live false-positive); follow-up: mobile session chip strip in the agent console (renders only with 2+ sessions); 864 backend + 251 frontend tests green; follow-up 8: picker becomes a centered full-width sheet on short/touch viewports with --touch-multiplier-scaled rows for 7" panels |

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
| [DL-072](DL-072-release-readiness-audit.md) | Release-readiness audit | Implemented — cross-platform spawn fix in electron main.js, NSIS/PowerShell installer fixes (missing install.bat, launcher path, user-writable install dir), tracked junk removed, secrets scan clean; electron-builder packaging fixed in DL-073 |
| [DL-073](DL-073-self-contained-installer.md) | Self-contained installer | Implemented — PyInstaller-frozen backend (`vdock-backend.spec`) bundled via electron-builder `extraResources`; Electron spawns the exe with `DATA_DIR` → userData; build-backend/build-release scripts; fixed pre-existing `/api/assets` 500 + packaged-mode CSP blocking fonts/widget APIs; Setup + Portable exes built & smoke-tested |
| [DL-074](DL-074-tour-rewrite.md) | Guided tour realignment + Help guide | Implemented — 9-step routed tour (profiles → dashboard → settings → back to dashboard), `optional` auto-skip for conditional UI, stale selectors fixed, mobile-chrome fallbacks; Help guide gained Troubleshooting tab + current-feature coverage; verified live in Playwright on both tour paths |
| [DL-075](DL-075-cross-platform-release-pipeline.md) | Cross-platform release pipeline | Implemented — native-runner release workflow (win/mac/linux freeze + per-OS backend smoke test + electron-builder), Linux AppImage+deb targets, PNG icon fix for POSIX Tray/window, real 1024px keycap-grid icon (ico/png/favicons — favicons were silently 404ing), secret-driven signing wired + RELEASING.md cert guide |
| [DL-076](DL-076-toast-default-errors-only.md) | Default toast level to errors-only | Implemented — new installs now default `toastLevel` to `'errors-only'` instead of `'all'`; existing users' saved preference untouched |
| [DL-077](DL-077-touchscreen-second-monitor-tip.md) | Touch-to-wrong-monitor doc tip | Implemented — README "Using a touchscreen as a second monitor" subsection + Troubleshooting row, matching in-app Help & Guide troubleshooting entry, documenting Windows' built-in `multidigimon -touch` fix |
| [DL-078](DL-078-media-scene-layout-regroup.md) | Media scene layout regroup | Implemented — factory Media scene (`defaultProfile.ts`) and the live default profile now group volume (Mute/Down/Up/Slider) on row 0 and transport (Previous/Play-Pause/Next/Stop) on row 1; position-only change, no new buttons or logic |
| [DL-079](DL-079-factory-seed-backfill-agent-bar-resolution.md) | Factory-scene backfill + IDE scene→agent-bar resolution | Implemented — `setProfile` one-shot-backfills missing factory scenes (marker persisted, name-deduped); scene→profile resolution aliases plugin/template ids (`claude`→`claude-code`), falls through unknown `appId`s, and matches scene names to profiles — so the agent status bar shows on manually-added IDE scenes |
| [DL-080](DL-080-agent-waiting-edge-glow.md) | Edge-glow + bar highlight for waiting agent sessions | Implemented — `AgentWaitingGlow` breathes a green viewport edge-glow while an IDE scene's agent sits `ready`; the bar's session chip/rows flag the idle session; `agentWaitingGlowEnabled` setting (default on) in Agent attention alerts; follow-ups: waiting scene-pill ring on desktop + mobile rails (`sceneAgentIsWaiting`), chip `waiting` tag + nudge dot, mobile console session rings; follow-up #2: whole-dashboard double-blink flash (any scene's idle agent), `agentWaitingGlowStyle` select (flash/pulse/comet), ts-keyed Snooze chip that quiets all surfaces until the next waiting episode |
| [DL-081](DL-081-readme-declutter.md) | README de-densify | Implemented — 517 → 234 lines; most per-section tables converted to bullets/prose, Why VDock comparison table kept and trimmed, no content or anchor links removed |
| [DL-082](DL-082-scene-swipe-dissolve.md) | Swipe left/right scene switching + directional dissolve | Implemented — single `.main-content` `useSwipe` maps left/right (and keeps up/down) to scenes on desktop + mobile incl. the agent console; active rail segment dissolves live with the drag, committed switch plays a directional mask-wipe cross-dissolve on the keyed scene pane + sweep keyframes on the segments; page flips lose their swipe (steppers remain) |
| [DL-083](DL-083-safari-iphone-compat.md) | Safari/iPhone compatibility pass — viewport-fit cover, webkit mask/user-select/backdrop pairs, 100dvh, touch-action, input zoom, clipboard fallback | Implemented |
| [DL-084](DL-084-app-path-overrides.md) | Per-app executable path overrides (template gear + App launch paths panel); find_binary/open_app/keymap auto-launch honor them | Implemented |
| [DL-085](DL-085-antigravity-ide-pack.md) | Antigravity IDE pack + AI Coding template | Implemented — `antigravity` keymap/pack/profile (14 agent+editor commands), `antigravity.exe` context name, `antigravity` agent-state source; template card moved from AI Platforms to AI Coding wired to the new actions; added to App launch paths; probe finds the real Antigravity.exe |
| [DL-086](DL-086-scene-rail-logos.md) | Scene rail app logos + measured glider | Implemented — scenes show their template app logo (claudecode-color.png etc.) next to the label on desktop + mobile rails; pills 56px/48px; desktop glider now measures the real segment box (fixes partial active highlight) |
| [DL-087](DL-087-settings-topbar-apply.md) | Apply actions in Settings topbar; savebar removed | Implemented — Revert/Save & Apply (Buttons page) and Apply (other tabs) moved next to "Reset section"; bottom status bar and its CSS removed; dirty draft keeps an inline "Draft not applied" hint |
| [DL-088](DL-088-guide-tab.md) | User Guide as a Settings tab + content refresh | Implemented — modal converted to a full-height panel on a new Guide tab between Logs and About; sidebar collapses to a horizontal bar on mobile; copy updated for scene swipe, waiting glow/snooze, executable-path gear, AI Coding templates |
| [DL-089](DL-089-feature-request-and-credits.md) | "Request a feature" email flow + settings credit footer | Implemented — POST /api/feedback (≤4k msg, ≤2MB image, throttled, stored locally, FormSubmit relay, address server-side only); About gains the button + version badge next to the title; nav rail shows "Created by Daniel S. · v" + LinkedIn/GitHub/site icons |
| [DL-090](DL-090-server-tab-cleanup.md) | Server sub-nav removed + full settings audit | Implemented — "Startup & navigation"/"Connection" sub-links and chevron removed; every Server control verified live (autostart registry round-trip, launcher auto-close, new-tab settings, host/auth display, port check/save incl. collision + validation errors) |
| [DL-091](DL-091-log-viewer-search.md) | Log files card spacing + smart tail search | Implemented — files card gets padding/chrome so the header icon isn't clipped; search row filters the loaded tail (substring + `level:` prefix), highlights matches via spans, statusbar shows match count |
| [DL-092](DL-092-generic-agent-hooks.md) | Generic agent hooks + install dropdown | Implemented — Antigravity hook target (`~/.gemini/config/hooks.json`, `--event`-pinned commands, named `vdock-agent-state` entry); hook-status?agent=all; Integrations now has one dropdown listing all agents' install states instead of per-agent rows; copy generalized |
| [DL-093](DL-093-about-feature-list.md) | About "What's in it" feature list | Implemented — boxed 3-col `.feature` grid replaced by unboxed two-column hairline-separated list rows (icon + stacked label/desc); verified live at desktop/1024×600/700px |
| [DL-094](DL-094-settings-dock-footer.md) | Settings dock footer bar | Implemented — sidebar footer (Reload/Back + credit + social links) moved to a full-width sticky dock bar spanning under nav + content; sidebar is pure nav; verified at 1400×800/1024×600/700px |
| [DL-095](DL-095-buttons-topbar-polish.md) | Settings topbar polish + panel heads | Implemented — draft-hint → amber chip pill, hairline divider between Reset and the draft-lifecycle group, panel-head/preview-head unified at --fs-sm/--text; follow-up: bottom warn note removed → once-per-dirty-episode toast, new `Notification.important` flag pierces errors-only |
| [DL-096](DL-096-market-widget-left-align.md) | Screensaver market widget left alignment | Implemented — `.ss-market`/`.ss-market-row` flex-end → flex-start; quote rows now read `BIT $82,834` / `ETH $2,642.45` left-to-right under the MARKETS head; verified in the live layout editor |
| [DL-097](DL-097-action-sidebar-polish-footer.md) | Action sidebar polish + conditional animated footer | Implemented — reorder buttons removed (row itself toggles), icon-chip + count + rotating-chevron rows with per-category accents, `Collapse`-wrapped actions keep drag bindings; footer mounts only when it has content and slides up/down off the viewport edge |
| [DL-098](DL-098-screensaver-clock-toggle-defaults.md) | Screensaver clock toggle + slimmer new-user widget defaults | Implemented — clock toggleable via its own `screensaverClockEnabled` flag (existing users keep the clock; widget-array membership couldn't distinguish off vs legacy), fresh installs get Clock+Weather+News+Markets |
| [DL-099](DL-099-uninstall-cleanup.md) | Uninstall cleanup | Implemented — uninstall.bat/.sh for source installs (process kill by root path/ports, autostart + desktop launcher removal), NSIS `customUnInstall` clears the Run key, README "Uninstall" per-OS docs |
| [DL-100](DL-100-out-of-box-scene-set.md) | Out-of-box scene set = Media + Claude Code | Implemented — FACTORY_SEED_SCENES trimmed to claude-code, Websites builder dropped, one-time untouched-legacy Home/Claude scene prune gated on `factorySeedsApplied` absence; verified against the real profile |
| [DL-101](DL-101-screensaver-legacy-defaults.md) | Screensaver untouched-legacy defaults migration | Implemented — `applySettingsFromRemote` swaps to the DL-098 widget set only when the stored file provably predates the flag (no `screensaverClockEnabled` + legacy five-widget list + default layout); one-shot by construction |
| [DL-102](DL-102-header-reveal-fab.md) | Header reveal → independent floating button | Implemented — docked footer pill removed, compact floating FAB bottom-right (lifts above footer when mounted), footer strip reclaimed when header is hidden |
| [DL-103](DL-103-about-actions-tour-copy.md) | About action row trim + tour copy | Implemented — Help&guide + GitHub buttons removed (dupes of Guide tab / credit links), Launch tutorial leftmost + primary, tour calls out left/right scene swipe |
| [DL-104](DL-104-header-overlay-no-reflow.md) | Header overlay — no grid reflow + window-glyph reveal | Implemented — header wrapper goes absolute over the deck (grid pinned, same model as the mobile header), reveal button is now a mini window-with-header glyph (accent band + caret, 56×46) |
| [DL-105](DL-105-waiting-alerts-require-prompt.md) | Waiting alerts only after first prompt | Implemented — per-session sticky `prompted` flag (hook flags every event except SessionStart/Notification); waiting chip/glow/ring, picker rows + idle-notification alert suppressed for never-prompted sessions; permission unaffected; verified live end-to-end |
| [DL-106](DL-106-factory-background-bubbles.md) | Out-of-box dashboard background = Floating Bubbles | Implemented — `FACTORY_BACKGROUND_ID='bubble-float'` seeds fresh installs + Appearance reset; `'default'` sentinel untouched so existing users keep the gradient |
| [DL-107](DL-107-scene-pill-labels.md) | Scene-pill labels always readable | Implemented — segments no longer flex-shrink (rail scrolls instead of truncating), label cap 112→200px, ≤1100px headers get slimmer pills |
| [DL-108](DL-108-launcher-electron-run-as-node.md) | Launcher scrubs ELECTRON_RUN_AS_NODE | Implemented — ambient var from Electron-based tool shells made `electron .` run as plain Node and crash main.js at startup; env is sanitized before spawn |
| [DL-109](DL-109-background-component-failures.md) | Fix hard-failing component backgrounds + honest preview failure state | Implemented — MoltenMetal GLSL `int*float` cast, ShapeWaves vgpu `kind:'2d'`, failed previews show a labelled "Preview unavailable" instead of a bare checkerboard; coverage pinned by background-health.test.ts; verified live via BroadcastChannel sweep |
| [DL-110](DL-110-edit-mode-drag-ghost-leaks.md) | Edit-mode drag ghosts leak + reveal FAB overlaps edit footer | Implemented — touch-ghost path gated to touch/pen pointers (mouse keeps native HTML5 drag), ghost cleanup now covers touchcancel/pointercancel/blur/unmount in both drag systems, reveal FAB hidden while editing; verified live with synthetic pointer/touch input |
