<template>
  <!-- DL-125: third screensaver style — a fullscreen system monitor.
       Nothing here is interactive: every tap bubbles to the ScreenSaver
       root dismiss handler, like the spectrum stage without its media bar. -->
  <div class="stats-stage" :class="{ 'is-stale': stale }">
    <header class="st-head">
      <div class="st-id">
        <span class="st-dot" :class="{ 'st-dot-bad': stale || error }"></span>
        <span class="st-host">{{ stats?.hostname || 'this machine' }}</span>
        <span v-if="uptimeText" class="st-meta">up {{ uptimeText }}</span>
        <span v-if="stale" class="st-flag">retrying</span>
      </div>
      <div class="st-clock">{{ clockText }}</div>
    </header>

    <div v-if="stats" class="st-grid">
      <!-- CPU: hero number + per-core strip — the strip redraws every poll
           so the board always reads alive. -->
      <section class="st-card">
        <div class="st-card-head">
          <h3>CPU</h3>
          <span class="st-sub">{{ cpuSub }}</span>
        </div>
        <div class="st-hero">
          <span class="st-hero-num" :class="toneClass(stats.cpuPercent)">{{ fmtPct(stats.cpuPercent) }}</span>
        </div>
        <svg v-if="cpuHistory.length > 1" class="st-spark" viewBox="0 0 100 26" preserveAspectRatio="none" aria-hidden="true">
          <polyline :points="cpuSparkPoints" fill="none" stroke-width="1.5" />
        </svg>
        <div v-if="stats.cpuPerCore.length" class="st-cores" aria-hidden="true">
          <span
            v-for="(core, i) in stats.cpuPerCore"
            :key="i"
            class="st-core"
            :title="`Core ${i + 1}: ${Math.round(core)}%`"
          >
            <i :class="toneClass(core)" :style="{ height: clampPct(core) + '%' }"></i>
          </span>
        </div>
      </section>

      <section class="st-card">
        <div class="st-card-head">
          <h3>Memory</h3>
          <span class="st-sub">{{ memSub }}</span>
        </div>
        <div class="st-hero">
          <span class="st-hero-num" :class="toneClass(stats.memPercent)">{{ fmtPct(stats.memPercent) }}</span>
        </div>
        <span class="st-bar" role="meter" :aria-valuenow="stats.memPercent ?? undefined" aria-valuemin="0" aria-valuemax="100">
          <i class="st-fill" :class="toneClass(stats.memPercent)" :style="{ width: clampPct(stats.memPercent) + '%' }"></i>
        </span>
        <div class="st-detail">{{ memDetail }}</div>
      </section>

      <section class="st-card">
        <div class="st-card-head">
          <h3>Disk</h3>
          <span class="st-sub">{{ diskIoText }}</span>
        </div>
        <div v-if="stats.diskPartitions.length" class="st-parts">
          <div v-for="p in stats.diskPartitions" :key="p.mount" class="st-part">
            <span class="st-part-mount">{{ p.mount }}</span>
            <span class="st-bar" role="meter" :aria-valuenow="p.percent" aria-valuemin="0" aria-valuemax="100" :aria-label="`${p.mount} fullness`">
              <i class="st-fill" :class="toneClass(p.percent)" :style="{ width: clampPct(p.percent) + '%' }"></i>
            </span>
            <span class="st-part-val" :class="toneClass(p.percent)">{{ Math.round(p.percent) }}%</span>
          </div>
        </div>
        <div v-else-if="stats.diskPercent != null" class="st-hero">
          <span class="st-hero-num" :class="toneClass(stats.diskPercent)">{{ fmtPct(stats.diskPercent) }}</span>
        </div>
        <div v-else class="st-detail">No disk data</div>
      </section>

      <section class="st-card">
        <div class="st-card-head">
          <h3>Network</h3>
          <span class="st-sub">vs recent peak</span>
        </div>
        <div class="st-net">
          <div class="st-net-dir">
            <span class="st-net-label">Down</span>
            <span class="st-net-rate">{{ fmtRate(stats.netDownBps) }}</span>
          </div>
          <div class="st-net-dir">
            <span class="st-net-label">Up</span>
            <span class="st-net-rate">{{ fmtRate(stats.netUpBps) }}</span>
          </div>
        </div>
        <svg v-if="netHistory.length > 1" class="st-spark" viewBox="0 0 100 26" preserveAspectRatio="none" aria-hidden="true">
          <polyline :points="netSparkPoints" fill="none" stroke-width="1.5" />
        </svg>
      </section>
    </div>

    <div v-else class="st-empty">
      <FontAwesomeIcon :icon="['fas', 'server']" />
      <span>{{ error || (loading ? 'Reading metrics…' : 'No metrics') }}</span>
    </div>

    <footer v-if="stats" class="st-foot">
      <div v-if="stats.topProcesses.length" class="st-procs">
        <span class="st-procs-label">Top CPU</span>
        <span v-for="p in stats.topProcesses" :key="p.name" class="st-proc">
          {{ p.name }}<b>{{ p.cpuPercent != null ? Math.round(p.cpuPercent) + '%' : '' }}</b>
        </span>
      </div>
      <span class="spacer"></span>
      <div class="st-chips">
        <span v-if="stats.tempC != null" class="st-chip">{{ Math.round(stats.tempC) }}°C</span>
        <span v-if="stats.batteryPercent != null" class="st-chip">
          {{ stats.batteryCharging ? 'Charging' : 'Battery' }} {{ Math.round(stats.batteryPercent) }}%
        </span>
        <span v-if="stats.processCount != null" class="st-chip">{{ stats.processCount }} processes</span>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useSystemStats } from '@/composables/useSystemStats'

