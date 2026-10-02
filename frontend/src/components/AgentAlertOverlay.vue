<template>
  <Teleport to="body">
    <!-- The stack stays mounted so the last card's leave transition still
         plays; empty renders a zero-height invisible div. -->
    <TransitionGroup name="alert-pop" tag="div" class="agent-alert-stack">
      <div
        v-for="card in cards"
        :key="card.kind === 'rollup' ? 'rollup' : card.alert.source"
        class="agent-alert"
        role="alert"
      >
        <div class="alert-icon">
          <img
            v-if="card.kind === 'alert' && logoFor(card.alert.source)"
            class="alert-logo"
            :src="logoFor(card.alert.source)"
            alt=""
            data-testid="alert-logo"
          />
          <FontAwesomeIcon v-else :icon="['fas', 'robot']" />
          <span class="alert-pulse"></span>
        </div>
        <div class="alert-body">
          <template v-if="card.kind === 'rollup'">
            <div class="alert-title">{{ card.alerts.length }} agents need you</div>
            <div class="alert-message">{{ rollupLabel(card.alerts) }}</div>
          </template>
          <template v-else>
            <div class="alert-title">{{ alerts.sourceLabelFor(card.alert.source) }} needs you</div>
            <div class="alert-message">{{ card.alert.message }}</div>
            <div v-if="card.alert.project" class="alert-project">
              <FontAwesomeIcon :icon="['fas', 'folder']" /> {{ card.alert.project }}
            </div>
          </template>
        </div>
        <button
          class="alert-dismiss"
          @click="card.kind === 'rollup' ? alerts.dismiss() : alerts.dismiss(card.alert.source)"
        >
          <FontAwesomeIcon :icon="['fas', 'check']" /> {{ card.kind === 'rollup' ? 'Dismiss all' : 'Got it' }}
        </button>
      </div>
    </TransitionGroup>
  </Teleport>
  <!-- Persistent "who needs you" chips — they outlive the banner dismiss -->
  <AgentWaitingDock />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useAgentAlerts } from '@/services/agentAlerts'
import type { AgentAlert } from '@/services/agentAlerts'
import { useSettingsStore } from '@/stores/settings'
import { isAgentBarVisible } from '@/services/agentState'
import AgentWaitingDock from '@/components/AgentWaitingDock.vue'

const alerts = useAgentAlerts()
const settingsStore = useSettingsStore()
const enabled = computed(() => settingsStore.agentAlertsEnabled !== false)

// DL-119: one card per waiting source. A source whose action bar is already
// on screen stands down — the bar shows the state + Approve/Deny itself.
const visibleAlerts = computed(() =>
  alerts.alerts.value.filter((a) => !isAgentBarVisible(a.source))
)

type AlertCard =
  | { kind: 'alert'; alert: AgentAlert }
  | { kind: 'rollup'; alerts: AgentAlert[] }

// Up to two stacked cards; more collapse into a single "N agents need you"
// rollup so a crowded panel stays readable (and one-tap clearable).
const cards = computed<AlertCard[]>(() => {
  if (!enabled.value) return []
  const list = visibleAlerts.value
  if (list.length > 2) return [{ kind: 'rollup', alerts: list }]
  return list.map((alert) => ({ kind: 'alert' as const, alert }))
})

// Brand logos shipped in /public/logos; other sources keep the robot glyph.
const SOURCE_LOGOS: Record<string, string> = {
  claude: '/logos/claudecode-color.png',
}
function logoFor(source: string): string | undefined {
  return SOURCE_LOGOS[source]
}

function rollupLabel(list: AgentAlert[]): string {
  return list.map((a) => alerts.sourceLabelFor(a.source)).join(' · ')
}
</script>

<style scoped>
/* Sits above everything — dashboard (1000/2000), screensaver (500),
   tutorial (10000) — the whole point is you can't miss it. The dock sits
   just under at 29000 so its chips never cover the banner's buttons. */
/* Readable from arm's length on a 7" panel: every size follows the
   viewport, so it is large at 1024x600 and still fits a phone. */
