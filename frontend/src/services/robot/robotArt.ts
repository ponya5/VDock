/**
 * DL-153 — the robot's vector art: eye/mouth glyphs, status icons, props and
 * wearable accessories, as plain element descriptors rendered by
 * RobotArt.vue. Line art is white; colour only from the accent tokens.
 * Each def is drawn around (0,0); `anchor` places it in face viewBox units.
 */
import type { EyeGlyph, MouthGlyph } from './expressions'

export const COLORS = { white: '#fff', yellow: '#ffd84d', pink: '#ff6fa8', red: '#ff4d4d', blue: '#6cc7ff', orange: '#ff9a4d' } as const
const W = COLORS.white
export type ArtAnim = 'none' | 'bounce' | 'spin' | 'wave' | 'twinkle' | 'float' | 'drip' | 'pulse' | 'pop' | 'fall' | 'scan' | 'steam' | 'sway' | 'eq'
export interface ArtEl { tag: 'path' | 'circle' | 'rect'; attrs: Record<string, string | number>; anim?: ArtAnim; phase?: number }
export interface ArtDef { els: ArtEl[]; anim?: ArtAnim; anchor?: [number, number]; life?: number }

const line = (d: string, stroke: string = W, width = 4): ArtEl =>
  ({ tag: 'path', attrs: { d, fill: 'none', stroke, 'stroke-width': width, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' } })
const shape = (d: string, fill: string): ArtEl => ({ tag: 'path', attrs: { d, fill } })
const dot = (cx: number, cy: number, r: number, fill: string = W): ArtEl => ({ tag: 'circle', attrs: { cx, cy, r, fill } })

const HEART = 'M0 12 C-18 0 -14 -14 -6 -14 C-2 -14 0 -10 0 -8 C0 -10 2 -14 6 -14 C14 -14 18 0 0 12 Z'
const DROP = 'M0 -10 C6 -2 8 4 0 8 C-8 4 -6 -2 0 -10 Z'
const STAR5 = 'M0 -14 L4 -4 L14 -4 L6 3 L9 13 L0 7 L-9 13 L-6 3 L-14 -4 L-4 -4 Z'
const STAR4 = (x: number, y: number, s: number) =>
  `M${x} ${y - 8 * s} Q${x + s} ${y - s} ${x + 8 * s} ${y} Q${x + s} ${y + s} ${x} ${y + 8 * s} Q${x - s} ${y + s} ${x - 8 * s} ${y} Q${x - s} ${y - s} ${x} ${y - 8 * s} Z`

export const EYE_GLYPHS: Record<EyeGlyph, ArtDef> = {
  heart: { els: [shape(HEART, COLORS.pink)], anim: 'pulse' },
  spiral: { els: [line('M0 0 m-2 0 a2 2 0 1 1 4 0 a5 5 0 1 1 -10 0 a8 8 0 1 1 16 0 a11 11 0 1 1 -22 0', W, 3)], anim: 'spin' },
  x: { els: [line('M-10 -10 L10 10 M10 -10 L-10 10', W, 5)] },
  gt: { els: [line('M-8 -10 L8 0 L-8 10', W, 5)] },
  lt: { els: [line('M8 -10 L-8 0 L8 10', W, 5)] },
  star: { els: [shape(STAR5, COLORS.yellow)], anim: 'twinkle' },
  dot: { els: [dot(0, 0, 5)] },
}

export const MOUTH_GLYPHS: Record<MouthGlyph, ArtDef> = {
  pout: { els: [line('M-4 -8 C4 -8 4 0 -2 0 C4 0 4 8 -4 8', W, 4)] },
  teeth: { els: [{ tag: 'rect', attrs: { x: -16, y: -7, width: 32, height: 14, rx: 4, fill: 'none', stroke: W, 'stroke-width': 4 } }, line('M-8 -7 V7 M0 -7 V7 M8 -7 V7', W, 3)] },
}

const animated = (el: ArtEl, anim: ArtAnim, phase?: number): ArtEl =>
  phase === undefined ? { ...el, anim } : { ...el, anim, phase }

export const ICONS = {
  dots: { els: [animated(dot(-20, 0, 6), 'bounce', 0), animated(dot(0, 0, 6), 'bounce', 1), animated(dot(20, 0, 6), 'bounce', 2)] },
  spinner: { els: Array.from({ length: 8 }, (_, i) => dot(Math.cos(i * Math.PI / 4) * 22, Math.sin(i * Math.PI / 4) * 22, 2 + i * 0.5)), anim: 'spin' },
  exclaim: { els: [line('M0 -30 V8', W, 9), dot(0, 24, 5)], anim: 'pulse' },
  check: { els: [line('M-24 0 L-8 16 L24 -18', W, 8)], anim: 'pop' },
  equalizer: { els: Array.from({ length: 7 }, (_, i) => animated({ tag: 'rect', attrs: { x: -31 + i * 9, y: -20, width: 6, height: 40, rx: 3, fill: W } }, 'eq', i)) },
  envelope: { els: [{ tag: 'rect', attrs: { x: -30, y: -20, width: 60, height: 40, rx: 4, fill: 'none', stroke: W, 'stroke-width': 5 } }, line('M-30 -20 L0 4 L30 -20', W, 5)], anim: 'pop' },
  battery: { els: [{ tag: 'rect', attrs: { x: -28, y: -14, width: 52, height: 28, rx: 4, fill: 'none', stroke: W, 'stroke-width': 5 } }, { tag: 'rect', attrs: { x: 26, y: -6, width: 5, height: 12, rx: 1, fill: W } }, animated({ tag: 'rect', attrs: { x: -23, y: -9, width: 10, height: 18, rx: 2, fill: COLORS.red } }, 'pulse')] },
  warning: { els: [line('M0 -30 L30 22 L-30 22 Z', COLORS.red, 5), line('M0 -12 V6', COLORS.red, 5), dot(0, 14, 3, COLORS.red)], anim: 'pulse' },
  question: { els: [line('M-12 -16 C-12 -32 14 -32 14 -16 C14 -6 0 -4 0 8', W, 7), dot(0, 22, 4)], anim: 'sway' },
  download: { els: [line('M0 -26 V10 M-14 -4 L0 10 L14 -4 M-24 22 H24', W, 7)], anim: 'bounce' },
  bubble: { els: [line('M-30 -18 H30 Q36 -18 36 -12 V10 Q36 16 30 16 H-6 L-18 28 L-16 16 H-30 Q-36 16 -36 10 V-12 Q-36 -18 -30 -18 Z', W, 4), animated(dot(-14, -1, 4), 'bounce', 0), animated(dot(0, -1, 4), 'bounce', 1), animated(dot(14, -1, 4), 'bounce', 2)] },
} satisfies Record<string, ArtDef>
export type IconId = keyof typeof ICONS

export const PROPS = {
  wave: { els: [line('M-6 10 V-10 M0 10 V-14 M6 10 V-10 M12 12 V-2 M-10 2 C-12 14 -2 22 6 22 C14 22 16 14 14 6')], anim: 'wave', anchor: [172, 56], life: 2600 },
  sparkles: { els: [shape(STAR4(0, 0, 1), COLORS.yellow), animated(shape(STAR4(14, -12, 0.6), COLORS.yellow), 'twinkle', 1), animated(shape(STAR4(-12, 12, 0.5), COLORS.yellow), 'twinkle', 2)], anim: 'twinkle', anchor: [168, 34], life: 2400 },
  zzz: { els: [line('M-8 -4 H0 L-8 4 H0', W, 3), animated(line('M4 -14 H10 L4 -8 H10', W, 2.5), 'float', 1)], anim: 'float', anchor: [160, 30], life: 3000 },
  notes: { els: [line('M-4 6 V-12 L8 -14 V4', W, 3), dot(-7, 6, 4), dot(5, 4, 4)], anim: 'float', anchor: [168, 40], life: 2600 },
  heart: { els: [shape(HEART, COLORS.pink)], anim: 'float', anchor: [166, 36], life: 2400 },
  sweat: { els: [shape(DROP, COLORS.blue)], anim: 'drip', anchor: [148, 34], life: 2200 },
  anger: { els: [line('M-8 -3 Q-3 -3 -3 -8 M3 -8 Q3 -3 8 -3 M8 3 Q3 3 3 8 M-3 8 Q-3 3 -8 3', COLORS.red, 3.5)], anim: 'pulse', anchor: [150, 26], life: 2400 },
  question: { els: [line('M-6 -8 C-6 -16 7 -16 7 -8 C7 -3 0 -2 0 4', W, 4), dot(0, 11, 2.5)], anim: 'pop', anchor: [160, 28], life: 2000 },
  exclaim: { els: [line('M0 -14 V4', W, 5), dot(0, 12, 3)], anim: 'pop', anchor: [160, 28], life: 1800 },
  bulb: { els: [line('M0 -14 a10 10 0 1 1 0.1 0', COLORS.yellow, 3), line('M-5 8 H5 M-4 12 H4', COLORS.yellow, 3)], anim: 'pop', anchor: [100, 4], life: 2200 },
  confetti: { els: [animated({ tag: 'rect', attrs: { x: -20, y: -10, width: 4, height: 7, fill: COLORS.yellow } }, 'fall', 0), animated({ tag: 'rect', attrs: { x: -6, y: -16, width: 4, height: 7, fill: COLORS.pink } }, 'fall', 1), animated({ tag: 'rect', attrs: { x: 8, y: -8, width: 4, height: 7, fill: COLORS.blue } }, 'fall', 2), animated({ tag: 'rect', attrs: { x: 20, y: -14, width: 4, height: 7, fill: COLORS.orange } }, 'fall', 3)], anchor: [100, 10], life: 2600 },
  magnifier: { els: [line('M0 -9 a9 9 0 1 1 -0.1 0', W, 3.5), line('M6 6 L14 14', W, 4)], anim: 'scan', anchor: [100, 128], life: 3000 },
  laptop: { els: [line('M-14 -10 H14 V6 H-14 Z M-18 10 H18', W, 3)], anim: 'pop', anchor: [100, 132], life: 3000 },
  coffee: { els: [line('M-10 -6 H8 V8 Q8 12 4 12 H-6 Q-10 12 -10 8 Z M8 -2 Q14 -2 14 3 Q14 7 8 7', W, 3), animated(line('M-4 -10 Q-6 -14 -4 -18 M2 -10 Q0 -14 2 -18', W, 2), 'steam')], anchor: [36, 112], life: 4000 },
  thermometer: { els: [line('M0 -14 V6', W, 6), dot(0, 10, 5, COLORS.red), line('M0 -2 V6', COLORS.red, 3)], anim: 'pulse', anchor: [166, 50], life: 2600 },
  sun: { els: [dot(0, 0, 7, COLORS.yellow), line('M0 -14 V-10 M0 10 V14 M-14 0 H-10 M10 0 H14 M-10 -10 L-7 -7 M7 7 L10 10 M-10 10 L-7 7 M7 -7 L10 -10', COLORS.yellow, 2.5)], anim: 'spin', anchor: [172, 22], life: 3000 },
  umbrella: { els: [line('M-16 0 Q0 -18 16 0 Z', W, 3), line('M0 0 V12 Q0 16 -4 14', W, 3)], anim: 'sway', anchor: [100, 0], life: 3200 },
  snowflake: { els: [line('M0 -12 V12 M-10 -6 L10 6 M-10 6 L10 -6', COLORS.blue, 2.5)], anim: 'spin', anchor: [170, 26], life: 3000 },
  tear: { els: [shape(DROP, COLORS.blue)], anim: 'drip', anchor: [62, 84], life: 2200 },
} satisfies Record<string, ArtDef>
export type PropId = keyof typeof PROPS

// Accessories are drawn directly in face viewBox coordinates (anchor [0,0]).
export const ACCESSORIES = {
  headphones: { els: [line('M40 64 C40 -4 160 -4 160 64', W, 5), { tag: 'rect', attrs: { x: 28, y: 50, width: 16, height: 30, rx: 7, fill: W } }, { tag: 'rect', attrs: { x: 156, y: 50, width: 16, height: 30, rx: 7, fill: W } }] },
  sunglasses: { els: [{ tag: 'path', attrs: { d: 'M50 48 H94 V64 Q94 76 82 76 H62 Q50 76 50 64 Z M106 48 H150 V64 Q150 76 138 76 H118 Q106 76 106 64 Z', fill: '#000', stroke: W, 'stroke-width': 4 } }, line('M94 54 H106', W, 4)] },
  'party-hat': { els: [line('M100 -16 L84 24 H116 Z', W, 4), line('M92 4 L108 0 M88 14 L112 10', COLORS.pink, 3), dot(100, -18, 4, COLORS.yellow)] },
  'wizard-hat': { els: [line('M62 28 H138 M76 28 L104 -26 L124 28', W, 4), shape(STAR4(104, 6, 0.7), COLORS.yellow)] },
  nightcap: { els: [line('M70 30 Q100 -10 142 18 L150 34 M70 30 H132', W, 4), dot(150, 37, 5)] },
  scarf: { els: [line('M64 122 Q100 136 136 122', COLORS.pink, 7), line('M122 128 L126 146', COLORS.pink, 6)] },
  'chef-hat': { els: [line('M76 28 H124 V12 Q134 12 134 2 Q134 -10 120 -8 Q114 -18 100 -16 Q86 -18 80 -8 Q66 -10 66 2 Q66 12 76 12 Z', W, 4)] },
} satisfies Record<string, ArtDef>
export type AccessoryId = keyof typeof ACCESSORIES

const f2 = (n: number) => (Math.round(n * 100) / 100).toString()

/** Transform for an animated art element at time t (ms). Pure. */
export function artTransform(anim: ArtAnim | undefined, tMs: number, phase = 0, level = 0): string {
  const s = tMs / 1000
  switch (anim) {
    case 'bounce': return `translate(0 ${f2(-Math.max(0, Math.sin(s * 6 - phase * 0.9)) * 6)})`
    case 'spin': return `rotate(${f2((s * 120) % 360)})`
    case 'wave': return `rotate(${f2(Math.sin(s * 9) * 20)})`
    case 'twinkle': return `scale(${f2(0.75 + 0.25 * (0.5 + 0.5 * Math.sin(s * 5 + phase * 2)))})`
    case 'float': return `translate(${f2(Math.sin(s * 2 + phase) * 3)} ${f2(-(s * 10) % 18)})`
    case 'drip': return `translate(0 ${f2((s * 14) % 16)})`
    case 'pulse': return `scale(${f2(1 + 0.08 * Math.sin(s * 7))})`
    case 'pop': return 'scale(1)'
    case 'fall': return `translate(${f2(Math.sin(s * 3 + phase) * 6)} ${f2((s * 40 + phase * 9) % 60)}) rotate(${f2((s * 200 + phase * 50) % 360)})`
    case 'scan': return `translate(${f2(Math.sin(s * 1.6) * 30)} 0)`
    case 'steam': return `translate(0 ${f2(-(s * 6) % 6)})`
    case 'sway': return `rotate(${f2(Math.sin(s * 2.4) * 8)})`
    case 'eq': {
      const wobble = 0.35 + 0.65 * Math.abs(Math.sin(s * 7 + phase * 1.3))
      const h = Math.max(0.15, Math.min(1, level > 0 ? level * wobble * 1.4 : wobble))
      return `scale(1 ${f2(h)})`
    }
    default: return ''
  }
}

/** Pop-in (overshoot) → hold → fade-out envelope for transient props. */
export function propEnvelope(ageMs: number, lifeMs: number): { scale: number; opacity: number } {
  const IN = 260
  const OUT = 350
  if (ageMs <= 0) return { scale: 0.3, opacity: 0 }
  if (ageMs < IN) {
    const u = ageMs / IN
    return { scale: 0.3 + 0.7 * (1 + 0.25 * Math.sin(u * Math.PI)) * u, opacity: Math.min(1, u * 2) }
  }
  if (ageMs > lifeMs - OUT) {
    const u = Math.max(0, (lifeMs - ageMs) / OUT)
    return { scale: 0.85 + 0.15 * u, opacity: u }
  }
  return { scale: 1, opacity: 1 }
}
