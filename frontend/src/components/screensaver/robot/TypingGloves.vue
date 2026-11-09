<template>
  <!-- DL-165: two black gloves, fingers spread and angled down onto the keys; each finger taps in turn.
       Drawn in the typing scene's coordinate space (keyboard front edge around y 118). -->
  <g fill="#0b0b10" stroke="#fff" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round">
    <g v-for="(h, hi) in hands" :key="hi"
       :transform="`translate(${h.x} ${f(h.y + lift(hi))}) rotate(${h.r}) scale(${h.s})`">
      <!-- fingers: fanned, each dips when it strikes -->
      <g v-for="(fg, fi) in fingers" :key="fi"
         :transform="`translate(${fg.x} 8) rotate(${fg.a}) translate(0 ${f(dip(hi, fi))})`">
        <path stroke-width="1.9" :d="`M-3.3 0 V${fg.l} Q0 ${fg.l + 6} 3.3 ${fg.l} V0 Z`" />
      </g>
      <!-- thumb -->
      <g :transform="`translate(${h.flip * 13} -2) rotate(${h.flip * -52}) translate(0 ${f(dip(hi, 5))})`">
        <path d="M-4.6 0 V10 Q0 17 4.6 10 V0 Z" />
      </g>
      <!-- palm over the finger roots -->
      <path d="M-15 -11 Q-17 4 -9 12 L9 12 Q17 4 15 -11 Q0 -19 -15 -11 Z" />
      <path d="M-6 -6 Q0 -9 6 -6" stroke-width="1.6" opacity="0.55" fill="none" />
    </g>
  </g>
</template>

<script setup lang="ts">
const props = defineProps<{ t: number; fast?: boolean }>()
const f = (n: number) => Math.round(n * 100) / 100

// local space: fingers point +y; the hand is then tilted so they point down-left, as in the reference
const hands = [
  { x: 32, y: 90, r: 24, s: 1.0, flip: 1 },
  { x: 62, y: 96, r: 24, s: 1.0, flip: 1 },
]
const fingers = [
  { x: -10.5, a: -22, l: 14 },
  { x: -3.5, a: -8, l: 18 },
  { x: 3.5, a: 7, l: 17 },
  { x: 10.5, a: 21, l: 13 },
]
const speed = () => (props.fast ? 22 : 11)
/** A finger dips (presses a key) when its own sine peaks; hands alternate. */
function dip(hand: number, finger: number): number {
  const s = props.t / 1000
  const k = Math.sin(s * speed() + finger * 1.7 + hand * 3.1)
  return Math.max(0, k) * 2.6
}
/** The whole hand rises a little between strikes. */
function lift(hand: number): number {
  return Math.sin((props.t / 1000) * speed() * 0.5 + hand * Math.PI) * 1.4
}
</script>
