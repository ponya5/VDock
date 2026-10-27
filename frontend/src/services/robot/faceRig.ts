/**
 * DL-153 — parametric robot face. A face is a flat set of numbers; an eye is
 * a rounded rect drawn as exactly 8 cubic segments (4 corners + 4 edges) and
 * the mouth as exactly 4 cubics (upper lip + lower lip), so any expression
 * interpolates smoothly into any other. Coordinates are in a 200×140 viewBox.
 */
export const VIEW = { w: 200, h: 140 } as const
export const EYE_CENTERS = { L: [72, 62], R: [128, 62] } as const
export const MOUTH_CENTER = [100, 100] as const

export const EYE_KEYS = ['w', 'h', 'r', 'lidTop', 'lidBottom', 'lidTilt', 'curveUp', 'curveDown', 'x', 'y', 'opacity'] as const
export type EyeKey = typeof EYE_KEYS[number]
export type EyeParams = Record<EyeKey, number>

export const FACE_KEYS = ['lookX', 'lookY', 'tilt', 'bounce', 'scale', 'mouthWidth', 'mouthOpen', 'mouthCurve',
  'mouthSkew', 'mouthWave', 'mouthOpacity', 'tongue', 'blush'] as const
export type FaceKey = typeof FACE_KEYS[number]
export type FaceScalars = Record<FaceKey, number>

export interface FaceParams { eyeL: EyeParams; eyeR: EyeParams; face: FaceScalars }

export const DEFAULT_EYE: EyeParams = {
  w: 30, h: 50, r: 1, lidTop: 0, lidBottom: 0, lidTilt: 0, curveUp: 0, curveDown: 0, x: 0, y: 0, opacity: 1,
}
export const DEFAULT_FACE: FaceScalars = {
  lookX: 0, lookY: 0, tilt: 0, bounce: 0, scale: 1,
  mouthWidth: 22, mouthOpen: 0, mouthCurve: 0.6, mouthSkew: 0, mouthWave: 0, mouthOpacity: 1, tongue: 0, blush: 0,
}

export function defaultParams(): FaceParams {
  return { eyeL: { ...DEFAULT_EYE }, eyeR: { ...DEFAULT_EYE }, face: { ...DEFAULT_FACE } }
}

const LOOK_EYE = { x: 16, y: 11 }
const LOOK_MOUTH = { x: 9, y: 6 }
const MIN_EYE_H = 4
const K = 0.5523 // circle-ish cubic handle ratio

const f2 = (n: number) => (Math.round(n * 100) / 100).toString()
const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v))

export function eyeCenter(side: 'L' | 'R', p: FaceParams): [number, number] {
  const e = side === 'L' ? p.eyeL : p.eyeR
  const [bx, by] = EYE_CENTERS[side]
  return [bx + e.x + p.face.lookX * LOOK_EYE.x, by + e.y + p.face.lookY * LOOK_EYE.y]
}

export function mouthCenter(p: FaceParams): [number, number] {
  return [MOUTH_CENTER[0] + p.face.lookX * LOOK_MOUTH.x, MOUTH_CENTER[1] + p.face.lookY * LOOK_MOUTH.y]
}

