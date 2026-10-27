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
export interface ArtEl { tag: 'path' | 'circle' | 'rect' | 'ellipse'; attrs: Record<string, string | number>; anim?: ArtAnim; phase?: number }
export interface ArtDef { els: ArtEl[]; anim?: ArtAnim; anchor?: [number, number]; life?: number; /** Extra size on top of the pop-in envelope (DL-155). */ scale?: number }

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

// --- DL-155: full-colour props -------------------------------------------------
// Gradients live once in RobotFace's <defs>; art references them as url(#rb-<id>).
export interface GradientDef { id: string; x1?: number; y1?: number; x2?: number; y2?: number; stops: ReadonlyArray<readonly [number, string]> }
export const GRADIENTS: readonly GradientDef[] = [
  { id: 'rb-skin', x1: 0, y1: 0, x2: 0, y2: 1, stops: [[0, '#ffffff'], [1, '#c9d4ff']] },
  { id: 'rb-sleeve', x1: 0, y1: 0, x2: 0, y2: 1, stops: [[0, '#6cc7ff'], [1, '#3a7bff']] },
  { id: 'rb-cuff', x1: 0, y1: 0, x2: 0, y2: 1, stops: [[0, '#ff8fbd'], [1, '#ff4f93']] },
  { id: 'rb-metal', x1: 0, y1: 0, x2: 0, y2: 1, stops: [[0, '#e8ecf8'], [1, '#8d96b5']] },
  { id: 'rb-metal-dark', x1: 0, y1: 0, x2: 0, y2: 1, stops: [[0, '#4a516e'], [1, '#262b40']] },
  { id: 'rb-screen', x1: 0, y1: 0, x2: 1, y2: 1, stops: [[0, '#14204a'], [1, '#0a0f26']] },
  { id: 'rb-gold', x1: 0, y1: 0, x2: 1, y2: 1, stops: [[0, '#fff1a8'], [0.5, '#ffd84d'], [1, '#e8a317']] },
  { id: 'rb-mug', x1: 0, y1: 0, x2: 1, y2: 0, stops: [[0, '#ffffff'], [1, '#c4cdf5']] },
  { id: 'rb-glass', x1: 0.2, y1: 0, x2: 0.8, y2: 1, stops: [[0, '#fff7c2'], [0.6, '#ffd84d'], [1, '#ff9a4d']] },
  { id: 'rb-heart', x1: 0.2, y1: 0, x2: 0.8, y2: 1, stops: [[0, '#ff9cc7'], [1, '#ff3f7f']] },
  { id: 'rb-red', x1: 0, y1: 0, x2: 0, y2: 1, stops: [[0, '#ff7a7a'], [1, '#e02a2a']] },
  { id: 'rb-blue', x1: 0, y1: 0, x2: 0, y2: 1, stops: [[0, '#bfe6ff'], [1, '#3f9bff']] },
  { id: 'rb-sun', x1: 0.2, y1: 0.2, x2: 0.8, y2: 0.8, stops: [[0, '#fff3a0'], [1, '#ff9a4d']] },
  { id: 'rb-ice', x1: 0, y1: 0, x2: 1, y2: 1, stops: [[0, '#e6f6ff'], [1, '#6cc7ff']] },
]
const G = (id: string) => `url(#rb-${id})`
const ell = (cx: number, cy: number, rx: number, ry: number, fill: string, extra: Record<string, string | number> = {}): ArtEl =>
  ({ tag: 'ellipse', attrs: { cx, cy, rx, ry, fill, ...extra } })
const box = (x: number, y: number, w: number, h: number, rx: number, fill: string, extra: Record<string, string | number> = {}): ArtEl =>
  ({ tag: 'rect', attrs: { x, y, width: w, height: h, rx, fill, ...extra } })
const shine = (cx: number, cy: number, rx: number, ry: number): ArtEl => ell(cx, cy, rx, ry, W, { opacity: 0.55 })
const COFFEE_BROWN = '#8a4f24'

