<template>
  <div class="agent-target">
    <button
      ref="chipRef"
      type="button"
      class="agent-target-chip"
      :class="{ pinned: pinnedPid !== null, waiting: showWaitingHint }"
      :title="`Buttons target: ${targetLabel}`"
      aria-haspopup="listbox"
      :aria-expanded="targetOpen"
      @click="toggleTargetPicker"
    >
      <FontAwesomeIcon :icon="['fas', 'crosshairs']" class="agent-target-icon" />
      <span class="agent-target-label">{{ targetLabel }}</span>
      <span v-if="showWaitingHint" class="row-tag tag-waiting chip-tag">waiting</span>
      <FontAwesomeIcon :icon="['fas', 'chevron-down']" class="agent-target-caret" />
      <!-- Another session is the idle one — a nudge dot so the user knows
           the picker holds a session that wants input. -->
      <span v-if="!showWaitingHint && anotherSessionWaiting" class="chip-waiting-nudge" aria-hidden="true" />
    </button>
    <!-- Teleported: ancestor backdrop-filter makes it the containing block
         for fixed/absolute descendants AND a stacking context that paints
         under the deck grid — a popover left inside it shows as a sliver
         behind the buttons and its backdrop only covers the bar. -->
    <Teleport to="body">
      <div
        v-if="targetOpen"
        class="agent-target-backdrop"
        @click="targetOpen = false"
      />
      <div
        v-if="targetOpen"
        class="agent-target-pop"
        :class="{ 'pop-sheet': popSheet }"
        :style="popStyle"
        role="listbox"
      >
        <div
          class="agent-target-row"
          :class="{ active: pinnedPid === null }"
          role="option"
          :aria-selected="pinnedPid === null"
        >
          <button
            type="button"
            class="row-pick"
            @click="chooseTarget(null)"
          >
            <FontAwesomeIcon :icon="['fas', 'wand-magic-sparkles']" class="row-icon" />
            <span class="row-text">
              <span class="row-main">Auto</span>
              <span class="row-sub">focused project, else newest session</span>
            </span>
          </button>
        </div>
        <div
          v-for="s in rows"
          :key="s.pid"
          class="agent-target-row"
          :class="{ active: s.pid === pinnedPid, waiting: waitingGlowOn && s.state === 'ready' && s.prompted === true }"
          role="option"
          :aria-selected="s.pid === pinnedPid"
        >
          <button
            type="button"
            class="row-pick"
            @click="chooseTarget(s.pid)"
          >
            <span
              class="row-badge"
              :style="{ background: s.accent }"
              aria-hidden="true"
            >{{ s.badge || '·' }}</span>
            <span class="row-dot" :class="`dot-${s.state || 'idle'}`" />
            <span class="row-text">
              <span class="row-main">
                {{ s.label }}
                <span v-if="s.pid === resolvedPid && pinnedPid === null" class="row-tag">auto</span>
                <span v-if="waitingGlowOn && s.state === 'ready' && s.prompted === true" class="row-tag tag-waiting">waiting</span>
              </span>
              <span class="row-sub">{{ rowSub(s) }}</span>
            </span>
            <FontAwesomeIcon
              v-if="s.pid === pinnedPid"
              :icon="['fas', 'thumbtack']"
              class="row-pin"
            />
          </button>
          <button
            type="button"
            class="row-locate"
            title="Flash this session's window"
            aria-label="Flash this session's window"
            @click.stop="emit('identify', s.pid)"
          >
            <FontAwesomeIcon :icon="['fas', 'eye']" />
          </button>
        </div>
        <p v-if="!rows.length" class="agent-target-empty">
          No live session windows found
        </p>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
// Shared agent-session target picker (DL-071 follow-up): one chip showing
// the current target plus a teleported listbox — anchored dropdown on
// roomy viewports, centered sheet on touch/small screens. Used by the
// desktop AgentActionBar and the MobileAgentConsole, which previously
// rendered a wrapping chip strip that ate a second row of the status
// card. Picking semantics differ per surface (mobile releases the pin on
// re-tap and vibrates), so the picker emits the raw intent and the parent
// applies it.
import { computed, ref } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import type { AgentSessionInfo, AgentSessionRow } from '@/composables/useAgentTargets'