/** Eye outline: rounded rect with lids, slanted top lid, ^/‿ bend. */
export function eyePath(e: EyeParams, cx: number, cy: number, side: 'L' | 'R'): string {
  const w = Math.max(2, e.w)
  const h = Math.max(2, e.h)
  const left = cx - w / 2
  const right = cx + w / 2
  let top = cy - h / 2 + clamp(e.lidTop, 0, 1) * h
  let bottom = cy + h / 2 - clamp(e.lidBottom, 0, 1) * h
  if (bottom - top < MIN_EYE_H) {
    const mid = (top + bottom) / 2
    top = mid - MIN_EYE_H / 2
    bottom = mid + MIN_EYE_H / 2
  }
  // Slant: positive lidTilt lowers the INNER top corner (angry), negative raises it (sad).
  const inner = side === 'L' ? 1 : -1 // +1: inner corner is on the right
  const slant = clamp(e.lidTilt, -1, 1) * h * 0.22
  const topLeftY = top - (slant / 2) * inner
  const topRightY = top + (slant / 2) * inner
  const span = bottom - Math.max(topLeftY, topRightY)
  const rr = Math.max(0, Math.min(clamp(e.r, 0, 1) * Math.min(w, h) / 2, w / 2, Math.max(span, MIN_EYE_H) / 2))
  const k = rr * K

  // Points clockwise from top-left corner end; each segment is one cubic.
  const pts: Array<[number, number, number, number, number, number]> = []
  const startX = left + rr
  const startY = topLeftY
  const lerpTop = (x: number) => topLeftY + (topRightY - topLeftY) * ((x - left) / w)
  // 1 top edge
  pts.push([startX + (right - rr - startX) / 3, lerpTop(startX + (right - rr - startX) / 3),
    right - rr - (right - rr - startX) / 3, lerpTop(right - rr - (right - rr - startX) / 3), right - rr, topRightY])
  // 2 top-right corner
  pts.push([right - rr + k, topRightY, right, topRightY + rr - k, right, topRightY + rr])
  // 3 right edge
  pts.push([right, topRightY + rr + (bottom - rr - topRightY - rr) / 3, right, bottom - rr - (bottom - rr - topRightY - rr) / 3, right, bottom - rr])
  // 4 bottom-right corner
  pts.push([right, bottom - rr + k, right - rr + k, bottom, right - rr, bottom])
  // 5 bottom edge
  pts.push([right - rr - (right - left - 2 * rr) / 3, bottom, left + rr + (right - left - 2 * rr) / 3, bottom, left + rr, bottom])
  // 6 bottom-left corner
  pts.push([left + rr - k, bottom, left, bottom - rr + k, left, bottom - rr])
  // 7 left edge
  pts.push([left, bottom - rr - (bottom - rr - topLeftY - rr) / 3, left, topLeftY + rr + (bottom - rr - topLeftY - rr) / 3, left, topLeftY + rr])
  // 8 top-left corner
  pts.push([left, topLeftY + rr - k, left + rr - k, topLeftY, startX, startY])

  // ^ / ‿ bend: shift every point vertically by a parabola across the width.
  // curveUp pushes the ends down (middle stays highest → ^);
  // curveDown pulls the ends up (middle lowest → ‿ crescent).
  const bendA = h * 0.32 * (clamp(e.curveUp, 0, 1) - clamp(e.curveDown, 0, 1))
  const bend = (x: number, y: number): [number, number] => {
    const u = clamp((x - cx) / (w / 2), -1, 1)
    return [x, y + bendA * u * u]
  }
  const P = (x: number, y: number) => {
    const [bx, by] = bend(x, y)
    return `${f2(bx)} ${f2(by)}`
  }
  let d = `M${P(startX, startY)}`
  for (const [x1, y1, x2, y2, x, y] of pts) d += ` C${P(x1, y1)} ${P(x2, y2)} ${P(x, y)}`
  return d + ' Z'
}

/** Mouth: closed shape, upper lip then lower lip; zero-area when shut (drawn as a stroke). */
export function mouthPath(f: FaceScalars, cx: number, cy: number): string {
  const hw = Math.max(1, f.mouthWidth / 2)
  const curve = clamp(f.mouthCurve, -1, 1)
  const skew = clamp(f.mouthSkew, -1, 1)
  const wave = clamp(f.mouthWave, 0, 1) * 4
  const open = clamp(f.mouthOpen, 0, 1)
  const lx = cx - hw
  const rx = cx + hw
  const ly = cy - curve * 4 - skew * 4
  const ry = cy - curve * 4 + skew * 4
  const mx = cx + skew * 3
  const my = cy + curve * 5
  const lowY = my + open * 16 * (curve >= 0 ? 1 : 0.6)
  const P = (x: number, y: number) => `${f2(x)} ${f2(y)}`
  // upper lip: left → mid → right (wave pushes the control points in opposite directions)
  let d = `M${P(lx, ly)}`
  d += ` C${P(lx + hw * 0.35, my + wave)} ${P(mx - hw * 0.35, my - wave)} ${P(mx, my)}`
  d += ` C${P(mx + hw * 0.35, my + wave)} ${P(rx - hw * 0.35, my - wave)} ${P(rx, ry)}`
  // lower lip: right → mid → left
  d += ` C${P(rx - hw * 0.2, ry + (lowY - my) * 0.9)} ${P(mx + hw * 0.5, lowY)} ${P(mx, lowY)}`
  d += ` C${P(mx - hw * 0.5, lowY)} ${P(lx + hw * 0.2, ly + (lowY - my) * 0.9)} ${P(lx, ly)}`
  return d + ' Z'
}

export function tonguePath(f: FaceScalars, cx: number, cy: number): string {
  const open = clamp(f.mouthOpen, 0, 1)
  const hw = Math.max(1, f.mouthWidth / 2) * 0.45
  const my = cy + clamp(f.mouthCurve, -1, 1) * 5 + open * 16 * 0.55
  const P = (x: number, y: number) => `${f2(x)} ${f2(y)}`
  return `M${P(cx - hw, my)} C${P(cx - hw, my + 9 * open)} ${P(cx + hw, my + 9 * open)} ${P(cx + hw, my)} Z`
}
