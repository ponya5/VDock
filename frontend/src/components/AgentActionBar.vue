<template>
  <div
    v-if="isVisible"
    class="agent-action-bar"
    :class="[`state-${displayState}`, { 'is-linked': !!linkAccent, 'is-working': displayState === 'working' }]"
    :style="linkAccent ? { '--link-accent': linkAccent } : undefined"
    role="toolbar"
    :aria-label="`${profile?.label} actions`"
  >
    <AgentStatusBanner
      variant="bar"
      :state="displayState"
      :agent-name="profile?.label ?? 'Agent'"
      :detail="stateEntry?.message || ''"
      :since-ms="sinceMs"
      :linked="linked"
      :link-accent="linkAccent"
      :others-summary="othersSummary"
    />
    <AgentSessionPicker
      v-if="sessionMarker"
      :rows="sessionRows"
      :pinned-pid="pinnedPid"
      :resolved-pid="resolvedPid"
      :waiting-glow-on="waitingGlowOn"
      :target-label="targetLabel"
      :effective-session="effectiveSession"
      :linked-accent="linkAccent"
      :linked-badge="linked?.badge"
      @pick="chooseTarget"
      @identify="identify"
      @opened="refreshTargets"
    />
    <AgentViewToggle
      v-if="showViewToggle"
      :model-value="agentView.mode.value"
      @update:model-value="agentView.setMode"
    />
    <div v-if="actionsVisible" class="agent-actions" :class="{ linked: !!linkAccent }">
      <span v-if="linked" class="agent-actions-for" data-testid="actions-for" :title="`These buttons act on ${linked.label}`">
        <FontAwesomeIcon :icon="['fas', 'link']" /> {{ linked.label }}
      </span>
      <button
        v-for="action in visibleActions"
        :key="action.id"
        type="button"
        class="agent-action"
        :class="{ primary: action.isPrimary, running: runningActionId === action.id, done: flashActionId === action.id }"
        :disabled="runningActionId !== null"
        :title="action.description"
        @click="runAction(action)"
      >
        <FontAwesomeIcon
          class="agent-action-icon"
          :icon="['fas', runningActionId === action.id ? 'spinner' : flashActionId === action.id ? 'check' : action.icon]"
          :spin="runningActionId === action.id"
        />
        <span class="agent-action-label">{{ action.label }}</span>
      </button>
    </div>
    <!-- DL-166: an indeterminate stripe along the whole bar's bottom edge while the agent works: the across-the-desk cue. -->
    <span v-if="displayState === 'working'" class="agent-bar-stripe" aria-hidden="true" />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, toRef, watchEffect } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import type { Scene } from '@/types'
import type { AgentStateName } from '@/api/appProfiles'
import { useDashboardStore } from '@/stores/dashboard'
import { useSettingsStore } from '@/stores/settings'
import { trackAgentSurfaceVisibility, useAgentSession } from '@/composables/useAgentSession'
import {
  profileSessionMarker,
  useAgentTargets,
} from '@/composables/useAgentTargets'
import { isAgentWaitingDismissed } from '@/services/agentWaiting'
import AgentSessionPicker from '@/components/AgentSessionPicker.vue'
import AgentStatusBanner from '@/components/AgentStatusBanner.vue'
import AgentViewToggle from '@/components/AgentViewToggle.vue'
import { useAgentSceneView } from '@/composables/useAgentSceneView'
import { useAgentStateSince } from '@/composables/useAgentStateSince'
import { groupSceneButtons } from '@/utils/agentCategories'
import { summarizeOtherSessions, toAgentState } from '@/utils/agentSessionSummary'

/**
 * Agent action bar (DL-064): on a Claude Code / Cursor / Devin scene, shows
 * what the agent is doing right now and the actions that fit that moment —
 * Submit while it waits for a prompt, Interrupt while it works, Approve/Deny
 * while a permission dialog is open.
 */

const props = defineProps<{ scene: Scene | null }>()

const dashboardStore = useDashboardStore()
// The linked session's own state drives the buttons (set below, once the session list is known).
const stateOverride = ref<AgentStateName | null>(null)
const settingsStore = useSettingsStore()
const {
  profile,
  stateEntry,
  currentState,
  stateLabel,
  isAgentPossiblyRunning,
  visibleActions,
  runningActionId,
  flashActionId,
  runAction,
} = useAgentSession(toRef(props, 'scene'), stateOverride)

