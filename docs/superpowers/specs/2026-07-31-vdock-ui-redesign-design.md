# VDock UI Redesign — Design Spec

**Date:** 2026-07-31
**Branch:** `feat/ui-redesign`
**Status:** Awaiting review

---

## 1. Summary

Redesign VDock's interface for a 7" 1024×600 HDMI touch screen used as a secondary display, and add three animation capabilities that Elgato's Stream Deck software either can't do or does badly:

1. **Per-icon loop animations** — every button animates on its own clock
2. **Grid transitions** — a light-bar sweep plays across all buttons when the page changes
3. **Ambient deck overlay** — one continuous animation spanning the whole grid

Plus a preset library so adding an app button takes two taps instead of ten, and a wallpaper system with animated and video backgrounds.

**Guiding constraint:** the device has **no keyboard and no mouse**. Every interaction is a fingertip on glass.

---

## 2. Constraints

| Constraint | Implication |
|---|---|
| 1024×600 landscape | Vertical space is scarce; horizontal is plentiful. Left rails beat top bars. |
| Touch only, no keyboard | **No text inputs anywhere in the primary flow.** No search boxes. Browse, don't type. |
| Fingertip targets | Minimum 48px hit area (WCAG 2.1 AA is 44px; we go slightly above). |
| Secondary display | The user is looking at their main monitor most of the time. Glanceable > dense. |
| Pi-class hardware possible | Blur filters and simultaneous animations are expensive. Needs a performance tier. |
| Existing users | Profile JSON must keep loading. All changes additive and backward-compatible. |

---

## 3. Current state (verified)

Measured on commit `163fc8d`.

### 3.1 Oversized files

| File | Lines |
|---|---|
| `frontend/src/components/ButtonEditor.vue` | 3,484 |
| `frontend/src/views/DashboardView.vue` | 3,159 |
| `frontend/src/views/SettingsView.vue` | 1,658 |
| `frontend/src/components/AssetPicker.vue` | 852 |

`DashboardView.vue` contains `createPreconfiguredButton()` — a **~640-line `switch` statement** (approx. lines 854–1495) hardcoding every button preset. Adding 60 app presets here would push the file past 3,800 lines. This is the single biggest structural blocker.

### 3.2 What already works

- **Button effects (10):** glass, neumorphism, gradient, glow, neon, metallic, liquid, holographic, shadow, emissive
- **Button animations (10):** pulse, shimmer, bounce, rotate, wiggle, float, scale, slide, fade, spin
- **Animated backgrounds (~19):** 10 WebGL/canvas components via `BackgroundRenderer.vue` (Aurora, Silk, Lightning, PrismaticBurst, Iridescence, LightRays, DarkVeil, FloatingLines, FloatingLinesWave, LightPillar) plus ~9 CSS-only ones in `main.css`
- **Media buttons:** `media_url` + `media_type: 'image' | 'gif' | 'video'` — GIF and video buttons render today
- **Asset library:** ~130 animated GIFs in `public/assets/animations/gifs/buttons/`, 35 brand logos in `public/logos/`
- **Touch gestures:** long-press, double-tap, swipe (`composables/useGestures.ts`)
- **Page transitions:** `page-slide-left` / `page-slide-right`, directional, `0.28s cubic-bezier(0.4, 0, 0.2, 1)` (`DashboardView.vue:3078–3099`)
- **Accessibility:** `prefers-reduced-motion` disables all animation app-wide (`main.css`)

### 3.3 Gaps

| Gap | Evidence |
|---|---|
| Effects have **hardcoded colours** | `neon` is always `#00f2ff`, `emissive` always `#4a9eff` — every button using an effect looks identical |
| GIF **replaces** the icon | Can't have an animation behind a logo — `media_url` and `icon` are mutually exclusive in `DeckButton.vue` |
| Almost no transitions | Only **3** `<Transition>` components exist: `NotificationCenter`, `QuickSearch`, `DashboardView`. Scene switching has **zero** animation. |
| No shared easing tokens | Ad-hoc `cubic-bezier` values scattered across files |
| Keyboard-dependent UI | Search input at `DashboardView.vue:159`; `QuickSearch.vue` is a keyboard palette; `fuse.js` is a dependency purely for search |
| No video wallpaper | `BackgroundRenderer.vue` has no `<video>`; dashboard backgrounds are `background-image` only |
| Background list is a union type | `stores/settings.ts:25` — adding one background means editing the type, the renderer, and the settings dropdown |
| Effects GIF library is empty | `public/assets/animations/gifs/effects/index.json` → `{"animations": []}` |
| No grid-level animation | Nothing spans multiple buttons |

---

## 4. Design

### 4.1 Preset registry

