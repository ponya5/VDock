<template>
  <div
    v-if="visible"
    class="screensaver"
    :class="{ 'ss-edit-mode': layoutEdit }"
    @click="onRootTap"
    @touchstart.passive="onRootTap"
  >
    <!-- Custom screensaver background on its own layer so it never has to
         fight the base color for specificity. Component-kind entries
         (WebGL/CSS effects) mount directly; a scrim keeps text readable. -->
    <div v-if="hasCustomBg" class="ss-bg" :class="ssBgClass" :style="ssBgStyle"></div>
    <component :is="ssBgComponent" v-if="ssBgComponent" class="ss-bg-component" />
    <div v-if="hasCustomBg" class="ss-dim"></div>

    <div class="ss-glow"></div>

    <!-- Weather pinned to its own corner so it never competes for reading
         space with the clock or the widgets below it. -->
    <div
      v-if="showWeatherWidget"
      class="ss-pos ss-weather-corner"
      :class="{ 'ss-editing': layoutEdit }"
      :style="[posStyle('weather'), { '--ss-weather-scale': String(weatherScale) }]"
      @pointerdown="startDrag('weather', $event)"
    >
      <FontAwesomeIcon :icon="weatherIcon" class="ss-weather-corner-icon" />
      <div class="ss-weather-corner-info">
        <span class="ss-weather-corner-temp">{{ tempStr }}</span>
        <span class="ss-weather-corner-loc">{{ location }}</span>
      </div>
      <span
        v-if="layoutEdit"
        class="ss-resize"
        @pointerdown.stop="startResize('weather', $event)"
      ></span>
    </div>

    <div
      class="ss-pos ss-body"
      :class="{ 'ss-editing': layoutEdit }"
      :style="clockStyle"
      @pointerdown="startDrag('clock', $event)"
    >
      <div class="ss-time">{{ timeStr }}</div>
      <div class="ss-date">{{ dateStr }}</div>
      <span
        v-if="layoutEdit"
        class="ss-resize"
        @pointerdown.stop="startResize('clock', $event)"
      ></span>
    </div>

    <!-- News, market and world clock sit side by side across the lower half.
         Each lives in its own .ss-pos wrapper so the layout editor can move
         and resize them independently. -->
    <div
      v-if="showNewsWidget"
      class="ss-pos"
      :class="{ 'ss-editing': layoutEdit }"
      :style="posStyle('news', widgetScaleNum)"
      @pointerdown="startDrag('news', $event)"
    >
      <!-- Tappable rows instead of a one-at-a-time carousel: a tap lands
           on the headline you actually saw, and the stop modifiers keep it
           from reaching the root dismiss handler. Rotation steps a whole
           window of rows at a time (see useNews). -->
      <div
        class="ss-news"
        @click.stop="pauseRotation()"
        @touchstart.stop="pauseRotation()"
      >
        <FontAwesomeIcon :icon="['fas', 'newspaper']" class="ss-news-icon" />
        <div class="ss-news-rows" aria-live="polite">
          <button
            v-for="(item, i) in newsWindow"
            :key="`${i}-${item.url || item.title}`"
            type="button"
            class="ss-news-row"
            :title="item.url"
            @click.stop="openArticle(item)"
          >
            <span class="ss-news-title">{{ item.title }}</span>
            <span class="ss-news-row-meta">
              <span class="ss-news-source">{{ item.source }}</span>
              <svg
                class="ss-news-open"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                aria-hidden="true"
              >
                <path d="M7 17L17 7M7 7h10v10" />
              </svg>
            </span>
          </button>

          <div v-if="!newsWindow.length" class="ss-news-empty">
            {{ newsError || 'Loading headlines…' }}
          </div>
        </div>
      </div>
      <span
        v-if="layoutEdit"
        class="ss-resize"
        @pointerdown.stop="startResize('news', $event)"
      ></span>
    </div>

    <div
      v-if="showMarketWidget"
      class="ss-pos"
      :class="{ 'ss-editing': layoutEdit }"
      :style="posStyle('market', widgetScaleNum)"
      @pointerdown="startDrag('market', $event)"
    >
      <div class="ss-chip">
        <div v-for="coin in marketPrices" :key="coin.id" class="ss-chip-line">
          <span class="ss-chip-label">{{ coin.symbol }}</span>
          <span class="ss-chip-value">${{ coin.price.toLocaleString() }}</span>
        </div>
      </div>
      <span
        v-if="layoutEdit"
        class="ss-resize"
        @pointerdown.stop="startResize('market', $event)"
      ></span>
    </div>

    <div
      v-if="showWorldClockWidget"
      class="ss-pos"
      :class="{ 'ss-editing': layoutEdit }"
      :style="posStyle('worldclock', widgetScaleNum)"
      @pointerdown="startDrag('worldclock', $event)"
    >
      <div class="ss-chip">
        <div v-for="tz in worldClocks" :key="tz.label" class="ss-chip-line">
          <span class="ss-chip-label">{{ tz.label }}</span>
          <span class="ss-chip-value">{{ tz.time }}</span>
        </div>
      </div>
      <span
        v-if="layoutEdit"
        class="ss-resize"
        @pointerdown.stop="startResize('worldclock', $event)"
      ></span>
    </div>

    <!-- Layout editor toolbar. Its own events are stopped so a tap here can
         never reach the dismiss handler or start a drag. -->
    <div
      v-if="layoutEdit"
      class="ss-edit-toolbar"
      @click.stop
      @touchstart.stop
      @pointerdown.stop
    >
      <span class="ss-edit-hint">Drag widgets to move · corner dot resizes</span>
      <button type="button" class="ss-edit-btn" @click="resetLayout">Reset</button>
      <button type="button" class="ss-edit-btn ss-edit-btn-primary" @click="saveLayout">Save</button>
      <button type="button" class="ss-edit-btn" @click="emit('dismiss')">Done</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useWeather } from '@/composables/useWeather'
