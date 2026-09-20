# Competitive Analysis — Stream Deck Alternatives

Research into Elgato Virtual Stream Deck, Touch Portal, WebDeck, and
VSDinside Stream Dock M18 — what each does, strengths/weaknesses, and what
VDock should borrow.

---

## The products

### 1. Elgato Virtual Stream Deck

**What it is:** A software-only Stream Deck that lives on your screen —
unlimited virtual keys, customizable shapes/layouts, draggable action
palette. Free, but **bundled**: requires owning an Elgato/Corsair device
(Stream Deck, Scimitar mouse, Xeneon touchscreen) to unlock.

**Signature features:**
- **Summon to cursor** — a global hotkey pops a floating mini-deck at your
  mouse position; press a key, it vanishes. The standout interaction.
- Pin a deck window anywhere on screen; mouse or touch.
- Full Stream Deck ecosystem behind it — Marketplace plugins, per-app
  profiles that auto-switch, folders, dials (on SD+), multi-actions.

| Pros | Cons |
|---|---|
| Summon-to-cursor is genuinely innovative — deck appears only when needed | Requires buying Elgato hardware to unlock |
| Marketplace plugin/profile ecosystem is unmatched | Closed ecosystem, account/store dependency |
| Polished UX, per-app auto-profiles | Windows/Mac only, no free tier |
| Keys can be any shape/layout, not just a grid | — |

### 2. Touch Portal

**What it is:** Desktop server (Windows/Mac) + mobile app — your phone or
old tablet becomes the deck. Free tier is deliberately crippled (4×2 grid,
2 pages, no plugins); **Pro upgrade $13.99 one-time** unlocks the real app.
Separate paid upgrades for multiple devices, etc.

**Signature features:**
- **Multi-action macro buttons** — one press runs a sequence of actions.
- **Logic layer** — Values (global states), Events, toggle/radio/master-slave
  buttons: buttons that behave differently depending on current state.
- **Sliders** — volume, brightness etc. as draggable controls, not buttons.
- Huge community asset DB: pages, icon packs, plugins (OBS, Spotify,
  Discord, Philips Hue, smart home, game telemetry via SimHub, etc.).
- Revives old devices — Android 5.0+/iOS 12+.

| Pros | Cons |
|---|---|
| Deepest logic/automation model of the four (states, events, conditionals) | Free tier is a demo — 4×2 grid, 2 pages, no plugins |
| Sliders and on-press/on-release event separation | UX is dense and desktop-editor-centric; steep learning curve |
| Massive community plugin/page/icon ecosystem | Fragmented upgrades (Pro, multiple devices, packs) |
| Works on ancient phones/tablets | License locked per app store (iOS ≠ Android) |

### 3. WebDeck (open source)

**What it is:** Flask app you host on your PC; any browser + touchscreen
device on the network becomes the deck. Scan a QR code on the tray icon →
your phone is connected. GPLv3, ~960 stars, Windows-only today.

| Pros | Cons |
|---|---|
| Zero-install client — any device with a browser is a deck | Windows-only host; Linux/Mac "planned" for years |
| QR-code pairing — frictionless device onboarding | No logic/multi-action layer; simpler action model |
| Free and open source, no account | Single-maintainer pace; no marketplace/ecosystem |
| Closest architectural sibling to VDock (Flask + web UI) | Minimal design polish vs. VDock |

### 4. VSDinside Stream Dock M18

**What it is:** Budget hardware deck — 15 LCD keys + **3 tactile buttons**
+ RGB light strip, positioned as the anti-Elgato on price and openness.

| Pros | Cons |
|---|---|
| Tactile keys alongside screen keys — physical confirmation | It's hardware — most ideas don't transfer to VDock |
| RGB strip doubles as ambient status feedback | Unproven software depth/ecosystem |
| Much cheaper than Elgato | Small brand, long-term support question |

**Transferable ideas:** press feedback that feels physical (sound/animation
on tap), a persistent ambient status element (the RGB strip → a status
edge/bar on the dashboard).

---

## Where VDock already wins

- **Free everything** — no hardware unlock (Elgato), no crippled free tier
  (Touch Portal), no store account.
- **AI-agent integration nobody has** — Claude Code hooks, agent attention
  alerts, dev-focused action packs (VS Code, JetBrains, Devin, `gh`).
- **Ambient/dashboard layer** — screensaver with live widgets (weather,
  news, sports, markets, world clock) makes it useful when *not* touching.
- **Onboarding** — tutorial tour, annotated help, starter scenes out of box.
- Open source, self-hosted, no telemetry.

## Gaps worth closing — recommended additions

Ranked by impact-per-effort against what competitors proved users want:

### Tier 1 — high impact, fits existing architecture

1. **Multi-action macro buttons** (Touch Portal's core strength).
   One button → sequenced steps with optional delays: `hotkey → wait 300ms
   → open url → hotkey`. The action model already exists; this is a list +
   runner, plus a step editor in ButtonEditor. *Biggest single gap.*

2. **Toggle/stateful buttons** (Touch Portal logic, lite).
   A button with on/off visual state: mic mute shows red when muted, a
   "focus mode" button stays lit while active. Scope it modestly:
   two-state buttons with per-state icon/color/label + state-aware action
   (press A vs press B). Full if/else logic is a stretch goal, not v1.

3. **Slider controls** (Touch Portal).
   Volume and brightness as draggable sliders on the deck — on a 7" touch
   panel this is the most natural control type we lack. Could live as a
   new docked-sidebar element or a dedicated cell type.

4. **QR-code remote connect + mobile layout** (WebDeck's whole product).
   VDock is already a Flask-served web app — a phone on the LAN can *already*
   load it. What we lack: a "Connect a device" QR in Settings (URL + port)
   and a phone-portrait layout. Turns "dedicated panel" into "panel +
   whatever device is in your hand" for free.

5. **Summon/quick deck overlay** (Virtual Stream Deck's signature).
   Global hotkey → compact deck popup at cursor/focused corner. We already
   have overlay machinery (agent alert, screensaver, tour) — a fourth
   overlay kind is cheap and very demo-able.

### Tier 2 — solid additions

6. **Press feedback** (M18 tactile analog) — optional click sound + press
   animation scale/haptic-style bounce on tap. Cheap, makes the panel feel
   physical.
7. **Scene/profile export & import** — share a scene as a JSON pack
   (buttons + styling), import from file/URL. Seed a community library the
   way Touch Portal's asset DB works — starts as simple file sharing.
8. **On-press vs on-release events** — push-to-talk style: hold = action
   engaged, release = disengaged. Pairs naturally with toggle buttons.
9. **Ambient status strip** (M18's RGB strip) — thin edge bar showing
   agent-alert/notification state as ambient color.

### Tier 3 — stretch / probably skip

10. **Conditional logic engine** (Touch Portal Values/Events) — powerful
    but heavy; revisit after toggle buttons prove the appetite.
11. **Plugin marketplace** — real ecosystem play; only worth it with users.
    Templates + import/export covers 80% today.
12. **Hardware dial equivalents** — virtual rotary knobs; sliders cover the
    use case on a pure touch panel.

## Bottom line

VDock's moat vs. all four: **free + AI-agent-native + ambient dashboard +
zero lock-in**. The biggest capability gaps are all in the *action model* —
multi-actions, button state, sliders — plus the two zero-cost wins our
architecture already enables (QR remote access, summon overlay). None
require a marketplace, an account, or new hardware.
