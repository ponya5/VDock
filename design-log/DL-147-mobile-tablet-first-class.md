# DL-147 - Phones and tablets as first-class touch decks

Four phases, one user review stop after each. Plan:
`docs/superpowers/plans/2026-10-03-dl147-mobile-tablet-first-class.md`.
Runs **after DL-146 Phase 3b lands** (3b owns `views/SettingsView.vue`,
`frontend/src/settings/*`, `components/settings/**`). The exact interleave with
DL-146 3c and Phase 4 is in the plan's "Interleave with DL-146" section; short
version: DL-147 P1 -> DL-146 3c -> DL-147 P2 -> P3 -> P4 -> DL-146 Phase 4.

## Problem

User request: "Most users don't have a free touch screen, but they have mobile
phones / tablets to use instead. Add a full ability to enjoy VDock intuitively
with the correct UI using mobile (which we already do) and tablets, as the
touch screen." Standing guidance: intuitive, not overloaded, value for
developers; no new settings pages unless unavoidable; secrets only in
`backend/.env`.

VDock already has a lot of phone work (DL-057, 059-063, 065, 067, 071, 082,
083, 137, 138). What it does not have is a **model of what device it is on**.
"Mobile" is one boolean that means "touch and the short side is ≤ 700 px",
which lumps phones together with the 7" panel and leaves tablets on the desktop
path. Tablets were never designed for, and one tablet size has a blank deck.

Audit: 2026-10-03, `main` @ `c9754ca` plus DL-146 work in progress. Live checks
used Playwright (`playwright-core` from a temp folder, `isMobile` + `hasTouch`
emulation) against the Vite dev server on :4444 proxying the real backend on
:5000. **Every non-GET `/api` request was intercepted and answered locally**
(19 intercepted, among them `POST /api/actions/execute` from a touch hold on a
key and `PUT /api/user-settings`), so nothing was pressed, saved or executed on
the PC. Mission Control was opened with a routed fake `/api/agent-mission`
payload (three fake sessions). Screenshots: `design-log/refs/dl147-before-*.jpg`.

## Existing architecture (what is there)

