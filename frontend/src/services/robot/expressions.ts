/**
 * DL-153 — expression presets. Each is a partial FaceParams target over the
 * neutral face, plus optional glyph eyes/mouth. Inspired by Taby, EMO,
 * LeTianPai and robot-face icon sheets; all values are our own.
 */
import { defaultParams, type EyeParams, type FaceParams, type FaceScalars } from './faceRig'

export type EyeGlyph = 'heart' | 'spiral' | 'x' | 'gt' | 'lt' | 'star' | 'dot'
export type MouthGlyph = 'pout' | 'teeth'

export interface ExpressionDef {
  eyes?: Partial<EyeParams>
  eyeL?: Partial<EyeParams>
  eyeR?: Partial<EyeParams>
  face?: Partial<FaceScalars>
  glyphs?: readonly [EyeGlyph | null, EyeGlyph | null]
  mouthGlyph?: MouthGlyph
}

const HAPPY_EYE = { lidBottom: 0.55, curveUp: 1 }
const CONTENT_EYE = { lidTop: 0.55, curveDown: 1 }

export const EXPRESSIONS = {
  neutral: {},
  happy: { eyes: HAPPY_EYE, face: { mouthCurve: 1, mouthWidth: 26 } },
  joy: { eyes: HAPPY_EYE, face: { mouthCurve: 1, mouthOpen: 0.7, mouthWidth: 30, tongue: 1, bounce: -4 } },
  grin: { face: { mouthCurve: 1, mouthOpen: 0.6, mouthWidth: 34 } },
  content: { eyes: CONTENT_EYE, face: { mouthCurve: 0.6 } },
  'wink-l': { eyeL: HAPPY_EYE, face: { mouthCurve: 0.8, mouthSkew: 0.5 } },
  'wink-r': { eyeR: HAPPY_EYE, face: { mouthCurve: 0.8, mouthSkew: -0.5 } },
  'look-l': { face: { lookX: -1 } },
  'look-r': { face: { lookX: 1 } },
  'look-up': { face: { lookY: -1 } },
  'look-down': { face: { lookY: 1 } },
  'side-eye': { eyes: { lidTop: 0.45 }, face: { lookX: 1, mouthCurve: 0, mouthWidth: 18 } },
  glare: { eyes: { lidTop: 0.35, lidTilt: 0.6 }, face: { mouthCurve: -0.3 } },
  angry: { eyes: { lidTop: 0.4, lidTilt: 1, h: 44 }, face: { mouthCurve: -0.8, mouthWidth: 26 } },
  squint: { eyes: { lidTop: 0.35, lidBottom: 0.35 }, face: { mouthCurve: 0.2 } },
  focused: { eyes: { h: 30, w: 34, lidTop: 0.15 }, face: { mouthOpacity: 0 } },
  bored: { eyes: { lidTop: 0.5 }, face: { mouthCurve: 0, mouthWidth: 16 } },
  unimpressed: { eyes: { lidTop: 0.5, lidBottom: 0.2 }, face: { mouthCurve: -0.1, mouthWidth: 24 } },
  suspicious: { eyeL: { lidTop: 0.55 }, eyeR: { lidTop: 0.15 }, face: { lookX: -0.5, mouthSkew: 0.6, mouthCurve: 0 } },
  sleepy: { eyes: { lidTop: 0.7 }, face: { mouthWidth: 14, mouthCurve: 0.1, lookY: 0.3 } },
  asleep: { eyes: { lidTop: 0.6, lidBottom: 0.4, curveDown: 0.6 }, face: { mouthWidth: 12, mouthCurve: 0.2, lookY: 0.4 } },
  surprised: { eyes: { h: 58, w: 32 }, face: { mouthWidth: 12, mouthOpen: 0.6, mouthCurve: 0 } },
  shocked: { glyphs: ['dot', 'dot'], face: { mouthWidth: 14, mouthOpen: 0.8, mouthCurve: 0 } },
  love: { glyphs: ['heart', 'heart'], face: { mouthCurve: 1, blush: 0.6 } },
  starstruck: { glyphs: ['star', 'star'], face: { mouthCurve: 1, mouthOpen: 0.5 } },
  dizzy: { glyphs: ['spiral', 'spiral'], face: { mouthWave: 1, mouthCurve: 0 } },
  dead: { glyphs: ['x', 'x'], face: { mouthCurve: 0, mouthWidth: 22 } },
  laughing: { glyphs: ['gt', 'lt'], face: { mouthCurve: 1, mouthOpen: 0.9, mouthWidth: 30 } },
  crying: { eyes: CONTENT_EYE, face: { mouthCurve: -0.8 } },
  sad: { eyes: { lidTop: 0.3, lidTilt: -0.6, h: 44 }, face: { mouthCurve: -0.8, lookY: 0.3 } },
  worried: { eyes: { w: 24, h: 40, lidTilt: -0.4, lidTop: 0.15 }, face: { mouthWave: 0.8, mouthCurve: -0.2 } },
  shy: { eyes: HAPPY_EYE, face: { lookX: -0.6, lookY: 0.6, blush: 1, mouthCurve: 0.6, mouthWidth: 14 } },
  puppy: { eyes: { w: 36, h: 56 }, face: { mouthCurve: 0.4, mouthWidth: 14, lookY: -0.2 } },
  thinking: { eyes: { lidBottom: 0.15 }, face: { lookX: 0.7, lookY: -0.8, mouthSkew: 0.7, mouthCurve: 0 } },
  mischievous: { eyes: { lidTop: 0.35, lidTilt: 0.5, lidBottom: 0.2 }, face: { mouthCurve: 0.8, mouthSkew: 0.8 } },
  smug: { eyes: CONTENT_EYE, face: { mouthCurve: 0.7, mouthSkew: 0.8 } },
  pout: { eyes: { w: 26, h: 40 }, mouthGlyph: 'pout', face: { mouthOpacity: 0 } },
  whistle: { eyes: { lidTop: 0.2 }, face: { lookX: -0.8, lookY: -0.5, mouthWidth: 8, mouthOpen: 0.4, mouthCurve: 0 } },
  'teeth-grit': { eyes: { lidTop: 0.35, lidBottom: 0.3, lidTilt: 0.5 }, mouthGlyph: 'teeth', face: { mouthOpacity: 0 } },
  yawn: { eyes: { lidTop: 0.75, lidBottom: 0.2 }, face: { mouthWidth: 18, mouthOpen: 1, mouthCurve: -0.2 } },
} as const satisfies Record<string, ExpressionDef>

export type ExpressionId = keyof typeof EXPRESSIONS
export const EXPRESSION_IDS = Object.keys(EXPRESSIONS) as ExpressionId[]

export function resolveExpression(id: ExpressionId): {
  params: FaceParams; glyphs: [EyeGlyph | null, EyeGlyph | null]; mouthGlyph: MouthGlyph | null
} {
  const def: ExpressionDef = EXPRESSIONS[id] ?? EXPRESSIONS.neutral
  const p = defaultParams()
  Object.assign(p.eyeL, def.eyes, def.eyeL)
  Object.assign(p.eyeR, def.eyes, def.eyeR)
  Object.assign(p.face, def.face)
  return { params: p, glyphs: def.glyphs ? [...def.glyphs] as [EyeGlyph | null, EyeGlyph | null] : [null, null], mouthGlyph: def.mouthGlyph ?? null }
}
