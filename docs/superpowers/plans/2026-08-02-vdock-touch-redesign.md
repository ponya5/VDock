# VDock Touch Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 7 touch UX issues on the 7" 1024×600 screen: remove duplicate scene pills from footer, rebuild header as swipe-down reveal with large touch targets, disable accidental pinch resize, add screensaver overlay, and remove the persistent widget sidebar.

**Architecture:** Each task is self-contained and modifies exactly one component or store. The screensaver is a new fixed-position Vue overlay driven by an idle timer in DashboardView. The header hides itself after 5 s of inactivity using a local ref timer — no global state beyond the existing `settingsStore.showHeader` flag.

**Tech Stack:** Vue 3 Composition API, TypeScript, Pinia, Electron, existing `useSwipe` / `useTouchActionDrag` composables.

---

## File Map

| File | Action |
|---|---|
| `frontend/src/stores/settings.ts` | Add `screensaverTimeout`, default `showHeader` to `false` |
| `frontend/src/components/DeckFooter.vue` | Remove `scene-pills` block + its wrapper div |
| `frontend/src/components/DeckGrid.vue` | Remove `usePinch` call + `pinchScale` ref |
| `frontend/src/components/DeckHeader.vue` | Remove Full Screen + Hide buttons; upsize avatar / pills / buttons; add 5 s auto-hide timer + progress bar; preserve swipe-down reveal; add swipe-up dismiss |
| `frontend/src/components/EditSidebar.vue` | Verify touch drag-and-drop wiring; fix any issues found |
| `frontend/src/views/DashboardView.vue` | Remove `<WidgetColumn>`; add `<ScreenSaver>` + idle timer |
| `frontend/src/components/ScreenSaver.vue` | **New** — fullscreen clock + weather + next-event overlay |
| `frontend/src/views/SettingsView.vue` | Add screensaver timeout slider in Display sub-tab |

---

## Task 1: Settings store — screensaverTimeout + showHeader default false

**Files:**
- Modify: `frontend/src/stores/settings.ts`

- [ ] **Step 1: Add the `screensaverTimeout` ref** directly after `weatherManualCity`:

```typescript
// in useSettingsStore, after const weatherManualCity = ref('')
const screensaverTimeout = ref(120) // seconds; 0 = disabled
```

- [ ] **Step 2: Change `showHeader` default from true to false**

```typescript
// Change:
const showHeader = ref(true)
// To:
const showHeader = ref(false)
```

- [ ] **Step 3: Update `loadSettings` to load `screensaverTimeout` and fix `showHeader` default**

In the `loadSettings` function, after `weatherManualCity.value = settings.weatherManualCity || ''` add:

```typescript
screensaverTimeout.value = settings.screensaverTimeout !== undefined ? settings.screensaverTimeout : 120
```

And change the `showHeader` load line from:
```typescript
showHeader.value = settings.showHeader !== false
```
To:
```typescript
showHeader.value = settings.showHeader === true
```

- [ ] **Step 4: Update `saveSettings` to persist `screensaverTimeout`**

In the `saveSettings` function object, after `weatherManualCity: weatherManualCity.value` add:
```typescript
screensaverTimeout: screensaverTimeout.value,
```

- [ ] **Step 5: Add `screensaverTimeout` to the watch array and expose it**

In the `watch([...], ...)` array at line 135, add `screensaverTimeout` to the array.

In the `return { ... }` at the bottom of the store, add:
```typescript
screensaverTimeout,
```

- [ ] **Step 6: Commit**
```bash
git add frontend/src/stores/settings.ts
git commit -m "feat: add screensaverTimeout setting, default showHeader to false"
```

---

## Task 2: Footer — remove duplicate scene pills

**Files:**
- Modify: `frontend/src/components/DeckFooter.vue`

- [ ] **Step 1: Remove the `footer-right` div and its contents**

In the template, remove this entire block:
```html
<!-- Right Side: Scene Pills -->
<div class="footer-right">
  <div v-if="scenes.length > 0" class="scene-pills">
    <button
      v-for="(scene, idx) in scenes"
      :key="scene.id"
      class="scene-pill touch-target"
      :class="{ active: currentSceneIndex === idx }"
      @click="emit('setScene', idx)"
    >
      <FontAwesomeIcon v-if="scene.icon" :icon="scene.icon.split(':')" class="scene-pill-icon" />
      <span>{{ scene.name }}</span>
    </button>
  </div>
</div>
```

