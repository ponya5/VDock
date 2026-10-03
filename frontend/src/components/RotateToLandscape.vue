<template>
  <div v-if="blocked" class="rotate-gate" role="alert" aria-live="assertive">
    <div class="rotate-gate-card">
      <FontAwesomeIcon :icon="['fas', 'mobile-screen']" class="rotate-gate-icon" />
      <h2 class="rotate-gate-title">Rotate your device</h2>
      <p class="rotate-gate-text">
        VDock works in landscape on mobile — turn your phone sideways to use the deck.
      </p>
      <p class="rotate-gate-hint">
        Nothing happening? Check that rotation lock is off.
      </p>
      <button type="button" class="rotate-gate-dismiss" @click="dismissed = true">
        Continue anyway
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useMobileViewport } from '@/utils/mobileViewport'
import { useDeviceClass } from '@/composables/useDeviceClass'
import { useDevicePrefs } from '@/services/devicePrefs'

// A wide grid cannot be comfortable in portrait as authored, so touch
// devices short on space get a rotate prompt. Phones are exempt while the
// deck folds itself into portrait (DL-147: device pref layout "fit", the
// default); "as designed" brings the prompt back. Surfaces with their own
// portrait layout are exempt too: the screensaver (DL-063) and the mobile
// agent console (DL-065). The compact-touch detection is shared
// (useMobileViewport) so the same flag also strips config affordances.
const props = defineProps<{ portraitAllowed?: boolean }>()
const { isMobileViewport, isPortrait } = useMobileViewport()
const { layoutClass } = useDeviceClass()
const devicePrefs = useDevicePrefs()
const dismissed = ref(false)

const deckReflows = computed(() => layoutClass.value === 'phone' && devicePrefs.layout === 'fit')

const blocked = computed(() =>
  isMobileViewport.value && isPortrait.value && !deckReflows.value && !dismissed.value && !props.portraitAllowed
)
</script>

<style scoped>
.rotate-gate {
  position: fixed;
  inset: 0;
  z-index: 12000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding:
    max(var(--spacing-xl), env(safe-area-inset-top, 0px))
    max(var(--spacing-xl), env(safe-area-inset-right, 0px))
    max(var(--spacing-xl), env(safe-area-inset-bottom, 0px))
    max(var(--spacing-xl), env(safe-area-inset-left, 0px));
  background: rgba(8, 10, 16, 0.97);
}

.rotate-gate-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
  max-width: 300px;
  text-align: center;
}

.rotate-gate-icon {
  font-size: clamp(3.00rem, 10vw + 1.00rem, 4.00rem);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-sm);
  animation: rotate-prompt 2.4s var(--ease-out, ease) infinite;
}

@keyframes rotate-prompt {
  0%, 25%   { transform: rotate(0deg); }
  55%, 75%  { transform: rotate(90deg); }
  100%      { transform: rotate(0deg); }
}

.rotate-gate-title {
  margin: 0;
  font-size: clamp(1.00rem, 2vw + 0.63rem, 1.50rem);
  font-weight: 600;
  color: var(--color-text);
}

.rotate-gate-text {
  margin: 0;
  font-size: clamp(0.70rem, 2vw + 0.44rem, 1.05rem);
  line-height: 1.5;
  color: var(--color-text-secondary);
}

.rotate-gate-hint {
  margin: var(--spacing-sm) 0 0;
  font-size: clamp(0.60rem, 2vw + 0.38rem, 0.90rem);
  color: var(--color-text-secondary);
  opacity: 0.7;
}

.rotate-gate-dismiss {
  margin-top: var(--spacing-md);
  padding: 0;
  background: none;
  border: none;
  font-size: clamp(0.60rem, 2vw + 0.38rem, 0.90rem);
  color: var(--color-text-secondary);
  text-decoration: underline;
  cursor: pointer;
  opacity: 0.7;
}

.rotate-gate-dismiss:hover { opacity: 1; }

@media (prefers-reduced-motion: reduce) {
  .rotate-gate-icon { animation: none; }
}
</style>