| Area | Where | What it does |
|---|---|---|
| Phone detection | `utils/mobileViewport.ts` | `isMobileViewport = min(innerW, innerH) ≤ 700 && (pointer:coarse \|\| maxTouchPoints > 0)`; `isPortrait`. Used by 11 files |
| Other detection rules | `DockedSidebar.vue:120-149` (`innerWidth < 768` mobile, `< 480` narrow, `≤1100 \|\| ≤650` compact); `stores/settings.ts:1107-1122` (`≤1100 \|\| ≤650 \|\| touch`); `AgentSessionPicker.vue:164` (`max-width:720px, max-height:800px, pointer:coarse`); `LightPillar.vue:174` (user-agent sniff); `DashboardView.vue:1682` (`@media (max-width: 768px)`) | Six different rules for "small / touch / mobile" |
| Touch scaling | `stores/settings.ts:261-274, 1020-1035` | `touchMode` normal/touch-friendly/tablet = 1.0/1.5/2.0 -> CSS vars `--touch-multiplier`, `--min-touch-target`, `--button-min-height`, spacing; `TouchModeSelector.vue`, `AppearanceButtons.vue:17-31` |
| Phone chrome | `MobileDeckChrome.vue` | Scene rail, page steppers, fullscreen button + "Tap for fullscreen" / iPhone "Add to Home Screen" callout (DL-067), ⋮ menu = Refresh, Exit VDock |
| Phone agent console | `MobileAgentConsole.vue` | Portrait console on agent scenes (DL-065) |
| Portrait gate | `RotateToLandscape.vue` | Phones in portrait get "Rotate your device" unless screensaver/agent console (DL-060) |
| Phone = control surface | `stores/dashboard.ts:470-476`, `DashboardView.vue:108,1158` | Edit mode blocked, no profile UI, no tour (DL-061) |
| Grid fit | `DeckGrid.vue:186-286` | Compact square cells when a desktop window's aspect mismatches; phones stretch-fill (`fit`) |
| Gestures | `composables/useGestures.ts`, `services/sceneSwipe.ts`, `DashboardView.vue` `.main-content` `touch-action: pan-y` | Swipe = scene switch (DL-082); long-press only in edit mode (DL-055) |
| Hold keys | `DeckButton.vue:13-15, 778-823` | `press:'hold'` / `release_action` dispatch on pointerdown, release on pointerup/**pointercancel**; `setPointerCapture`; `@contextmenu.prevent="handleRightClick"` -> emits `edit` |
| Haptics | `utils/haptics.ts` | `vibrate(50)` on key press, 10 ms scene select, slider ticks (Android only; iOS Safari has no `navigator.vibrate`) |
| Fullscreen | `utils/fullscreenSupport.ts`, `MobileDeckChrome.vue` | Detects missing Fullscreen API (iPhone) and standalone mode |
| PWA | `vite.config.ts:35-92`, `index.html` | `vite-plugin-pwa` autoUpdate, manifest with 192/512 "any" + 512 maskable, `display: standalone`; `viewport-fit=cover`, `apple-mobile-web-app-capable`, `black-translucent` status bar; `main.ts` reloads on SW `controllerchange` |
| Socket | `api/socket.ts` | socket.io auto-reconnect, URL = `location.protocol//location.hostname:5000`, auth token in handshake; resync on `connect` in `settings.ts:1174`, `agentState.ts:64`, `nowPlaying.ts:123`. Key presses go over **HTTP** `POST /api/actions/execute` (`dashboard.ts:654`), so a dead socket does not drop presses |
| Settings sync | DL-138, `stores/settings.ts` | Field-level last-write-wins across **all** devices; every persisted setting is shared |
| Connect a device | `components/settings/panels/ConnectPanel.vue`, `composables/useServerConfig.ts` | Steps, Allow LAN switch, deck address + custom host, `lanReachable` no-cors probe every 5 s, QR of `lanUrl` |
| Auth over LAN | DL-126, `routes/auth.py`, `AuthGate.vue`, `services/auth.ts` | Password -> JWT in localStorage, socket handshake token, 5 failures/min/IP throttle |

## Findings

### Cross-cutting

**X1. Touch scaling is shared across every device.** `touchMode` is a normal
persisted setting, so DL-138 sync gives one value to the desktop, the panel,
every phone and every tablet. `detectSmallScreenDefaults()`
(`settings.ts:1107-1122`) flips it to `tablet` (2.0x, min target 48) on any
compact **or touch** device and saves. On this machine the server file holds
`touchMode: tablet, minimumTouchTargetSize: 48` (verified via
`GET /api/user-settings`), so the 1440x900 desktop also runs at 2.0x. A user who
picks "Normal" on the PC un-scales their phone, and the reverse. This is the
root of several "degraded" rows below (oversized header FAB on phones, 2x footer
controls on tablets in edit mode).

**X2. Six device rules, no device class.** See the table above. Concrete
mismatch: `DashboardView.vue:1682` stacks the layout at `max-width: 768px`
while `DockedSidebar.vue:120` only switches to its horizontal mobile form at
`innerWidth < 768`. At exactly 768 px wide the sidebar stays a full-height
column inside a column layout (see T1).

**X3. Safe-area insets are almost unused.** `viewport-fit=cover` +
`black-translucent` let content run under the notch / home indicator, but only
`LiveActionMenu.vue`, `MobileAgentConsole.vue` and `SpectrumStage.vue` use
`env(safe-area-inset-*)`. `MobileDeckChrome`, the header reveal FAB, Mission
Control, toasts and the rotate gate do not. Code evidence only (emulation has no
notch); matters most for iPhone landscape and Home Screen (standalone) launches.

**X4. No keep-screen-on.** No `navigator.wakeLock` anywhere. Wake Lock needs a
secure context, so over `http://192.168.x.x` it is unavailable even when added.
A tablet on a stand dims and locks after the OS timeout.

**X5. PWA install vs plain HTTP, and `USE_SSL` is a no-op.** The manifest and
icons are correct. Service worker registration and Android "Install app" need a
secure context, so over plain LAN HTTP Android Chrome only creates a shortcut
that opens in a browser tab, and no service worker runs on the phone. iOS
"Add to Home Screen" does work over HTTP and launches standalone (the DL-067
callout already says so). **`USE_SSL` is never wired:** `app.py:526`
`socketio.run(app, host, port, debug, allow_unsafe_werkzeug)` has no
`ssl_context`. `USE_SSL` only affects the boot validator (cert files must
exist, `config.py:372`) and an HSTS header (`app.py:100`), and
`useServerConfig.ts:26` hard-codes `http://` in the QR. Turning it on today
gives an HSTS header over plain HTTP and nothing else.

**X6. Reconnect is silent and profile edits never reach an open phone.**
socket.io reconnects by itself and three stores re-sync on `connect`. Gaps:
(a) no UI shows "disconnected"; after a phone wakes, live faces (agent state,
now playing, toggles) are stale until the socket comes back, with no hint;
(b) nothing triggers an immediate reconnect on `visibilitychange`; (c) the
backend never tells clients that a profile changed (no `profile_*` emit in
`backend/`). A layout edited on the PC stays stale on an open phone or tablet
until someone taps Refresh. Server-originated emits from HTTP handlers do not
reach clients on this stack (`dashboard.ts:503-512`), so a relay has to be
client-initiated, like `user_settings_changed` (`app.py:401`).

**X7. A failed profile fetch on wake can create a duplicate profile.**
`DashboardView.vue:1124-1146`: if `getProfile(activeProfileId)` fails *and*
`loadProfiles()` returns nothing (network blip, 401 before unlock),
`createDefaultProfileForFirstTimeUser()` (`:961`) creates a new "My VDock"
profile on the server. Phones and tablets connect over Wi-Fi and wake from
sleep, so they hit this path far more often than the desktop. Code evidence.

**X8. "No profile loaded" on a fresh browser.** It is not a "this browser has
no profile" state. A new origin reads the server-persisted `activeProfileId`
(DL-061 follow-up) and loads the desktop's profile; it loaded at every size in
this audit. "No profile loaded" means the backend has **zero** profiles (the
desktop was never set up), the API is unreachable (wrong host, firewall,
Vite on loopback, DL-069), or the API returned 401 before the lock screen
resolved. A phone gets a profile by connecting to a backend that already has
one. Nothing is stored per phone.

**X9. Exit VDock is one confirm away on every phone** (`MobileDeckChrome.vue:114`).
With Allow LAN on and no password (this machine), anyone on the Wi-Fi can quit
the desktop app. Not changed here: DL-146 3c adds the password nudge on the
Connect page, which is the real fix. Noted for the README "phone" section.

### Surface fit audit

Viewports: phone portrait 390x844 (P-P), phone landscape 844x390 (P-L), small
tablet portrait 768x1024 (T-P; also probed 744x1133, 800x1280, 820x1180),
small tablet landscape 1024x768 (T-L), large tablet 1280x800 and 1366x1024
(T-XL), 7" panel 1024x600 touch, not mobile UA (Panel), desktop 1440x900 no
touch (Desk). Verdicts: **W** works, **D** degraded, **B** broken, **-** not
applicable by design, **n/v** not verified. "Small" = interactive element
below 44 px in either dimension (from `getBoundingClientRect`).

| # | Surface | P-P | P-L | T-P | T-L / T-XL | Panel | Desk | Evidence |
|---|---|---|---|---|---|---|---|---|
| S1 | Deck grid (Media 3x6) | **B** | W | **B** (768) / D (800-820) / W (744) | W | W | W | P-P: rotate gate blocks; behind it cells are **56x252** slivers (`dl147-before-phone-portrait-deck.jpg`). T-P 768: `.main-content` at y=1024, **h=0**, docked sidebar 168x1024, deck invisible (`dl147-before-tablet-small-portrait-deck.jpg`, X2). 800/820 wide: 96-99 px squares in a band, about half the screen empty. 744: sidebar becomes an 80 px top bar, 114 px keys. P-L 131x101, T-L 133, 1280 172, 1366 186, Panel 161x171 (`dl147-before-panel-7in-deck.jpg`), Desk 199 |
| S2 | Scene switcher | W | W | W | W | W | W | Phone rail scrolls horizontally (last pill off-screen by design); tablets use the DeckHeader pills after the reveal FAB; swipe works (DL-082) |
| S3 | Agent scene | W | W | W | W | W | W | Phone console renders, one 36 px chip (`dl147-before-phone-portrait-agent-scene.jpg`); tablets get action bar + grid |
| S4 | Header reveal FAB | D | D | W | W | D | W | At the shared 2.0x the FAB is about 200x110 and covers the bottom-right keys on P-L/Panel (`dl147-before-phone-landscape-deck.jpg`); X1 |
| S5 | Edit mode | - (blocked) | - | D | **D** | - (compact) | W | T-L: keys shrink 133 -> **63 px**, 40x40 edit/copy/delete chips cover the key faces, edit sidebar takes about 40% of the width, footer controls at 2x (Add Page about 230x85) (`dl147-before-tablet-small-landscape-edit-mode.jpg`); 26 small targets |
| S6 | ButtonEditor | **B** (policy) | **B** (policy) | D | D | D | W | `contextmenu` on a key opens the editor **on phones**, against DL-061 (`dl147-before-phone-landscape-button-editor.jpg`): `DeckButton.vue:10` -> `useButtonActions.ts:217` is not gated. Small on every touch class: Save icon 37x32, close 30x41, Expand 29x23, checkbox 13x20 |
| S7 | Hold-to-talk / hold keys | **B** | **B** | **B** | **B** | **B** | W | Touch hold + 16 px drift -> `pointerdown, pointercancel` (recorded): `touch-action: manipulation` (`DeckButton.vue:1007`) lets the browser take the pan, and `pointercancel` is wired to release (`:15`). Dictation stops mid-sentence. On Android a long-press also fires `contextmenu` -> ButtonEditor opens **during** the hold (code path S6; headless emulation does not synthesise long-press `contextmenu`, so confirm on a real device). No `-webkit-touch-callout: none` on keys (iOS callout risk) |
| S8 | Slider quick-jump chips | D | D | D | D | D | D | 26 px tall at every class (Panel 57x26, Desk 72x20) |
| S9 | Live-button menus / press sheet | n/v | n/v | n/v | n/v | n/v | n/v | Needs live CI/PR buttons (GitHub token). `LiveActionMenu.vue` already uses safe-area insets. Verify in P1 with a routed fake live payload |
| S10 | Mission Control | W | W | W | W | W | W | Groups, Approve/Deny/Open all ≥44 px tall at 390 px (`dl147-before-phone-portrait-mission-control.jpg`); close button 40x40 (D-minor). **No persistent way to open it on a phone**: only the waiting-dock chip (when something waits) or a deck key with the action |
| S11 | Agent alert overlay / dock / glow | D | D | D | D | D | D | Toast "Dismiss" 18x21, "Show Details" 117-125x24-26 at every class. Glow not visually checked |
| S12 | Screensaver | W | W | W | W | W | W | Phone shows clock + world clock (DL-063); no overflow at any size |
| S13 | Settings | D | W | D | D | D | D | Phones do not normally reach Settings (DL-061). At 390 the first sweep laid out at **523 px** (page zoomed out), the second at 390, while DL-146 3b was being edited live: re-check after 3b. Topbar actions wrap into two rows (about 200 px) above content (`dl147-before-phone-portrait-settings-appearance.jpg`). Tablet/Panel: nav items 40 px, sub-tabs 28-29 px, topbar buttons 34 px (`dl147-before-tablet-small-landscape-settings-appearance.jpg`). DL-146 Task 3.20 covers 44 px for 1024x600/800x480 only |
| S14 | Connect a device page | W | W | W | W | W | W | 0 small targets at 390 px. Gaps: QR is always `http://` (X5); with a password set the phone must type it into `AuthGate` (friction against "connected in a minute"); nothing tells the user how to get a full-screen "app" on the device |
| S15 | Notifications (toasts) | D | D | D | D | D | D | Same as S11 dismiss target |
| S16 | Reconnect after sleep | D | D | D | D | W | W | X6 (code) |

Bottom line: **broken today** = phone portrait deck (gate + slivers),
768-px tablet portrait (blank deck), hold-to-talk on every touch device, and
phone editing via long-press. **Degraded** = shared touch scale, tablet portrait
dead space, tablet edit mode, sub-44 px chips/toasts/editor controls, no
keep-awake, silent reconnect, stale profiles, missing safe-area padding.

## Device-class model

One module, `frontend/src/composables/useDeviceClass.ts`, module-level
singleton refs (same pattern as `mobileViewport.ts`), updated on `resize` and
`orientationchange` (and `matchMedia('(pointer: coarse)')` change).

```ts
export type DeviceClass = 'phone' | 'tablet' | 'panel' | 'desktop'
export type Orientation = 'portrait' | 'landscape'
export interface DeviceInfo {
  deviceClass: Ref<DeviceClass>
  orientation: Ref<Orientation>      // from innerWidth/innerHeight
  isTouch: Ref<boolean>              // coarse || maxTouchPoints > 0
  isCompactTouch: Ref<boolean>       // == today's isMobileViewport, exactly
  isStandalone: Ref<boolean>         // display-mode: standalone || navigator.standalone
}
export function classifyDevice(i: { screenW: number; screenH: number; coarse: boolean;
  touchPoints: number; electron: boolean }): DeviceClass   // pure, unit-tested
```

Rules (first match wins). `short`/`long` come from **`screen.width/height`**
(CSS px), not `innerWidth`, so an on-screen keyboard
(`interactive-widget=resizes-content`) or a resized window cannot flip the class.
Orientation and grid fit keep using `innerWidth/innerHeight`.

| # | Condition | Class | Examples |
|---|---|---|---|
| 1 | Electron (`useElectron().isElectron()`) | `panel` if touch && short ≤ 700, else `desktop` | the 7" panel window; the desktop app |
| 2 | no touch | `desktop` | any mouse-only browser |
| 3 | short ≤ 700 && long < 960 | `phone` | 390x844, 430x932, 800x480 kiosk browsers (same chrome as today) |
| 4 | short ≤ 700 | `panel` | 1024x600 touch display in a browser |
| 5 | coarse | `tablet` | iPad mini 744, iPad 820, Android 800x1280, 1024x768, 1280x800, 1366x1024 |
| 6 | else | `desktop` | touch laptop with a fine primary pointer |

`isCompactTouch` keeps the legacy formula (`min(innerW, innerH) ≤ 700 &&
touch`) so every existing `useMobileViewport()` caller behaves identically.
`utils/mobileViewport.ts` becomes a re-export shim. New behaviour reads
`deviceClass`; callers move off the legacy flag only where a phase says so.
Each conversion changes behaviour on purpose and gets a test.

The dashboard root gets `device-<class>` and `orient-<orientation>` classes, so
CSS can target classes instead of new width media queries.

**Layout class (split-screen).** `deviceClass` is hardware-stable (screen
size), but layout follows the window: `layoutClass = 'phone'` when
`deviceClass === 'tablet' && innerWidth < 600` (iPad/Android split view or
slide-over, a narrow freeform window), otherwise `layoutClass = deviceClass`.
The root class is `device-<layoutClass>`. Rotating or resizing never changes
the active scene, page or profile; only the layout reflows.

## Decisions

1. **Device class, not breakpoints.** One composable (above), one pure
   `classifyDevice()` with a table-driven test. P1 moves `DockedSidebar`'s
   three width rules, `settings.ts` `detectSmallScreenDefaults`, the
   `AgentSessionPicker` media query and the `LightPillar` UA sniff onto it.
   `DashboardView.vue:1682` `@media (max-width: 768px)` is replaced by
   `.device-phone` / `.device-tablet.orient-portrait` rules with the same
   boundary as the sidebar.
2. **Presentation is per device; content is shared.** New device-local prefs in
   `localStorage['vdock_device_prefs']` (`services/devicePrefs.ts`), **never**
   part of `PersistedUserSettings`, so DL-138 sync, PUT and broadcast never see
   them: `touchMode: 'auto' | 'normal' | 'touch-friendly' | 'tablet'`
   (default `auto`), `layout: 'fit' | 'designed'` (default `fit`),
   `keepAwake: boolean` (default `true`). Effective multiplier: `desktop` and
   `panel` use the shared `touchMode` as today (**no change on the PC or the
   panel**); `phone` auto = 1.0 (the fit pipeline already scales keys), `tablet`
   auto = 1.5. `detectSmallScreenDefaults()` only runs for the `panel` class,
   which is DL-009's intent, so phones and tablets stop writing the shared key.
   The shared value on this machine (`tablet`) is **not** migrated. Profiles,
   scenes, keys, screensaver and alert settings stay shared.
3. **Portrait = runtime reflow, not per-device layouts.** Per-device-class
   layouts (`pages[].layouts[class]`) were rejected: a data-model change and
   migration for every profile and template, four grids to edit per page, and
   an editor UI for a class the user may never own. Instead
   `utils/gridReflow.ts` exports a pure
   `reflowPage(page, { width, height, minCell }) -> RenderPage` used **only**
   when (a) the class is `phone` or `tablet`, (b) orientation is portrait,
   (c) the authored grid is landscape (`cols > rows`), (d) not in edit mode,
   (e) the device pref `layout === 'fit'`. Algorithm: enabled buttons in
   reading order (row, col); target `cols' = clamp(rows, 2, cols)` (3x6 -> 3
   columns); spans clamped to `cols'`; first-fit packing that keeps order;
   empty authored cells dropped; cell = `min(w / cols', h / rows')`; when the
   cell would fall below `minCell` (phone 72 px, tablet 96 px) the pane
   scrolls **vertically** (never horizontally). Nothing is saved; edit mode
   shows the authored grid. Landscape keeps today's fit pipeline. No
   migration, no profile schema change.
4. **The phone rotate gate retires** (user decision D1) when `layout === 'fit'`:
   portrait is how people hold phones, and reflow makes it usable. With
   `layout: 'designed'` the DL-060 gate comes back. The agent-console and
   screensaver exemptions stay.
5. **Phones stay a control surface (DL-061 kept).** Close the loophole:
   `contextmenu` opens the editor only after a **mouse** pointerdown and never
   on the `phone` class; on touch it is always `preventDefault`ed. Tablets keep
   editing (they are big enough) and get a fit pass in P3.
6. **Hold keys own their touch.** Keys whose action is hold/press/
   `release_action` get `touch-action: none` (class `is-hold`, set before
   pointerdown, so the browser never claims the pan and never sends
   `pointercancel`) plus `-webkit-touch-callout: none` on all keys. Scene swipe
   still works from every other key and from empty space.
7. **Phone as approval remote, inside existing surfaces.** The ⋮ menu gets
   "Mission Control" with a needs-you count, and the ⋮ button shows a dot when
   something waits (data: the existing socket-fed `agentState`, no new
   polling). On `phone`/`tablet` a session entering `permission` dismisses the
   screensaver (today only the agent-console scene does, `DashboardView.vue:772-781`).
   Approve/Deny vibrate 15 ms. No new modal, no new settings.
8. **Keep awake = deck mode.** On `phone`/`tablet`, while fullscreen **or**
   standalone and the page is visible, and `keepAwake` is on: use Wake Lock
   when `isSecureContext && 'wakeLock' in navigator`, otherwise a muted,
   `playsinline`, looping tiny video (the NoSleep technique, own ~40-line
   implementation, bundled ≤ 10 KB asset). Released on exit/hidden and
   re-acquired on visible. Toggle lives in the phone ⋮ menu; tablets inherit
   the default. No new settings page.
9. **Reconnect is visible and self-healing.** `services/connection.ts` tracks
   `connected | reconnecting | offline`; a slim `ConnectionBanner.vue` overlay
   (absolute, no layout shift) shows after 2 s disconnected and changes to
   "Can't reach VDock at <host> - is the PC awake?" + Retry after 15 s.
   `visibilitychange -> visible` with a dead socket reconnects at once; every
   reconnect after the first calls `refreshVdock()` unless editing.
10. **Profile change relay, client-initiated.** After a successful
    `saveProfile()` the client emits `profile_changed {id}`; the backend relays
    it to other clients (`broadcast=True, include_self=False`, same as
    `user_settings_changed`); receivers showing that profile and not editing
    re-fetch it (debounced 500 ms). Fixes X6(c) without server-push plumbing.
11. **No profile bootstrap from phones/tablets, and none after a failed
    fetch.** `createDefaultProfileForFirstTimeUser()` runs only when
    `loadProfiles()` **succeeded** with an empty list **and** the class is
    `desktop`/`panel`. Otherwise the existing "Set up a profile on the VDock
    desktop app first" hint shows, with a Retry.
12. **Pairing through the QR when a password is set.** When `require_auth` is
    on, the Connect page asks `POST /api/auth/pair-token` (auth-protected:
    the desktop window showing the QR is already signed in) for a single-use,
    10-minute, 32-byte URL-safe token and encodes `<lanUrl>/?pair=<token>`.
    The phone exchanges it once via `POST /api/auth/pair` for the normal JWT
    (same throttle as login), stores it with `setAuthToken`, and strips the
    query with `router.replace`. Tokens are never logged; the QR refreshes
    every 9 minutes while the page is open. No short typed code (deferred).
13. **Install guidance, honest about HTTP.** Phone ⋮ menu "Add to Home Screen"
    opens a small sheet (iOS: Share -> Add to Home Screen, launches full-screen;
    Android: ⋮ -> Add to Home screen, opens as a browser shortcut over Wi-Fi),
    hidden when standalone, and reuses the DL-067 copy. The Connect page gets a
    fourth step, "Optional: add it to the Home Screen". No coach-mark overlays.
14. **`USE_SSL`: wire it or stop pretending (user decision D3).**
    Recommended: wire it (S effort): `socketio.run(..., ssl_context=(cert, key))`
    when `USE_SSL` and both files exist; `lanUrl` uses `https` when `use_ssl`.
    Document mkcert in `docs/development/` (not the README). Real install, a
    service worker on the phone and native Wake Lock then work for users who
    trust a local CA. HTTPS by default and in-app cert generation stay out.
15. **44 px everywhere, without moving the panel/desktop layout.** Undersized
    controls get a hit area of at least 44x44 through padding or a transparent
    `::before` hit-slop. Visual size and layout boxes stay the same on
    panel/desktop, enlarged only where the class is `phone`/`tablet`. The
    audit measures the **effective** hit area (`elementFromPoint` sampled
    ±22 px from the centre), not just the box.
16. **A device audit tool lives in the repo.** `frontend/scripts/device-audit.mjs`
    (dev-only, `playwright-core` devDependency, no browser download; uses an
    installed Chromium via `PLAYWRIGHT_CHROMIUM_EXECUTABLE` or
    `npx playwright install chromium`), `npm run audit:devices`. It runs every
    device class, blocks every non-GET `/api` call, writes metrics JSON +
    screenshots, and compares the panel/desktop deck geometry with a committed
    baseline (`frontend/scripts/device-audit.baseline.json`). Not in CI (no
    browser there). It is also the screenshot tool for DL-146 Phase 4.

### Ranked mobile features (value for developers / effort)

| Feature | Value | Effort | Verdict |
|---|---|---|---|
| Fix S1/S6/S7/T-P 768 (broken) | Very high | S | **P1** |
| Device-local touch scale (X1) | High | S | **P1** |
| Portrait reflow + retire gate | High (phones held in portrait) | M | **P2** |
| Phone approval remote (⋮ Mission Control + wake on permission + haptic) | High (approve agents from the couch/desk) | S | **P2** |
| Safe-area padding | Med | XS | **P2** |
| Tablet portrait fit + tablet edit-mode fit | Med-High | M | **P3** |
| Keep awake in deck mode | High for tablets on a stand | S | **P3** |
| Reconnect banner + resume + profile relay | High (silent staleness is the #1 "it's broken" report on phones) | S-M | **P4** |
| QR pairing with a password | High once DL-146 3c pushes passwords | M | **P4** |
| Add-to-Home-Screen sheet + Connect step | Med | XS | **P4** |
| Wire `USE_SSL` (D3) | Med (enables real PWA + Wake Lock for power users) | S | **P4 optional** |
| Haptics | exists (press/scene/slider) | - | **Cut** (only the 15 ms approve/deny tick in P2) |
| Swipe between scenes | exists (DL-082) | - | **Cut** |
| Pull-to-refresh / overscroll suppression | exists (`overscroll-behavior-y: contain`, `touch-action: pan-y`) | - | **Cut** (verify only) |
| Web Push / Notification API | Med | L: secure context + trusted cert + VAPID keys + SW push + `pywebpush`; iOS only for installed PWAs | **Defer** |
| Short typed pairing code | Low (QR covers it) | S | **Defer** |
| Orientation lock (`screen.orientation.lock`) | Low (fullscreen-only, Android-only) | XS | **Defer** |
| Per-device-class saved layouts | Low after reflow | L | **Rejected** (decision 3) |
| Editing on phones | Low (desktop/tablet do it better) | L | **Rejected** (DL-061) |

### Acceptance (all phases, measured by `npm run audit:devices` + a real phone)

- **First-time phone user connects via QR and presses a key in under 60 s**:
  PC shows Connect (LAN already on) -> scan -> deck interactive. Measured by
  the user on a real phone with a stopwatch; proxy in the audit: first
  `.deck-button` interactive < 5 s after navigation, and **zero blocking
  layers** in portrait (no rotate gate, no AuthGate when `?pair=` is valid, no
  tour).
- **No horizontal scroll and every target ≥ 44 px effective** at every device
  class (P-P, P-L, T-P 744/768/820, T-L, 1280x800, 1366x1024, Panel, Desk) for
  the dashboard, agent scene, Mission Control, ButtonEditor (tablet/desk),
  edit mode (tablet/desk), screensaver, Connect, Settings (tablet/desk). The
  allowlist is in the script with a reason per entry (for example
  `input[type=range]` measured by its row).
- **Panel and desktop unchanged**: deck chrome type, cell sizes (±2 px) and
  header/footer presence at 1024x600 and 1440x900 equal the committed baseline.
- **"Show header" FAB never overlaps the agent waiting dock** (user-reported,
  fixed via `html.reveal-fab-visible` in `DashboardView.vue` /
  `AgentWaitingDock.vue`, pinned by `header-reveal-dock.test.ts`): the FAB box
  and `.agent-waiting-dock` box do not intersect, at every device class and
  every tablet-matrix size, with a waiting session present.

### Tablet test matrix (CSS px; portrait and landscape each)

| Device | Portrait | Landscape | Gate |
|---|---|---|---|
| iPad mini (6th/7th) | 744x1133 | 1133x744 | P1 (portrait), P3 |
| iPad (legacy 9.7"/10.2" class) | 768x1024 | 1024x768 | P1 (portrait), P3 |
| iPad 10th gen / Air 10.9" | 820x1180 | 1180x820 | P1 (portrait), P3 |
| iPad Air/Pro 11" | 834x1194 | 1194x834 | P1 (portrait), P3 |
| iPad Pro 12.9" / Air 13" | 1024x1366 | 1366x1024 | P3 |
| Galaxy Tab A / S (10-11") | 800x1280 | 1280x800 | P3 |
| Amazon Fire HD 10 | 800x1280 | 1280x800 | P3 (same box as Galaxy; Silk UA) |
| Galaxy Tab S Ultra (14.6") | 924x1480 | 1480x924 | Extended, non-gating (less common) |
| Split view (half of iPad 10th) | 405x1180 | 590x820 | P3: must render `layoutClass = phone` |

For every row and orientation: full deck visible (no blank `.main-content`),
no horizontal scroll, every target ≥ 44 px effective, safe-area insets
respected (audit sets 24 px top / 20 px bottom insets with CDP
`Emulation.setSafeAreaInsetsOverride` if the bundled Chromium supports it,
otherwise "needs real device"; no interactive element may sit inside the
inset), rotation keeps the current scene and page,
and no FAB/dock overlap. Each gets
`design-log/refs/dl147-after-tablet-<w>x<h>-<portrait|landscape>.jpg`.
Phase 1 must pass the four portrait rows marked P1 (blank-deck fix); Phase 3
must pass every gating row in both orientations.

## Risks

- **Class misdetection.** Foldables (673x841 unfolded) are classified tablet
  by rule 5, which is fine. iPad with a trackpad may report `pointer: fine`
  and become desktop (acceptable: it then behaves like a laptop). An 800x480
  panel in a plain browser becomes `phone`, the same chrome it has today. The
  table test pins all of these.
- **Reflow surprises a user** who designed the 3x6 order on purpose. Mitigated:
  reading order is preserved, edit mode shows the authored grid, and ⋮ ->
  "Layout: as designed" brings the old behaviour (and the rotate gate) back
  per device.
- **`touch-action: none` on hold keys** stops scrolling when a drag starts on
  such a key in a vertically scrolling reflowed pane. Acceptable: hold keys are
  for holding, and every other key and the gaps still scroll.
- **Video keep-awake** costs battery and iOS Low Power Mode may ignore it.
  Only active in fullscreen/standalone on phone/tablet, with an off switch.
- **Pairing token in a URL** can end up in browser history on the phone.
  Single-use and 10-minute TTL limit it; it is stripped from the address bar
  at once; a used or expired token falls back to the normal lock screen.
- **Concurrent DL-146 work.** `DashboardView.vue` is touched by DL-146 Task
  3.17 (`?edit=1`) and by DL-147 P1-P4; `ConnectPanel.vue` by Task 3.19 and
  DL-147 P4; `AppearanceButtons.vue` by DL-147 P3 only. The plan sequences them.
- **Dev-server-only audit drift.** The panel loads `frontend/dist`. Every phase
  ends with `npm run build` (AGENTS.md).
- **HTTP in the QR** while `use_ssl` is on (after D3 = wire) must flip to
  `https`, or phones land on a dead port. Covered by a `useServerConfig` test.

## Out of scope

Native iOS/Android apps; Web Push and the Notification API; HTTPS by default
and in-app certificate generation; offline action queueing (a service worker
caching API calls); multi-PC pairing; Bluetooth/USB; editing on phones;
per-device saved layouts; a Settings redesign (DL-146 owns Settings, DL-147
only checks it at tablet sizes and hands findings to Task 3.20); README text
(DL-146 Phase 4, which takes DL-147's screenshots).

## User decisions

- **D1** Retire the phone portrait rotate gate when reflow is on (recommended)
  or keep phones landscape-only and reflow tablets only.
- **D2** Device-local touch scale with phone auto = 1.0, tablet auto = 1.5
  (recommended), leaving the PC's shared value as is. Optionally reset the
  desktop's shared `touchMode` to Normal (it is `tablet` today only because a
  touch device wrote it).
- **D3** Wire `USE_SSL` (recommended, S) or remove the toggle/claim.
- **D4** Pairing tokens in the QR when a password is set (recommended), or
  keep typing the password.
- **D5** Add `playwright-core` as a frontend devDependency for
  `npm run audit:devices` (recommended; no browsers are downloaded by it).

## Implementation Results

### Phase 1 - Device-class foundation + broken-surface fixes

**Status: implemented and verified (unit + live); STOP for user review.**
Decisions applied: D1 (rotate gate retires in Phase 2 - not touched here), D2
(device-local touch scale). D5 is a later-phase decision, so the audit script
(Task 1.2) is **not** built; live checks use the Cursor browser instead.

Baseline: vue-tsc clean, vitest 697 passing (101 files). After: 812 passing
(106 files). Backend untouched.

Changes:
- `composables/useDeviceClass.ts` (new): pure `classifyDevice()` + `resolveLayoutClass()`,
  singleton refs `deviceClass`, `layoutClass`, `orientation`, `viewportWidth`, `isTouch`,
  `isCompactTouch`, `isStandalone`. `utils/mobileViewport.ts` is now a shim over it
  (`isMobileViewport` = `isCompactTouch`, legacy formula pinned by a 40-combo test).
- `services/devicePrefs.ts` (new): `localStorage['vdock_device_prefs']` (`touchMode`
  auto|normal|touch-friendly|tablet, `layout` fit|designed, `keepAwake`); not in
  `PersistedUserSettings`, so never PUT/broadcast (tested).
- `stores/settings.ts`: effective touch scale - phone auto 1.0, tablet auto 1.5, explicit
  device pref overrides; desktop/panel unchanged. `--min-touch-target` floored at 44 on
  phone/tablet. `detectSmallScreenDefaults()` no longer runs on phone/tablet.
- `utils/dashboardLayout.ts` (new): one rule for "stacked deck + sidebar shape".
  `DockedSidebar` and `DashboardView` (`.layout-stacked`, replacing
  `@media (max-width: 768px)`) both use it. Root gets `device-<layoutClass>` /
  `orient-<orientation>` classes.
- `DeckButton.vue`: `is-hold` (push-to-talk / release_action / press-trigger keys,
  not in edit mode) -> `touch-action: none`; `-webkit-touch-callout: none` on all keys;
  `contextmenu` opens the editor only after a **mouse** pointerdown.
  `useButtonActions.handleButtonEdit` is a no-op on the phone class outside edit mode.
- `services/initialProfile.ts` (new) + `profiles.loadProfiles()` now returns whether the
  backend answered: a default profile is created only when the list request succeeded,
  was empty, and the class is desktop/panel. Otherwise "Can't reach VDock" + Retry, or the
  existing desktop-setup hint.
- `LightPillar` (UA sniff) and `AgentSessionPicker` (touch test) read the device class.

Deviations from the plan:
- `detectSmallScreenDefaults()` is skipped on phone/tablet only (not "panel only"), so
  non-touch compact desktop windows keep today's behaviour ("no change on the PC").
- `DockedSidebar`'s `isCompactScreen` width cap (<=1100 / <=650) is left as is: it is a
  width cap, not a layout rule, and moving it risks the 7" panel.
- At exactly 768 px a desktop/panel window is now a column (not stacked); before, the CSS
  stacked while the sidebar stayed a column. This is the same bug as the tablet blank deck.
- Electron classification uses `innerWidth/innerHeight` (the window is the panel); the
  assumption that `screen` is correct in the panel window is unverified.
- Tasks 1.2 (audit script) and the `live-menu` check in 1.8 are not done (D5 not decided).
- Tests for 1.6 were written right after the implementation rather than strictly first.
- The phone **portrait rotate gate is unchanged** in Phase 1: retiring it needs the
  Phase 2 grid reflow (without it portrait shows the 56x252 slivers from the audit).

Verification: `vue-tsc` clean, vitest 812 passing, `npm run build`, `scripts/check.ps1`
all PASS (backend suite included; no backend files touched).

Live (Cursor browser on the built bundle at :5000, CDP device emulation, read-only - no
key pressed, no settings or profile written; emulation reset afterwards). Class / stacked
/ deck / `--touch-multiplier`:

| Size | Class | Deck | Notes |
|---|---|---|---|
| 744x1133 | tablet, stacked | 8 keys, 114 px | no horizontal scroll |
| 768x1024 | tablet, stacked | 8 keys, 118 px, `.main-content` 768x1024 (was h=0) | blank deck fixed |
| 820x1180 | tablet, stacked | 8 keys, 127 px | multiplier 1.5 |
| 834x1194 | tablet, stacked | 8 keys, 129 px | multiplier 1.5 |
| 844x390 | phone | 8 keys, 131x101 (unchanged) | multiplier 1.0, FAB 120x68 (was about 200x110) |
| 390x844 | phone | rotate gate still shown | by design until Phase 2 |
| 1024x600 touch | panel | 161x171 (identical to before) | shared multiplier 2 kept |
| 1440x900 | desktop | 199x199 (identical to before) | shared multiplier 2 kept |

Screenshots: `design-log/refs/dl147-after-tablet-{744x1133,768x1024,820x1180,834x1194}-portrait.jpg`,
`dl147-after-phone-844x390-landscape.jpg`, `dl147-after-panel-1024x600.jpg`,
`dl147-after-desktop-1400x900.jpg` (all <= 345 KB). The stacked tablet portrait still has
dead space above/below the grid and an empty fixed sidebar strip overlapping the header
FAB area; that fit pass is Phase 3.

Not verified live: hold-to-talk drift and long-press editor on a real touch device (CDP
input is blocked here; covered by `deck-button-touch.test.ts`, needs a real Android phone),
the FAB vs agent-dock overlap at each class (needs a waiting session; pinned by
`header-reveal-dock.test.ts`, only the `reveal-fab-visible` class was confirmed live),
Electron `screen` size inside the 7" panel window, S9 live-button menus.

### Phase 2 - Phone experience (portrait reflow, approval remote, safe areas)
_Not started._

### Phase 3 - Tablet experience (portrait fit, edit-mode fit, keep awake)
_Not started._

### Phase 4 - Reconnect, profile relay, pairing, install guidance, HTTPS (D3)
_Not started._