const props = defineProps<{
  rows: AgentSessionRow[]
  pinnedPid: number | null
  resolvedPid: number | null
  /** True while the waiting-glow feature is on and unsnoozed. */
  waitingGlowOn: boolean
  targetLabel: string
  /** The session commands actually land on — resolved by the composable
      (focus/hwnd-aware), NOT a rows lookup. Drives the chip's waiting hint. */
  effectiveSession: AgentSessionInfo | null
}>()

const emit = defineEmits<{
  pick: [pid: number | null]
  identify: [pid: number]
  /** Popover opened — parents refresh the session list. */
  opened: []
}>()

const showWaitingHint = computed(() =>
  props.waitingGlowOn && props.effectiveSession?.state === 'ready' &&
  props.effectiveSession?.prompted === true
)
// A session other than the current target sits idle — the chip nudges the
// user into the picker, where that row carries the waiting flag.
const anotherSessionWaiting = computed(() =>
  props.waitingGlowOn &&
  props.rows.some(s => s.state === 'ready' && s.prompted === true && s.pid !== props.effectiveSession?.pid)
)

const targetOpen = ref(false)
const chipRef = ref<HTMLElement | null>(null)
const popStyle = ref<Record<string, string>>({})
const popSheet = ref(false)

function toggleTargetPicker() {
  targetOpen.value = !targetOpen.value
  if (!targetOpen.value) return
  emit('opened')
  // Sheet vs anchored dropdown is decided HERE alone (DL-071 follow-up 9)
  // — a .pop-sheet class carries the sheet styles, so the JS and the CSS
  // can't disagree. Touchscreens that aren't the primary pointer still
  // report maxTouchPoints, so they get the finger-sized sheet too.
  popSheet.value =
    window.matchMedia?.('(max-width: 720px), (max-height: 800px), (pointer: coarse)').matches === true ||
    navigator.maxTouchPoints > 0
  const rect = chipRef.value?.getBoundingClientRect()
  if (rect) {
    const style: Record<string, string> = { top: `${rect.bottom + 8}px` }
    if (!popSheet.value) {
      style.left = `${Math.max(8, Math.min(rect.left, window.innerWidth - 340))}px`
    }
    popStyle.value = style
  }
}

/** What identifies this session to a human: what it's doing (hook detail),
    then the window title, then when it started. */
function rowSub(s: AgentSessionRow): string {
  const bits: string[] = []
  if (s.detail) bits.push(s.detail)
  if (s.title && s.title !== s.label) bits.push(s.title)
  if (s.started) {
    bits.push(`since ${new Date(s.started * 1000)
      .toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`)
  }
  return bits.join(' · ') || s.cwd || ''
}

function chooseTarget(pid: number | null) {
  targetOpen.value = false
  emit('pick', pid)
}
</script>

<style scoped>
.agent-target {
  position: relative;
  flex: 0 1 auto;
  min-width: 0;
  display: flex;
  align-items: stretch;
}

.agent-target-chip {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  min-height: 44px;
  max-width: clamp(160px, 24vw, 320px);
  padding: 0 clamp(10px, 1.2vw, 14px);
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.06);
  color: inherit;
  font-size: clamp(0.9rem, 2.6vh, 1.1rem);
  font-weight: 600;
  cursor: pointer;
  touch-action: manipulation;
  white-space: nowrap;
}