- [ ] **Step 2: Remove unused props and emit from the script**

Remove from the `Props` interface: `scenes`, `currentSceneIndex`.
Remove from `defineProps<Props>()`: those fields are now gone from the interface.
Remove from `emit` definition: `setScene: [index: number]`.

- [ ] **Step 3: Remove unused CSS**

Delete these CSS rule blocks from `<style scoped>`:
- `.footer-right { ... }`
- `.scene-pills { ... }`
- `.scene-pill { ... }`
- `.scene-pill:hover { ... }`
- `.scene-pill.active { ... }`
- `.scene-pill-icon { ... }`

- [ ] **Step 4: Update min-height to 44 px**

In `.deck-footer`, change `height: 52px` to `min-height: 44px`.

- [ ] **Step 5: Fix DashboardView.vue — remove the scene props passed to DeckFooter**

In `DashboardView.vue`, find the `<DeckFooter>` element and remove:
```html
:scenes="currentProfile?.scenes || []"
:current-scene-index="currentSceneIndex"
@set-scene="setScene"
```

- [ ] **Step 6: Commit**
```bash
git add frontend/src/components/DeckFooter.vue frontend/src/views/DashboardView.vue
git commit -m "fix: remove duplicate scene pills from footer"
```

---

## Task 3: DeckGrid — disable accidental pinch resize

**Files:**
- Modify: `frontend/src/components/DeckGrid.vue`

- [ ] **Step 1: Remove the `pinchScale` ref and the `usePinch` call**

Find and delete these lines (around line 148–153):
```typescript
const pinchScale = ref(1)
usePinch(gridRef, {
  onPinch: (scale) => {
    pinchScale.value = Math.max(0.6, Math.min(2.0, scale))
  }
})
```

- [ ] **Step 2: Fix `gridStyle` to not use `pinchScale`**

In the `gridStyle` computed, find:
```typescript
const transformScale = props.buttonSize * pinchScale.value
```
Change to:
```typescript
const transformScale = props.buttonSize
```

- [ ] **Step 3: Remove the `usePinch` import**

In the import line `import { useSwipe, usePinch, useLongPress } from '@/composables/useGestures'`, remove `usePinch`:
```typescript
import { useSwipe, useLongPress } from '@/composables/useGestures'
```

- [ ] **Step 4: Verify no TypeScript errors**
```bash
cd frontend && npx vue-tsc --noEmit
```
Expected: no errors related to `pinchScale` or `usePinch`.

- [ ] **Step 5: Commit**
```bash
git add frontend/src/components/DeckGrid.vue
git commit -m "fix: remove accidental pinch-resize gesture from DeckGrid"
```

---

## Task 4: DeckHeader — rebuild layout for 7" touch

**Files:**
- Modify: `frontend/src/components/DeckHeader.vue`

This task covers HTML structure + CSS only. Timer logic is Task 5.

- [ ] **Step 1: Remove Full Screen and Hide buttons from template**

In the `<div class="header-right">` block, delete:
```html
<button
  class="btn-fullscreen btn-12 animate-tap"
  @click="handleToggleFullscreen"
  ...
>...</button>
<div class="header-right-separator"></div>
<button
  class="btn-hide-header btn-12 animate-tap"
  @click="settingsStore.showHeader = false"
  ...
>...</button>
<div class="header-right-separator"></div>
```

Also remove the first separator after them (the one before Profiles button).

- [ ] **Step 2: Strip text labels — make buttons icon-only**

Change the three remaining buttons (Profiles, Edit, Settings) to icon-only:
```html
<button class="btn-icon-circle animate-tap" @click="emit('navigateProfiles')" title="Profiles" aria-label="Profiles">
  <FontAwesomeIcon :icon="['fas', 'users']" />
</button>
<button
  :class="['btn-icon-circle animate-tap', { 'edit-active': isEditMode }]"
  @click="emit('toggleEdit')"
  title="Toggle Edit Mode"
  aria-label="Toggle Edit Mode"
>
  <FontAwesomeIcon :icon="['fas', isEditMode ? 'eye' : 'edit']" />
</button>
<button class="btn-icon-circle animate-tap" @click="emit('navigateSettings')" title="Settings" aria-label="Settings">
  <FontAwesomeIcon :icon="['fas', 'cog']" />
</button>
```

- [ ] **Step 3: Remove unused script references**

