<template>
  <div
    v-if="isVisible"
    class="agent-action-bar"
    :class="`state-${currentState}`"
    role="toolbar"
    :aria-label="`${profile?.label} actions`"
  >
    <div class="agent-state-pill" :title="stateEntry?.message || stateLabel">
      <span class="agent-state-dot" />
      <span class="agent-state-text">
        <strong>{{ profile?.label }}</strong>
        <span>{{ stateLabel }}</span>
      </span>
    </div>
    <div v-if="sessionMarker" class="agent-target">
      <button
        ref="chipRef"
        type="button"
        class="agent-target-chip"
        :class="{ pinned: pinnedPid !== null }"
        :title="`Buttons target: ${targetLabel}`"
        aria-haspopup="listbox"
        :aria-expanded="targetOpen"
        @click="toggleTargetPicker"
      >
        <FontAwesomeIcon :icon="['fas', 'crosshairs']" class="agent-target-icon" />
        <span class="agent-target-label">{{ targetLabel }}</span>
        <FontAwesomeIcon :icon="['fas', 'chevron-down']" class="agent-target-caret" />
      </button>
      <!-- Teleported: the bar's backdrop-filter makes it the containing block
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
          :style="popStyle"
          role="listbox"
        >
          <button
            type="button"
            class="agent-target-row"
            :class="{ active: pinnedPid === null }"
            @click="chooseTarget(null)"
          >
            <FontAwesomeIcon :icon="['fas', 'wand-magic-sparkles']" class="row-icon" />
            <span class="row-text">
              <span class="row-main">Auto</span>
              <span class="row-sub">focused project, else newest session</span>
            </span>
          </button>
          <div
            v-for="s in sessionRows"
            :key="s.pid"
            class="agent-target-row"
            :class="{ active: s.pid === pinnedPid }"
            role="option"
            :aria-selected="s.pid === pinnedPid"
          >
            <button
              type="button"
              class="row-pick"
              @click="chooseTarget(s.pid)"
            >
              <span class="row-dot" :class="`dot-${s.state || 'idle'}`" />
              <span class="row-text">
                <span class="row-main">
                  {{ s.label }}
                  <span v-if="s.pid === resolvedPid && pinnedPid === null" class="row-tag">auto</span>
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
              @click.stop="identify(s.pid)"
            >
              <FontAwesomeIcon :icon="['fas', 'eye']" />
            </button>
          </div>
          <p v-if="!sessionRows.length" class="agent-target-empty">
            No live session windows found
          </p>
        </div>
      </Teleport>
    </div>
    <div class="agent-actions">
      <button
        v-for="action in visibleActions"
        :key="action.id"
        type="button"
        class="agent-action"
        :class="{ primary: action.isPrimary, running: runningActionId === action.id }"
        :disabled="runningActionId !== null"
        :title="action.description"
        @click="runAction(action)"
      >
        <FontAwesomeIcon
          class="agent-action-icon"
          :icon="['fas', runningActionId === action.id ? 'spinner' : action.icon]"
          :spin="runningActionId === action.id"
        />
        <span class="agent-action-label">{{ action.label }}</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, toRef } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import type { Scene } from '@/types'
import { useDashboardStore } from '@/stores/dashboard'
import { trackAgentSurfaceVisibility, useAgentSession } from '@/composables/useAgentSession'
import {
  profileSessionMarker,
  useAgentTargets,
  type AgentSessionRow,
} from '@/composables/useAgentTargets'

/**
 * Agent action bar (DL-064): on a Claude Code / Cursor / Devin scene, shows
 * what the agent is doing right now and the actions that fit that moment —
 * Submit while it waits for a prompt, Interrupt while it works, Approve/Deny
 * while a permission dialog is open.
 */

const props = defineProps<{ scene: Scene | null }>()

