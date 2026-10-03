# Morning test guide — research upgrade (DL-114 → DL-133)

Everything below is committed on `research_upgrade1`, built
into `frontend/dist`, and running live on the backend at
`http://127.0.0.1:5000`. **541 frontend + 1111 backend tests pass.**

> **Updated for 2.3.0 (DL-146):** the app is now at 2.3.0 with 947 frontend and 1544 backend tests.
> Settings is reorganised (Overview, Appearance, Agents & automation, Integrations, Devices & network, System),
> so older "Settings → Server / Connect a device / Integrations" paths below now live under those sections.
> `backend/test-scripts/` was removed from the repo (DL-146). Real-device checks are in the last section.

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
  `Connected — vdock 2.3.0, 11 tools`.
- Cursor/Claude config snippets are in that modal (copy buttons).

## 6. Cursor launcher + scene (orchestrated-test result)

- Cursor scene has a **Launch Cursor** button pointing at your Start
  Menu `.lnk`. Tap it — **Cursor actually opens now** (fixed the
  `ELECTRON_RUN_AS_NODE` env poisoning that made every Electron launch die
  silently while reporting success).
- With Cursor running, the **agent bar** appears on the Cursor scene
  (Continue / Stop / New Chat / Submit) and app-detection reports
  `cursor`.

## 7. Spectrum + screensaver fixes (DL-133 — newest)

- **Spectrum follows the music.** The tap is no longer pinned to the
  default speaker — if audio renders on another endpoint (or the default
  device changes), the saver hops to it within ~4 s of silence. Verified
  live: sine on the Lenovo headset loopback → bars lit, then hopped back
  to Realtek when it stopped.
  - ⚠️ Honest caveat: **Spotify was in Connect/remote playback during
    testing** — its session was Active but rendered silence on every
    endpoint (verified via the endpoint peak meter). If you see a flat
    spectrum while Spotify "plays", check it's actually outputting on
    this PC — when audio truly plays locally, the bars move.
- **Bigger Now Playing card** on the spectrum saver — 560 px card,
  ~120 px art, bigger transport buttons; still bottom-anchored, spectrum
  keeps the screen.
- **Screensaver Type is now the first panel** in Settings → Appearance →
  Screen saver, with a new **Shuffle** option + "Rotate every" interval
  (1/5/10/30 min). Shuffle opens on a random view and keeps rotating —
  the saved pick stays "Shuffle".
- Factory default stays **Widget dashboard**.

## 8. Settings / security / misc fixes

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

## Phone & tablet checklist (real devices, DL-145 / DL-147)

Automated tests and emulation cannot cover these. Do them once on real hardware and note any that fail.
Set a deck password first (Settings → Devices & network → Connect a device).

- [ ] **Approve / Deny** a live Claude Code permission prompt from the phone's approval remote; confirm the answer lands in the right terminal.
- [ ] **Hold-to-talk** on the phone: hold, speak, release; the text appears and you submit it yourself.
- [ ] **Add to Home Screen**: the icon looks right, the deck opens full-screen with no browser bars (iOS Safari / Android Chrome).
- [ ] **QR pairing**: scan the Connect-page QR with a password set; time how long until the deck is usable. A reused or 10-minute-old code must be rejected.
- [ ] **Wake lock**: leave the tablet deck open for several minutes; the screen should not dim. It should dim again after leaving the deck.
- [ ] **Reconnect**: lock the phone for a minute, wake it; the deck returns to the same scene without a manual refresh.
- [ ] **Docker running state**: with Docker Desktop running containers, the Docker key shows the running count; stop/start and logs work from its menu.
- [ ] **Win+H dictation**: Dictate to Agent types into the agent window (allow online speech recognition once if Windows asks).
- [ ] **Mic mute on a call**: the Mic Mute key mutes the real microphone in Teams/Zoom/Meet and the LIVE / MUTED face matches.

## If something's off

Every change is documented in `design-log/DL-114` … `DL-133` with
frozen design + implementation results. `git log` / `git show 34acf1e`
for the full diff. Profile backup before all mutations:
`backend/data/backups/profile-pre-orchestrated-tests-*.json`.