// DL-166: the bar (status banner + view toggle) shows on every AI coding scene outside edit mode, so
// "No session" / "Running" are visible too. The state-aware action buttons keep the old, stricter condition.
const isAgentScene = computed(() => Boolean(profile.value?.state_actions))
const isVisible = computed(() => !dashboardStore.isEditMode && isAgentScene.value)
const actionsVisible = computed(() => isAgentPossiblyRunning.value && visibleActions.value.length > 0)
const displayState = computed(() => (isAgentPossiblyRunning.value ? currentState.value : 'offline'))

// Groups / All toggle: only meaningful when the scene splits into 2+ categories.
const agentView = useAgentSceneView(computed(() => props.scene?.id))
const showViewToggle = computed(() => groupSceneButtons(props.scene).length >= 2)

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

// DL-165: which session the buttons are linked to, shown in its colour; the buttons follow *its* state.
const linked = computed(() => sessionRows.value.find(r => r.pid === effectiveSession.value?.pid) ?? null)
watchEffect(() => { stateOverride.value = linked.value ? toAgentState(linked.value.state) : null })
const linkAccent = computed(() => linked.value?.accent ?? null)
const othersSummary = computed(() => summarizeOtherSessions(sessionRows.value, linked.value?.pid))
const sinceMs = useAgentStateSince(
  computed(() => `${profile.value?.status_source ?? 'agent'}:${linked.value?.pid ?? 'all'}`),
  displayState,
)

trackAgentSurfaceVisibility(computed(() => profile.value?.status_source), actionsVisible)
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
  position: relative;
}

.agent-action-bar.state-ready { --agent-accent: #22c55e; }
.agent-action-bar.state-working { --agent-accent: #38bdf8; }
.agent-action-bar.state-permission { --agent-accent: #f59e0b; }
.agent-action-bar.state-unknown { --agent-accent: #94a3b8; }
.agent-action-bar.state-offline { --agent-accent: #64748b; }

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

/* DL-166: working stripe across the whole bar (the across-the-desk cue). */
.agent-bar-stripe {
  position: absolute; left: 16px; right: 16px; bottom: 0; height: 4px; overflow: hidden;
  border-radius: 4px 4px 0 0; background: rgba(56, 189, 248, 0.22); pointer-events: none;
}
.agent-bar-stripe::after {
  content: ''; position: absolute; top: 0; bottom: 0; width: 35%; background: #38bdf8;
  animation: agent-bar-sweep 1.6s ease-in-out infinite;
}
@keyframes agent-bar-sweep { from { transform: translateX(-100%); } to { transform: translateX(290%); } }
@media (prefers-reduced-motion: reduce) {
  .agent-bar-stripe::after { animation: none; width: 100%; }
}

/* A shrunk desktop window: one slim bar - status and target on a line, the action
   buttons in a row beneath - instead of tall touch-sized tiles that run off the window. */
@media (max-width: 600px), (max-height: 460px) {
  html:not(.device-phone):not(.device-tablet):not(.device-panel) .agent-action-bar {
    --agent-action-height: 38px;
    flex-direction: row; flex-wrap: wrap; gap: 6px;
    margin: 6px 6px 0; padding: 6px; border-radius: 12px;
  }
  html:not(.device-phone):not(.device-tablet):not(.device-panel) .agent-actions { display: flex; flex: 1 1 100%; gap: 6px; }
  html:not(.device-phone):not(.device-tablet):not(.device-panel) .agent-action {
    flex: 1 1 56px; min-width: 0; flex-direction: row; gap: 6px;
    padding: 0 6px; border-radius: 10px; font-size: 0.75rem;
  }
  html:not(.device-phone):not(.device-tablet):not(.device-panel) .agent-action-icon { font-size: 1em; }
  html:not(.device-phone):not(.device-tablet):not(.device-panel) .agent-action-label {
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis; min-width: 0;
  }
}
/* DL-165: the link to a session - its colour on the badge, the chip edge, a tab over the buttons and each button's top edge. */
.agent-actions.linked { position: relative; padding-top: 6px; }
.agent-actions-for {
  position: absolute; top: -13px; left: 10px; z-index: 2; max-width: 70%;
  display: inline-flex; align-items: center; gap: 5px; padding: 1px 9px; border-radius: 8px 8px 0 0;
  background: var(--link-accent); color: #0b1220; font-weight: 700;
  font-size: clamp(0.6rem, 0.8vw + 0.34rem, 0.8rem); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.agent-actions.linked .agent-action { border-top: 3px solid var(--link-accent); }
.agent-action-bar.is-linked { border-left: 4px solid var(--link-accent); }
.agent-action.done { background: #16a34a; border-color: #4ade80; color: #fff; }
</style>
