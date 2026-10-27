<template>
  <!-- DL-155 follow-up A: arm + fist gripping a prop at its grip point (prop-local
       coordinates). Slides in from the side, fingers flex while it holds. -->
  <g :transform="`translate(${held.grip[0]} ${held.grip[1]}) scale(${held.side} 1)`" data-part="held-hand">
    <g :transform="`translate(${f((1 - slide) * 120)} 0)`">
      <path d="M12 2 Q54 16 128 4" fill="none" stroke="#3a7bff" stroke-width="9" stroke-linecap="round" />
      <path d="M12 2 Q30 8 50 8" fill="none" stroke="#6cc7ff" stroke-width="3.5" stroke-linecap="round" opacity="0.55" />
      <rect x="9" y="-9" width="9" height="19" rx="4" fill="url(#rb-cuff)" transform="rotate(8 13 0)" />
      <ellipse cx="0" cy="1" rx="11" ry="10.5" fill="url(#rb-skin)" stroke="#9aa6dd" stroke-width="1" />
      <ellipse
        v-for="(y, i) in KNUCKLES" :key="i"
        :cx="f(-3 + Math.sin(t / 110 + i * 1.4) * 0.9)" :cy="y" rx="6.5" ry="3.6"
        fill="url(#rb-skin)" stroke="#9aa6dd" stroke-width="0.9"
      />
      <ellipse cx="2" cy="-12" rx="6" ry="3.4" fill="url(#rb-skin)" stroke="#9aa6dd" stroke-width="0.9" transform="rotate(-20 2 -12)" />
      <ellipse cx="2" cy="-4" rx="5" ry="2" fill="#fff" opacity="0.5" />
    </g>
  </g>
</template>

<script setup lang="ts">
import type { HeldDef } from '@/services/robot/heldProps'

defineProps<{ held: HeldDef; slide: number; t: number }>()
const KNUCKLES = [-7, -2.4, 2.2, 6.8] as const
const f = (n: number) => Math.round(n * 100) / 100
</script>