const { stats, loading, error, stale, start, stop } = useSystemStats()

const HISTORY_LEN = 48
const cpuHistory = ref<number[]>([])
const netHistory = ref<number[]>([])

watch(stats, (s) => {
  if (!s) return
  if (s.cpuPercent != null) {
    cpuHistory.value = [...cpuHistory.value.slice(-(HISTORY_LEN - 1)), s.cpuPercent]
  }
  if (s.netDownBps != null || s.netUpBps != null) {
    const total = (s.netDownBps ?? 0) + (s.netUpBps ?? 0)
    netHistory.value = [...netHistory.value.slice(-(HISTORY_LEN - 1)), total]
  }
})

function sparkPoints(series: number[], max: number): string {
  if (!series.length) return ''
  const peak = Math.max(max, ...series) || 1
  const step = series.length > 1 ? 100 / (series.length - 1) : 0
  return series
    .map((v, i) => `${(i * step).toFixed(1)},${(25 - (Math.min(v, peak) / peak) * 23).toFixed(1)}`)
    .join(' ')
}

const cpuSparkPoints = computed(() => sparkPoints(cpuHistory.value, 100))
const netSparkPoints = computed(() => sparkPoints(netHistory.value, 1))

/* Live clock — a per-second pulse keeps the board visibly fresh between
   the 2.5 s metric polls. */
const now = ref(new Date())
let clockTimer: ReturnType<typeof setInterval> | null = null
const clockText = computed(() =>
  now.value.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
)

onMounted(() => {
  start()
  clockTimer = setInterval(() => { now.value = new Date() }, 1000)
})
onUnmounted(() => {
  stop()
  if (clockTimer) clearInterval(clockTimer)
})

const clampPct = (v: number | null) => Math.min(100, Math.max(0, v ?? 0))
const fmtPct = (v: number | null) => (v == null ? '—' : `${Math.round(v)}%`)

/** Same thresholds as SystemStatsWidget / the backend stamps: warn ≥85,
 *  critical ≥95. */
const toneClass = (v: number | null) =>
  v == null ? '' : v >= 95 ? 'is-crit' : v >= 85 ? 'is-warn' : ''