import { useNews } from '@/composables/useNews'
import type { NewsHeadline } from '@/services/newsService'
import { useMarket } from '@/composables/useMarket'
import { useSettingsStore } from '@/stores/settings'
import { resolveBackground, DEFAULT_BACKGROUND_ID } from '@/data/backgrounds'
import { backgroundClassFor, backgroundStyleFor } from '@/utils/backgroundStyle'
import {
  defaultScreensaverLayout,
  type ScreensaverLayout,
  type ScreensaverWidgetId,
} from '@/utils/screensaverLayout'

const props = defineProps<{ visible: boolean; layoutEdit?: boolean }>()
const emit = defineEmits<{ dismiss: []; 'save-layout': [layout: ScreensaverLayout] }>()

const settingsStore = useSettingsStore()

const time = ref(new Date())
let clockTimer: ReturnType<typeof setInterval> | null = null

const { weather, start: startWeather, stop: stopWeather } = useWeather()
const {
  windowed: newsWindow,
  error: newsError,
  pause: pauseRotation,
  start: startNews,
  stop: stopNews
} = useNews()
const { prices: marketPrices, start: startMarket, stop: stopMarket } = useMarket()

// In layout-edit mode the screensaver never dismisses — taps belong to the
// drag/resize machinery and the toolbar instead.
function onRootTap() {
  if (!props.layoutEdit) emit('dismiss')
}

// Tap a headline -> read the article. The news card's handlers are .stop-ped
// so the tap never reaches the root dismiss handler; the article opens in
// the system browser through the Electron bridge, or a new tab otherwise.
function openArticle(item: NewsHeadline) {
  if (props.layoutEdit) return
  pauseRotation()
  if (!item.url) return
  const bridge = (window as Window & {
    electronAPI?: { openExternal?: (url: string) => Promise<void> }
  }).electronAPI
  if (bridge?.openExternal) {
    void bridge.openExternal(item.url)
  } else {
    window.open(item.url, '_blank', 'noopener,noreferrer')
  }
}

const timeStr = computed(() =>
  time.value.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
)
const dateStr = computed(() =>
  time.value.toLocaleDateString([], { weekday: 'long', month: 'short', day: 'numeric' }).toUpperCase()
)

