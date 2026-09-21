<template>
  <div
    v-if="visible"
    class="screensaver"
    :class="{ 'ss-edit-mode': layoutEdit, 'ss-mobile': isMobileViewport }"
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

    <!-- Weather — top-left pill (editorial layout). -->
    <div
      v-if="showWeatherWidget"
      :ref="el => setWidgetEl('weather', el)"
      class="ss-pos ss-weather"
      :class="{ 'ss-editing': layoutEdit }"
      :style="[posStyle('weather'), { '--ss-weather-scale': String(weatherScale) }]"
      @pointerdown="startDrag('weather', $event)"
    >
      <FontAwesomeIcon :icon="weatherIcon" class="ss-weather-icon" />
      <div class="ss-weather-info">
        <span class="ss-weather-loc">{{ location }}</span>
        <span class="ss-weather-temp">{{ tempStr }}</span>
      </div>
      <span
        v-if="layoutEdit"
        class="ss-resize"
        @pointerdown.stop="startResize('weather', $event)"
      ></span>
    </div>

    <!-- Market — top-right serif quote rows. -->
    <div
      v-if="showMarketWidget"
      :ref="el => setWidgetEl('market', el)"
      class="ss-pos"
      :class="{ 'ss-editing': layoutEdit }"
      :style="posStyle('market', widgetScaleNum)"
      @pointerdown="startDrag('market', $event)"
    >
      <div class="ss-market">
        <div class="ss-section-head">
          <h2>Markets</h2>
          <span class="ss-hairline"></span>
        </div>
        <div v-for="coin in marketPrices" :key="coin.id" class="ss-market-row">
          <span class="ss-market-symbol">{{ coin.symbol }}</span>
          <span class="ss-market-value">${{ coin.price.toLocaleString() }}</span>
        </div>
        <div v-if="!marketPrices.length" class="ss-empty">
          {{ marketError || 'Loading prices…' }}
        </div>
      </div>
      <span
        v-if="layoutEdit"
        class="ss-resize"
        @pointerdown.stop="startResize('market', $event)"
      ></span>
    </div>

    <div
      :ref="el => setWidgetEl('clock', el)"
      class="ss-pos ss-body"
      :class="{ 'ss-editing': layoutEdit }"
      :style="clockStyle"
      @pointerdown="startDrag('clock', $event)"
    >
      <div class="ss-time">
        <span>{{ hourStr }}</span><span class="ss-time-colon">:</span><span>{{ minuteStr }}</span>
      </div>
      <div class="ss-date-line">
        <span class="ss-rule"></span>
        <span class="ss-date">{{ dateStr }}</span>
        <span class="ss-rule"></span>
      </div>
      <span
        v-if="layoutEdit"
        class="ss-resize"
        @pointerdown.stop="startResize('clock', $event)"
      ></span>
    </div>

    <!-- Reading sections across the lower half: headlines, sports and world
         time. Each lives in its own .ss-pos wrapper so the layout editor can
         move and resize them independently. -->
    <div
      v-if="showNewsWidget"
      :ref="el => setWidgetEl('news', el)"
      class="ss-pos"
      :class="{ 'ss-editing': layoutEdit }"
      :style="posStyle('news', widgetScaleNum)"
      @pointerdown="startDrag('news', $event)"
    >
      <!-- Numbered articles instead of anonymous rows: a tap lands on the
           headline you actually saw, and the stop modifiers keep it from
           reaching the root dismiss handler. Rotation steps a whole window
           of articles at a time (see useNews). -->
      <section
        class="ss-section ss-news"
        @click.stop="pauseRotation()"
        @touchstart.stop="pauseRotation()"
      >
        <div class="ss-section-head">
          <h2>Headlines</h2>
          <span class="ss-hairline"></span>
        </div>
        <div class="ss-article-grid" aria-live="polite">
          <article
            v-for="(item, i) in newsWindow"
            :key="`${i}-${item.url || item.title}`"
            class="ss-article"
            :title="item.url"
            @click.stop="openArticle(item, pauseRotation)"
          >
            <div class="ss-article-meta">
              <span class="ss-article-num">{{ pad2(i + 1) }}</span>
              <span class="ss-article-source">{{ item.source }}</span>
              <svg
                class="ss-article-open"
                viewBox="0 0 16 16"
                fill="none"
                stroke="currentColor"
                stroke-width="1.5"
                stroke-linecap="round"
                stroke-linejoin="round"
                aria-hidden="true"
              >
                <path d="M4.5 11.5L11.5 4.5M5.5 4.5H11.5V10.5" />
              </svg>
            </div>
            <h3 class="ss-article-title">{{ item.title }}</h3>
          </article>

          <div v-if="!newsWindow.length" class="ss-empty">
            {{ newsError || 'Loading headlines…' }}
          </div>
        </div>
      </section>
      <span
        v-if="layoutEdit"
        class="ss-resize"
        @pointerdown.stop="startResize('news', $event)"
      ></span>
    </div>

    <div
      v-if="showSportsWidget"
      :ref="el => setWidgetEl('sports', el)"
      class="ss-pos"
      :class="{ 'ss-editing': layoutEdit }"
      :style="posStyle('sports', widgetScaleNum)"
      @pointerdown="startDrag('sports', $event)"
    >
      <section
        class="ss-section ss-sports"
        @click.stop="pauseSports()"
        @touchstart.stop="pauseSports()"
      >
        <div class="ss-section-head">
          <h2>Sports</h2>
          <span class="ss-hairline"></span>
        </div>
        <div class="ss-article-list" aria-live="polite">
          <article
            v-for="(item, i) in sportsWindow"
            :key="`${i}-${item.url || item.title}`"
            class="ss-article"
            :title="item.url"
            @click.stop="openArticle(item, pauseSports)"
          >
            <div class="ss-article-meta">
              <span class="ss-article-num">{{ pad2(i + 1) }}</span>
              <span class="ss-article-source">{{ item.source }}</span>
              <svg
                class="ss-article-open"
                viewBox="0 0 16 16"
                fill="none"
                stroke="currentColor"
                stroke-width="1.5"
                stroke-linecap="round"
                stroke-linejoin="round"
                aria-hidden="true"
              >
                <path d="M4.5 11.5L11.5 4.5M5.5 4.5H11.5V10.5" />
              </svg>
            </div>
            <h3 class="ss-article-title">{{ item.title }}</h3>
          </article>

          <div v-if="!sportsWindow.length" class="ss-empty">
            {{ sportsError || 'Loading sports…' }}
          </div>
        </div>
      </section>
      <span
        v-if="layoutEdit"
        class="ss-resize"
        @pointerdown.stop="startResize('sports', $event)"
      ></span>
    </div>

    <div
      v-if="showWorldClockWidget"
      :ref="el => setWidgetEl('worldclock', el)"
      class="ss-pos"
      :class="{ 'ss-editing': layoutEdit }"
      :style="posStyle('worldclock', widgetScaleNum)"
      @pointerdown="startDrag('worldclock', $event)"
    >
      <section class="ss-section ss-worldclock">
        <div class="ss-section-head">
          <h2>World time</h2>
          <span class="ss-hairline"></span>
        </div>
        <div class="ss-tz">
          <div v-for="tz in worldClocks" :key="tz.label" class="ss-tz-row">
            <span class="ss-tz-label">{{ tz.label }}</span>
            <span class="ss-tz-time">{{ tz.time }}</span>
          </div>
        </div>
      </section>
      <span
        v-if="layoutEdit"
        class="ss-resize"
        @pointerdown.stop="startResize('worldclock', $event)"
      ></span>
    </div>

    <!-- Alignment guides — full-span dashed rules shown while a dragged
         widget snaps to another widget's edge/center or the viewport
         center line. -->
    <template v-if="layoutEdit">
      <div
        v-for="x in guideV"
        :key="`gv${x}`"
        class="ss-guide ss-guide-v"
        :style="{ left: `${x}%` }"
      ></div>
      <div
        v-for="y in guideH"
        :key="`gh${y}`"
        class="ss-guide ss-guide-h"
        :style="{ top: `${y}%` }"
      ></div>
    </template>

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
import {
  DEFAULT_SPORTS_FEEDS,
  parseFeedList,
  type NewsHeadline,
} from '@/services/newsService'
import { useMarket } from '@/composables/useMarket'
import { useSettingsStore } from '@/stores/settings'
import { resolveBackground, DEFAULT_BACKGROUND_ID } from '@/data/backgrounds'
import { backgroundClassFor, backgroundStyleFor } from '@/utils/backgroundStyle'
import {
  defaultScreensaverLayout,
  type ScreensaverLayout,
  type ScreensaverWidgetId,
} from '@/utils/screensaverLayout'
import { useMobileViewport } from '@/utils/mobileViewport'

