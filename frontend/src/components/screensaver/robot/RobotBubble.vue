<template>
  <!-- DL-153: quip bubble. Appears/leaves with a short CSS fade on the bubble
       box only — the face itself is never CSS-animated. -->
  <Transition name="rb">
    <div v-if="text" :key="text" class="robot-bubble" role="status">{{ text }}</div>
  </Transition>
</template>

<script setup lang="ts">
defineProps<{ text: string | null }>()
</script>

<style scoped>
.robot-bubble {
  position: absolute; left: 50%; top: 6%; transform: translateX(-50%);
  max-width: 82%; padding: 0.52em 1em; border: 2px solid rgba(255, 255, 255, 0.9); border-radius: 1.1em;
  color: #fff; background: rgba(8, 10, 18, 0.92);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.65), 0 0 14px rgba(108, 199, 255, 0.16);
  font-size: clamp(13px, 1.8vw, 24px); font-weight: 500; letter-spacing: 0.01em; white-space: nowrap;
  pointer-events: none;
}
.robot-bubble::after {
  content: ''; position: absolute; left: 50%; bottom: -8px;
  width: 12px; height: 12px; background: rgba(8, 10, 18, 0.92);
  border-right: 2px solid rgba(255, 255, 255, 0.9); border-bottom: 2px solid rgba(255, 255, 255, 0.9);
  transform: translateX(-50%) rotate(45deg);
}
.rb-enter-active, .rb-leave-active { transition: opacity 0.25s cubic-bezier(0.22, 1, 0.36, 1), transform 0.25s cubic-bezier(0.22, 1, 0.36, 1); }
.rb-enter-from, .rb-leave-to { opacity: 0; transform: translateX(-50%) translateY(8px) scale(0.95); }
</style>