const weatherIcon = computed(() => weather.value?.icon || ['fas', 'cloud-sun'])
const tempStr = computed(() => weather.value ? `${weather.value.temperature}°C` : '--°C')
const location = computed(() => weather.value?.location || '—')

const showWeatherWidget = computed(() => settingsStore.screensaverWidgets.includes('weather'))
// Touch mode feeds the same scale as the user sliders: a small panel running
// tablet mode gets readable widgets without finding the sliders, and the
// percentage still adjusts on top. Capped at 1.5 — the full tablet
// multiplier would push the widget column past a 480px-tall screen.
const touchScale = computed(() => Math.min(settingsStore.touchModeMultiplier, 1.5))
// User-set percentage (default 100) that enlarges the corner pill for small
// touch panels, where the vw-clamped sizes end up too small to glance at.
// Capped at 2x combined — the pill is anchored to a corner, so an unchecked
// value would clip off the screen edge.
const weatherScale = computed(() =>
  Math.min((settingsStore.screensaverWeatherSize / 100) * touchScale.value, 2)
)
const showNewsWidget = computed(() => settingsStore.screensaverWidgets.includes('news'))
const showMarketWidget = computed(() => settingsStore.screensaverWidgets.includes('market'))
const showWorldClockWidget = computed(() => settingsStore.screensaverWidgets.includes('worldclock'))

// User-tunable text scale for the info widgets (Settings → Screensaver →
// Widget size), amplified in touch modes. Capped at 1.35 so the three-across
// row still fits a 7" panel; the layout editor's per-widget scale has its
// own wider range for intentional resizing.
const widgetScaleNum = computed(() =>
  Math.min(((settingsStore.screensaverWidgetSize || 100) / 100) * touchScale.value, 1.35)
)

// --- Screensaver background --------------------------------------------------
// 'default' keeps the classic dark look; anything else paints the .ss-bg
// layer (catalog CSS/image) or mounts the component directly.
const ssBgId = computed(() => settingsStore.screensaverBackground || DEFAULT_BACKGROUND_ID)
const hasCustomBg = computed(() => ssBgId.value !== DEFAULT_BACKGROUND_ID)
const ssBgClass = computed(() => (hasCustomBg.value ? backgroundClassFor(ssBgId.value) : ''))
const ssBgStyle = computed(() => (hasCustomBg.value ? backgroundStyleFor(ssBgId.value) : {}))
const ssBgComponent = computed(() => {
  if (!hasCustomBg.value) return null
  const option = resolveBackground(ssBgId.value)
  return option.kind === 'component' ? option.component : null
})

// Drift state is declared up here because the layout-edit watcher below
// (immediate: true) can zero it before the later section would run.
const driftX = ref(0)
const driftY = ref(0)
let driftTimer: ReturnType<typeof setInterval> | null = null
let driftTick = 0

// --- Layout: positions are widget centers in viewport percent -----------------
// Normal mode reads the persisted layout; edit mode works on a local copy
// that is only written back when the user hits Save.
const editLayout = ref<ScreensaverLayout>(defaultScreensaverLayout())
const activeLayout = computed(() =>
  props.layoutEdit ? editLayout.value : settingsStore.screensaverLayout
)

watch(() => props.layoutEdit, (editing) => {
  if (editing) {
    editLayout.value = JSON.parse(JSON.stringify(settingsStore.screensaverLayout))
    driftX.value = 0
    driftY.value = 0
  }
}, { immediate: true })

function posStyle(id: ScreensaverWidgetId, sizeScale = 1) {
  const l = activeLayout.value[id]
  return {
    left: `${l.x}%`,
    top: `${l.y}%`,
    transform: `translate(-50%, -50%) scale(${l.scale * sizeScale})`,
  }
}

const clockStyle = computed(() => {
  const l = activeLayout.value.clock
  return {
    left: `${l.x}%`,
    top: `${l.y}%`,
    transform:
      `translate(-50%, -50%) translate(${driftX.value}px, ${driftY.value}px) ` +
      `scale(${l.scale})`,
  }
})

// --- Drag & resize (edit mode) ------------------------------------------------
const clampPos = (v: number) => Math.min(94, Math.max(6, v))
const clampScale = (v: number) => Math.min(2.5, Math.max(0.5, v))