const props = defineProps<{ visible: boolean; layoutEdit?: boolean }>()
const emit = defineEmits<{ dismiss: []; 'save-layout': [layout: ScreensaverLayout] }>()

const settingsStore = useSettingsStore()
const { isMobileViewport } = useMobileViewport()

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
// Same headlines machinery, pointed at the sports feed list — falls back to
// the built-in sports sources when the user has not configured their own.
const {
  windowed: sportsWindow,
  error: sportsError,
  pause: pauseSports,
  start: startSports,
  stop: stopSports
} = useNews(() => {
  const feeds = parseFeedList(settingsStore.sportsFeeds)
  return feeds.length ? feeds : DEFAULT_SPORTS_FEEDS
}, 'Sports')
const {
  prices: marketPrices,
  error: marketError,
  start: startMarket,
  stop: stopMarket
} = useMarket()

// In layout-edit mode the screensaver never dismisses — taps belong to the
// drag/resize machinery and the toolbar instead.
function onRootTap() {
  if (!props.layoutEdit) emit('dismiss')
}

// Tap a headline -> read the article. The section's handlers are .stop-ped
// so the tap never reaches the root dismiss handler; the article opens in
// the system browser through the Electron bridge, or a new tab otherwise.
// pauseFn freezes whichever rotation the tapped article belongs to.
function openArticle(item: NewsHeadline, pauseFn: () => void = pauseRotation) {
  if (props.layoutEdit) return
  pauseFn()
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

// Split parts so the colon can carry the accent colour, like the mockup.
const hourStr = computed(() => String(time.value.getHours()).padStart(2, '0'))
const minuteStr = computed(() => String(time.value.getMinutes()).padStart(2, '0'))
const dateStr = computed(() => {
  const d = time.value
  const weekday = d.toLocaleDateString([], { weekday: 'long' })
  const month = d.toLocaleDateString([], { month: 'long' })
  return `${weekday} · ${d.getDate()} ${month}`
})

const pad2 = (n: number) => String(n).padStart(2, '0')

const weatherIcon = computed(() => weather.value?.icon || ['fas', 'cloud-sun'])
const tempStr = computed(() => weather.value ? `${weather.value.temperature}°C` : '--°C')
const location = computed(() => weather.value?.location || '—')

// On phones the screensaver is deliberately sparse: clock + world clock
// only — feeds/weather/markets would be unreadable density on a small
// screen (DL-063). World clock is always on for mobile regardless of the
// desktop widget picks.
const showWeatherWidget = computed(() => !isMobileViewport.value && settingsStore.screensaverWidgets.includes('weather'))
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
const showNewsWidget = computed(() => !isMobileViewport.value && settingsStore.screensaverWidgets.includes('news'))
const showMarketWidget = computed(() => !isMobileViewport.value && settingsStore.screensaverWidgets.includes('market'))
const showWorldClockWidget = computed(() => isMobileViewport.value || settingsStore.screensaverWidgets.includes('worldclock'))
const showSportsWidget = computed(() => !isMobileViewport.value && settingsStore.screensaverWidgets.includes('sports'))

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

// Measured widget boxes → edge clamping. Positions anchor widget centers,
// so a wide widget near an edge can overflow the viewport (e.g. the three
// reading sections on a 7" panel). Measure each wrapper's layout size —
// offsetWidth ignores the transform, so multiply by the applied scale — and
// clamp the center so the rendered box always stays inside the screen.
const viewport = ref({ w: 0, h: 0 })
const widgetEls = new Map<ScreensaverWidgetId, HTMLElement>()
const widgetSizes = ref<Partial<Record<ScreensaverWidgetId, { w: number; h: number }>>>({})
let widgetObserver: ResizeObserver | null = null

function setWidgetEl(id: ScreensaverWidgetId, el: Element | null) {
  const prev = widgetEls.get(id)
  if (prev === el) return
  if (prev) widgetObserver?.unobserve(prev)
  if (el instanceof HTMLElement) {
    widgetEls.set(id, el)
    widgetObserver?.observe(el)
    measureWidget(id)
  } else {
    widgetEls.delete(id)
    delete widgetSizes.value[id]
  }
}

function measureWidget(id: ScreensaverWidgetId) {
  const el = widgetEls.get(id)
  if (el) widgetSizes.value[id] = { w: el.offsetWidth, h: el.offsetHeight }
}

function onViewportResize() {
  viewport.value = { w: window.innerWidth, h: window.innerHeight }
}

// Breathing room around each widget. Also covers the clock's ±20px drift.
const SS_EDGE_MARGIN_PX = 24

function clampCenter(id: ScreensaverWidgetId, x: number, y: number, scale: number) {
  const size = widgetSizes.value[id]
  const { w: vw, h: vh } = viewport.value
  if (!size || !vw || !vh) return { x: clampPos(x), y: clampPos(y) }
  const halfW = ((size.w * scale) / vw) * 50
  const halfH = ((size.h * scale) / vh) * 50
  const mx = (SS_EDGE_MARGIN_PX / vw) * 100
  const my = (SS_EDGE_MARGIN_PX / vh) * 100
  // A widget wider/taller than the viewport centers on that axis.
  const minX = Math.min(50, halfW + mx)
  const maxX = Math.max(50, 100 - halfW - mx)
  const minY = Math.min(50, halfH + my)
  const maxY = Math.max(50, 100 - halfH - my)
  return {
    x: Math.min(maxX, Math.max(minX, x)),
    y: Math.min(maxY, Math.max(minY, y)),
  }
}

// Info widgets take the widget-size slider on top of the layout scale.
const usesWidgetScale = (id: ScreensaverWidgetId) =>
  id === 'market' || id === 'news' || id === 'sports' || id === 'worldclock'

// Effective scale for a widget, capped by the measured viewport: a widget
// that renders taller than ~46% of the screen (or wider than ~62%) can never
// be laid out next to the others without overlap on a 7" display, no matter
// where its saved center points.
function transformScale(id: ScreensaverWidgetId, layoutScale: number) {
  let k = layoutScale * (usesWidgetScale(id) ? widgetScaleNum.value : 1)
  const size = widgetSizes.value[id]
  const { w: vw, h: vh } = viewport.value
  if (size && vw && vh) {
    k = Math.min(k, (vh * 0.46) / size.h, (vw * 0.62) / size.w)
  }
  return Math.max(0.4, k)
}

// Widgets mounted right now — separation only runs between these.
const mountedWidgets = computed<ScreensaverWidgetId[]>(() => {
  const ids: ScreensaverWidgetId[] = ['clock']
  if (showWeatherWidget.value) ids.push('weather')
  if (showMarketWidget.value) ids.push('market')
  if (showNewsWidget.value) ids.push('news')
  if (showSportsWidget.value) ids.push('sports')
  if (showWorldClockWidget.value) ids.push('worldclock')
  return ids
})

interface WidgetBox {
  id: ScreensaverWidgetId
  x: number
  y: number
  halfW: number // half extents, in % of viewport
  halfH: number
  k: number // transform scale actually applied
}

function widgetBox(id: ScreensaverWidgetId, padClock = true): WidgetBox {
  const l = activeLayout.value[id]
  const k = transformScale(id, l.scale)
  const c = clampCenter(id, l.x, l.y, k)
  const size = widgetSizes.value[id]
  const { w: vw, h: vh } = viewport.value
  let halfW = size && vw ? ((size.w * k) / vw) * 50 : 5
  let halfH = size && vh ? ((size.h * k) / vh) * 50 : 5
  // The clock drifts ±20px from its center — reserve that excursion so
  // neighbors never clip it mid-drift. Alignment guides pass padClock=false:
  // they must line up with the visible box, not the invisible reserve.
  if (padClock && id === 'clock' && vw && vh) {
    halfW += (20 / vw) * 100
    halfH += (20 / vh) * 100
  }
  return { id, x: c.x, y: c.y, halfW, halfH, k }
}

// Saved layouts can overlap (dragged before a widget existed, or defaults
// changed between versions). Push colliding boxes apart along the axis of
// least correction — recomputed from the saved centers every render, so the
// result is deterministic, self-heals as content resizes, and never touches
// the stored layout. Skipped in edit mode: the editor must show the real
// saved positions the user is manipulating.
const displayCenters = computed<Partial<Record<ScreensaverWidgetId, { x: number; y: number }>>>(() => {
  const boxes = new Map(mountedWidgets.value.map(id => [id, widgetBox(id)] as const))
  if (!props.layoutEdit) {
    const SEP_GAP = 1.5 // % of viewport kept between widget boxes
    const { w: vw, h: vh } = viewport.value
    const mx = vw ? (SS_EDGE_MARGIN_PX / vw) * 100 : 2.4
    const my = vh ? (SS_EDGE_MARGIN_PX / vh) * 100 : 4
    // How far a widget can travel along `sign` on the given axis before it
    // reaches its own viewport clamp bound — a widget pinned at the edge has
    // zero room and yields nothing, so the free one takes the whole push.
    const room = (w: WidgetBox, axis: 'x' | 'y', sign: number) => {
      if (axis === 'x') {
        const lim = Math.min(50, w.halfW + mx)
        const max = Math.max(50, 100 - w.halfW - mx)
        return sign > 0 ? Math.max(0, max - w.x) : Math.max(0, w.x - lim)
      }
      const lim = Math.min(50, w.halfH + my)
      const max = Math.max(50, 100 - w.halfH - my)
      return sign > 0 ? Math.max(0, max - w.y) : Math.max(0, w.y - lim)
    }
    for (let pass = 0; pass < 8; pass++) {
      let moved = false
      const ids = [...boxes.keys()]
      for (let i = 0; i < ids.length; i++) {
        for (let j = i + 1; j < ids.length; j++) {
          const a = boxes.get(ids[i])!
          const b = boxes.get(ids[j])!
          const needX = a.halfW + b.halfW + SEP_GAP - Math.abs(a.x - b.x)
          const needY = a.halfH + b.halfH + SEP_GAP - Math.abs(a.y - b.y)
          if (needX <= 0 || needY <= 0) continue
          moved = true
          // Push apart along the axis needing the smaller correction,
          // distributed by how much room each side can actually yield.
          const axis: 'x' | 'y' = needX <= needY ? 'x' : 'y'
          const need = Math.min(needX, needY)
          const d = axis === 'x' ? Math.sign(b.x - a.x) || 1 : Math.sign(b.y - a.y) || 1
          const roomA = room(a, axis, -d)
          const roomB = room(b, axis, d)
          const total = roomA + roomB
          if (total <= 0) continue
          const share = Math.min(need, total)
          if (axis === 'x') {
            a.x -= d * share * (roomA / total)
            b.x += d * share * (roomB / total)
          } else {
            a.y -= d * share * (roomA / total)
            b.y += d * share * (roomB / total)
          }
          for (const w of [a, b]) {
            const c = clampCenter(w.id, w.x, w.y, w.k)
            w.x = c.x
            w.y = c.y
          }
        }
      }
      if (!moved) break
    }
  }
  const out: Partial<Record<ScreensaverWidgetId, { x: number; y: number }>> = {}
  for (const [id, b] of boxes) out[id] = { x: b.x, y: b.y }
  return out
})

// `_sizeScale` is kept for the existing call sites; the widget-size slider is
// already folded into transformScale for the ids it applies to.
function posStyle(id: ScreensaverWidgetId, _sizeScale = 1) {
  const l = activeLayout.value[id]
  const k = transformScale(id, l.scale)
  const c = displayCenters.value[id] ?? clampCenter(id, l.x, l.y, k)
  return {
    left: `${c.x}%`,
    top: `${c.y}%`,
    transform: `translate(-50%, -50%) scale(${k})`,
  }
}

const clockStyle = computed(() => {
  const l = activeLayout.value.clock
  const k = transformScale('clock', l.scale)
  const c = displayCenters.value.clock ?? clampCenter('clock', l.x, l.y, k)
  return {
    left: `${c.x}%`,
    top: `${c.y}%`,
    transform:
      `translate(-50%, -50%) translate(${driftX.value}px, ${driftY.value}px) ` +
      `scale(${k})`,
  }
})

// --- Drag & resize (edit mode) ------------------------------------------------
const clampPos = (v: number) => Math.min(94, Math.max(6, v))
const clampScale = (v: number) => Math.min(2.5, Math.max(0.5, v))

interface SnapHold {
  guide: number        // % position of the alignment line snapped to
  anchorOffset: number // dragged-box anchor's offset from its center
}

let dragState: {
  id: ScreensaverWidgetId
  startX: number
  startY: number
  origX: number
  origY: number
  snapX: SnapHold | null
  snapY: SnapHold | null
} | null = null
let resizeState: { id: ScreensaverWidgetId; startY: number; origScale: number } | null = null

// Alignment guides shown while a drag snap holds — viewport % positions.
const guideV = ref<number[]>([])
const guideH = ref<number[]>([])
const SS_SNAP_PX = 8
const SS_SNAP_RELEASE_PX = 14

function startDrag(id: ScreensaverWidgetId, e: PointerEvent) {
  if (!props.layoutEdit) return
  e.preventDefault()
  e.stopPropagation()
  const l = editLayout.value[id]
  dragState = {
    id,
    startX: e.clientX,
    startY: e.clientY,
    origX: l.x,
    origY: l.y,
    snapX: null,
    snapY: null,
  }
  window.addEventListener('pointermove', onDragMove)
  window.addEventListener('pointerup', endInteraction, { once: true })
  window.addEventListener('pointercancel', endInteraction, { once: true })
}

// Snap one axis: compare the dragged box's edge/center anchors against the
// other widgets' edges/centers and the viewport center line. An engaged snap
// holds until the raw position clears the release band, so the boundary
// doesn't flicker.
function snapAxis(
  drag: { id: ScreensaverWidgetId; snapX: SnapHold | null; snapY: SnapHold | null },
  axis: 'x' | 'y',
  rawCenter: number,
  k: number,
): { pos: number; guide: number | null } {
  const { w: vw, h: vh } = viewport.value
  const span = axis === 'x' ? vw : vh
  const snapThresh = span ? (SS_SNAP_PX / span) * 100 : 0
  const releaseThresh = span ? (SS_SNAP_RELEASE_PX / span) * 100 : 0
  const hold = axis === 'x' ? drag.snapX : drag.snapY

  if (hold) {
    const snapped = hold.guide - hold.anchorOffset
    if (Math.abs(rawCenter - snapped) <= releaseThresh) {
      return { pos: snapped, guide: hold.guide }
    }
    if (axis === 'x') drag.snapX = null
    else drag.snapY = null
  }
  if (!span || !snapThresh) return { pos: rawCenter, guide: null }

  const size = widgetSizes.value[drag.id]
  const half = size ? (((axis === 'x' ? size.w : size.h) * k) / span) * 50 : 5
  const anchors = [-half, 0, half]
  const targets = [50] // viewport center line
  for (const id of mountedWidgets.value) {
    if (id === drag.id) continue
    const b = widgetBox(id, false)
    if (axis === 'x') targets.push(b.x - b.halfW, b.x, b.x + b.halfW)
    else targets.push(b.y - b.halfH, b.y, b.y + b.halfH)
  }

  let best: { guide: number; anchorOffset: number; d: number } | null = null
  for (const o of anchors) {
    for (const t of targets) {
      const d = t - (rawCenter + o)
      if (Math.abs(d) <= snapThresh && (!best || Math.abs(d) < Math.abs(best.d))) {
        best = { guide: t, anchorOffset: o, d }
      }
    }
  }
  if (!best) return { pos: rawCenter, guide: null }

  const next: SnapHold = { guide: best.guide, anchorOffset: best.anchorOffset }
  if (axis === 'x') drag.snapX = next
  else drag.snapY = next
  return { pos: best.guide - best.anchorOffset, guide: best.guide }
}

function onDragMove(e: PointerEvent) {
  if (!dragState) return
  const dx = ((e.clientX - dragState.startX) / window.innerWidth) * 100
  const dy = ((e.clientY - dragState.startY) / window.innerHeight) * 100
  const l = editLayout.value[dragState.id]
  const k = transformScale(dragState.id, l.scale)
  const rawX = dragState.origX + dx
  const rawY = dragState.origY + dy

  const sx = snapAxis(dragState, 'x', rawX, k)
  const sy = snapAxis(dragState, 'y', rawY, k)
  const c = clampCenter(dragState.id, sx.pos, sy.pos, k)

  // Edge clamping can shift a snapped position — then the alignment isn't
  // real, so drop the guide rather than show it where the widget isn't.
  if (sx.guide != null && c.x !== sx.pos) {
    dragState.snapX = null
    sx.guide = null
  }
  if (sy.guide != null && c.y !== sy.pos) {
    dragState.snapY = null
    sy.guide = null
  }

  l.x = c.x
  l.y = c.y
  guideV.value = sx.guide != null ? [sx.guide] : []
  guideH.value = sy.guide != null ? [sy.guide] : []
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
  guideV.value = []
  guideH.value = []
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
  onViewportResize()
  window.addEventListener('resize', onViewportResize)
  if (typeof ResizeObserver !== 'undefined') {
    widgetObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        for (const [id, el] of widgetEls) {
          if (el === entry.target) {
            measureWidget(id)
            break
          }
        }
      }
    })
    for (const el of widgetEls.values()) widgetObserver.observe(el)
  }
  if (showWeatherWidget.value) startWeather()
  if (showNewsWidget.value) startNews()
  if (showSportsWidget.value) startSports()
  if (showMarketWidget.value) startMarket()
})