.agent-target-chip.pinned {
  border-color: color-mix(in srgb, var(--agent-accent) 60%, transparent);
  color: color-mix(in srgb, var(--agent-accent) 80%, #e5e7eb);
}

.agent-target-chip.waiting {
  border-color: #4ade80;
  background: rgba(34, 197, 94, 0.2);
  animation: chip-waiting-pulse 1.6s ease-in-out infinite;
}

@keyframes chip-waiting-pulse {
  0%, 100% {
    background: rgba(34, 197, 94, 0.2);
    box-shadow: 0 0 0 2px rgba(34, 197, 94, 0.5), 0 0 14px rgba(34, 197, 94, 0.5);
  }
  50% {
    background: rgba(34, 197, 94, 0.36);
    box-shadow: 0 0 0 4px rgba(134, 239, 172, 0.8), 0 0 30px rgba(34, 197, 94, 0.85);
  }
}

/* The "waiting" tag spells out what the pulse means — same chip style the
   picker rows flag idle sessions with. */
.chip-tag {
  margin-left: 2px;
  flex-shrink: 0;
}

/* A session other than the target sits idle — small beacon on the chip. */
.chip-waiting-nudge {
  position: absolute;
  top: -5px;
  right: -5px;
  width: 13px;
  height: 13px;
  border-radius: 50%;
  background: #22c55e;
  border: 2px solid rgba(15, 20, 28, 0.9);
  box-shadow: 0 0 10px rgba(34, 197, 94, 0.9), 0 0 0 3px rgba(34, 197, 94, 0.3);
  animation: agent-picker-pulse 1.2s ease-in-out infinite;
}

.agent-target-chip:hover {
  background: rgba(255, 255, 255, 0.12);
}

.agent-target-icon {
  color: var(--agent-accent);
  flex-shrink: 0;
}

.agent-target-label {
  overflow: hidden;
  text-overflow: ellipsis;
}

.agent-target-caret {
  font-size: 0.75em;
  opacity: 0.7;
  flex-shrink: 0;
}

.agent-target-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1500;
}

/* Structural sizes (row heights, locate button, dot, padding) scale with
   --touch-multiplier / --min-touch-target; TEXT follows a viewport-height
   clamp instead — tablet mode doubles targets but the app keeps text
   modest, and a 2× font on a 7" panel reads worse than a tall row
   (DL-071 follow-up 8). --agent-accent can't resolve under <body> (the
   popover is teleported), so every use falls back to the working-state
   accent. */
