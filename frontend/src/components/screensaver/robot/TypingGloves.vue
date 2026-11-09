<template>
  <!-- DL-165: two black gloves seen from behind, fingers reaching up-and-inwards over the keys, each with a tiny face
       on the back of the hand; fingers dip in turn as they strike. Scene coordinate space. -->
  <g fill="#0b0b10" stroke="#fff" stroke-width="2.3" stroke-linejoin="round" stroke-linecap="round">
    <g v-for="(h, hi) in hands" :key="hi"
       :transform="`translate(${h.x} ${f(h.y + lift(hi))}) rotate(${h.r}) scale(${h.s})`">
      <!-- fingers (point up in local space), fanned -->
      <g v-for="(fg, fi) in fingers" :key="fi"
         :transform="`translate(${fg.x} -8) rotate(${fg.a}) translate(0 ${f(dip(hi, fi))})`">
        <path stroke-width="1.9" :d="`M-3.3 0 V${-fg.l} Q0 ${-fg.l - 6} 3.3 ${-fg.l} V0 Z`" />
      </g>
      <!-- thumb -->
      <g :transform="`translate(${h.flip * 14} 4) rotate(${h.flip * 52}) translate(0 ${f(dip(hi, 5))})`">
        <path d="M-4.6 0 V-10 Q0 -17 4.6 -10 V0 Z" />
      </g>
      <!-- back of the hand with its little face -->
      <path d="M-15 12 Q-17 -4 -9 -11 L9 -11 Q17 -4 15 12 Q0 18 -15 12 Z" />
      <g stroke="none" fill="#fff">
        <circle cx="-4.2" cy="1.5" r="1.7" /><circle cx="4.2" cy="1.5" r="1.7" />
      </g>
      <path d="M-3.4 6.5 Q0 9.2 3.4 6.5" stroke-width="1.3" fill="none" />
    </g>
  </g>
</template>

<script setup lang="ts">
const props = defineProps<{ t: number; fast?: boolean }>()
const f = (n: number) => Math.round(n * 100) / 100

// left glove bottom-left reaching up-right, right glove reaching up-left (as in the reference)
const hands = [
  { x: 26, y: 126, r: 30, s: 0.9, flip: -1 },
  { x: 68, y: 117, r: -30, s: 0.9, flip: 1 },
]
const fingers = [
  { x: -10.5, a: -14, l: 13 },
  { x: -3.5, a: -5, l: 17 },
  { x: 3.5, a: 5, l: 16 },
  { x: 10.5, a: 14, l: 12 },
]
const speed = () => (props.fast ? 22 : 11)
/** A finger dips (strikes a key) when its own sine peaks; the two hands alternate. */
function dip(hand: number, finger: number): number {
  const s = props.t / 1000
  return Math.max(0, Math.sin(s * speed() + finger * 1.7 + hand * 3.1)) * 2.4
}
/** The whole hand lifts a little between strikes. */
function lift(hand: number): number {
  return Math.sin((props.t / 1000) * speed() * 0.5 + hand * Math.PI) * 1.3
}
</script>