function fmtRate(bps: number | null): string {
  if (bps == null) return '—'
  if (bps >= 1024 * 1024) return `${(bps / (1024 * 1024)).toFixed(1)} MB/s`
  if (bps >= 1024) return `${Math.round(bps / 1024)} KB/s`
  return `${Math.round(bps)} B/s`
}

const uptimeText = computed(() => {
  const h = stats.value?.uptimeHours
  if (h == null) return null
  if (h >= 48) return `${Math.round(h / 24)}d`
  if (h >= 1) return `${Math.floor(h)}h ${Math.round((h % 1) * 60)}m`
  return `${Math.round(h * 60)}m`
})

const cpuSub = computed(() => {
  const s = stats.value
  if (!s) return ''
  const cores = s.cpuPerCore.length ? `${s.cpuPerCore.length} threads` : null
  const freq = s.cpuFreqMhz != null ? `${(s.cpuFreqMhz / 1000).toFixed(1)} GHz` : null
  return [cores, freq].filter(Boolean).join(' · ') || ' '
})

const memSub = computed(() => 'RAM')

const memDetail = computed(() => {
  const s = stats.value
  if (!s || s.memUsedGb == null || s.memTotalGb == null) return ' '
  return `${s.memUsedGb.toFixed(1)} of ${s.memTotalGb.toFixed(1)} GB in use`
})

const diskIoText = computed(() => {
  const s = stats.value
  if (!s || (s.diskReadBps == null && s.diskWriteBps == null)) return ' '
  return `R ${fmtRate(s.diskReadBps)} · W ${fmtRate(s.diskWriteBps)}`
})
</script>

<style scoped>
.stats-stage {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  padding: clamp(18px, 3.5vh, 40px) clamp(20px, 4vw, 56px);
  background: #04060c;
  color: rgba(255, 255, 255, 0.94);
  font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
}

.st-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: clamp(10px, 1.6vh, 18px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
}

.st-id {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.st-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #3ddc97;
  flex: none;
}
.st-dot-bad { background: #f5b547; }

.st-host {
  font-size: clamp(0.7rem, 1.4vw, 0.95rem);
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.75);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.st-meta {
  font-size: clamp(0.6rem, 1.1vw, 0.75rem);
  letter-spacing: 0.1em;
  color: rgba(255, 255, 255, 0.4);
  white-space: nowrap;
}

.st-flag {
  font-size: 0.6rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #fbbf24;
}

.st-clock {
  font-family: 'Instrument Serif', Georgia, 'Times New Roman', serif;
  font-size: clamp(1.4rem, 3.4vw, 2.6rem);
  line-height: 1;
  font-variant-numeric: tabular-nums;
  color: rgba(255, 255, 255, 0.92);
}

.st-grid {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  grid-template-rows: repeat(2, minmax(0, 1fr));
  gap: clamp(12px, 2vw, 28px);
  padding: clamp(14px, 2.4vh, 26px) 0;
}

.st-card {
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: clamp(12px, 1.8vh, 20px) clamp(14px, 2vw, 24px);
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.03);
  overflow: hidden;
}

.st-card-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
}

.st-card-head h3 {
  margin: 0;
  font-size: clamp(0.6rem, 1.1vw, 0.8rem);
  font-weight: 500;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.5);
}

.st-sub {
  font-size: clamp(0.55rem, 1vw, 0.72rem);
  color: rgba(255, 255, 255, 0.38);
  white-space: nowrap;
}

.st-hero {
  flex: 1;
  display: flex;
  align-items: center;
  min-height: 0;
}

.st-hero-num {
  font-family: 'Instrument Serif', Georgia, 'Times New Roman', serif;
  font-size: clamp(2.2rem, 7.5vh, 4.6rem);
  line-height: 1;
  font-variant-numeric: tabular-nums;
}