onUnmounted(() => {
  if (clockTimer) clearInterval(clockTimer)
  if (driftTimer) clearInterval(driftTimer)
  widgetObserver?.disconnect()
  widgetObserver = null
  endInteraction()
  window.removeEventListener('resize', onViewportResize)
  window.removeEventListener('pointerup', endInteraction)
  window.removeEventListener('pointercancel', endInteraction)
  stopWeather()
  stopNews()
  stopSports()
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

/* --- Editorial type system (mockup) -----------------------------------------
   JetBrains Mono for meta/labels, Instrument Serif for display values,
   gold accent for the colon + article numbers. */
.screensaver {
  font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
}

.ss-serif,
.ss-time,
.ss-weather-temp,
.ss-market-value,
.ss-tz-time,
.ss-article-title {
  font-family: 'Instrument Serif', Georgia, 'Times New Roman', serif;
}

.ss-time {
  display: flex;
  align-items: center;
  font-size: clamp(5rem, 17vw, 21rem);
  line-height: 0.86;
  letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums;
  color: rgba(255, 255, 255, 0.94);
}

.ss-time-colon {
  color: var(--ss-accent, #f2b040);
  opacity: 0.85;
  padding: 0 0.04em 0.06em 0.04em;
}

.ss-date-line {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: clamp(1rem, 2.4vw, 2rem);
  margin-top: clamp(0.8rem, 2.4vh, 1.6rem);
}

.ss-rule {
  width: clamp(40px, 7vw, 120px);
  height: 1px;
  background-color: rgba(255, 255, 255, 0.22);
}

.ss-date {
  font-size: calc(clamp(0.7rem, 1.6vw, 1.4rem) * min(var(--touch-multiplier, 1), 1.3));
  letter-spacing: 0.32em;
  text-transform: uppercase;
  white-space: nowrap;
  color: rgba(255, 255, 255, 0.55);
}

/* --- Weather: top-left glance pill ----------------------------------------- */
.ss-weather {
  --ss-weather-scale: 1;
  display: flex;
  align-items: center;
  gap: calc(0.7rem * var(--ss-weather-scale));
  pointer-events: none;
}

.ss-weather-icon {
  font-size: calc(clamp(1.6rem, 3vw, 3.4rem) * var(--ss-weather-scale));
  color: var(--ss-accent, #f2b040);
  flex-shrink: 0;
}

.ss-weather-info {
  display: flex;
  flex-direction: column;
  gap: calc(0.3rem * var(--ss-weather-scale));
}

.ss-weather-loc {
  font-size: calc(clamp(0.55rem, 1vw, 0.95rem) * var(--ss-weather-scale));
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.5);
}

.ss-weather-temp {
  font-size: calc(clamp(1.8rem, 3.4vw, 4rem) * var(--ss-weather-scale));
  line-height: 0.9;
  font-variant-numeric: tabular-nums;
  color: rgba(255, 255, 255, 0.94);
}

/* --- Market: top-right serif quote rows ------------------------------------- */
.ss-market {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.9rem;
}

.ss-market-row {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.25rem;
}

.ss-market-symbol {
  font-size: clamp(0.55rem, 1vw, 0.95rem);
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.5);
}

.ss-market-value {
  font-size: clamp(1.8rem, 3.4vw, 4rem);
  line-height: 0.9;
  font-variant-numeric: tabular-nums;
  color: rgba(255, 255, 255, 0.94);
}

/* --- Sections: headlines / sports / world time ------------------------------ */
.ss-section {
  display: flex;
  flex-direction: column;
  gap: clamp(0.8rem, 2vh, 1.6rem);
  min-width: 0;
}

.ss-section-head {
  display: flex;
  align-items: center;
  gap: 1.1rem;
}

.ss-section-head h2 {
  margin: 0;
  font-size: clamp(0.6rem, 1.1vw, 1rem);
  font-weight: 500;
  line-height: 1;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  white-space: nowrap;
  color: rgba(255, 255, 255, 0.5);
}

.ss-hairline {
  flex-grow: 1;
  height: 1px;
  background-color: rgba(255, 255, 255, 0.14);
}

/* Numbered articles — a tap lands on the headline you actually saw, unlike
   a sliding carousel row. */
.ss-article-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  column-gap: clamp(1.2rem, 3vw, 3rem);
  row-gap: clamp(0.9rem, 2.4vh, 2rem);
}

.ss-article-list {
  display: flex;
  flex-direction: column;
  gap: clamp(0.9rem, 2.4vh, 2rem);
}

.ss-article {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  min-width: 0;
  cursor: pointer;
  border-radius: 8px;
  padding: 4px 6px;
  margin: -4px -6px;
  min-height: 44px;
  min-height: max(var(--min-touch-target, 44px), 44px);
  transition: background 0.15s ease;
}

.ss-article:hover {
  background: rgba(255, 255, 255, 0.06);
}

.ss-article:active {
  background: rgba(255, 255, 255, 0.12);
}

.ss-article:focus-visible {
  outline: 2px solid var(--ss-accent, #f2b040);
  outline-offset: -2px;
}

.ss-article-meta {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  font-size: clamp(0.55rem, 1vw, 0.9rem);
  line-height: 1;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.5);
}

.ss-article-num {
  color: var(--ss-accent, #f2b040);
}

.ss-article-source {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ss-article-open {
  width: 0.95em;
  height: 0.95em;
  margin-left: auto;
  flex-shrink: 0;
  opacity: 0.55;
}

.ss-article-title {
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  font-size: clamp(1rem, 1.9vw, 2.1rem);
  font-weight: 400;
  line-height: 1.16;
  color: rgba(255, 255, 255, 0.94);
  text-wrap: pretty;
}

.ss-empty {
  padding: 10px 4px;
  font-size: 0.9em;
  opacity: 0.7;
}

/* Section widths — headlines widest, sports and world time narrower. */
.ss-news {
  width: clamp(300px, 46vw, 720px);
}

.ss-sports {
  width: clamp(220px, 24vw, 420px);
}

.ss-worldclock {
  width: clamp(180px, 19vw, 360px);
}

.ss-news,
.ss-sports,
.ss-worldclock {
  max-height: 52vh;
  overflow: hidden;
}

/* World time rows: mono city label beside a large serif time. */
.ss-tz {
  display: flex;
  flex-direction: column;
}

.ss-tz-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 0.8rem;
  padding: clamp(0.5rem, 1.6vh, 1.1rem) 0;
  border-top: 1px solid rgba(255, 255, 255, 0.14);
}

.ss-tz-row:first-child {
  border-top: none;
}

.ss-tz-label {
  font-size: clamp(0.6rem, 1.3vw, 1.2rem);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.62);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ss-tz-time {
  font-size: clamp(1.6rem, 3vw, 3.4rem);
  line-height: 1;
  font-variant-numeric: tabular-nums;
  color: rgba(255, 255, 255, 0.94);
}

/* The market chip is right-aligned; stretch its section head full width. */
.ss-market .ss-section-head {
  align-self: stretch;
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

.ss-guide {
  position: absolute;
  pointer-events: none;
  /* Above the widgets (z 2), under the edit toolbar (z 4). */
  z-index: 3;
}

.ss-guide-v {
  top: 0;
  bottom: 0;
  width: 0;
  border-left: 2px dashed var(--accent, #7aa2ff);
  transform: translateX(-1px);
  filter: drop-shadow(0 0 3px rgba(0, 0, 0, 0.9)) drop-shadow(0 0 1px rgba(0, 0, 0, 0.9));
}

.ss-guide-h {
  left: 0;
  right: 0;
  height: 0;
  border-top: 2px dashed var(--accent, #7aa2ff);
  transform: translateY(-1px);
  filter: drop-shadow(0 0 3px rgba(0, 0, 0, 0.9)) drop-shadow(0 0 1px rgba(0, 0, 0, 0.9));
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
  .ss-article {
    transition: none;
  }
}

/* Short screens (7" panels are ~480px tall): the reading sections can't fit
   two-line headlines under the clock, so titles drop to one line and the
   grid tightens up. */
@media (max-height: 560px) {
  /* 17vw of an 800px panel is a ~136px digit row — too tall to sit above the
     sections, so the clock itself shrinks on short screens. */
  .ss-time {
    font-size: clamp(3.5rem, 17vh, 10rem);
  }

  .ss-article-grid,
  .ss-article-list {
    row-gap: 0.7rem;
    gap: 0.7rem;
  }

  .ss-article {
    min-height: 40px;
    min-height: max(40px, calc(var(--min-touch-target, 44px) * 0.9));
  }

  .ss-article-title {
    -webkit-line-clamp: 1;
    font-size: clamp(0.85rem, 2vw, 1.4rem);
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

/* ── Mobile screensaver (DL-063) ─────────────────────────────────────────
   Phones get a dedicated sparse layout: clock + world clock, centered in a
   flow column — the saved desktop positions/drift would scatter widgets
   off a small screen, so .ss-pos is flattened (inline styles need
   !important). Landscape-first sizing: height is the scarce dimension. */
.screensaver.ss-mobile {
  gap: clamp(10px, 4vh, 22px);
  padding: 0 5vw;
}

.screensaver.ss-mobile .ss-pos {
  position: static !important;
  left: auto !important;
  top: auto !important;
  transform: none !important;
}

.screensaver.ss-mobile .ss-time {
  font-size: clamp(3rem, 26vh, 9rem);
}

.screensaver.ss-mobile .ss-date-line {
  margin-top: clamp(4px, 1.5vh, 10px);
  gap: 0.7rem;
}

.screensaver.ss-mobile .ss-rule {
  width: clamp(28px, 8vw, 64px);
}

.screensaver.ss-mobile .ss-date {
  font-size: clamp(0.55rem, 3vw, 0.85rem);
  letter-spacing: 0.24em;
}

/* World clock: vertical rows become a wrapped row of compact chips —
   label over time — so several zones fit without a tall list. */
.screensaver.ss-mobile .ss-worldclock {
  width: 100%;
  max-width: 560px;
  gap: clamp(6px, 1.8vh, 12px);
}

.screensaver.ss-mobile .ss-section-head {
  justify-content: center;
}

.screensaver.ss-mobile .ss-section-head .ss-hairline {
  display: none;
}

.screensaver.ss-mobile .ss-tz {
  flex-direction: row;
  flex-wrap: wrap;
  justify-content: center;
}

.screensaver.ss-mobile .ss-tz-row {
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 4px 16px;
  border-top: none;
  border-left: 1px solid rgba(255, 255, 255, 0.14);
}

.screensaver.ss-mobile .ss-tz-row:first-child {
  border-left: none;
}

.screensaver.ss-mobile .ss-tz-label {
  font-size: clamp(0.55rem, 2.6vw, 0.75rem);
}

.screensaver.ss-mobile .ss-tz-time {
  font-size: clamp(1.05rem, 5.5vh, 1.7rem);
}
</style>