let dragState: {
  id: ScreensaverWidgetId
  startX: number
  startY: number
  origX: number
  origY: number
} | null = null
let resizeState: { id: ScreensaverWidgetId; startY: number; origScale: number } | null = null

function startDrag(id: ScreensaverWidgetId, e: PointerEvent) {
  if (!props.layoutEdit) return
  e.preventDefault()
  e.stopPropagation()
  const l = editLayout.value[id]
  dragState = { id, startX: e.clientX, startY: e.clientY, origX: l.x, origY: l.y }
  window.addEventListener('pointermove', onDragMove)
  window.addEventListener('pointerup', endInteraction, { once: true })
  window.addEventListener('pointercancel', endInteraction, { once: true })
}

function onDragMove(e: PointerEvent) {
  if (!dragState) return
  const dx = ((e.clientX - dragState.startX) / window.innerWidth) * 100
  const dy = ((e.clientY - dragState.startY) / window.innerHeight) * 100
  const l = editLayout.value[dragState.id]
  l.x = clampPos(dragState.origX + dx)
  l.y = clampPos(dragState.origY + dy)
}

function startResize(id: ScreensaverWidgetId, e: PointerEvent) {
  if (!props.layoutEdit) return
  e.preventDefault()
  e.stopPropagation()
  resizeState = { id, startY: e.clientY, origScale: editLayout.value[id].scale }
  window.addEventListener('pointermove', onResizeMove)
  window.addEventListener('pointerup', endInteraction, { once: true })
  window.addEventListener('pointercancel', endInteraction, { once: true })
}

function onResizeMove(e: PointerEvent) {
  if (!resizeState) return
  const dy = e.clientY - resizeState.startY
  editLayout.value[resizeState.id].scale = clampScale(resizeState.origScale + dy / 160)
}

function endInteraction() {
  dragState = null
  resizeState = null
  window.removeEventListener('pointermove', onDragMove)
  window.removeEventListener('pointermove', onResizeMove)
}

function resetLayout() {
  editLayout.value = defaultScreensaverLayout()
}

function saveLayout() {
  emit('save-layout', JSON.parse(JSON.stringify(editLayout.value)))
}

const WORLD_CLOCK_DEFAULTS = [
  { label: 'New York', tz: 'America/New_York' },
  { label: 'London', tz: 'Europe/London' },
  { label: 'Tokyo', tz: 'Asia/Tokyo' },
]

// Common city names → IANA zones so users can type "Berlin" instead of
// "Europe/Berlin". Explicit "Label=Zone" entries always win.
const CITY_TIMEZONES: Record<string, string> = {
  'new york': 'America/New_York', nyc: 'America/New_York', 'los angeles': 'America/Los_Angeles',
  la: 'America/Los_Angeles', chicago: 'America/Chicago', denver: 'America/Denver',
  toronto: 'America/Toronto', vancouver: 'America/Vancouver', 'mexico city': 'America/Mexico_City',
  'sao paulo': 'America/Sao_Paulo', 'buenos aires': 'America/Argentina/Buenos_Aires',
  london: 'Europe/London', dublin: 'Europe/Dublin', paris: 'Europe/Paris',
  berlin: 'Europe/Berlin', amsterdam: 'Europe/Amsterdam', madrid: 'Europe/Madrid',
  rome: 'Europe/Rome', zurich: 'Europe/Zurich', stockholm: 'Europe/Stockholm',
  oslo: 'Europe/Oslo', copenhagen: 'Europe/Copenhagen', helsinki: 'Europe/Helsinki',
  warsaw: 'Europe/Warsaw', prague: 'Europe/Prague', vienna: 'Europe/Vienna',
  athens: 'Europe/Athens', istanbul: 'Europe/Istanbul', moscow: 'Europe/Moscow',
  'tel aviv': 'Asia/Jerusalem', jerusalem: 'Asia/Jerusalem', dubai: 'Asia/Dubai',
  mumbai: 'Asia/Kolkata', delhi: 'Asia/Kolkata', bangalore: 'Asia/Kolkata',
  bangkok: 'Asia/Bangkok', singapore: 'Asia/Singapore', 'hong kong': 'Asia/Hong_Kong',
  shanghai: 'Asia/Shanghai', beijing: 'Asia/Shanghai', tokyo: 'Asia/Tokyo',
  seoul: 'Asia/Seoul', sydney: 'Australia/Sydney', melbourne: 'Australia/Melbourne',
  auckland: 'Pacific/Auckland', cairo: 'Africa/Cairo', johannesburg: 'Africa/Johannesburg',
  lagos: 'Africa/Lagos', nairobi: 'Africa/Nairobi',
}

