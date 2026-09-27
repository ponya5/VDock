# DL-078: Regroup the default Media scene — volume vs. transport controls

## Background

The factory Media scene interleaved volume and playback controls across
two rows with no grouping logic: row 0 held Volume Up/Down/Mute, row 1
held Play/Pause, Previous, Next, Stop in that order — so Play/Pause sat
disconnected from Previous/Next (which is how the user's own live profile,
carrying an extra hand-added Volume Slider button, had also drifted:
Play/Pause alone on row 2 while Previous/Next/Stop sat on row 1).

The user asked explicitly for a **layout-only** change — "don't change the
code!! it's not a feature! just arrange the buttons better" — so this is
purely `position` field edits, no new logic, no new buttons, no action
changes.

## Design

Two functional groups, one row each:

- **Row 0 — volume:** Mute, Volume Down, Volume Up (Volume Slider too, for
  profiles that have one) — matches how a physical remote or OS volume
  flyout groups mute/down/up together.
- **Row 1 — transport:** Previous → Play/Pause → Next → Stop, the same
  left-to-right order as a real media remote's ⏮ ⏯ ⏭ ⏹ row.

Applied in two places, both pure data (button `position` values only):

- `frontend/src/utils/defaultProfile.ts`'s `createDefaultScene()` — the
  single source of truth for the factory Media scene, reused by first-run
  bootstrap, migration, and "Reset to Default." No buttons added, removed,
  or changed — only `position` fields.
- The user's own already-created profile
  (`backend/data/profiles/0027a602-99fa-4a3f-882d-2f32e6bccc9a.json`) so
  the fix is visible immediately without needing a profile reset, which
  would have discarded their manually-added Volume Slider button.

## Implementation Results

Moved 2 buttons in the template (`Mute`→col 0, `Volume Up`→col 2, both row
0 — Volume Down already sat at col 1) and 2 buttons in the live profile
(`Previous`→row 1 col 0, `Play/Pause`→row 1 col 1; Next/Stop/Volume Slider
were already correctly placed). Verified visually via a live browser
screenshot against the running dev server — Mute/Volume Down/Volume
Up/Volume Slider now read left-to-right on row 0, Previous/Play-Pause/
Next/Stop on row 1.

### Verification

- Frontend: 59 files / 254 tests green; `vue-tsc --noEmit` clean.
- Confirmed live in a browser against the running dev server (screenshot
  taken) — not just template inspection.
