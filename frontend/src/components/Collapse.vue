<script setup lang="ts">
defineProps<{ open: boolean }>()
</script>

<template>
  <div class="collapse" :class="{ open }">
    <div class="collapse-inner">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.collapse {
  display: grid;
  grid-template-rows: 0fr;
  transition: grid-template-rows 250ms var(--ease-out);
}

.collapse.open {
  grid-template-rows: 1fr;
}

.collapse-inner {
  overflow: hidden;
  min-height: 0;
  opacity: 0;
  visibility: hidden;
  transform: translateY(-6px);
  transition:
    opacity 200ms ease,
    transform 250ms var(--ease-out),
    visibility 250ms;
}

.collapse.open .collapse-inner {
  opacity: 1;
  visibility: visible;
  transform: none;
}

@media (prefers-reduced-motion: reduce) {
  .collapse {
    transition: none;
  }

  .collapse-inner {
    transform: none;
    transition: opacity 150ms ease, visibility 150ms;
  }
}
</style>
