<template>
  <div class="page-indicator">
    <div 
      v-for="i in total" 
      :key="i"
      class="dot"
      :class="{ 'active': i - 1 === current }"
      @click="i - 1 !== current && emit('select', i - 1)"
    ></div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  total: number
  current: number
}>()
const emit = defineEmits<{
  select: [index: number]
}>()
</script>

<style scoped>
.page-indicator {
  display: flex; gap: 8px; justify-content: center; padding: 8px;
}
.dot {
  width: 8px; height: 8px; border-radius: 50%; background: rgba(255, 255, 255, 0.3); transition: all 0.3s; cursor: pointer;
}
.dot.active {
  background: white; transform: scale(1.2);
}
</style>
