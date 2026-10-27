<template>
  <!-- DL-156: storyboard scenes (desk + laptop, magnifier, phone call, clipboard,
       waving hand, sneakers, hand on chin, cheering fists). Outline cartoon style:
       white line, black fill. Everything is a pure function of p (springy
       slide-in) and t, like the glove scenes. -->
  <g :data-scene="scene" :opacity="opacity" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
    <!-- typing at the laptop -->
    <g v-if="scene === 'typing'" :transform="`translate(${f(-(1 - u) * 130)} 0)`">
      <rect x="-22" y="130" width="120" height="14" fill="#a85f43" stroke-width="1.6" />
      <path d="M-8 64 L46 56 L58 116 L2 122 Z" fill="#7d7d7d" />
      <path d="M-4 68 L43 61 L53 111 L5 117 Z" fill="none" stroke-width="1" opacity="0.7" />
      <path d="M-8 118 H66 V125 H-8 Z" fill="#9a9a9a" stroke-width="1.8" />
      <path d="M38 121 h5 M46 121 h5" stroke-width="1.4" />
      <g :transform="`translate(62 ${f(108 + Math.sin(t / 1000 * 13) * 1.2)})`"><ToonHand kind="mitten" :t="t" tap /></g>
    </g>
    <!-- magnifier over the right eye -->
    <g v-else-if="scene === 'inspect'" :transform="`translate(${f((1 - u) * 130 + Math.sin(t / 1000 * 1.6) * 4)} ${f(Math.sin(t / 1000 * 3.2) * 1.6)})`">
      <circle cx="104" cy="56" r="29" fill="#000" stroke="none" />
      <rect x="85" :y="f(29 + magnify)" width="38" height="54" rx="17" fill="#fff" stroke="none" />
      <circle cx="104" cy="56" r="34" stroke-width="3.2" />
      <circle cx="104" cy="56" r="29.5" stroke-width="1.5" />
      <path d="M124 82 L134 116" stroke-width="8" /><path d="M124 82 L134 116" stroke="#000" stroke-width="3.6" />
      <g transform="translate(138 126)"><ToonHand kind="fist" /></g>
      <path d="M152 34 L160 28 M156 50 L166 48" stroke-width="2" :opacity="0.5 + 0.5 * Math.sin(t / 150)" />
    </g>
    <!-- phone call, clock on the wall, laptop on the right -->
    <g v-else-if="scene === 'call'">
      <rect x="-22" y="130" width="244" height="14" fill="#a85f43" stroke-width="1.6" />
      <g :transform="`translate(0 ${f(-(1 - u) * 60)})`">
        <circle cx="8" cy="8" r="24" stroke-width="3" /><circle cx="8" cy="8" r="20.5" stroke-width="1.2" />
        <path :transform="`rotate(${f((t / 1000 * 22) % 360)} 8 8)`" d="M8 8 V-4" stroke-width="2.4" />
        <path :transform="`rotate(${f((t / 1000 * 260) % 360)} 8 8)`" d="M8 8 V-9" stroke="#ff4d4d" stroke-width="1.8" />
      </g>
      <g :transform="`translate(${f(-(1 - u) * 90)} ${f(Math.sin(t / 1000 * 6) * 1.2)})`">
        <path d="M2 74 Q-14 100 12 126" stroke-width="10" /><path d="M2 74 Q-14 100 12 126" stroke="#000" stroke-width="5.6" />
        <ellipse cx="6" cy="72" rx="9" ry="12" transform="rotate(-18 6 72)" fill="#000" /><ellipse cx="18" cy="127" rx="10" ry="8" fill="#000" />
        <g transform="translate(24 106) rotate(-12)"><ToonHand kind="fist" /></g>
      </g>
      <g :transform="`translate(${f((1 - u) * 90)} 0)`">
        <path d="M150 120 H222 V126 H150 Z" fill="#9a9a9a" stroke-width="1.8" />
        <path d="M196 64 L222 58 V120 H186 Z" fill="#7d7d7d" />
        <g :transform="`translate(166 ${f(112 + Math.sin(t / 1000 * 13) * 1.2)})`"><ToonHand kind="mitten" :t="t" tap /></g>
      </g>
    </g>
    <!-- clipboard + pen -->
    <g v-else-if="scene === 'notes'" :transform="`translate(0 ${f((1 - u) * 110)})`">
      <g transform="rotate(-8 44 118)">
        <rect x="10" y="70" width="66" height="90" rx="4" fill="#ffb768" /><rect x="14" y="76" width="58" height="80" rx="2" stroke-width="1" opacity="0.5" />
        <rect x="32" y="64" width="22" height="12" rx="4" fill="#9a9a9a" stroke-width="1.8" />
        <circle cx="26" cy="73" r="1.8" fill="#fff" stroke="none" /><circle cx="58" cy="73" r="1.8" fill="#fff" stroke="none" />
        <path d="M24 100 H62" stroke="#e8884a" stroke-width="2" stroke-dasharray="40 40" :stroke-dashoffset="f(40 - ((t / 40) % 40))" />
      </g>
      <g transform="translate(14 122)"><ToonHand kind="fist" /></g>
      <g :transform="`translate(${f(Math.sin(t / 1000 * 14) * 2.5)} ${f(Math.cos(t / 1000 * 9.5) * 2)})`">
        <path d="M134 96 L88 86" stroke-width="9" /><path d="M134 96 L88 86" stroke="#9aa4e8" stroke-width="5" />
        <g transform="translate(138 112)"><ToonHand kind="fist" /></g>
      </g>
    </g>
    <!-- waving hand (relax: bottom right, hello: bottom left) -->
    <g v-else-if="scene === 'relax' || scene === 'hello'" :transform="`translate(${scene === 'relax' ? 172 : 26} ${f(122 + (1 - u) * 80)})`">
      <g :transform="`rotate(${f(Math.sin(t / 1000 * 8) * 16)} 0 16) scale(${scene === 'relax' ? 1.25 : -1.25} 1.25)`"><ToonHand kind="open" /></g>
      <path :d="scene === 'relax' ? 'M-34 -34 L-40 -42 M-26 -42 L-28 -52 M-16 -46 L-12 -54' : 'M34 -34 L40 -42 M26 -42 L28 -52 M16 -46 L12 -54'" stroke-width="2.2" :opacity="0.4 + 0.6 * Math.abs(Math.sin(t / 220))" />
    </g>
    <!-- red sneakers walking in -->
    <g v-else-if="scene === 'sneakers'" :transform="`translate(100 ${f(104 + (1 - u) * 110)}) scale(1.7)`">
      <RobotArt :def="PROPS.sneakers" :t="t" :level="0" />
    </g>
    <!-- thinking, hand on chin -->
    <g v-else-if="scene === 'chin'" :transform="`translate(${f(-(1 - u) * 90 + Math.sin(t / 1000 * 4) * 1.5)} ${f(Math.sin(t / 1000 * 4))})`">
      <g transform="translate(78 112) scale(1.3) rotate(-18)"><ToonHand kind="point" /></g>
    </g>
    <!-- cheering fists + sparkles -->
    <g v-else-if="scene === 'cheer'">
      <g :transform="`translate(${f(28 - (1 - u) * 70)} ${f(108 - Math.abs(Math.sin(t / 1000 * 7)) * 8)}) scale(1.25) rotate(-14)`"><ToonHand kind="fist" /></g>
      <g :transform="`translate(${f(172 + (1 - u) * 70)} ${f(108 - Math.abs(Math.sin(t / 1000 * 7 + 1)) * 8)}) scale(-1.25 1.25) rotate(-14)`"><ToonHand kind="fist" /></g>
      <path v-for="(s, i) in SPARKS" :key="i" :d="spark(s[0], s[1], s[2] * (0.75 + 0.25 * Math.sin(t / 1000 * 6 + i * 2)))" fill="#fff" stroke="none" />
      <path d="M182 -12 L188 -22 M192 2 L202 -4" stroke-width="2.2" :opacity="0.4 + 0.6 * Math.abs(Math.sin(t / 200))" />
    </g>
  </g>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import ToonHand from './ToonHand.vue'
import RobotArt from './RobotArt.vue'
import { PROPS } from '@/services/robot/robotArt'
import type { SceneId } from '@/services/robot/scenes'

const props = defineProps<{ scene: SceneId; p: number; t: number; opacity: number }>()
const u = computed(() => Math.min(1, Math.max(0, props.p)))
// the magnified eye wobbles a little as the lens sweeps
const magnify = computed(() => Math.sin(props.t / 1000 * 3) * 2)
const f = (n: number) => Math.round(n * 100) / 100

const SPARKS = [[16, 18, 1.5], [44, -6, 1.1], [190, 26, 1.4], [168, -10, 0.9]] as const
const spark = (x: number, y: number, s: number) =>
  `M${x} ${y - 8 * s} Q${x + s} ${y - s} ${x + 8 * s} ${y} Q${x + s} ${y + s} ${x} ${y + 8 * s} Q${x - s} ${y + s} ${x - 8 * s} ${y} Q${x - s} ${y - s} ${x} ${y - 8 * s} Z`
</script>
