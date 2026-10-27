<template>
  <!-- DL-153: one vector art def; per-element transforms come from the rAF clock. -->
  <g :transform="artTransform(def.anim, t, 0, level)">
    <component
      :is="el.tag"
      v-for="(el, i) in def.els"
      :key="i"
      v-bind="el.attrs"
      :transform="el.anim ? artTransform(el.anim, t, el.phase ?? 0, level) : undefined"
      :style="el.anim === 'eq' ? 'transform-box: fill-box; transform-origin: center bottom' : undefined"
    />
  </g>
</template>

<script setup lang="ts">
import { artTransform, type ArtDef } from '@/services/robot/robotArt'

defineProps<{ def: ArtDef; t: number; level: number }>()
</script>
