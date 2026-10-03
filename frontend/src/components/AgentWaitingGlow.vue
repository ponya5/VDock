<template>
  <Teleport to="body">
    <div
      v-if="isWaiting"
      class="agent-waiting-glow"
      :class="[`style-${glowStyle}`, { 'no-anim': !settingsStore.animationsEnabled }]"
      :style="brandVars"
      role="status"
      :aria-label="`${waitingLabel} is waiting for input`"
    />
    <!-- Travelling "comet" on a second layer — one of three frame styles
         (DL-080 follow-up #2). Decorative only: the status div above carries
         the announcement. -->
    <div
      v-if="isWaiting && glowStyle === 'orbit' && settingsStore.animationsEnabled"
      class="agent-waiting-orbit"
      :style="brandVars"
      aria-hidden="true"
    />
    <!-- Snooze lives on the frame itself: one tap silences every waiting
         surface (frame, pill ring, session chips) until the agent records a
         fresh `ready` event — it keys off the entry ts, not a timer. -->
    <Transition name="snooze-pop">
      <div v-if="isWaiting" class="agent-waiting-snooze" :style="brandVars">
        <img v-if="brand.logo" :src="brand.logo" alt="" class="snooze-logo" data-testid="snooze-logo" />
        <FontAwesomeIcon v-else :icon="['fas', 'robot']" class="snooze-icon" />
        <span class="snooze-label">{{ waitingLabel }} is waiting for input</span>
        <button type="button" class="snooze-btn" @click="snooze">Dismiss 3m</button>
      </div>
    </Transition>
    <!-- Snoozed: the waiting chip is gone, so give the user a way to end the
         snooze early instead of waiting out the clock. -->
    <Transition name="snooze-pop">
      <div v-if="isSnoozed" class="agent-snoozed" :style="snoozedVars" data-testid="snoozed-chip">
        <FontAwesomeIcon :icon="['fas', 'bell-slash']" class="snooze-icon" />
        <span class="snooze-label">{{ snoozedLabel }} alert dismissed · {{ snoozeLeftText }} left</span>
        <button type="button" class="snooze-btn" data-testid="resume-btn" @click="resume">Undo dismiss</button>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useDashboardStore } from '@/stores/dashboard'
import { useSettingsStore } from '@/stores/settings'
import { useAppIntegrations } from '@/composables/useAppIntegrations'
import {
  sceneWaitingAgent, sceneSnoozedAgent, dismissAgentWaiting, resumeAgentWaiting, agentSnoozeRemainingMs,
} from '@/services/agentWaiting'
import { agentBrandFor, agentBrandVars } from '@/services/agentBrand'
import { initAgentState } from '@/services/agentState'
import { loadProfileMaps } from '@/services/appDetection'

/**
 * Waiting-agent alert frame (DL-080): while ANY scene in the active profile
 * has an agent session sitting `ready` — idle, waiting for a command — the
 * whole dashboard frame flashes so the user can't miss it, and the scene
 * rails ring the pill that wants a visit. Gated by `agentWaitingGlowEnabled`
 * (default on); the frame style follows `agentWaitingGlowStyle`
 * (flash | pulse | orbit). Complements the permission state's
 * AgentAlertOverlay banner.
 */

const dashboardStore = useDashboardStore()
const settingsStore = useSettingsStore()
const appIntegrations = useAppIntegrations()

// Idempotent — the rails wire the same feed, but the glow must not depend
// on a rail being mounted (and must resolve scenes even if it mounts first).
onMounted(() => {
  initAgentState()
  void loadProfileMaps()
})

const waitingInfo = computed(() => {
  for (const scene of dashboardStore.currentProfile?.scenes ?? []) {
    const waiting = sceneWaitingAgent(scene, appIntegrations.value)
    if (waiting) return waiting
  }
  return null
})

const isWaiting = computed(() =>
  settingsStore.agentWaitingGlowEnabled !== false &&
  !dashboardStore.isEditMode &&
  waitingInfo.value !== null
)

const waitingLabel = computed(() => waitingInfo.value?.profile?.label ?? 'Agent')
const brand = computed(() => agentBrandFor(waitingInfo.value?.entry.source))
const brandVars = computed(() => agentBrandVars(waitingInfo.value?.entry.source))
const glowStyle = computed(() => settingsStore.agentWaitingGlowStyle ?? 'flash')

function snooze() {
  dismissAgentWaiting(waitingInfo.value?.entry.source)
}

