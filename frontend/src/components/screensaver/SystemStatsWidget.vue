<template>
  <section class="ssw" :class="{ 'is-stale': stale }">
    <div class="ssw-head">
      <h2>System</h2>
      <span class="ssw-hairline"></span>
      <span v-if="stale" class="ssw-flag" title="Showing the last reading — backend unreachable">retrying</span>
    </div>

    <div v-if="stats" class="ssw-rows">
      <div class="ssw-row">
        <span class="ssw-label">CPU</span>
        <span class="ssw-meter" role="meter" :aria-valuenow="stats.cpuPercent ?? undefined" aria-valuemin="0" aria-valuemax="100">
          <span class="ssw-fill" :class="toneClass(stats.cpuPercent)" :style="{ width: meterWidth(stats.cpuPercent) }"></span>
        </span>
        <span class="ssw-value">{{ fmtPct(stats.cpuPercent) }}</span>
      </div>

      <div class="ssw-row">
        <span class="ssw-label">MEM</span>
        <span class="ssw-meter" role="meter" :aria-valuenow="stats.memPercent ?? undefined" aria-valuemin="0" aria-valuemax="100">
          <span class="ssw-fill" :class="toneClass(stats.memPercent)" :style="{ width: meterWidth(stats.memPercent) }"></span>
        </span>
        <span class="ssw-value">{{ fmtPct(stats.memPercent) }}</span>
      </div>

      <div class="ssw-row">
        <span class="ssw-label">DISK</span>
        <span class="ssw-meter" role="meter" :aria-valuenow="stats.diskPercent ?? undefined" aria-valuemin="0" aria-valuemax="100">
          <span class="ssw-fill" :class="toneClass(stats.diskPercent)" :style="{ width: meterWidth(stats.diskPercent) }"></span>
        </span>
        <span class="ssw-value">{{ fmtPct(stats.diskPercent) }}</span>
      </div>

      <!-- GPU is absent from /metrics/all on machines without a readable GPU
           — the row only exists when a real number arrived. -->
      <div v-if="stats.gpuPercent != null" class="ssw-row">
        <span class="ssw-label">GPU</span>
        <span class="ssw-meter" role="meter" :aria-valuenow="stats.gpuPercent" aria-valuemin="0" aria-valuemax="100">
          <span class="ssw-fill" :class="toneClass(stats.gpuPercent)" :style="{ width: meterWidth(stats.gpuPercent) }"></span>
        </span>
        <span class="ssw-value">{{ fmtPct(stats.gpuPercent) }}</span>
      </div>

      <div class="ssw-row">
        <span class="ssw-label">NET</span>
        <span class="ssw-meter" role="meter" :aria-valuenow="netMeterPct" aria-valuemin="0" aria-valuemax="100" aria-label="Network activity vs recent peak">
          <span class="ssw-fill" :style="{ width: netMeterPct + '%' }"></span>
        </span>
        <span class="ssw-value ssw-value-net">{{ netText }}</span>
      </div>
    </div>

    <div v-else-if="error" class="ssw-empty ssw-down">
      <FontAwesomeIcon :icon="['fas', 'server']" class="ssw-down-icon" />
      <span>{{ error }}</span>
    </div>
    <div v-else class="ssw-empty">{{ loading ? 'Loading…' : '—' }}</div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useSystemStats } from '@/composables/useSystemStats'

// Contract: the parent may pass layoutEdit while dragging/resizing — this
// widget is passive so it only needs to accept the prop.
defineProps<{ layoutEdit?: boolean }>()

const { stats, loading, error, stale, start, stop } = useSystemStats()

onMounted(start)
onUnmounted(stop)

const fmtPct = (v: number | null) => (v == null ? '—' : `${Math.round(v)}%`)

const meterWidth = (v: number | null) => `${Math.min(100, Math.max(0, v ?? 0))}%`

/** Neutral white fill at normal load; warning orange at ≥85%, critical red
 *  at ≥95% — the same thresholds the backend stamps on each section. */
