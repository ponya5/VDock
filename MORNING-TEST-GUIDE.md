# Morning test guide — research upgrade (DL-114 → DL-132)

Everything below is committed on `research_upgrade1` (`34acf1e`), built
into `frontend/dist`, and running live on the backend at
`http://127.0.0.1:5000`. **528 frontend + 1104 backend tests pass.**

Fresh start tip: the backend may still be the dev-spawned process. If
anything looks stale, restart it — `cd backend && venv\Scripts\python.exe app.py`.

---

## 1. Guide landing page (new — DL-132)

- **Open it:** Settings → **Guide** (sidebar, now has a ↗ icon) — opens in a
  **new browser window**. Or go straight to `http://127.0.0.1:5000/guide`.
- **What to check:** hero + tagline, **search box** (try `mcp`,
  `screensaver`, `agent scene` — multi-word AND search; `/` focuses it,
  `Esc` clears, `Enter` jumps to the first hit), section chips, 12 feature
  sections with **real screenshots** of your deck, and the same
  Daniel-footer as Settings at the bottom.
- The old in-Settings guide tab is gone — the sidebar item is the doorway.
  Search "guide" in Settings search and it opens the window too.

## 2. Header reveal + countdown pill (DL-130)

- Hide the header (Appearance → Layout, or swipe up). Bigger **Header ⌄**
  chip sits bottom-right — tap it.
- Header slides in with a **countdown pill** (gradient ring, stars, live
  "5s…4s…"). **Tap the pill → "Pinned"** — header stays open until you
  unpin. Unpinned, it hides on schedule.

## 3. Now Playing + Play/Stop (DL-128/129)

- Media scene: **2-cell Now Playing card** (art, title, artist·Spotify,
  progress) — **tap it = play/pause**. Next to it, **Play / Stop** is one
  button that shows what it'll do (stop icon while playing).

## 4. Tour behavior (DL-131)

- Settings → About → **Launch tutorial**. Steps only move when **you**
  press Next/Back/Skip — no auto-advance, even if a step's target is
  hidden (it shows a centered card until the target appears, then snaps
  the spotlight onto it).

## 5. MCP server + integrations (DL-121/127, hardened)

- Settings → **Integrations** → top sub-tabs: Apps & scenes / Agent
  alerts / Triggers / MCP server.
- MCP panel → **Help & test** → **Run self-test** → should print
  `Connected — vdock 2.1.0, 11 tools`.
- Cursor/Claude config snippets are in that modal (copy buttons).

## 6. Cursor launcher + scene (orchestrated-test result)

- Cursor scene has a **Launch Cursor** button pointing at your Start
  Menu `.lnk`. Tap it — **Cursor actually opens now** (fixed the
  `ELECTRON_RUN_AS_NODE` env poisoning that made every Electron launch die
  silently while reporting success).
- With Cursor running, the **agent bar** appears on the Cursor scene
  (Continue / Stop / New Chat / Submit) and app-detection reports
  `cursor`.

## 7. Settings / security / misc fixes

- Auth: Settings → Server → Authentication — set a password, deck locks
  itself, unlock = real session.
- Devin session picker no longer lists ~26 IDE helpers — only real
  `devin.exe` CLI sessions.
- Geolocation (weather "use machine location"), triggers/schedules,
  spectrum + stats screen savers, notification center — all earlier
  upgrade items, all tested.

---

## Known notes (not bugs)

- Headless/desktop-with-touch viewports take the **mobile chrome** path
  (bottom scene rail + agent console instead of the grid) — by design.
- Foreground-window detection only works from an interactive desktop —
  on the real panel it's fine.
- `backend/test-scripts/` holds the playwright capture/e2e scripts the
  test agents used — kept for reruns.

## If something's off

Every change is documented in `design-log/DL-114` … `DL-132` with
frozen design + implementation results. `git log` / `git show 34acf1e`
for the full diff. Profile backup before all mutations:
`backend/data/backups/profile-pre-orchestrated-tests-*.json`.
