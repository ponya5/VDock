<template>
  <Teleport to="body">
    <div
      v-if="isWaiting"
      class="agent-waiting-glow"
      :class="[`style-${glowStyle}`, { 'no-anim': !settingsStore.animationsEnabled }]"
      role="status"
      :aria-label="`${waitingLabel} is waiting for input`"
    />
    <!-- Travelling "comet" on a second layer — one of three frame styles
         (DL-080 follow-up #2). Decorative only: the status div above carries
         the announcement. -->
    <div
      v-if="isWaiting && glowStyle === 'orbit' && settingsStore.animationsEnabled"
      class="agent-waiting-orbit"
      aria-hidden="true"
    />
    <!-- Snooze lives on the frame itself: one tap silences every waiting
         surface (frame, pill ring, session chips) until the agent records a
         fresh `ready` event — it keys off the entry ts, not a timer. -->
    <Transition name="snooze-pop">
      <div v-if="isWaiting" class="agent-waiting-snooze">
        <FontAwesomeIcon :icon="['fas', 'robot']" class="snooze-icon" />
        <span class="snooze-label">{{ waitingLabel }} is waiting for input</span>
        <button type="button" class="snooze-btn" @click="snooze">Snooze</button>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useDashboardStore } from '@/stores/dashboard'
import { useSettingsStore } from '@/stores/settings'
import { useAppIntegrations } from '@/composables/useAppIntegrations'
import { sceneWaitingAgent, dismissAgentWaiting } from '@/services/agentWaiting'
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
const glowStyle = computed(() => settingsStore.agentWaitingGlowStyle ?? 'flash')

function snooze() {
  dismissAgentWaiting(waitingInfo.value?.entry.source)
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
  border: 3px solid rgba(34, 197, 94, 0.5);
  box-shadow:
    inset 0 0 clamp(24px, 6vh, 64px) rgba(34, 197, 94, 0.35),
    0 0 clamp(16px, 3vh, 36px) rgba(34, 197, 94, 0.25);
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
  border-color: rgba(34, 197, 94, 0.85);
}

@keyframes agent-waiting-flash {
  0%, 12%, 26%, 100% {
    border-color: rgba(34, 197, 94, 0.4);
    box-shadow:
      inset 0 0 clamp(24px, 6vh, 64px) rgba(34, 197, 94, 0.3),
      0 0 clamp(16px, 3vh, 36px) rgba(34, 197, 94, 0.2);
  }
  4%, 17% {
    border-color: rgba(134, 239, 172, 1);
    box-shadow:
      inset 0 0 clamp(56px, 12vh, 130px) rgba(34, 197, 94, 0.75),
      0 0 clamp(36px, 7vh, 72px) rgba(34, 197, 94, 0.65);
  }
}

@keyframes agent-waiting-breathe {
  0%, 100% {
    border-color: rgba(34, 197, 94, 0.5);
    box-shadow:
      inset 0 0 clamp(24px, 6vh, 64px) rgba(34, 197, 94, 0.35),
      0 0 clamp(16px, 3vh, 36px) rgba(34, 197, 94, 0.25);
  }
  50% {
    border-color: rgba(34, 197, 94, 0.95);
    box-shadow:
      inset 0 0 clamp(48px, 10vh, 110px) rgba(34, 197, 94, 0.6),
      0 0 clamp(28px, 5vh, 56px) rgba(34, 197, 94, 0.5);
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
    rgba(34, 197, 94, 0.55) 0.78turn,
    rgba(134, 239, 172, 0.95) 0.88turn,
    #e7fce9 0.905turn,
    rgba(134, 239, 172, 0.95) 0.93turn,
    rgba(34, 197, 94, 0.55) 0.99turn,
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
.agent-waiting-snooze {
  position: fixed;
  bottom: 12px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 2100;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px 8px 14px;
  border-radius: 999px;
  background: rgba(8, 26, 14, 0.92);
  border: 1.5px solid rgba(34, 197, 94, 0.7);
  box-shadow: 0 0 24px rgba(34, 197, 94, 0.35), 0 8px 24px rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(8px);
  color: #bbf7d0;
  font-size: 0.85rem;
  white-space: nowrap;
}

.snooze-icon {
  color: #4ade80;
}

.snooze-label {
  font-weight: 600;
}

.snooze-btn {
  padding: 6px 14px;
  border-radius: 999px;
  border: none;
  background: #22c55e;
  color: #052e14;
  font-size: 0.8rem;
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
  .agent-waiting-snooze {
    gap: 8px;
    padding: 6px 8px 6px 12px;
    font-size: 0.78rem;
  }
}

@media (prefers-reduced-motion: reduce) {
  .agent-waiting-glow { animation: none; border-color: rgba(34, 197, 94, 0.85); }
  .agent-waiting-orbit { display: none; }
}
</style>
