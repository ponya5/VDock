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
    <AgentSessionPicker
      v-if="sessionMarker"
      :rows="sessionRows"
      :pinned-pid="pinnedPid"
      :resolved-pid="resolvedPid"
      :waiting-glow-on="waitingGlowOn"
      :target-label="targetLabel"
      :effective-session="effectiveSession"
      @pick="chooseTarget"
      @identify="identify"
      @opened="refreshTargets"
    />
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
import { computed, toRef } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import type { Scene } from '@/types'
import { useDashboardStore } from '@/stores/dashboard'
import { useSettingsStore } from '@/stores/settings'
import { trackAgentSurfaceVisibility, useAgentSession } from '@/composables/useAgentSession'
import {
  profileSessionMarker,
  useAgentTargets,
} from '@/composables/useAgentTargets'
import { isAgentWaitingDismissed } from '@/services/agentWaiting'
import AgentSessionPicker from '@/components/AgentSessionPicker.vue'

/**
 * Agent action bar (DL-064): on a Claude Code / Cursor / Devin scene, shows
 * what the agent is doing right now and the actions that fit that moment —
 * Submit while it waits for a prompt, Interrupt while it works, Approve/Deny
 * while a permission dialog is open.
 */

const props = defineProps<{ scene: Scene | null }>()

const dashboardStore = useDashboardStore()
const settingsStore = useSettingsStore()
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
  effectiveSession,
  targetLabel,
  refresh: refreshTargets,
  setTarget,
  identify,
} = useAgentTargets(sessionMarker)

// DL-080: the "waiting" cue the edge glow announces globally; the picker
// chip and its rows point at WHICH session is idle. A snoozed episode
// (dismissAgentWaiting) quiets the pulse/nudge until the next ready event.
const waitingGlowOn = computed(() =>
  settingsStore.agentWaitingGlowEnabled !== false &&
  !isAgentWaitingDismissed(profile.value?.status_source)
)

async function chooseTarget(pid: number | null) {
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
  flex-wrap: wrap; /* tablets: when the buttons can't fit beside the state + picker, they drop to their own row */
  align-items: stretch;
  gap: clamp(8px, 1.4vw, 14px);
  margin: 12px 12px 0;
  padding: clamp(6px, 1.2vh, 10px);
  border-radius: 18px;
  flex-shrink: 0;
  background: rgba(15, 20, 28, 0.72);
  border: 1px solid color-mix(in srgb, var(--agent-accent) 45%, transparent);
  box-shadow: 0 0 18px color-mix(in srgb, var(--agent-accent) 22%, transparent);
  -webkit-backdrop-filter: blur(10px);
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

.agent-actions {
  display: flex;
  flex: 1 1 340px;
  flex-wrap: wrap;
  min-width: 0;
  gap: clamp(6px, 1vw, 10px);
}

.agent-action {
  /* A floor keeps every label readable; extra buttons wrap instead of
     squeezing to "S…" / "C…". */
  flex: 1 1 96px;
  min-width: 88px;
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
  /* Wrap onto a second line rather than truncating. */
  overflow: hidden;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  text-align: center;
  line-height: 1.15;
  overflow-wrap: anywhere;
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
   into equal columns rather than shrinking below a touchable width. */
@media (max-width: 720px) {
  .agent-action-bar {
    flex-direction: column;
  }

  .agent-actions {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  }
}

/* Up to 7"-panel and 10" tablet widths: stack icon over label so six buttons
   fit a row (or a wrapped grid) without truncating their labels. */
@media (max-width: 1400px) {
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
