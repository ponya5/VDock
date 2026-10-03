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
    <!-- Aurora / Sonar / Laser: an effect layer above the frame (DL-080
         follow-up). Decorative only. -->
    <div
      v-if="isWaiting && fxStyle && settingsStore.animationsEnabled"
      class="agent-waiting-fx"
      :class="`fx-${glowStyle}`"
      :style="brandVars"
      aria-hidden="true"
    >
      <span v-if="glowStyle === 'sonar'"></span>
      <span v-if="glowStyle === 'sonar'"></span>
      <span v-if="glowStyle === 'sonar'"></span>
    </div>
    <!-- Snooze lives on the frame itself: one tap silences every waiting
         surface (frame, pill ring, session chips) until the agent records a
         fresh `ready` event — it keys off the entry ts, not a timer. -->
    <Transition name="snooze-pop">
      <div v-if="isWaiting" class="agent-waiting-snooze" :style="brandVars">
        <img v-if="brand.logo" :src="brand.logo" alt="" class="snooze-logo" data-testid="snooze-logo" />
        <FontAwesomeIcon v-else :icon="['fas', 'robot']" class="snooze-icon" />
        <span class="snooze-label">{{ waitingLabel }} is waiting for input</span>
        <button type="button" class="snooze-btn" @click="snooze">Snooze 3m</button>
        <button type="button" class="snooze-btn is-secondary" data-testid="dismiss-btn" title="Silence until the agent is idle again" @click="dismiss">Dismiss</button>
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
// Styles drawn by the extra effect layer (the frame itself just holds steady).
const fxStyle = computed(() => ['aurora', 'sonar', 'laser'].includes(glowStyle.value))

function snooze() {
  dismissAgentWaiting(waitingInfo.value?.entry.source)
}
// Full dismiss: no timer — stays quiet until the agent next goes idle.
function dismiss() {
  dismissAgentWaiting(waitingInfo.value?.entry.source, Infinity)
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

/* Aurora / Sonar / Laser keep the frame steady and let the fx layer move. */
.agent-waiting-glow.style-aurora,
.agent-waiting-glow.style-sonar,
.agent-waiting-glow.style-laser {
  animation: none;
  border-color: rgba(var(--agent-rgb), 0.6);
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

/* ---- Effect layer (Aurora / Sonar / Laser) ---------------------------- */
@property --agent-aurora {
  syntax: '<angle>';
  inherits: false;
  initial-value: 0deg;
}

.agent-waiting-fx {
  position: fixed;
  inset: 0;
  z-index: 1400;
  pointer-events: none;
  overflow: hidden;
}

/* Aurora: two broad bands of light flow round a continuous ring while the
   whole frame breathes. Slow (9s lap) so it reads as ambient, not alarming. */
.agent-waiting-fx.fx-aurora {
  border: 5px solid transparent;
  background: conic-gradient(
    from var(--agent-aurora) at 50% 50%,
    rgba(var(--agent-rgb), 0.25) 0turn,
    rgba(var(--agent-light-rgb), 0.95) 0.12turn,
    var(--agent-pale) 0.2turn,
    rgba(var(--agent-light-rgb), 0.95) 0.3turn,
    rgba(var(--agent-rgb), 0.25) 0.5turn,
    rgba(var(--agent-light-rgb), 0.95) 0.62turn,
    var(--agent-pale) 0.7turn,
    rgba(var(--agent-light-rgb), 0.95) 0.8turn,
    rgba(var(--agent-rgb), 0.25) 1turn
  ) border-box;
  -webkit-mask: linear-gradient(#fff 0 0) padding-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask: linear-gradient(#fff 0 0) padding-box, linear-gradient(#fff 0 0);
  mask-composite: exclude;
  filter: drop-shadow(0 0 14px rgba(var(--agent-rgb), 0.85));
  animation: agent-fx-aurora 9s linear infinite, agent-fx-aurora-breathe 3.2s ease-in-out infinite;
}

/* Sonar: rings ping out from the middle of the screen and fade at the edge. */
.agent-waiting-fx.fx-sonar span {
  position: absolute;
  inset: 0;
  border: 3px solid rgba(var(--agent-light-rgb), 0.9);
  border-radius: clamp(16px, 4vh, 36px);
  box-shadow: 0 0 28px rgba(var(--agent-rgb), 0.7), inset 0 0 28px rgba(var(--agent-rgb), 0.5);
  opacity: 0;
  animation: agent-fx-sonar 3.6s cubic-bezier(0.15, 0.6, 0.35, 1) infinite;
}
.agent-waiting-fx.fx-sonar span:nth-child(2) { animation-delay: 1.2s; }
.agent-waiting-fx.fx-sonar span:nth-child(3) { animation-delay: 2.4s; }

/* Laser: a scan line sweeps the screen top to bottom, bright leading edge. */
.agent-waiting-fx.fx-laser::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 24vh;
  background: linear-gradient(
    to bottom,
    transparent,
    rgba(var(--agent-rgb), 0.16) 55%,
    rgba(var(--agent-light-rgb), 0.7) 93%,
    var(--agent-pale) 100%
  );
  box-shadow: 0 8px 30px rgba(var(--agent-light-rgb), 0.85);
  animation: agent-fx-laser 3s cubic-bezier(0.45, 0, 0.3, 1) infinite;
}

@keyframes agent-fx-aurora { to { --agent-aurora: 1turn; } }
@keyframes agent-fx-aurora-breathe {
  0%, 100% { opacity: 0.75; }
  50% { opacity: 1; }
}
@keyframes agent-fx-sonar {
  0% { transform: scale(0.18); opacity: 0.95; }
  100% { transform: scale(1.02); opacity: 0; }
}
@keyframes agent-fx-laser {
  from { transform: translateY(-100%); }
  to { transform: translateY(100vh); }
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

.snooze-btn.is-secondary {
  background: transparent;
  color: var(--agent-text);
  border: 1.5px solid rgba(var(--agent-rgb), 0.7);
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
    padding: 8px 10px 8px 12px;
    font-size: calc(0.85rem * min(var(--touch-multiplier, 1), 1.6));
    max-width: calc(100vw - 16px);
  }
}

@media (prefers-reduced-motion: reduce) {
  .agent-waiting-glow { animation: none; border-color: rgba(var(--agent-rgb), 0.85); }
  .agent-waiting-orbit { display: none; }
  .agent-waiting-fx { display: none; }
}
</style>