.agent-target-pop {
  position: fixed;
  z-index: 1501;
  min-width: calc(320px * var(--touch-multiplier, 1));
  max-width: min(calc(480px * var(--touch-multiplier, 1)), 92vw);
  max-height: 70vh;
  overflow-y: auto;
  padding: calc(8px * var(--touch-multiplier, 1));
  border-radius: 14px;
  background: rgba(18, 24, 33, 0.96);
  border: 1px solid color-mix(in srgb, var(--agent-accent, #38bdf8) 35%, transparent);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.5);
  -webkit-backdrop-filter: blur(12px);
  backdrop-filter: blur(12px);
  color: #e5e7eb;
}

.agent-target-row {
  display: flex;
  align-items: center;
  gap: 4px;
  border-radius: 10px;
}

.agent-target-row:hover {
  background: rgba(255, 255, 255, 0.08);
}

.agent-target-row.active {
  background: color-mix(in srgb, var(--agent-accent, #38bdf8) 18%, transparent);
}

.agent-target-row.waiting {
  background: rgba(34, 197, 94, 0.18);
  box-shadow:
    inset 4px 0 0 #22c55e,
    inset 0 0 0 1.5px rgba(34, 197, 94, 0.55);
  animation: row-waiting-pulse 1.6s ease-in-out infinite;
}

@keyframes row-waiting-pulse {
  0%, 100% {
    background: rgba(34, 197, 94, 0.18);
    box-shadow: inset 4px 0 0 #22c55e, inset 0 0 0 1.5px rgba(34, 197, 94, 0.55);
  }
  50% {
    background: rgba(34, 197, 94, 0.34);
    box-shadow: inset 4px 0 0 #86efac, inset 0 0 0 1.5px rgba(134, 239, 172, 0.85);
  }
}

.tag-waiting {
  background: rgba(34, 197, 94, 0.25);
  color: #86efac;
  animation: agent-picker-pulse 2.4s ease-in-out infinite;
}

/* The row is a container: row-pick selects, row-locate flashes the window. */
.row-pick {
  flex: 1;
  min-width: 0;
  min-height: max(56px, var(--min-touch-target, 44px));
  display: flex;
  align-items: center;
  gap: calc(10px * var(--touch-multiplier, 1));
  padding: 10px 4px 10px 14px;
  border: none;
  background: transparent;
  color: inherit;
  font-size: clamp(1rem, 1.2vh + 0.65rem, 1.3rem);
  text-align: left;
  cursor: pointer;
  touch-action: manipulation;
}

.row-locate {
  flex-shrink: 0;
  width: max(48px, var(--min-touch-target, 44px));
  height: max(48px, var(--min-touch-target, 44px));
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-right: 4px;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: rgba(229, 231, 235, 0.5);
  font-size: 1.05rem;
  cursor: pointer;
  touch-action: manipulation;
}

.row-locate:hover {
  background: rgba(255, 255, 255, 0.12);
  color: var(--agent-accent, #38bdf8);
}

.row-icon {
  color: var(--agent-accent, #38bdf8);
  flex-shrink: 0;
}

/* Per-session identity chip — accent-colored, carries the host-app
   initials (WT/CU/PS); distinguishes sessions at a glance (DL-071 #11). */
.row-badge {
  flex-shrink: 0;
  min-width: calc(30px * var(--touch-multiplier, 1));
  height: calc(30px * var(--touch-multiplier, 1));
  padding: 0 5px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #10131a;
  font-size: calc(0.78rem * var(--touch-multiplier, 1));
  font-weight: 800;
  letter-spacing: 0.02em;
}

.row-dot {
  width: calc(11px * var(--touch-multiplier, 1));
  height: calc(11px * var(--touch-multiplier, 1));
  border-radius: 50%;
  flex-shrink: 0;
  background: #6b7280;
}

.row-dot.dot-ready { background: #22c55e; }
.row-dot.dot-working { background: #38bdf8; }
.row-dot.dot-permission { background: #f59e0b; }

.row-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}

.row-main {
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.row-tag {
  margin-left: 6px;
  padding: 1px 6px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.12);
  font-size: 0.7em;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.row-sub {
  font-size: 0.85em;
  color: rgba(229, 231, 235, 0.55);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.row-pin {
  color: var(--agent-accent, #38bdf8);
  flex-shrink: 0;
}

.agent-target-empty {
  padding: calc(12px * var(--touch-multiplier, 1)) calc(14px * var(--touch-multiplier, 1));
  margin: 0;
  font-size: 0.95rem;
  color: rgba(229, 231, 235, 0.55);
}

/* Sheet layout for the session popover — a centered, finger-sized list
   under the bar on narrow/short/touch screens (DL-071 follow-up 8). The
   class is set by toggleTargetPicker (JS is the single source of truth so
   media query and positioning can't desync, follow-up 9): it fires when
   (max-width:720px), (max-height:800px), (pointer:coarse), or
   navigator.maxTouchPoints > 0 — the last one has no CSS media
   equivalent, which is why the sheet can't live in a media query alone. */
.agent-target-pop.pop-sheet {
  left: 8px;
  right: 8px;
  margin-inline: auto;
  min-width: 0;
  max-width: calc(560px * var(--touch-multiplier, 1));
  max-height: 55vh;
}

.agent-target-pop.pop-sheet .row-pick {
  min-height: max(60px, calc(var(--min-touch-target, 44px) + 16px));
  font-size: clamp(1.05rem, 1.4vh + 0.7rem, 1.4rem);
}

.agent-target-pop.pop-sheet .row-sub {
  font-size: 0.92em;
}

.agent-target-pop.pop-sheet .row-locate {
  width: max(52px, var(--min-touch-target, 44px));
  height: max(52px, var(--min-touch-target, 44px));
}

@keyframes agent-picker-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.35; }
}

@media (prefers-reduced-motion: reduce) {
  .agent-target-chip.waiting,
  .chip-waiting-nudge,
  .agent-target-row.waiting { animation: none; }
}
</style>