Remove `handleToggleFullscreen`, `isFullscreenActive`, `refreshFullscreenState`, `handleFullscreenChange` functions and their `onMounted`/`onUnmounted` registrations. Remove the `toggleFullscreen` and `isFullscreen` imports from `useElectron`.

- [ ] **Step 4: Replace CSS with touch-sized rules**

In `<style scoped>`, replace `.deck-header`, `.header-right .btn-12`, `animate-tap`, avatar sizes, and add the new `.btn-icon-circle` rule. Replace the entire style block with:

```css
.deck-header-wrapper {
  width: 100%;
  z-index: 100;
}

.header-hidden {
  height: 0;
  overflow: visible;
}

.header-reveal-trigger {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 16px;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  cursor: pointer;
  z-index: 110;
}

.reveal-handle {
  width: 60px;
  height: 6px;
  background-color: rgba(255, 255, 255, 0.25);
  border-bottom-left-radius: 4px;
  border-bottom-right-radius: 4px;
  transition: background-color 0.2s ease;
}

.header-reveal-trigger:hover .reveal-handle,
.header-reveal-trigger:active .reveal-handle {
  background-color: var(--color-primary, #007aff);
}

.deck-header {
  position: relative;
  width: 100%;
  min-height: 90px;
  padding: 0.6rem 1rem;
  box-sizing: border-box;
  overflow: visible;
}

.header-background {
  position: absolute;
  inset: 0;
  background: rgba(8, 8, 28, 0.92);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  z-index: 0;
}

.header-content {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  min-height: 68px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  min-width: 0;
  flex: 1;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex-shrink: 0;
}

.profile-avatar-container {
  position: relative;
  width: 56px;
  height: 56px;
  flex-shrink: 0;
}

.profile-avatar,
.profile-avatar-placeholder {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  display: block;
}

.profile-avatar {
  object-fit: cover;
  border: 2px solid rgba(255, 255, 255, 0.3);
}

.profile-avatar-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.13);
  border: 2px solid rgba(255, 255, 255, 0.28);
  color: #fff;
  font-size: 1.5rem;
}

.avatar-status-indicator {
  position: absolute;
  bottom: 2px;
  right: 2px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #2ecc71;
  border: 2px solid rgba(0, 0, 0, 0.5);
}

.animate-tap {
  touch-action: manipulation;
}

/* Large circular icon buttons */
.btn-icon-circle {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
  border: 2px solid rgba(255, 255, 255, 0.18);
  color: rgba(255, 255, 255, 0.9);
  font-size: 1.5rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s ease, box-shadow 0.2s ease;
  touch-action: manipulation;
  flex-shrink: 0;
}

.btn-icon-circle:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.15);
}

.btn-icon-circle:active:not(:disabled) {
  background: rgba(255, 255, 255, 0.22);
}

.btn-icon-circle.edit-active {
  background: linear-gradient(135deg, rgba(52, 152, 219, 0.35), rgba(52, 152, 219, 0.7));
  border-color: rgba(52, 152, 219, 0.65);
  box-shadow: 0 0 18px rgba(52, 152, 219, 0.4);
}

/* Auto-hide countdown bar */
.autohide-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 4px;
  background: linear-gradient(90deg, var(--color-primary, #007aff), rgba(0, 122, 255, 0.25));
  border-radius: 0 2px 2px 0;
  transition: width 0.1s linear;
  pointer-events: none;
}

/* Enhanced scene nav sizing */
.enhanced-scene-nav {
  --pill-height: 56px;
}
```

- [ ] **Step 5: Add progress bar element to header template**

Inside `<header v-else class="deck-header dashboard-header">`, before the closing `</header>`, add:
```html
<div class="autohide-progress" :style="{ width: progressWidth + '%' }"></div>
```

And add `progressWidth` as a prop/data: this will be driven by the timer in Task 5 (`ref(100)`).

- [ ] **Step 6: Verify no TS errors**
```bash
cd frontend && npx vue-tsc --noEmit
```

- [ ] **Step 7: Commit**
```bash
git add frontend/src/components/DeckHeader.vue
git commit -m "feat: rebuild DeckHeader with 90px height and 64px touch buttons"
```

---

## Task 5: DeckHeader — auto-hide timer + swipe-up dismiss

**Files:**
- Modify: `frontend/src/components/DeckHeader.vue`

- [ ] **Step 1: Add timer refs to script setup**

