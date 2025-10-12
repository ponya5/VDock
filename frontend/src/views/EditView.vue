<template>
  <div class="edit-view">
    <h1>Edit Mode - Coming Soon</h1>
    <p>Advanced editing features will be available here.</p>
    <button class="btn btn-primary" @click="router.push('/')">Back to Deck</button>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<style scoped>
.edit-view {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: var(--spacing-lg);
}
</style>