function parseClockEntry(raw: string): { label: string; tz: string } | null {
  const entry = raw.trim()
  if (!entry) return null
  const eq = entry.indexOf('=')
  if (eq > 0) {
    const label = entry.slice(0, eq).trim()
    const tz = entry.slice(eq + 1).trim()
    return label && tz ? { label, tz } : null
  }
  const mapped = CITY_TIMEZONES[entry.toLowerCase()]
  if (mapped) return { label: entry, tz: mapped }
  // Bare IANA zone like "Europe/Berlin" — label from the last path segment.
  if (entry.includes('/')) return { label: entry.split('/').pop()!.replace(/_/g, ' '), tz: entry }
  return null
}

const worldClockZones = computed(() => {
  const configured = (settingsStore.worldClockTimezones || '')
    .split(/[\n,]+/)
    .map(parseClockEntry)
    .filter((z): z is { label: string; tz: string } => z !== null)
  return configured.length ? configured : WORLD_CLOCK_DEFAULTS
})

const worldClocks = computed(() =>
  worldClockZones.value
    .map(z => {
      try {
        return {
          label: z.label,
          time: new Intl.DateTimeFormat([], { hour: '2-digit', minute: '2-digit', hour12: false, timeZone: z.tz }).format(time.value),
        }
      } catch {
        return null // invalid zone entry — drop it rather than break the widget
      }
    })
    .filter((z): z is { label: string; time: string } => z !== null)
)

// Drift: ±20 px on X and Y on a 30-second sine cycle
// Reset drift position each time the screensaver becomes visible so the
// clock never appears shifted on re-show.
watch(() => props.visible, (v) => {
  if (v) driftTick = 0
})

function updateDrift() {
  if (props.layoutEdit) return // drag target must not move under the pointer
  driftTick += 1
  driftX.value = Math.sin(driftTick / 60) * 20
  driftY.value = Math.cos(driftTick / 90) * 16
}

onMounted(() => {
  clockTimer = setInterval(() => { time.value = new Date() }, 1000)
  driftTimer = setInterval(updateDrift, 500)
  startWeather()
  if (showNewsWidget.value) startNews()
  if (showMarketWidget.value) startMarket()
})

onUnmounted(() => {
  if (clockTimer) clearInterval(clockTimer)
  if (driftTimer) clearInterval(driftTimer)
  endInteraction()
  window.removeEventListener('pointerup', endInteraction)
  window.removeEventListener('pointercancel', endInteraction)
  stopWeather()
  stopNews()
  stopMarket()
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
  overflow: hidden;
}

/* Custom screensaver background layer. Kept as a child div (rather than on
   .screensaver) so the scoped base background never outranks it. */
.ss-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}

.ss-bg-component {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}

/* Readability scrim over any custom background. */
.ss-dim {
  position: absolute;
  inset: 0;
  z-index: 1;
  background: rgba(5, 5, 16, 0.5);
  pointer-events: none;
}

.ss-glow {
  position: absolute;
  top: 26%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 400px;
  height: 200px;
  background: radial-gradient(ellipse, rgba(0, 80, 200, 0.18), transparent 70%);
  pointer-events: none;
  z-index: 1;
}

/* Every widget sits in an absolutely positioned wrapper whose left/top come
   from the saved layout (center-anchored viewport percent). */
.ss-pos {
  position: absolute;
  z-index: 2;
}

.ss-body {
  text-align: center;
  transition: transform 0.5s ease;
}

.ss-edit-mode {
  cursor: default;
}