const dashboardStore = useDashboardStore()
const {
  profile,
  stateEntry,
  currentState,
  stateLabel,
  isAgentPossiblyRunning,
  visibleActions,
  runningActionId,
  runAction,
} = useAgentSession(toRef(props, 'scene'))

const isVisible = computed(() =>
  !dashboardStore.isEditMode && isAgentPossiblyRunning.value && visibleActions.value.length > 0
)

// DL-071: when several agent sessions run at once, this picker pins which one
// the buttons drive. The marker comes from the profile's commands ('claude',
// 'devin'); plain editor profiles have none and the chip stays hidden.
const sessionMarker = computed(() => profileSessionMarker(profile.value))
const {
  sessionRows,
  pinnedPid,
  resolvedPid,
  targetLabel,
  refresh: refreshTargets,
  setTarget,
  identify,
} = useAgentTargets(sessionMarker)
const targetOpen = ref(false)
const chipRef = ref<HTMLElement | null>(null)
const popStyle = ref<Record<string, string>>({})

function toggleTargetPicker() {
  targetOpen.value = !targetOpen.value
  if (!targetOpen.value) return
  void refreshTargets()
  // Anchor the teleported popover under the chip; clamp to the viewport so a
  // chip near the right edge never pushes the list offscreen. On narrow
  // screens the CSS takes over (`left/right: 8px` full-width sheet), so the
  // inline left is only set for wide viewports.
  const rect = chipRef.value?.getBoundingClientRect()
  if (rect) {
    const style: Record<string, string> = { top: `${rect.bottom + 8}px` }
    if (window.innerWidth > 720) {
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

async function chooseTarget(pid: number | null) {
  targetOpen.value = false
  // Picking a session flashes its window — "this one" made visible.
  if (pid !== null) void identify(pid)
  await setTarget(pid)
}

trackAgentSurfaceVisibility(computed(() => profile.value?.status_source), isVisible)
</script>

<style scoped>
/* Touch-sized for 7" panels: every height scales with the viewport so the bar
   stays one comfortable row at 1024x600 and still fits at 800x480. */
.agent-action-bar {
  --agent-accent: #38bdf8;
  --agent-action-height: clamp(52px, 11vh, 84px);
  display: flex;
  align-items: stretch;
  gap: clamp(8px, 1.4vw, 14px);
  margin: 12px 12px 0;
  padding: clamp(6px, 1.2vh, 10px);
  border-radius: 18px;
  flex-shrink: 0;
  background: rgba(15, 20, 28, 0.72);
  border: 1px solid color-mix(in srgb, var(--agent-accent) 45%, transparent);
  box-shadow: 0 0 18px color-mix(in srgb, var(--agent-accent) 22%, transparent);
  backdrop-filter: blur(10px);
  color: #e5e7eb;
}

.agent-action-bar.state-ready { --agent-accent: #22c55e; }
.agent-action-bar.state-working { --agent-accent: #38bdf8; }
.agent-action-bar.state-permission { --agent-accent: #f59e0b; }
.agent-action-bar.state-unknown { --agent-accent: #94a3b8; }

.agent-state-pill {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex: 0 0 auto;
  padding: 0 clamp(6px, 1vw, 12px);
}

.agent-state-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--agent-accent);
  box-shadow: 0 0 8px var(--agent-accent);
  flex-shrink: 0;
}

.state-working .agent-state-dot,
.state-permission .agent-state-dot {
  animation: agent-pulse 1.2s ease-in-out infinite;
}

.agent-state-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  line-height: 1.15;
  font-size: clamp(0.85rem, 2.6vh, 1.05rem);
  white-space: nowrap;
}

.agent-state-text strong {
  font-size: clamp(1rem, 3vh, 1.25rem);
}

.agent-state-text span {
  color: color-mix(in srgb, var(--agent-accent) 70%, #e5e7eb);
}

/* --- Session target picker (DL-071) ------------------------------------- */

.agent-target {
  position: relative;
  flex: 0 1 auto;
  min-width: 0;
  display: flex;
  align-items: stretch;
}

.agent-target-chip {
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

.agent-target-pop {
  position: fixed;
  z-index: 1501;
  min-width: 320px;
  max-width: min(480px, 92vw);
  max-height: 60vh;
  overflow-y: auto;
  padding: 8px;
  border-radius: 14px;
  background: rgba(18, 24, 33, 0.96);
  border: 1px solid color-mix(in srgb, var(--agent-accent) 35%, transparent);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(12px);
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
  background: color-mix(in srgb, var(--agent-accent) 18%, transparent);
}

/* The row is a container: row-pick selects, row-locate flashes the window. */
.row-pick {
  flex: 1;
  min-width: 0;
  min-height: 56px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 4px 10px 12px;
  border: none;
  background: transparent;
  color: inherit;
  font-size: clamp(0.95rem, 2.4vh, 1.1rem);
  text-align: left;
  cursor: pointer;
  touch-action: manipulation;
}

.row-locate {
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-right: 4px;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: rgba(229, 231, 235, 0.5);
  font-size: 1rem;
  cursor: pointer;
  touch-action: manipulation;
}

.row-locate:hover {
  background: rgba(255, 255, 255, 0.12);
  color: var(--agent-accent);
}

.row-icon {
  color: var(--agent-accent);
  flex-shrink: 0;
}

.row-dot {
  width: 10px;
  height: 10px;
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
  font-size: 0.82em;
  color: rgba(229, 231, 235, 0.55);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.row-pin {
  color: var(--agent-accent);
  flex-shrink: 0;
}

.agent-target-empty {
  padding: 10px 12px;
  margin: 0;
  font-size: 0.85rem;
  color: rgba(229, 231, 235, 0.55);
}

.agent-actions {
  display: flex;
  flex: 1;
  min-width: 0;
  gap: clamp(6px, 1vw, 10px);
}

.agent-action {
  flex: 1 1 0;
  min-width: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: var(--agent-action-height);
  padding: 0 clamp(8px, 1.2vw, 16px);
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.06);
  color: inherit;
  font-size: clamp(0.9rem, 2.6vh, 1.2rem);
  font-weight: 600;
  cursor: pointer;
  touch-action: manipulation;
  transition: background 0.15s ease, transform 0.1s ease;
}

.agent-action-icon {
  font-size: 1.25em;
  flex-shrink: 0;
}

.agent-action-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.agent-action:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.12);
}

.agent-action:active:not(:disabled) {
  transform: scale(0.97);
}

.agent-action:disabled {
  cursor: default;
  opacity: 0.6;
}

.agent-action.primary {
  background: var(--agent-accent);
  border-color: transparent;
  color: #0b1015;
}

.agent-action.running {
  opacity: 1;
}

@keyframes agent-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.35; }
}

/* Portrait / narrow panels: the state gets its own row and the actions wrap
   into equal columns rather than shrinking below a touchable width. The
   session popover becomes a full-width sheet under the bar with finger-sized
   rows — a 280 px floating dropdown is unusable on a phone. */
@media (max-width: 720px) {
  .agent-action-bar {
    flex-direction: column;
  }

  .agent-target-pop {
    left: 8px;
    right: 8px;
    min-width: 0;
    max-width: none;
    max-height: 55vh;
  }

  .row-pick {
    min-height: 52px;
  }

  .row-locate {
    width: 44px;
    height: 44px;
  }

  .agent-actions {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  }
}

/* Up to 7"-panel widths: stack icon over label so six buttons fit a row (or
   a wrapped grid) without truncating their labels. */
@media (max-width: 1100px) {
  .agent-action {
    flex-direction: column;
    gap: 4px;
    font-size: clamp(0.85rem, 2.6vh, 1.1rem);
  }

  .agent-action-icon {
    font-size: 1.4em;
  }
}

@media (prefers-reduced-motion: reduce) {
  .agent-state-dot { animation: none !important; }
}
</style>
