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
  position: absolute; left: 50%; top: 8%; transform: translateX(-50%);
  max-width: 80%; padding: 0.5em 0.9em; border: 2px solid rgba(255, 255, 255, 0.85); border-radius: 1em;
  color: #fff; background: #000; font-size: clamp(13px, 1.8vw, 24px); font-weight: 400; white-space: nowrap;
  pointer-events: none;
}
.rb-enter-active, .rb-leave-active { transition: opacity 0.25s ease, transform 0.25s ease; }
.rb-enter-from, .rb-leave-to { opacity: 0; transform: translateX(-50%) translateY(6px); }
</style>