.ss-edit-mode .ss-body {
  transition: none;
}

.ss-time {
  font-size: clamp(4.5rem, 15vw, 10rem);
  font-weight: 200;
  letter-spacing: 0.08em;
  color: rgba(255, 255, 255, 0.92);
  line-height: 1;
}

.ss-date {
  margin-top: 0.5rem;
  font-size: calc(clamp(0.85rem, 1.8vw, 1.15rem) * min(var(--touch-multiplier, 1), 1.3));
  letter-spacing: 0.2em;
  color: rgba(255, 255, 255, 0.38);
}

/* --- Weather: pinned to its own corner ------------------------------------ */
/* Kept out of the reading area entirely -- it's a glance-and-go value, not
   something you read, so it never has to fight the news list for space on a
   small touch panel. */
.ss-weather-corner {
  --ss-weather-scale: 1;
  display: flex;
  align-items: center;
  gap: calc(0.6rem * var(--ss-weather-scale));
  padding: calc(0.5rem * var(--ss-weather-scale)) calc(0.9rem * var(--ss-weather-scale));
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 999px;
  pointer-events: none;
}

.ss-weather-corner-icon {
  font-size: calc(clamp(1.3rem, 2.4vw, 1.8rem) * var(--ss-weather-scale));
  color: #ff9f0a;
  flex-shrink: 0;
}

.ss-weather-corner-info {
  display: flex;
  flex-direction: column;
  line-height: 1.15;
}

.ss-weather-corner-temp {
  font-size: calc(clamp(1rem, 1.8vw, 1.3rem) * var(--ss-weather-scale));
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
}

.ss-weather-corner-loc {
  font-size: calc(clamp(0.65rem, 1vw, 0.78rem) * var(--ss-weather-scale));
  color: rgba(255, 255, 255, 0.45);
}

/* --- Widgets: news card + compact chips, each in its own .ss-pos wrapper --- */
.ss-news {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.3rem;
  width: clamp(220px, 28vw, 360px);
  max-height: 46vh;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 14px;
  box-sizing: border-box;
}

.ss-news-icon {
  font-size: clamp(1.3rem, 2.2vw, 1.7rem);
  color: rgba(255, 255, 255, 0.5);
  flex-shrink: 0;
}

/* Four stacked tappable rows. A carousel slide can't be tapped reliably on
   a touch panel -- it may rotate out mid-tap -- so the rows stay put and the
   rotation moves a whole window at a time. */