const toneClass = (v: number | null) =>
  v == null ? '' : v >= 95 ? 'is-crit' : v >= 85 ? 'is-warn' : ''

function fmtRate(bps: number | null): string {
  if (bps == null) return '—'
  if (bps >= 1024 * 1024) return `${(bps / (1024 * 1024)).toFixed(1)} MB/s`
  if (bps >= 1024) return `${Math.round(bps / 1024)} KB/s`
  return `${Math.round(bps)} B/s`
}

const netText = computed(() => {
  const s = stats.value
  if (!s || (s.netDownBps == null && s.netUpBps == null)) return '—'
  return `↓ ${fmtRate(s.netDownBps)}  ↑ ${fmtRate(s.netUpBps)}`
})

/** No fixed NIC speed is known, so the NET meter scales against the rolling
 *  peak throughput — it reads "busy vs the recent high", not a fake %. */
const netMeterPct = computed(() => {
  const s = stats.value
  if (!s || !s.netPeakBps) return 0
  const now = (s.netDownBps ?? 0) + (s.netUpBps ?? 0)
  return Math.min(100, Math.round((now / s.netPeakBps) * 100))
})
</script>

<style scoped>
/* Mirrors ScreenSaver.vue's .ss-section / .ss-section-head / .ss-market /
   .ss-empty visual language — scoped here because the parent's scoped styles
   don't reach child components. */
.ssw {
  display: flex;
  flex-direction: column;
  gap: clamp(0.6rem, 1.6vh, 1.1rem);
  width: clamp(190px, 22vw, 280px);
  min-width: 0;
  font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
}

.ssw-head {
  display: flex;
  align-items: center;
  gap: 1.1rem;
}

.ssw-head h2 {
  margin: 0;
  font-size: clamp(0.6rem, 1.1vw, 1rem);
  font-weight: 500;
  line-height: 1;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  white-space: nowrap;
  color: rgba(255, 255, 255, 0.5);
}

.ssw-hairline {
  flex-grow: 1;
  height: 1px;
  background-color: rgba(255, 255, 255, 0.14);
}

.ssw-flag {
  font-size: 0.55rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #fbbf24;
  white-space: nowrap;
}

.ssw-rows {
  display: flex;
  flex-direction: column;
  gap: clamp(0.45rem, 1.2vh, 0.8rem);
}

.ssw-row {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  min-height: 20px;
}

.ssw-label {
  width: 2.6em;
  flex-shrink: 0;
  font-size: clamp(0.55rem, 1vw, 0.85rem);
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.5);
}

.ssw-meter {
  flex: 1;
  min-width: 30px;
  height: 4px;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.12);
  overflow: hidden;
}

.ssw-fill {
  display: block;
  height: 100%;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.65);
  transition: width 0.4s ease, background-color 0.4s ease;
}

.ssw-fill.is-warn {
  background: #fb923c;
}

.ssw-fill.is-crit {
  background: #ef4444;
}

.ssw-value {
  flex-shrink: 0;
  min-width: 3em;
  text-align: right;
  font-size: clamp(0.6rem, 1.1vw, 0.95rem);
  font-variant-numeric: tabular-nums;
  color: rgba(255, 255, 255, 0.94);
}

.ssw-value-net {
  /* "↓ 1.2 MB/s  ↑ 340 KB/s" is the widest value — keep it on one line. */
  min-width: 0;
  font-size: clamp(0.5rem, 0.95vw, 0.8rem);
  white-space: nowrap;
}

/* Stale-keep-last: numbers stay but visibly dimmed, like the weather chip's
   is-unavailable — old data must never read as live data. */
.is-stale .ssw-value,
.is-stale .ssw-fill {
  opacity: 0.45;
}

.ssw-empty {
  padding: 10px 4px;
  font-size: 0.9em;
  opacity: 0.7;
  color: rgba(255, 255, 255, 0.62);
}

.ssw-down {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.ssw-down-icon {
  opacity: 0.5;
}
</style>