After the existing refs at the top of `<script setup>`, add:
```typescript
const headerRef = ref<HTMLElement | null>(null)
const progressWidth = ref(100)
let autohideTimer: ReturnType<typeof setInterval> | null = null
let autohideRemainingMs = 5000
const AUTOHIDE_MS = 5000
const TICK_MS = 50
```

- [ ] **Step 2: Add ref to the header element in template**

Change `<header v-else class="deck-header dashboard-header">` to:
```html
<header v-else ref="headerRef" class="deck-header dashboard-header">
```

- [ ] **Step 3: Add timer start/stop/reset functions**

```typescript
function startAutohide() {
  stopAutohide()
  autohideRemainingMs = AUTOHIDE_MS
  progressWidth.value = 100
  autohideTimer = setInterval(() => {
    autohideRemainingMs -= TICK_MS
    progressWidth.value = Math.max(0, (autohideRemainingMs / AUTOHIDE_MS) * 100)
    if (autohideRemainingMs <= 0) {
      stopAutohide()
      settingsStore.showHeader = false
    }
  }, TICK_MS)
}

function stopAutohide() {
  if (autohideTimer) {
    clearInterval(autohideTimer)
    autohideTimer = null
  }
}

function resetAutohide() {
  autohideRemainingMs = AUTOHIDE_MS
  progressWidth.value = 100
}
```

- [ ] **Step 4: Watch `showHeader` to start/stop the timer**

```typescript
import { ref, watch, onMounted, onUnmounted } from 'vue'

watch(() => settingsStore.showHeader, (visible) => {
  if (visible) {
    startAutohide()
  } else {
    stopAutohide()
  }
})
```

- [ ] **Step 5: Reset timer on button tap — add `@pointerdown="resetAutohide"` to header-right**

In the template, on the `<div class="header-right">` element add:
```html
<div class="header-right" @pointerdown="resetAutohide">
```

- [ ] **Step 6: Confirm swipe-down reveal is preserved**

The existing `DeckHeader.vue` (lines ~161–167) already has:
```typescript
useSwipe(triggerRef, {
  onSwipeEnd: (direction) => {
    if (direction === 'DOWN') {
      revealHeader()
    }
  }
})
```
And `revealHeader()` sets `settingsStore.showHeader = true`. Confirm this code is still present and untouched after Task 4 edits. Do NOT remove it. If it was accidentally deleted in Task 4, restore it now.

- [ ] **Step 7: Add swipe-up on header to dismiss**

In `onMounted`, after the existing code, add:
```typescript
useSwipe(headerRef, {
  threshold: 40,
  onSwipeEnd: (direction) => {
    if (direction === 'UP') {
      stopAutohide()
      settingsStore.showHeader = false
    }
  }
})
```

- [ ] **Step 8: Clean up timer on unmount**

Replace or update `onUnmounted` to be:
```typescript
onUnmounted(() => {
  stopAutohide()
})
```

(The `fullscreenchange` listener was removed in Task 4 along with the fullscreen logic.)

- [ ] **Step 9: Commit**
```bash
git add frontend/src/components/DeckHeader.vue
git commit -m "feat: DeckHeader swipe-down reveal with 5s auto-hide and swipe-up dismiss"
```

---

## Task 6: Touch drag-and-drop — verify and fix

**Files:**
- Modify (only if broken): `frontend/src/components/EditSidebar.vue`, `frontend/src/components/DeckGrid.vue`

The infrastructure is already implemented: `EditSidebar.vue` calls `bindTouchDragSource` on each action item via `registerTouchDragSources()`, and `DeckGrid.vue` listens for the `vdock-touch-drop` custom event and emits `actionDrop`. This task verifies end-to-end that it works in the running Electron app, and patches anything broken.

- [ ] **Step 1: Run the app in edit mode and test long-press drag**

Start the dev server (`npm run dev` in `frontend/`) and open the Electron window. Enter edit mode (tap the pencil icon after swiping down for the header). Long-press (≥ 350 ms) an action item in the sidebar — e.g. "Volume Up". Verify:
  - A ghost clone of the item follows your finger.
  - Dragging over an empty grid cell highlights it.
  - Lifting your finger drops the action onto the cell.

- [ ] **Step 2: If ghost does NOT appear — check `touch-action: none` on action items**

Open `EditSidebar.vue`. Confirm `.action-item` has `touch-action: none` in the scoped CSS. If missing, add:
```css
.action-item {
  touch-action: none;
}
```

