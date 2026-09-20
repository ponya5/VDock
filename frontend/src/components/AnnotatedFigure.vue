<template>
  <figure class="annotated-figure">
    <div class="shot-wrap">
      <img :src="img" :alt="title" class="shot" loading="lazy" />
      <span
        v-for="m in markers"
        :key="m.n"
        class="marker"
        :class="{ active: activeMarker === m.n }"
        :style="{ left: m.x + '%', top: m.y + '%' }"
        @click.stop="activeMarker = activeMarker === m.n ? null : m.n"
      >{{ m.n }}</span>
    </div>
    <figcaption class="captions">
      <div
        v-for="m in markers"
        :key="m.n"
        class="caption-row"
        :class="{ active: activeMarker === m.n }"
        @click="activeMarker = activeMarker === m.n ? null : m.n"
      >
        <span class="caption-n">{{ m.n }}</span>
        <span class="caption-text">{{ m.label }}</span>
      </div>
    </figcaption>
  </figure>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { HelpMarker } from '@/data/helpScreens'

defineProps<{
  title: string
  img: string
  markers: HelpMarker[]
}>()

const activeMarker = ref<number | null>(null)
</script>

<style scoped>
.annotated-figure {
  margin: 0;
}

.shot-wrap {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--color-border, #2a3444);
}

.shot {
  display: block;
  width: 100%;
  height: auto;
}

/* Arrow marker: badge + stem pointing up-left toward the feature */
.marker {
  position: absolute;
  transform: translate(-50%, -50%);
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--color-primary, #4f8ef7);
  color: #fff;
  font-size: 0.78rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 0 0 3px rgba(0, 0, 0, 0.45), 0 0 14px rgba(79, 142, 247, 0.8);
  z-index: 2;
}

.marker::after {
  content: '';
  position: absolute;
  left: 50%;
  bottom: -10px;
  width: 2px;
  height: 10px;
  background: var(--color-primary, #4f8ef7);
  box-shadow: 0 0 6px rgba(79, 142, 247, 0.9);
}

.marker.active {
  background: #ffd166;
  color: #1a1a1a;
}

.captions {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 12px;
}

.caption-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 7px 10px;
  border-radius: 8px;
  cursor: pointer;
  border: 1px solid transparent;
  transition: background 0.15s ease;
}

.caption-row:hover,
.caption-row.active {
  background: rgba(79, 142, 247, 0.12);
  border-color: rgba(79, 142, 247, 0.35);
}

.caption-n {
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--color-primary, #4f8ef7);
  color: #fff;
  font-size: 0.72rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.caption-row.active .caption-n {
  background: #ffd166;
  color: #1a1a1a;
}

.caption-text {
  font-size: 0.85rem;
  line-height: 1.45;
  color: var(--color-text-secondary, #a8b3c4);
}
</style>
