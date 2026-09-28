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
  /* --ease-io (symmetric in-out) instead of --ease-out: the fast-start
     curve made large sections travel most of their height in the first
     ~50ms, which read as a snap rather than a glide. */
  transition: grid-template-rows 320ms var(--ease-io);
}

.collapse.open {
  grid-template-rows: 1fr;
}

.collapse-inner {
  overflow: hidden;
  min-height: 0;
  opacity: 0;
  visibility: hidden;
  transform: translateY(-8px);
  transition:
    opacity 240ms var(--ease-out),
    transform 320ms var(--ease-io),
    visibility 320ms;
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
