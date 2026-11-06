<template>
  <!-- DL-155 follow-up A / DL-163: arm + articulated fist gripping a prop at its
       grip point (prop-local coordinates). Slides in from the side, fingers and
       thumb flex organically while it holds. -->
  <g :transform="`translate(${held.grip[0]} ${held.grip[1]}) scale(${held.side} 1)`" data-part="held-hand">
    <g :transform="`translate(${f((1 - slide) * 120)} 0)`">
      <path d="M12 2 Q54 16 128 4" fill="none" stroke="url(#rb-sleeve)" stroke-width="10" stroke-linecap="round" />
      <path d="M12 1 Q34 8 58 7" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round" opacity="0.45" />
      <rect x="8.5" y="-9.5" width="10" height="20" rx="4.5" fill="url(#rb-cuff)" stroke="#9aa6dd" stroke-width="0.8" transform="rotate(8 13 0)" />
      <circle cx="13.5" cy="0" r="1.5" fill="#6cc7ff" opacity="0.85" />
      <ellipse cx="0" cy="1" rx="11.5" ry="10.8" fill="url(#rb-skin)" stroke="#9aa6dd" stroke-width="1" />
      <ellipse
        v-for="(y, i) in KNUCKLES" :key="i"
        :cx="f(-3.2 + Math.sin(t / 110 + i * 1.4) * 1.15)" :cy="y" rx="6.8" ry="3.7"
        fill="url(#rb-skin)" stroke="#9aa6dd" stroke-width="0.9"
      />
      <circle
        v-for="(y, i) in KNUCKLES" :key="`s${i}`"
        :cx="f(-5 + Math.sin(t / 110 + i * 1.4) * 1.15)" :cy="y - 0.8" r="1.1"
        fill="#fff" opacity="0.6"
      />
      <ellipse
        cx="2" cy="-11.8" rx="6.4" ry="3.6"
        fill="url(#rb-skin)" stroke="#9aa6dd" stroke-width="0.9"
        :transform="`rotate(${f(-20 + Math.sin(t / 140) * 5)} 2 -11.8)`"
      />
      <ellipse cx="2.5" cy="-4" rx="5.2" ry="2.2" fill="#fff" opacity="0.55" />
    </g>
  </g>
</template>

<script setup lang="ts">
import type { HeldDef } from '@/services/robot/heldProps'

defineProps<{ held: HeldDef; slide: number; t: number }>()
const KNUCKLES = [-7, -2.4, 2.2, 6.8] as const
const f = (n: number) => Math.round(n * 100) / 100
</script>
