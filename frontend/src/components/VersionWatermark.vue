<template>
  <span class="version-watermark" aria-hidden="true" data-testid="version-watermark">v{{ appVersion }}</span>
</template>

<script setup lang="ts">
import { version as appVersion } from '../../package.json'
</script>

<style scoped>
/* Corner mark: never takes pointer events and sits below every overlay, so it
   cannot block or cover an interface element. */
.version-watermark {
  position: fixed;
  left: max(6px, env(safe-area-inset-left));
  bottom: max(2px, env(safe-area-inset-bottom));
  z-index: 1;
  font-size: clamp(9px, 0.7vw, 11px);
  line-height: 1;
  letter-spacing: 0.04em;
  color: rgba(255, 255, 255, 0.4);
  text-shadow: 0 0 3px rgba(0, 0, 0, 0.6);
  pointer-events: none;
  user-select: none;
}
</style>