- [ ] **Step 3: If drop lands but action is NOT added to grid — add a console.log in DeckGrid**

In `DeckGrid.vue`, inside `handleGlobalTouchDrop`, add temporarily:
```typescript
console.log('[VDock] touch-drop received', payload, dropPosition)
```
Run again. If logged but no button appears, check that `props.isEditMode` is `true` at the time of the drop event. If the guard is the problem, the event fires before `isEditMode` is set — no fix needed (user must be in edit mode).

- [ ] **Step 4: Remove diagnostic logs**

- [ ] **Step 5: Commit (only if changes were made)**
```bash
git add frontend/src/components/EditSidebar.vue frontend/src/components/DeckGrid.vue
git commit -m "fix: verify and patch touch drag-and-drop from sidebar to grid"
```

---

## Task 7: Settings navigation fix  

**Files:**
- Modify: `frontend/src/components/DeckHeader.vue`

The Settings button emits `navigateSettings` → `router.push('/settings')`. Most likely cause: 300 ms touch delay. The fix is `touch-action: manipulation` on the button (already added globally to `.animate-tap` and `.btn-icon-circle` in Task 4). If still broken after that, follow the diagnostic steps below.

- [ ] **Step 1: Confirm `touch-action: manipulation` is on the settings button**

The `.btn-icon-circle` CSS added in Task 4 already includes `touch-action: manipulation`. Verify the Settings button uses that class. It should be:
```html
<button class="btn-icon-circle animate-tap" @click="emit('navigateSettings')" ...>
```

- [ ] **Step 2: Add diagnostic log temporarily and test**

In `DashboardView.vue`, change:
```typescript
@navigate-settings="router.push('/settings')"
```
To a method:
```typescript
@navigate-settings="handleNavigateSettings"
```

And add to the script:
```typescript
function handleNavigateSettings() {
  console.log('[VDock] Settings button tapped, navigating...')
  router.push('/settings')
}
```

Run the app, tap Settings, check the Electron devtools console (`Ctrl+Shift+I`).

- [ ] **Step 3: If console.log fires but navigation fails — check router guards**

Open `frontend/src/router/index.ts`. Look for any `beforeEach` guard that might be blocking. If found, add a `console.log` inside it:
```typescript
router.beforeEach((to, from, next) => {
  console.log('[Router]', from.path, '→', to.path)
  next()
})
```

- [ ] **Step 4: Remove diagnostic logs once fixed**
```typescript
function handleNavigateSettings() {
  router.push('/settings')
}
```

- [ ] **Step 5: Commit**
```bash
git add frontend/src/views/DashboardView.vue frontend/src/components/DeckHeader.vue
git commit -m "fix: settings navigation touch-action and diagnostic"
```

---

## Task 8: ScreenSaver.vue — new component

**Files:**
- Create: `frontend/src/components/ScreenSaver.vue`

- [ ] **Step 1: Create the file with the clock-centric layout**