.agent-alert-stack {
  position: fixed;
  top: clamp(12px, 3vh, 28px);
  left: 50%;
  transform: translateX(-50%);
  z-index: 30000;
  display: flex;
  flex-direction: column;
  gap: clamp(10px, 2vh, 18px);
  width: min(880px, calc(100vw - 24px));
}

.agent-alert {
  display: flex;
  align-items: center;
  gap: clamp(14px, 2.4vw, 26px);
  width: 100%;
  box-sizing: border-box;
  padding: clamp(14px, 3vh, 26px) clamp(16px, 2.6vw, 30px);
  border-radius: clamp(16px, 2.6vh, 24px);
  background: rgba(46, 32, 8, 0.97);
  border: 2px solid #f5a524;
  box-shadow: 0 0 0 5px rgba(245, 165, 36, 0.2), 0 18px 56px rgba(0, 0, 0, 0.65);
  -webkit-backdrop-filter: blur(10px);
  backdrop-filter: blur(10px);
  color: #ffd89e;
}

.alert-icon {
  position: relative;
  flex-shrink: 0;
  width: clamp(52px, 12vh, 84px);
  height: clamp(52px, 12vh, 84px);
  border-radius: clamp(12px, 2.2vh, 18px);
  background: rgba(245, 165, 36, 0.16);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: clamp(1.5rem, 5.5vh, 2.4rem);
  color: #f5a524;
}

.alert-logo {
  width: 62%;
  height: 62%;
  object-fit: contain;
}

.alert-pulse {
  position: absolute;
  inset: -4px;
  border-radius: clamp(14px, 2.6vh, 20px);
  border: 2px solid rgba(245, 165, 36, 0.6);
  animation: alert-pulse 1.6s ease-out infinite;
}

@keyframes alert-pulse {
  0% { transform: scale(0.9); opacity: 1; }
  100% { transform: scale(1.35); opacity: 0; }
}

.alert-body {
  flex: 1;
  min-width: 0;
}

.alert-title {
  font-size: clamp(1.2rem, 4.4vh, 2rem);
  font-weight: 700;
  line-height: 1.2;
  color: #ffe4b3;
}

.alert-message {
  font-size: clamp(1rem, 3.2vh, 1.45rem);
  line-height: 1.35;
  color: #f0cf9a;
  margin-top: 4px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.alert-project {
  font-size: clamp(0.85rem, 2.6vh, 1.15rem);
  color: #c9a061;
  margin-top: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.alert-dismiss {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 clamp(18px, 3vw, 34px);
  min-height: clamp(52px, 12vh, 84px);
  border-radius: clamp(12px, 2.2vh, 18px);
  border: none;
  background: #f5a524;
  color: #2a1c04;
  font-size: clamp(1rem, 3.4vh, 1.5rem);
  font-weight: 700;
  white-space: nowrap;
  touch-action: manipulation;
  cursor: pointer;
}

.alert-dismiss:hover { filter: brightness(1.08); }
.alert-dismiss:active { transform: scale(0.97); }

/* Phones in portrait: the button drops under the text so the message keeps
   the full width instead of wrapping one word per line. */
@media (max-width: 520px) {
  .agent-alert {
    flex-wrap: wrap;
  }

  .alert-body {
    flex: 1 1 0;
  }

  .alert-icon {
    width: 56px;
    height: 56px;
    font-size: clamp(1.4rem, 1.2rem + 1vw, 1.6rem);
  }

  .alert-title {
    font-size: clamp(1.15rem, 1rem + 1vw, 1.3rem);
  }

  .alert-message {
    font-size: clamp(0.95rem, 0.9rem + 0.5vw, 1.05rem);
  }

  .alert-dismiss {
    flex: 1 1 100%;
    justify-content: center;
    min-height: 56px;
    font-size: clamp(1.05rem, 1rem + 0.5vw, 1.15rem);
  }
}

.alert-pop-enter-active,
.alert-pop-leave-active {
  transition: transform 0.28s ease, opacity 0.28s ease;
}
.alert-pop-enter-from,
.alert-pop-leave-to {
  transform: translateY(-16px);
  opacity: 0;
}
</style>