export const PROPS = {
  wave: {
    els: [
      box(-12, 18, 24, 9, 3, G('cuff')),
      box(-11, -12, 5.5, 22, 2.75, G('skin')), box(-5, -17, 5.5, 27, 2.75, G('skin')),
      box(1, -15, 5.5, 25, 2.75, G('skin')), box(7, -9, 5.5, 20, 2.75, G('skin')),
      ell(0, 12, 13, 11, G('skin')),
      shape('M-11 12 Q-24 8 -21 -1 Q-19 -6 -14 -2 L-9 5 Z', G('skin')),
      line('M19 -8 Q26 0 19 8', COLORS.yellow, 2.5), line('M24 -12 Q34 0 24 12', COLORS.yellow, 2),
    ], anim: 'wave', anchor: [172, 56], life: 2600, scale: 1.25,
  },
  sparkles: {
    els: [shape(STAR4(0, 0, 1.5), G('gold')), animated(shape(STAR4(18, -14, 0.9), G('gold')), 'twinkle', 1),
      animated(shape(STAR4(-16, 14, 0.75), G('gold')), 'twinkle', 2), animated(dot(14, 16, 2.2, COLORS.pink), 'twinkle', 3),
      animated(dot(-18, -12, 2, COLORS.blue), 'twinkle', 4)],
    anim: 'twinkle', anchor: [168, 34], life: 2400,
  },
  zzz: {
    els: [line('M-10 -6 H2 L-10 6 H2', G('ice'), 4.5), animated(line('M6 -20 H15 L6 -11 H15', G('ice'), 3.5), 'float', 1),
      animated(line('M18 -34 H25 L18 -27 H25', COLORS.blue, 2.5), 'float', 2)],
    anim: 'float', anchor: [160, 30], life: 3000,
  },
  notes: {
    els: [line('M-8 10 V-14 L10 -17 V7', COLORS.pink, 3.5), ell(-11, 10, 5.5, 4.2, G('heart')), ell(7, 7, 5.5, 4.2, G('heart')),
      animated(line('M18 4 V-10 L28 -12 V0', COLORS.blue, 3), 'float', 1), animated(ell(15, 4, 4, 3, G('blue')), 'float', 1),
      animated(ell(25, 0, 4, 3, G('blue')), 'float', 1)],
    anim: 'float', anchor: [168, 40], life: 2600,
  },
  heart: {
    els: [shape(HEART, G('heart')), line(HEART, COLORS.red, 1.8), ell(-6, -8, 3.5, 2.2, W, { opacity: 0.6 })],
    anim: 'float', anchor: [166, 36], life: 2400, scale: 1.4,
  },
  sweat: { els: [shape(DROP, G('blue')), ell(-2.5, 0, 1.6, 3, W, { opacity: 0.7 })], anim: 'drip', anchor: [148, 34], life: 2200, scale: 1.4 },
  anger: {
    els: [dot(0, 0, 13, COLORS.orange), line('M-9 -4 Q-4 -4 -4 -9 M4 -9 Q4 -4 9 -4 M9 4 Q4 4 4 9 M-4 9 Q-4 4 -9 4', COLORS.red, 4.5)],
    anim: 'pulse', anchor: [150, 26], life: 2400,
  },
  question: {
    els: [dot(0, 0, 15, G('gold')), line('M-6 -6 C-6 -14 7 -14 7 -6 C7 -1 0 0 0 6', '#000', 3.8), dot(0, 11, 2.4, '#000')],
    anim: 'pop', anchor: [160, 28], life: 2000,
  },
  exclaim: {
    els: [dot(0, 0, 15, G('red')), line('M0 -9 V3', W, 4.5), dot(0, 9, 2.6, W)],
    anim: 'pop', anchor: [160, 28], life: 1800,
  },
  bulb: {
    els: [{ tag: 'circle', attrs: { cx: 0, cy: -4, r: 21, fill: COLORS.yellow, opacity: 0.28 } },
      shape('M-11 6 C-17 -2 -14 -18 0 -19 C14 -18 17 -2 11 6 C9 9 9 11 9 13 H-9 C-9 11 -9 9 -11 6 Z', G('glass')),
      line('M-4 12 V2 L0 -4 L4 2 V12', '#e8a317', 1.8), shine(-6, -11, 3, 5),
      box(-8, 13, 16, 4, 2, G('metal')), box(-6, 17, 12, 4, 2, G('metal-dark')),
      line('M0 -30 V-26 M-20 -22 L-17 -19 M20 -22 L17 -19 M-26 -6 H-22 M22 -6 H26', COLORS.yellow, 2.5)],
    anim: 'pop', anchor: [100, 4], life: 2200, scale: 1.1,
  },
  confetti: {
    els: [animated(box(-24, -10, 5, 9, 1, COLORS.yellow), 'fall', 0), animated(box(-14, -16, 5, 9, 1, COLORS.pink), 'fall', 1),
      animated(box(-4, -8, 5, 9, 1, COLORS.blue), 'fall', 2), animated(box(6, -15, 5, 9, 1, COLORS.orange), 'fall', 3),
      animated(box(16, -9, 5, 9, 1, COLORS.red), 'fall', 4), animated(box(26, -14, 5, 9, 1, COLORS.yellow), 'fall', 5),
      animated(dot(-19, -20, 3, COLORS.blue), 'fall', 6), animated(dot(1, -22, 3, COLORS.pink), 'fall', 7),
      animated(dot(21, -21, 3, COLORS.yellow), 'fall', 8), animated(dot(-9, -4, 2.5, COLORS.orange), 'fall', 9)],
    anchor: [100, 6], life: 2600, scale: 1.3,
  },
  magnifier: {
    els: [{ tag: 'circle', attrs: { cx: 0, cy: 0, r: 12, fill: G('blue'), opacity: 0.55 } },
      { tag: 'circle', attrs: { cx: 0, cy: 0, r: 12, fill: 'none', stroke: G('metal'), 'stroke-width': 4.5 } },
      line('M9 9 L20 20', COFFEE_BROWN, 6), shine(-4, -5, 3.5, 2)],
    anim: 'scan', anchor: [100, 128], life: 3000, scale: 1.2,
  },
  laptop: {
    els: [box(-17, -12, 34, 22, 3, G('metal-dark')), box(-14, -9, 28, 16, 1.5, G('screen')),
      box(-11, -6, 14, 2.2, 1, COLORS.pink), box(-11, -2, 20, 2.2, 1, COLORS.blue), box(-11, 2, 10, 2.2, 1, COLORS.yellow),
      shape('M-21 12 H21 L18 16 H-18 Z', G('metal'))],
    anim: 'pop', anchor: [100, 132], life: 3000, scale: 1.3,
  },
  coffee: {
    els: [ell(0, 15, 18, 4, G('metal'), { opacity: 0.9 }),
      shape('M-12 -6 H10 V8 Q10 14 4 14 H-6 Q-12 14 -12 8 Z', G('mug')),
      line('M10 -2 Q19 -2 19 4 Q19 10 10 9', COLORS.white, 3), ell(-1, -6, 11, 3, COFFEE_BROWN), shine(-6, 3, 1.8, 5),
      animated(line('M-6 -12 Q-9 -18 -6 -24 M2 -12 Q-1 -18 2 -24', COLORS.white, 2.4), 'steam')],
    anchor: [36, 112], life: 4000, scale: 1.25,
  },
  thermometer: {
    els: [box(-4, -18, 8, 26, 4, G('blue')), dot(0, 11, 7, G('red')), box(-1.6, -4, 3.2, 14, 1.6, COLORS.red),
      line('M6 -12 H10 M6 -6 H10 M6 0 H10', W, 1.8)],
    anim: 'pulse', anchor: [166, 50], life: 2600, scale: 1.2,
  },
  sun: {
    els: [dot(0, 0, 11, G('sun')), line('M0 -20 V-14 M0 14 V20 M-20 0 H-14 M14 0 H20 M-14 -14 L-10 -10 M10 10 L14 14 M-14 14 L-10 10 M10 -10 L14 -14', COLORS.yellow, 3.2),
      shine(-4, -4, 3, 2)],
    anim: 'spin', anchor: [172, 22], life: 3000,
  },
  umbrella: {
    els: [shape('M-22 2 Q-22 -20 0 -22 Q22 -20 22 2 Q15 -4 7 2 Q0 -4 -7 2 Q-15 -4 -22 2 Z', G('heart')),
      shape('M-7 2 Q0 -4 7 2 Q4 -12 0 -22 Q-4 -12 -7 2 Z', G('glass')),
      line('M0 2 V16 Q0 22 -5 20', COFFEE_BROWN, 3.2), dot(0, -23, 2, '#e8a317')],
    anim: 'sway', anchor: [100, 0], life: 3200, scale: 1.1,
  },
  snowflake: {
    els: [line('M0 -16 V16 M-14 -8 L14 8 M-14 8 L14 -8', G('ice'), 3), line('M-4 -13 L0 -9 L4 -13 M-4 13 L0 9 L4 13', COLORS.blue, 2), dot(0, 0, 3, W)],
    anim: 'spin', anchor: [170, 26], life: 3000,
  },
  tear: { els: [shape(DROP, G('blue')), ell(-2.5, 0, 1.6, 3, W, { opacity: 0.7 })], anim: 'drip', anchor: [62, 84], life: 2200, scale: 1.5 },
  rocket: {
    els: [animated(shape('M-6 14 Q0 34 6 14 Z', G('sun')), 'pulse', 0), animated(shape('M-3 14 Q0 26 3 14 Z', COLORS.yellow), 'pulse', 1),
      shape('M-8 8 L-17 18 L-8 16 Z', G('red')), shape('M8 8 L17 18 L8 16 Z', G('red')),
      shape('M0 -24 Q12 -10 9 12 H-9 Q-12 -10 0 -24 Z', G('skin')), shape('M0 -24 Q6 -18 8 -12 H-8 Q-6 -18 0 -24 Z', G('red')),
      dot(0, -3, 4.5, G('blue')), { tag: 'circle', attrs: { cx: 0, cy: -3, r: 4.5, fill: 'none', stroke: G('metal'), 'stroke-width': 1.6 } }],
    anim: 'float', anchor: [168, 62], life: 2800, scale: 1.2,
  },
  trophy: {
    els: [shape('M-12 -14 H12 V-2 Q12 10 0 12 Q-12 10 -12 -2 Z', G('gold')),
      line('M-12 -10 Q-22 -10 -20 -2 Q-18 4 -11 4 M12 -10 Q22 -10 20 -2 Q18 4 11 4', '#e8a317', 2.8),
      box(-2.5, 12, 5, 7, 1, G('gold')), box(-9, 19, 18, 5, 2, G('metal-dark')), shape(STAR4(0, -3, 0.9), W), shine(-6, -6, 2, 5)],
    anim: 'pop', anchor: [100, 4], life: 2600, scale: 1.2,
  },
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
    const v = u - 1
    const back = 1 + 3.5 * v * v * v + 2.5 * v * v // easeOutBack: peaks ~1.19, lands on 1
    return { scale: 0.3 + 0.7 * back, opacity: Math.min(1, u * 2) }
  }
  if (ageMs > lifeMs - OUT) {
    const u = Math.max(0, (lifeMs - ageMs) / OUT)
    return { scale: 0.85 + 0.15 * u, opacity: u }
  }
  return { scale: 1, opacity: 1 }
}