```vue
<template>
  <div
    v-if="visible"
    class="screensaver"
    @click="emit('dismiss')"
    @touchstart.passive="emit('dismiss')"
  >
    <div class="ss-glow"></div>

    <div class="ss-body" :style="driftStyle">
      <div class="ss-time">{{ timeStr }}</div>
      <div class="ss-date">{{ dateStr }}</div>
    </div>

    <div class="ss-bottom-bar">
      <div class="ss-card">
        <FontAwesomeIcon :icon="weatherIcon" class="ss-weather-icon" />
        <div class="ss-card-info">
          <span class="ss-card-main">{{ tempStr }}</span>
          <span class="ss-card-sub">{{ location }}</span>
        </div>
      </div>
      <div class="ss-card">
        <div class="ss-card-info">
          <span class="ss-card-main">{{ nextEventName }}</span>
          <span class="ss-card-sub">{{ nextEventTime }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useWeather } from '@/composables/useWeather'

defineProps<{ visible: boolean }>()
const emit = defineEmits<{ dismiss: [] }>()

const time = ref(new Date())
let clockTimer: ReturnType<typeof setInterval> | null = null

const { weather, start: startWeather, stop: stopWeather } = useWeather()

const timeStr = computed(() =>
  time.value.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
)
const dateStr = computed(() =>
  time.value.toLocaleDateString([], { weekday: 'long', month: 'short', day: 'numeric' }).toUpperCase()
)

const weatherIcon = computed(() => weather.value?.icon || ['fas', 'cloud-sun'])
const tempStr = computed(() => weather.value ? `${weather.value.temperature}°C` : '--°C')
const location = computed(() => weather.value?.location || '—')

const EVENTS = [
  { name: 'Daily Standup', time: '10:00 AM' },
  { name: 'Product Review', time: '2:00 PM' },
  { name: 'Gym Session',    time: '6:30 PM' },
]

function getNextEvent() {
  const now = time.value
  const h = now.getHours()
  const m = now.getMinutes()
  const currentMinutes = h * 60 + m
  const parsed = EVENTS.map(e => {
    const [hm, period] = e.time.split(' ')
    let [eh, em] = hm.split(':').map(Number)
    if (period === 'PM' && eh !== 12) eh += 12
    if (period === 'AM' && eh === 12) eh = 0
    return { ...e, totalMinutes: eh * 60 + em }
  })
  const upcoming = parsed.find(e => e.totalMinutes > currentMinutes)
  return upcoming || parsed[0]
}

const nextEventName = computed(() => getNextEvent().name)
const nextEventTime = computed(() => getNextEvent().time)

// Drift: ±20 px on X and Y on a 30-second sine cycle
const driftX = ref(0)
const driftY = ref(0)
let driftTimer: ReturnType<typeof setInterval> | null = null
let driftTick = 0

function updateDrift() {
  driftTick += 1
  driftX.value = Math.sin(driftTick / 60) * 20
  driftY.value = Math.cos(driftTick / 90) * 16
}

const driftStyle = computed(() => ({
  transform: `translate(${driftX.value}px, ${driftY.value}px)`,
}))

onMounted(() => {
  clockTimer = setInterval(() => { time.value = new Date() }, 1000)
  driftTimer = setInterval(updateDrift, 500)
  startWeather()
})

onUnmounted(() => {
  if (clockTimer) clearInterval(clockTimer)
  if (driftTimer) clearInterval(driftTimer)
  stopWeather()
})
</script>

<style scoped>
.screensaver {
  position: fixed;
  inset: 0;
  z-index: 500;
  background: #050510;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  user-select: none;
}

.ss-glow {
  position: absolute;
  top: 30%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 400px;
  height: 200px;
  background: radial-gradient(ellipse, rgba(0, 80, 200, 0.18), transparent 70%);
  pointer-events: none;
}

.ss-body {
  text-align: center;
  transition: transform 0.5s ease;
}

.ss-time {
  font-size: clamp(4rem, 12vw, 7rem);
  font-weight: 200;
  letter-spacing: 0.08em;
  color: rgba(255, 255, 255, 0.92);
  line-height: 1;
}

.ss-date {
  margin-top: 0.5rem;
  font-size: clamp(0.7rem, 1.5vw, 1rem);
  letter-spacing: 0.2em;
  color: rgba(255, 255, 255, 0.38);
}

.ss-bottom-bar {
  position: absolute;
  bottom: 2rem;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 1rem;
  width: min(90vw, 600px);
}

.ss-card {
  flex: 1;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 0.9rem 1.2rem;
  display: flex;
  align-items: center;
  gap: 0.9rem;
}

.ss-weather-icon {
  font-size: 2rem;
  color: #ff9f0a;
  flex-shrink: 0;
}

.ss-card-info {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.ss-card-main {
  font-size: 1.2rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.88);
}

.ss-card-sub {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.4);
}
</style>
```

- [ ] **Step 2: Commit**
```bash
git add frontend/src/components/ScreenSaver.vue
git commit -m "feat: add ScreenSaver component with clock, weather, and next-event"
```

---

## Task 9: DashboardView — idle timer, ScreenSaver, remove WidgetColumn

**Files:**
- Modify: `frontend/src/views/DashboardView.vue`

- [ ] **Step 1: Add ScreenSaver import and remove WidgetColumn import**

In the imports section:
```typescript
// Remove:
import WidgetColumn from '@/components/WidgetColumn.vue'

// Add:
import ScreenSaver from '@/components/ScreenSaver.vue'
```

- [ ] **Step 2: Remove the `showWidgets` ref**

Remove: `const showWidgets = ref(true)`

- [ ] **Step 3: Add idle timer refs**