Replace the 640-line switch with a data-driven registry.

```
frontend/src/data/presets/
├── types.ts      ButtonPreset interface
├── apps.ts       ~60 famous apps
├── system.ts     existing system/audio/media/window actions, migrated
└── index.ts      registry, category lookup, keyword match
```

```ts
interface ButtonPreset {
  id: string
  name: string
  category: PresetCategory
  brand:  { primary: string; glow?: string; text?: string }
  icon:   { type: 'logo' | 'fontawesome' | 'gif' | 'lottie'; value: string }
  effect?: EffectType          // layer 2 — animation inside the button
  loop?:   IconLoop            // per-icon animation
  action:  ButtonAction
  keywords?: string[]          // "chatgpt" also matches "gpt", "openai"
}
```

`createPreconfiguredButton(action, position)` collapses to `presetToButton(preset, position)`.

**Seed content:** the 35 existing logos in `public/logos/` become presets immediately. Israeli sites from the user's current Stream Deck layout (N12, Ynet, Walla, Mako, Sport1, ONE, Geektime, TGSpot, Lastartup, Letsai) are included in a `news` category.

**Categories:** `recent`, `ai`, `dev`, `media`, `social`, `news`, `system`.

### 4.2 Button layer model

A button is a **stack**, not a flat object. Each layer is independently configurable — this is the core of the "modularity and freedom" requirement, and it's what makes flames render *behind* a rocket rather than instead of it.

```
Layer 4   Label          text
Layer 3   Icon           logo / glyph / GIF / Lottie   + own loop animation
Layer 2   Effect         fire · plasma · particles · aurora · scanline · rain
Layer 1   Fill           none · solid · gradient · brand tint · image · video
──────────
Container Behaviour      pulse · float · breathe · tilt   (whole button)
```

```ts
interface ButtonLayers {
  fill?:   { type: 'none'|'solid'|'gradient'|'tint'|'image'|'video'; value?: string }
  effect?: { type: EffectType; tint: 'brand' | string; intensity?: number }
  icon?:   { type: IconType; value: string; loop?: IconLoop; size?: number }
  label?:  { text: string; secondary?: string }
  behaviour?: BehaviourType
}
```

**Backward compatibility:** existing buttons have no `layers` key. `DeckButton.vue` reads `button.layers` when present and falls back to the current `icon` / `media_url` / `style` fields when absent. A one-way migration helper upgrades profiles on save.

### 4.3 Brand-parametric effects

The fix for "animations aren't tied to the app brand." Effects read a per-button CSS custom property instead of hardcoded hex values:

```css
.deck-button { --btn-brand: <from layers.effect.tint or brand.primary>; }

.fx-glow {
  background:  color-mix(in srgb, var(--btn-brand) 12%, #0d0d0d);
  border:      1px solid color-mix(in srgb, var(--btn-brand) 40%, transparent);
  box-shadow:  0 0 16px color-mix(in srgb, var(--btn-brand) 35%, transparent);
}
```

One effect class serves every brand. Netflix glows red, Spotify green, Discord blurple — and any custom colour the user picks works too. Applies to `glow`, `neon`, `emissive`, `shimmer`, and the new effects.

`color-mix()` has full support in Chrome/Edge 111+ and Firefox 113+. VDock ships Electron, so the runtime is known-good. A Sass-generated fallback is not required.

### 4.4 Animation system — three independent layers

These compose; all three can run simultaneously.

| Layer | Trigger | Scope | Config location |
|---|---|---|---|
| **Per-icon loop** | continuous, own clock | one button | `layers.icon.loop` |
| **Grid transition** | once, on page/scene change | all buttons | scene setting |
| **Ambient overlay** | continuous | all buttons | scene setting |

#### Per-icon loops
`squash`, `bob`, `spin`, `pulse`, `swing`, `flip`, `jump`. Each icon gets a deterministic phase offset derived from its index (`i * 137 % 1900` ms) so neighbours never sync — this is what produces the organic look in the reference video.

#### Grid transitions
Fires on page or scene change. Sequence, matching the Elgato reference:

1. **0–220ms** — current faces scale out and fade
2. **staggered** — a bright vertical light bar sweeps each key, 620ms per key
3. **+180ms after each bar** — new face scales in from 1.18×

Styles: `light-bar` (default), `flip`, `iris`, `cascade`, `glitch`, `dissolve`.
Stagger: `by-column` (default), `by-row`, `diagonal`, `random`, `none`.

#### Ambient overlay
One animation spanning the entire grid. **Implementation:** each key contains a copy of the same animated layer, translated by its own grid offset:

```
transform: translate(-col × (cellW + gap), -row × (cellH + gap))
```