// Snoozed state — mirrors waitingInfo. `nowTick` only exists to re-run the
// countdown each second; Date.now() alone isn't reactive.
const snoozedInfo = computed(() => {
  for (const scene of dashboardStore.currentProfile?.scenes ?? []) {
    const snoozed = sceneSnoozedAgent(scene, appIntegrations.value)
    if (snoozed) return snoozed
  }
  return null
})
const isSnoozed = computed(() =>
  settingsStore.agentWaitingGlowEnabled !== false &&
  !dashboardStore.isEditMode &&
  !isWaiting.value &&
  snoozedInfo.value !== null
)
const snoozedLabel = computed(() => snoozedInfo.value?.profile?.label ?? 'Agent')
const snoozedVars = computed(() => agentBrandVars(snoozedInfo.value?.entry.source))

const nowTick = ref(0)
let tickTimer: ReturnType<typeof setInterval> | null = null
watch(isSnoozed, (on) => {
  if (on && !tickTimer) tickTimer = setInterval(() => { nowTick.value++ }, 1000)
  if (!on && tickTimer) { clearInterval(tickTimer); tickTimer = null }
}, { immediate: true })
onBeforeUnmount(() => { if (tickTimer) clearInterval(tickTimer) })

const snoozeLeftText = computed(() => {
  void nowTick.value
  const s = Math.ceil(agentSnoozeRemainingMs(snoozedInfo.value?.entry.source) / 1000)
  return s >= 60 ? `${Math.ceil(s / 60)}m` : `${Math.max(s, 0)}s`
})

function resume() {
  resumeAgentWaiting(snoozedInfo.value?.entry.source)
}
</script>

<style scoped>
/* Animating a custom property needs it registered as a real type; scoped
   styles don't transform at-rules, so this lands once, globally. */
@property --agent-orbit {
  syntax: '<angle>';
  inherits: false;
  initial-value: 0deg;
}

/* Fixed frame painted over the dashboard (1000/2000) but under dialogs and
   the agent-target popover (1500+): the waiting cue must not pretend to be a
   modal. pointer-events none keeps every press landing on the deck. */
.agent-waiting-glow {
  position: fixed;
  inset: 0;
  z-index: 1400;
  pointer-events: none;
  border: 3px solid rgba(var(--agent-rgb), 0.5);
  box-shadow:
    inset 0 0 clamp(24px, 6vh, 64px) rgba(var(--agent-rgb), 0.35),
    0 0 clamp(16px, 3vh, 36px) rgba(var(--agent-rgb), 0.25);
}

/* Flash (default): heartbeat double-blink — two quick bright pulses, then a
   rest. ~2 flashes per 2.4s cycle stays well under the photosensitive
   threshold while still reading as "alarm", not "ambient". */
.agent-waiting-glow.style-flash {
  animation: agent-waiting-flash 2.4s linear infinite;
}

/* Pulse: the original soft breathe — for users who find the flash too loud. */
.agent-waiting-glow.style-pulse {
  animation: agent-waiting-breathe 2.4s ease-in-out infinite;
}

.agent-waiting-glow.no-anim {
  animation: none;
  border-color: rgba(var(--agent-rgb), 0.85);
}

@keyframes agent-waiting-flash {
  0%, 12%, 26%, 100% {
    border-color: rgba(var(--agent-rgb), 0.4);
    box-shadow:
      inset 0 0 clamp(24px, 6vh, 64px) rgba(var(--agent-rgb), 0.3),
      0 0 clamp(16px, 3vh, 36px) rgba(var(--agent-rgb), 0.2);
  }
  4%, 17% {
    border-color: rgba(var(--agent-light-rgb), 1);
    box-shadow:
      inset 0 0 clamp(56px, 12vh, 130px) rgba(var(--agent-rgb), 0.75),
      0 0 clamp(36px, 7vh, 72px) rgba(var(--agent-rgb), 0.65);
  }
}

@keyframes agent-waiting-breathe {
  0%, 100% {
    border-color: rgba(var(--agent-rgb), 0.5);
    box-shadow:
      inset 0 0 clamp(24px, 6vh, 64px) rgba(var(--agent-rgb), 0.35),
      0 0 clamp(16px, 3vh, 36px) rgba(var(--agent-rgb), 0.25);
  }
  50% {
    border-color: rgba(var(--agent-rgb), 0.95);
    box-shadow:
      inset 0 0 clamp(48px, 10vh, 110px) rgba(var(--agent-rgb), 0.6),
      0 0 clamp(28px, 5vh, 56px) rgba(var(--agent-rgb), 0.5);
  }
}

