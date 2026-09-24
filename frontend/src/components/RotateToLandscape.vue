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

// The deck is landscape-only on phones: a 5-6 column grid can never be
// comfortable in portrait. The phone detection itself is shared
// (useMobileViewport) so the same flag also strips config affordances.
// Surfaces with their own portrait layout are exempt: the screensaver
// (DL-063) and the mobile agent console (DL-065).
const props = defineProps<{ portraitAllowed?: boolean }>()
const { isMobileViewport, isPortrait } = useMobileViewport()
const dismissed = ref(false)

const blocked = computed(() =>
  isMobileViewport.value && isPortrait.value && !dismissed.value && !props.portraitAllowed
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
  padding: var(--spacing-xl);
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
