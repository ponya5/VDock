# Project Rules

## Design log — required for every implementation

Every non-trivial implementation, feature, bug fix, or design change MUST be documented in `design-log/`. Conventions are defined in `design-log/README.md`.

- **New work:** create `design-log/DL-<NNN>-<short-slug>.md` (next sequential number) BEFORE writing code, with a `## Implementation Results` section appended once the work is done and verified.
- **Follow-ups:** changes to an already-logged feature append a follow-up/implementation-results section to that entry instead of creating a new file.
- Sections above `## Implementation Results` are frozen once implementation begins — corrections and deviations go in the results section.
- Update the index table in `design-log/README.md` when adding a new entry.
- Trivial changes (typo fixes, one-line tweaks) are exempt; when in doubt, log it.

## Serving the frontend to the 7" panel

The Flask backend serves `frontend/dist` (see `app.py` `frontend_index`/`dist_root`). The physical touch panel loads the **built bundle**, not the Vite dev server — after frontend changes, run `cd frontend && npm run build` or the device keeps showing the stale build. The dev server on :4444 is for live verification (Playwright) only.


## Definition of done — verify the outcome, not the code path

VDock is Windows-first and ships on Windows and macOS; mobile (phone/tablet over Wi-Fi) is the main surface. A change is done only when:

1. **The user-visible effect was observed**, not just a success response. Read the state back after acting (volume level, which window is in front, the agent session's screen text, the page on a phone viewport). An action that cannot confirm its effect must not report success — say what it could not do.
2. **It was tested from the real entry point**: the deck opened from another device via the LAN IP (phone/tablet viewport, Playwright), the backend started the way users start it (`~/Applications/VDock.app` / Start menu / packaged app — macOS permissions are charged to whichever app started it), and the button pressed through `POST /api/actions/execute` or the UI, never only the helper function.
3. **Windows is not affected** by a macOS fix (and vice versa): platform code stays behind its OS branch, shared changes are called out, and the backend suite passes. CI runs it on Windows, macOS and Linux — a skipped Win32 test locally is not a pass.
4. **Agent actions are tested against a throwaway session** (pin it via `POST /api/agent-sessions/target`), never the session doing the work, and destructive keys only with a reason.
5. **The report lists what was not verified** (no hardware, no Windows machine, needs a user permission) instead of implying it works.