/* The orbit: one bright arc travelling the perimeter once per lap, masked
   to a ring just inside the border. Linear timing — a lap is constant
   motion, not an ease. Mounted only for the 'orbit' style. */
.agent-waiting-orbit {
  position: fixed;
  inset: 0;
  z-index: 1400;
  pointer-events: none;
  border: 4px solid transparent;
  border-radius: 2px;
  background: conic-gradient(
    from var(--agent-orbit) at 50% 50%,
    transparent 0turn,
    transparent 0.62turn,
    rgba(var(--agent-rgb), 0.55) 0.78turn,
    rgba(var(--agent-light-rgb), 0.95) 0.88turn,
    var(--agent-pale) 0.905turn,
    rgba(var(--agent-light-rgb), 0.95) 0.93turn,
    rgba(var(--agent-rgb), 0.55) 0.99turn,
    transparent 1turn
  ) border-box;
  -webkit-mask: linear-gradient(#fff 0 0) padding-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask: linear-gradient(#fff 0 0) padding-box, linear-gradient(#fff 0 0);
  mask-composite: exclude;
  animation: agent-waiting-orbit 4.5s linear infinite;
}

@keyframes agent-waiting-orbit {
  to { --agent-orbit: 1turn; }
}

/* Snooze chip: the off switch attached to the frame, bottom-center where
   the footer strip is empty in normal mode. Above dashboard chrome (2000),
   below dialogs (10000) and the permission banner (30000). */
.agent-waiting-snooze,
.agent-snoozed {
  position: fixed;
  bottom: 12px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 2100;
  display: flex;
  align-items: center;
  gap: calc(10px * min(var(--touch-multiplier, 1), 1.6));
  padding:
    calc(10px * min(var(--touch-multiplier, 1), 1.6))
    calc(12px * min(var(--touch-multiplier, 1), 1.6))
    calc(10px * min(var(--touch-multiplier, 1), 1.6))
    calc(18px * min(var(--touch-multiplier, 1), 1.6));
  border-radius: 999px;
  background: rgba(var(--agent-bg-rgb), 0.92);
  border: 1.5px solid rgba(var(--agent-rgb), 0.7);
  box-shadow: 0 0 24px rgba(var(--agent-rgb), 0.35), 0 8px 24px rgba(0, 0, 0, 0.5);
  -webkit-backdrop-filter: blur(8px);
  backdrop-filter: blur(8px);
  color: var(--agent-text);
  font-size: calc(0.95rem * min(var(--touch-multiplier, 1), 1.6));
  white-space: nowrap;
}

.agent-snoozed {
  /* quieter than the alert chip — it's a status, not a call to action */
  opacity: 0.92;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
}

.snooze-icon {
  color: rgb(var(--agent-light-rgb));
}

.snooze-logo {
  width: 1.4em;
  height: 1.4em;
  object-fit: contain;
}

.snooze-label {
  font-weight: 600;
}

.snooze-btn {
  padding:
    calc(8px * min(var(--touch-multiplier, 1), 1.6))
    calc(18px * min(var(--touch-multiplier, 1), 1.6));
  min-height: max(36px, calc(var(--min-touch-target, 44px) * 0.8));
  border-radius: 999px;
  border: none;
  background: var(--agent-solid);
  color: var(--agent-on-solid);
  font-size: calc(0.9rem * min(var(--touch-multiplier, 1), 1.6));
  font-weight: 700;
  cursor: pointer;
  touch-action: manipulation;
}

.snooze-btn:hover { filter: brightness(1.1); }
.snooze-btn:active { transform: scale(0.96); }

.snooze-pop-enter-active,
.snooze-pop-leave-active {
  transition: transform 0.25s ease, opacity 0.25s ease;
}
.snooze-pop-enter-from,
.snooze-pop-leave-to {
  transform: translateX(-50%) translateY(12px);
  opacity: 0;
}

@media (max-width: 520px) {
  .agent-waiting-snooze,
  .agent-snoozed {
    gap: 8px;
    padding: 8px 10px 8px 12px;
    font-size: calc(0.85rem * min(var(--touch-multiplier, 1), 1.6));
    max-width: calc(100vw - 16px);
  }
}

@media (prefers-reduced-motion: reduce) {
  .agent-waiting-glow { animation: none; border-color: rgba(var(--agent-rgb), 0.85); }
  .agent-waiting-orbit { display: none; }
}
</style>
