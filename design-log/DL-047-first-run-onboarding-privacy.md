# DL-047 — First-Run Onboarding, Profiles-First Tour & Privacy Sanitization

## Background

Four-part request before going public:

1. First launch must track tutorial completion as a **boolean** — true once
   the user finishes/skips, suppressing auto-replay on later launches.
2. A new user's default profile must ship out-of-the-box scenes: **Media,
   Claude Code, Cursor, generic Websites**.
3. Remove personal/region-specific content from the public app — personal
   website, LinkedIn, personal email, Ko-fi, local profile files, and the
   Israeli news presets — nothing personal ships.
4. The first-run tour must **start on the Profiles screen**, guide the user
   to create/load their first profile, then continue on the dashboard.

## Problem

- Tour completion was a localStorage string (`vdock_tutorial_done`) —
  per-browser, cleared with cache, not part of the settings model.
- Default profile seeded `Home` + `AI Assistant` + `Tools` — not the
  requested scene set, and no website scene.
- `newsPresets` shipped personal-region Israeli sites; About linked the
  author's personal site/LinkedIn/email/Ko-fi; README carried a personal
  creator section; local `data/profiles/` held private profiles.
- The tour overlay swallowed all clicks (`position:fixed; inset:0` with no
  `pointer-events`), so a step that asks the user to tap a page element
  was impossible — and `click.self` dismissed the tour.

## Design

- **`tutorialCompleted: boolean`** added to `PersistedUserSettings` —
  defaults, interface, ref, payload builder, `applySettingsObject`,
  `loadSettings` defaults, watch list, and the backend
  `ALLOWED_USER_SETTING_KEYS` whitelist. Persisted to localStorage +
  `user_settings.json` via the existing sync path.
- Legacy `vdock_tutorial_done === '1'` migrates to the boolean on first
  read so existing installs don't get re-toured. `finish()` still writes
  the legacy key as a fallback marker.
- **Default profile** now seeds 4 scenes: Media (renamed `createDefaultScene`
  output — same media buttons), Claude Code (`claude_*` actions from the
  dev-claude-code template), Cursor (`cursor_*` actions from dev-cursor-ai),
  Websites (YouTube/Google/GitHub/Gmail/Reddit/Stack Overflow/Wikipedia/
  Discord — all generic `url` actions, no keys).
- **Tour step model** gained `advanceOnPath` — when the app lands on that
  path the step auto-advances. The Profiles step (`route:'/profiles'`,
  target `.profiles-grid`) completes itself when the user loads/creates a
  profile and lands on `/`. Welcome step also routes to `/profiles` so
  first run literally begins there.
- **Click-through overlay**: `.tour-overlay`/`.tour-dim` get
  `pointer-events:none`; only `.tour-bubble` keeps `pointer-events:auto`.
  `@click.self=finish` removed — backdrop clicks now reach the page
  (required by the interactive profile step).
- **Sanitization**: news presets → BBC/Reuters/AP/ESPN/Sky Sports/
  TechCrunch/The Verge/Hacker News/Ars Technica/WIRED; About links →
  repo GitHub + Issues; Ko-fi card → "Star on GitHub"; personal email →
  GitHub issues; package.json authors → "VDock Contributors"; copyright →
  contributors line; README creator section → Community section;
  SECURITY.md contact → advisory/issues; local profiles moved to
  `data/backups/` (dir already gitignored; profile JSONs are ignored too).

## Implementation Plan

- [x] Settings-backed `tutorialCompleted` boolean end-to-end
- [x] Default profile: Media + Claude Code + Cursor + Websites
- [x] Profiles-first tour with `advanceOnPath` continuation
- [x] Click-through tour overlay
- [x] Personal/region content sanitization + profile archive
- [x] Verify: tests, typecheck, build, live 1024×600 walkthrough

## Trade-offs

- Boolean lives in user settings (per-install, server-backed) rather than
  per-profile — tutorial completion is an app-level state, and one flag is
  what the request asked for.
- Removed `@click.self` tour dismissal — a stray tap ending the tour was a
  footgun; Skip is the explicit exit. Required anyway for click-through.
- Personal identity removed from app UI/README; the GitHub repo URL stays
  (it is the project's public home — unavoidable and appropriate).

## Verification Criteria

- Fresh launch: tour starts on `/profiles`, welcome shows, Next spotlights
  the profile grid, loading/creating a profile auto-advances to dashboard
  steps, Done persists `tutorialCompleted: true` locally + server-side,
  reload does not replay.
- `createDefaultProfile()` produces the four scenes; all buttons have
  actions inside the grid; no personal URLs anywhere in tracked files.
- Suites green; no overflow at 1024×600.

## Implementation Results

- **Boolean**: `tutorialCompleted` wired through defaults → interface →
  ref → `buildSettingsPayload` → `applySettingsObject` → `loadSettings` →
  return → watch list → backend `ALLOWED_USER_SETTING_KEYS`. Verified live:
  Done → `vdock_settings.tutorialCompleted=true` + `user_settings.json`
  `true`; reload → no tour.
- **Watch-list gap found**: `appScanningEnabled`/`agentAlertsEnabled` were
  settable but never persisted (not in the settings watch array — toggles
  reverted on reload, and they weren't allowlisted server-side either).
  All three keys added to both.
- **Profiles-first flow verified live at 1024×600** (fresh origin
  `127.0.0.1:4777`): load → auto-`/profiles` → welcome → Next → grid
  spotlight → click `▶` (passes through overlay) → lands `/` →
  `advanceOnPath` auto-advances to Scenes → full 13-step walk → Done →
  persisted true → reload clean.
- **Click-through overlay fix**: `.tour-overlay`/`.tour-dim`
  `pointer-events:none`, bubble `auto`; `@click.self=finish` removed.
  Before the fix the profile step's required click was physically
  impossible (overlay intercepted; self-click would have ended the tour).
- **Default profile**: `Media` (renamed from `Home`), `Claude Code`
  (8 buttons: resume, /code-review, /commit, claude.ai, explain, tests,
  fix, continue), `Cursor` (8: composer, chat, inline edit, palette,
  accept, reject, terminal, quick open), `Websites` (8 generic globals).
  Tests updated for new names + action-type allowlist.
- **Privacy sweep**: news presets now generic global sites; About → repo
  GitHub/Issues links + "Star on GitHub"; `ponya81@gmail.com` mailtos
  removed (About contact + UserGuideModal); package authors genericized;
  README creator section → Community; SECURITY.md contact → advisories;
  copyright → contributors; local Daniel/My VDock profiles archived to
  `data/backups/profiles-personal-2026-09-21/`; `dashboard.png` help shot
  regenerated with the new scenes.
- **Environment noise during verification**: a stale `:5000` backend plus
  old dev tabs formed a socket `user_settings_changed` mesh that kept
  force-feeding `tutorialCompleted:true` to the test client (the relay
  bypasses the whitelist). Killed the stale backend; isolated the test on
  a fresh origin. Not a code bug — but worth noting the relay accepts raw
  settings dicts from any connected client.
- Tests: 231/231 frontend, 757/757 backend, `vue-tsc` clean, `vite build`
  green.