After the existing refs near the top of `<script setup>`:
```typescript
const screensaverVisible = ref(false)
let idleTimer: ReturnType<typeof setTimeout> | null = null

function resetIdleTimer() {
  if (idleTimer) clearTimeout(idleTimer)
  const timeoutMs = settingsStore.screensaverTimeout * 1000
  if (timeoutMs <= 0) return
  idleTimer = setTimeout(() => {
    screensaverVisible.value = true
  }, timeoutMs)
}

function dismissScreensaver() {
  screensaverVisible.value = false
  resetIdleTimer()
}
```

- [ ] **Step 4: Register idle event listeners in `onMounted` and clean up in `onUnmounted`**

In `onMounted`, after the existing code, add:
```typescript
const IDLE_EVENTS = ['pointermove', 'pointerdown', 'keydown']
IDLE_EVENTS.forEach(ev => document.addEventListener(ev, resetIdleTimer, { passive: true }))
resetIdleTimer()
```

In `onUnmounted`, add:
```typescript
const IDLE_EVENTS = ['pointermove', 'pointerdown', 'keydown']
IDLE_EVENTS.forEach(ev => document.removeEventListener(ev, resetIdleTimer))
if (idleTimer) clearTimeout(idleTimer)
```

(Move the `IDLE_EVENTS` const to module scope so it's accessible in both lifecycle hooks.)

- [ ] **Step 5: Replace `<WidgetColumn>` with `<ScreenSaver>` in template**

Remove:
```html
<!-- Widget Column (displayed in non-edit mode) -->
<WidgetColumn v-if="!isEditMode && showWidgets" />
```

Add before the closing `</div>` of `.dashboard-view`:
```html
<ScreenSaver :visible="screensaverVisible" @dismiss="dismissScreensaver" />
```

- [ ] **Step 6: Verify no TS errors**
```bash
cd frontend && npx vue-tsc --noEmit
```

- [ ] **Step 7: Commit**
```bash
git add frontend/src/views/DashboardView.vue
git commit -m "feat: remove WidgetColumn, add ScreenSaver with idle timer"
```

---

## Task 10: SettingsView — screensaver timeout slider

**Files:**
- Modify: `frontend/src/views/SettingsView.vue`

- [ ] **Step 1: Find the Display sub-tab section**

Search for `appearanceSubTab === 'display'` in SettingsView.vue. Inside that `<div>`, add the screensaver section after the existing display settings:

```html
<!-- Screensaver -->
<div class="setting-group" id="setting-screensaver">
  <label class="setting-label">
    <FontAwesomeIcon :icon="['fas', 'moon']" />
    Screensaver Delay
  </label>
  <div class="setting-control">
    <input
      type="range"
      min="0"
      max="600"
      step="30"
      :value="settingsStore.screensaverTimeout"
      @input="settingsStore.screensaverTimeout = Number(($event.target as HTMLInputElement).value)"
      class="setting-slider"
    />
    <span class="setting-value">
      {{ settingsStore.screensaverTimeout === 0 ? 'Off' : formatScreensaverTimeout(settingsStore.screensaverTimeout) }}
    </span>
  </div>
  <p class="setting-description">Time before screensaver appears. 0 = disabled.</p>
</div>
```

- [ ] **Step 2: Add the `formatScreensaverTimeout` helper in the script**

In the script section, add:
```typescript
function formatScreensaverTimeout(seconds: number): string {
  if (seconds < 60) return `${seconds}s`
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return s === 0 ? `${m}m` : `${m}m ${s}s`
}
```

- [ ] **Step 3: Add the setting to the search index**

Find the `searchMatches` / keyword list in SettingsView.vue and add:
```typescript
{ label: 'Screensaver Delay', keywords: 'screensaver idle timeout sleep', tabId: 'appearance', subTab: 'display', icon: ['fas', 'moon'] },
```

- [ ] **Step 4: Commit**
```bash
git add frontend/src/views/SettingsView.vue
git commit -m "feat: add screensaver timeout slider to Settings display tab"
```

---

## Done

All 9 tasks complete. Expected result:
- Header hidden by default; swipe down from top to reveal (90 px, 64 px buttons); auto-hides after 5 s with progress bar; swipe up to dismiss manually.
- Footer shows only page dots + edit controls (no duplicate scene pills).
- Pinch gesture no longer resizes buttons.
- Touch drag-and-drop from Edit sidebar to grid uses existing infrastructure (already wired).
- Settings navigation works with `touch-action: manipulation`.
- WidgetColumn gone; ScreenSaver overlay appears after configurable idle time.
- Screensaver timeout configurable in Settings → Appearance → Display.