All keys render their slice of one continuous animation, perfectly aligned. Identical CSS animations started in the same frame stay in sync.

Two modes:
- **`keys`** — light lands only on buttons; gutters stay dark (authentic hardware look)
- **`full-bleed`** — a single layer over the whole grid including gutters. *Only possible because VDock is a screen, not 15 separate LCDs.*

Styles: `light-sweep`, `aurora`, `plasma`, `rainbow`, `fire-wall`, `scanline`, `rain`. Plus a tap-triggered ripple from the touch point.

#### Easing tokens
Replace ad-hoc values with three tokens in `main.css`:

```css
--ease-out:    cubic-bezier(0.22, 1, 0.36, 1);    /* entrances */
--ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1); /* overshoot */
--ease-io:     cubic-bezier(0.4, 0, 0.2, 1);      /* slides */
```

Existing page slide retunes from 280ms → 340ms with travel reduced to 34%.

### 4.5 Touch-first UI — no keyboard

**Every text input is removed from the primary flow.**

| Remove | Replace with |
|---|---|
| `Search actions…` input (`DashboardView.vue:159`) | Category rail + icon grid |
| `QuickSearch.vue` keyboard palette | Recent tab in the picker |
| Blind background dropdown | Wallpaper gallery with live animated thumbnails |

**Quick Add picker** (`components/QuickAddPicker.vue`) — opens on tapping an empty slot:
- Vertical icon rail on the left (7 categories), grid on the right
- `Recent` is the default tab — the user's usual apps are zero taps away
- 5×3 = 15 apps visible, swipe horizontally for more, dot indicators
- One tap adds a fully-configured button: icon, brand colour, effect, action
- Springs up in 440ms with icons staggering in at 22ms

Text entry survives only where genuinely unavoidable — a custom URL or shell command — and there it opens an on-screen keypad rather than assuming a hardware keyboard.

`fuse.js` can be dropped from dependencies once `QuickSearch.vue` is removed, unless retained for desktop-mode editing.

### 4.6 Wallpaper system

Convert `backgroundPreference` from a union type to a registry, mirroring the preset pattern:

```ts
interface Wallpaper {
  id: string
  name: string
  kind: 'css' | 'webgl' | 'image' | 'video' | 'gif'
  category: 'animated' | 'gradient' | 'pattern' | 'custom'
  component?: string       // for webgl
  src?: string             // for image/video/gif
  cost: 'low' | 'medium' | 'high'   // drives Performance mode
}
```

Additions:
- **`VideoWallpaper.vue`** — looping, muted, `playsinline` `.mp4`/`.webm`, same slot as the WebGL backgrounds. This is the Wallpaper-Engine-style capability that's missing today.
- **Animated GIF/APNG** wallpapers
- **Upload** via the existing `/api/upload` route
- **Touch gallery** with live animated thumbnails — nothing chosen blind
- **Per-scene wallpapers**, with an optional per-page override

Video auto-pauses on `document.visibilitychange` and when the window loses focus.

### 4.7 Layout shell

Approved layout (option C):

```
┌────────────────────────────────────────────┬────────┐
│ ▸ thin header: avatar · scene name · edit  │ Jul 31 │
├────────────────────────────────────────────┤ ────── │
│                                            │ 22:37  │
│         5 × 3 button grid                  │ ────── │
│         brand-glow buttons                 │  31°   │
│                                            │ Tel Av │
├────────────────────────────────────────────┤        │
│ ● 1  2  3        [Sites][AI][Dev][+]       │        │
└────────────────────────────────────────────┴────────┘
```

- **Thin header** — avatar, current scene name, edit toggle. Auto-hides; swipe down or tap to reveal.
- **Footer** — page dots on the left, scene pills on the right. Both reachable by thumb.
- **Right widget column** — clock, weather, calendar, matching the user's existing Stream Dock layout.

---

## 5. Component decomposition

### `DashboardView.vue` 3,159 → ~300

| New file | Responsibility |
|---|---|
| `components/dashboard/DeckHeader.vue` | Thin auto-hiding header |
| `components/dashboard/DeckFooter.vue` | Page dots + scene pills |
| `components/dashboard/WidgetColumn.vue` | Clock / weather / calendar |
| `components/dashboard/EditSidebar.vue` | Extracted edit panel |
| `components/dashboard/DeckOverlay.vue` | Ambient overlay layer |
| `components/QuickAddPicker.vue` | Touch app picker |
| `composables/useButtonActions.ts` | Click / edit / copy / delete handlers |
| `composables/useGridTransition.ts` | Transition orchestration |

### `ButtonEditor.vue` 3,484 → ~250 + panels