.is-warn { color: #fb923c; }
.is-crit { color: #ef4444; }

.st-spark {
  width: 100%;
  height: clamp(20px, 4vh, 34px);
  margin-top: auto;
  stroke: rgba(255, 255, 255, 0.55);
}

.st-cores {
  display: flex;
  align-items: flex-end;
  gap: 3px;
  height: clamp(26px, 5vh, 46px);
  margin-top: 8px;
}

.st-core {
  flex: 1;
  min-width: 2px;
  display: flex;
  align-items: flex-end;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.08);
  overflow: hidden;
}

.st-core i {
  display: block;
  width: 100%;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.7);
  transition: height 0.45s ease, background-color 0.45s ease;
}
.st-core i.is-warn { background: #fb923c; }
.st-core i.is-crit { background: #ef4444; }

.st-bar {
  display: block;
  height: 6px;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.1);
  overflow: hidden;
}

.st-fill {
  display: block;
  height: 100%;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.7);
  transition: width 0.45s ease, background-color 0.45s ease;
}
.st-fill.is-warn { background: #fb923c; }
.st-fill.is-crit { background: #ef4444; }

.st-detail {
  margin-top: 8px;
  font-size: clamp(0.55rem, 1vw, 0.75rem);
  color: rgba(255, 255, 255, 0.45);
}

.st-parts {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: clamp(8px, 1.6vh, 16px);
  min-height: 0;
}

.st-part {
  display: flex;
  align-items: center;
  gap: 10px;
}

.st-part-mount {
  width: 3.2em;
  flex: none;
  font-size: clamp(0.6rem, 1.1vw, 0.8rem);
  color: rgba(255, 255, 255, 0.55);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.st-part .st-bar { flex: 1; }

.st-part-val {
  min-width: 3em;
  text-align: right;
  font-size: clamp(0.6rem, 1.1vw, 0.8rem);
  font-variant-numeric: tabular-nums;
}

.st-net {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-around;
  gap: 12px;
  min-height: 0;
}

.st-net-dir {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.st-net-label {
  font-size: clamp(0.55rem, 1vw, 0.72rem);
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.4);
}

.st-net-rate {
  font-family: 'Instrument Serif', Georgia, 'Times New Roman', serif;
  font-size: clamp(1.3rem, 4vh, 2.4rem);
  line-height: 1;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.st-foot {
  display: flex;
  align-items: center;
  gap: 16px;
  padding-top: clamp(10px, 1.6vh, 18px);
  border-top: 1px solid rgba(255, 255, 255, 0.12);
  min-height: 0;
}

.st-procs {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
  overflow: hidden;
}

.st-procs-label {
  flex: none;
  font-size: 0.6rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.4);
}

.st-proc {
  font-size: clamp(0.55rem, 1vw, 0.75rem);
  color: rgba(255, 255, 255, 0.6);
  white-space: nowrap;
}
.st-proc b {
  margin-left: 5px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
  font-variant-numeric: tabular-nums;
}

.st-chips {
  display: flex;
  gap: 8px;
  flex: none;
}

.st-chip {
  padding: 4px 10px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 999px;
  font-size: clamp(0.55rem, 1vw, 0.72rem);
  color: rgba(255, 255, 255, 0.65);
  white-space: nowrap;
}

.spacer { flex: 1; }

/* Stale-keep-last: numbers stay visible but dimmed — same contract as the
   widget strip; old data must never read as live. */
.is-stale .st-hero-num,
.is-stale .st-fill,
.is-stale .st-core i,
.is-stale .st-net-rate,
.is-stale .st-procs {
  opacity: 0.45;
}

.st-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: rgba(255, 255, 255, 0.45);
  font-size: clamp(0.7rem, 1.4vw, 0.95rem);
}

/* Narrow/short screens (phone portrait): one tall column of cards. */
@media (max-width: 640px), (max-aspect-ratio: 4/5) {
  .st-grid { grid-template-columns: 1fr; grid-template-rows: none; overflow-y: auto; }
  .st-card { min-height: 120px; }
}

@media (prefers-reduced-motion: reduce) {
  .st-fill, .st-core i { transition: none; }
}
</style>