.ss-news-rows {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ss-news-row {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 3px;
  width: 100%;
  padding: 6px 10px;
  border: 0;
  border-radius: 9px;
  background: transparent;
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
  min-width: 0;
  min-height: 44px;
  /* The touch multiplier is deliberately NOT folded in here: the widget
     wrapper's transform scale already enlarges rows on touch panels, and
     applying it twice pushed the card past a 480px-tall screen. */
  min-height: max(var(--min-touch-target, 44px), 44px);
  transition: background 0.15s ease;
}

.ss-news-row:hover {
  background: rgba(255, 255, 255, 0.08);
}

.ss-news-row:active {
  background: rgba(255, 255, 255, 0.15);
}

.ss-news-row:focus-visible {
  outline: 2px solid var(--accent, #7aa2ff);
  outline-offset: -2px;
}

.ss-news-row-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.ss-news-open {
  width: 0.8em;
  height: 0.8em;
  flex-shrink: 0;
  opacity: 0.55;
}

.ss-news-empty {
  padding: 10px 4px;
  font-size: 0.9em;
  opacity: 0.7;
}

.ss-news-title {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  font-size: clamp(1rem, 2.2vw, 1.3rem);
  font-weight: 600;
  line-height: 1.3;
  color: rgba(255, 255, 255, 0.92);
  white-space: normal;
}

.ss-news-source {
  font-size: clamp(0.7rem, 1.2vw, 0.85rem);
  color: rgba(255, 255, 255, 0.42);
}

/* Market + world clock: compact chips. */
.ss-chip {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  padding: 0.85rem 1.1rem;
  width: clamp(140px, 19vw, 250px);
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  box-sizing: border-box;
}

.ss-chip-line {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 0.75rem;
}

.ss-chip-label {
  font-size: clamp(0.75rem, 1.4vw, 0.9rem);
  color: rgba(255, 255, 255, 0.45);
  white-space: nowrap;
}

.ss-chip-value {
  font-size: clamp(0.95rem, 1.8vw, 1.15rem);
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
  white-space: nowrap;
}

/* --- Layout edit mode ------------------------------------------------------ */
/* Children get pointer-events: none so a drag can't trigger a news row's
   click; the resize handle opts back in. */
.ss-editing {
  outline: 2px dashed rgba(255, 255, 255, 0.45);
  outline-offset: 8px;
  border-radius: 12px;
  cursor: grab;
  touch-action: none;
  pointer-events: auto;
}

.ss-editing:active {
  cursor: grabbing;
}

.ss-editing > *:not(.ss-resize) {
  pointer-events: none;
}

.ss-resize {
  position: absolute;
  right: -14px;
  bottom: -14px;
  width: clamp(26px, 4vw, 36px);
  height: clamp(26px, 4vw, 36px);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.92);
  border: 2px solid rgba(10, 10, 20, 0.6);
  cursor: nwse-resize;
  touch-action: none;
  z-index: 3;
}

.ss-resize::after {
  content: '';
  position: absolute;
  right: 5px;
  bottom: 5px;
  width: 10px;
  height: 10px;
  border-right: 2px solid #0a0a14;
  border-bottom: 2px solid #0a0a14;
}

.ss-edit-toolbar {
  position: absolute;
  left: 50%;
  bottom: clamp(0.8rem, 3vh, 2rem);
  transform: translateX(-50%);
  z-index: 4;
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.6rem 0.9rem;
  background: rgba(20, 20, 34, 0.92);
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 999px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45);
}

.ss-edit-hint {
  font-size: calc(0.8rem * min(var(--touch-multiplier, 1), 1.4));
  color: rgba(255, 255, 255, 0.6);
  white-space: nowrap;
  padding: 0 0.4rem;
}

.ss-edit-btn {
  min-height: 44px;
  min-height: max(var(--min-touch-target, 44px), calc(40px * var(--touch-multiplier, 1)));
  padding: 0 1.1rem;
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.9);
  font-size: calc(0.85rem * min(var(--touch-multiplier, 1), 1.4));
  cursor: pointer;
}

.ss-edit-btn:hover {
  background: rgba(255, 255, 255, 0.16);
}

.ss-edit-btn-primary {
  background: var(--accent, #7aa2ff);
  border-color: transparent;
  color: #0a0a14;
  font-weight: 700;
}

.ss-edit-btn-primary:hover {
  background: var(--accent, #7aa2ff);
  filter: brightness(1.1);
}

@media (prefers-reduced-motion: reduce) {
  .ss-news-row {
    transition: none;
  }
}

/* Short screens (7" panels are ~480px): four 2-line rows can't fit under the
   clock, so titles drop to one line and the rows tighten up. */
@media (max-height: 560px) {
  /* 15vw of an 800px panel is a 120px digit row — too tall to sit above the
     widget row, so the clock itself shrinks on short screens. */
  .ss-time {
    font-size: clamp(3.5rem, 17vh, 10rem);
  }

  .ss-news {
    padding: 0.7rem 1rem;
    gap: 0.7rem;
  }

  .ss-news-row {
    min-height: 40px;
    min-height: max(40px, calc(var(--min-touch-target, 44px) * 0.9));
  }

  .ss-news-title {
    -webkit-line-clamp: 1;
    font-size: clamp(0.85rem, 2vw, 1.05rem);
  }
}

/* Narrow portrait panels: free positions can't fit three widgets across, so
   fall back to a centered column. relative (not static) keeps the wrapper a
   positioning context for the .ss-resize handle in edit mode. */
@media (max-width: 620px) {
  .ss-pos {
    position: relative;
    left: auto !important;
    top: auto !important;
    transform: none !important;
    margin: 0.4rem 0;
  }

  .screensaver {
    overflow-y: auto;
    justify-content: flex-start;
    padding: 2rem 0;
  }
}
</style>