Split into tabbed panels mirroring the layer model — `FillPanel`, `EffectPanel`, `IconPanel`, `ActionPanel`, `AdvancedPanel`. The tab structure *is* the layer stack, so the editor teaches the model.

---

## 6. Performance

A Raspberry Pi will not run blur + WebGL + 15 icon loops + an overlay at 60fps.

**Performance mode** in Settings, three tiers:

| Tier | Behaviour |
|---|---|
| **Full** (default on desktop) | Everything enabled |
| **Balanced** | Overlay capped at 30fps, blur radii halved, `cost: high` wallpapers hidden |
| **Performance** (default on Pi) | Overlay off, icon loops off, transitions reduced to fade, CSS wallpapers only |

Rules that apply in every tier:
- Animate `transform` and `opacity` only; never `width`/`height`/`left`/`top`
- `will-change` applied during transitions, removed after
- Video and WebGL pause when the window is hidden
- `prefers-reduced-motion` overrides everything — unchanged from today

---

## 7. Phasing

Each phase leaves the app working and shippable.

| Phase | Scope | Depends on |
|---|---|---|
| **1 · Foundations** | Easing tokens; brand-parametric effects (`--btn-brand`); page-slide retune | — |
| **2 · Preset registry** | `data/presets/`, migrate the 640-line switch, ~60 app presets | — |
| **3 · Layer model** | `ButtonLayers`, `DeckButton.vue` rewrite, backward-compat fallback, 7 CSS effects | 1 |
| **4 · Animation system** | Per-icon loops, grid transitions, ambient overlay, `DeckOverlay.vue` | 1, 3 |
| **5 · Touch UI** | `QuickAddPicker.vue`, remove all search inputs, decompose `DashboardView` | 2 |
| **6 · Layout shell** | Thin header, footer, widget column | 5 |
| **7 · Wallpapers** | Registry, `VideoWallpaper.vue`, touch gallery, per-scene | 5 |
| **8 · Editor** | Decompose `ButtonEditor.vue` into layer panels | 3 |
| **9 · Performance** | Three-tier mode, profiling on target hardware | 4, 7 |

Phases 1–4 deliver the visible payoff. 5–9 are structural and can slip without losing the headline features.

---

## 8. Decisions taken

Made to unblock implementation. Each is cheap to reverse — flag any you disagree with.

| # | Decision | Rationale |
|---|---|---|
| D1 | **Picker layout B** — icon rail on the left | Landscape screen has horizontal space to spare and scarce vertical space. Rail is always visible, targets are larger. |
| D2 | **CSS effects first, Lottie in a later phase** | CSS effects are 0 KB, recolour to brand automatically, and are the cheapest option on a Pi. Lottie adds a ~250 KB dependency for content we don't have yet. Revisit after Phase 4. |
| D3 | **Overlay and transition are per-scene**, with a global default | Scenes are the natural unit — Gaming gets fire, AI gets plasma. A global default avoids configuring every scene. |
| D4 | **Wallpaper per-scene, optional per-page override** | Matches D3. Per-page alone would be tedious across many pages. |
| D5 | **Keep GIF/video buttons** | Already works, and the 130-GIF library plus real app logos are best served by raster. Don't build new features on it. |
| D6 | **Backward compatibility via fallback, not migration-on-load** | Profiles upgrade lazily on next save. No risky bulk rewrite of user data. |

---

## 9. Open for review

1. **D1 — picker A or B.** Mockups of both are in `.superpowers/brainstorm/*/content/picker-touch.html`.
2. **Israeli site presets** — is the list from the current Stream Deck layout complete, or are there others?
3. **Does `QuickSearch.vue` get deleted or kept for desktop editing?** Deleting it lets `fuse.js` go too.
4. **Target hardware** — is VDock ever run *on* the Pi, or only displayed on the 7" screen while the backend runs on the Windows machine? This decides whether Performance mode defaults matter at all.

---

## 10. Out of scope

- Backend / Flask action changes — the redesign is frontend-only
- New action types beyond what exists
- Multi-device sync
- Authentication changes
- Mobile phone layouts — this targets 1024×600 landscape specifically

---

## 11. Reference mockups

Interactive prototypes built during design, in `.superpowers/brainstorm/<session>/content/` (gitignored):

| File | Shows |
|---|---|
| `layout.html` | Three layout options; C selected |
| `motion.html` | Six motion demos with real timings |
| `picker-touch.html` | Touch pickers A and B |
| `animated-buttons.html` | Eight CSS effects, tier comparison, wallpaper gallery |
| `layers.html` | Interactive layer-stack builder |
| `overlay.html` | Ambient overlay, keys-only vs full-bleed |
| `transitions.html` | Grid transitions + per-icon loops |
