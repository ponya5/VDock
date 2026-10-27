/**
 * DL-153 — turns raw pointer movement (mouse hover or finger drag) over the
 * robot into gestures the mood engine reacts to. Pure; coordinates are face
 * viewBox units divided by 200, so the face spans x 0..1, y 0..0.7.
 */
export type PointerGesture = 'enter' | 'eyes' | 'mouth' | 'shake' | 'dizzy' | 'annoyed' | 'circle' | 'linger' | 'approach' | 'leave' | 'return'
export interface Rect { x: number; y: number; w: number; h: number }
export interface FaceRegions { face: Rect; eyes: Rect[]; mouth: Rect; center: [number, number] }

export const DEFAULT_REGIONS: FaceRegions = {
  face: { x: 0, y: 0, w: 1, h: 0.7 },
  eyes: [{ x: 0.25, y: 0.16, w: 0.22, h: 0.3 }, { x: 0.53, y: 0.16, w: 0.22, h: 0.3 }],
  mouth: { x: 0.38, y: 0.44, w: 0.24, h: 0.14 },
  center: [0.5, 0.35],
}

const inRect = (r: Rect, x: number, y: number) => x >= r.x && x <= r.x + r.w && y >= r.y && y <= r.y + r.h
const clamp = (v: number) => Math.max(-1, Math.min(1, v))

interface Sample { x: number; y: number; t: number }

export class PointerSense {
  private readonly r: FaceRegions
  private hist: Sample[] = []
  private inside = false
  private region: 'eyes' | 'mouth' | null = null
  private shakeStart = -1
  private lastShakeOk = -1
  private dizzyFired = false
  private annoyedFired = false
  private approachArmed = true
  private lingerFired = false
  private pos: { x: number; y: number } | null = null
  private _lastMoveAt = 0

  constructor(regions: FaceRegions = DEFAULT_REGIONS) { this.r = regions }

  get lastMoveAt(): number { return this._lastMoveAt }

  look(): { x: number; y: number } | null {
    if (!this.pos) return null
    return { x: clamp((this.pos.x - this.r.center[0]) / 0.5), y: clamp((this.pos.y - this.r.center[1]) / 0.35) }
  }

  move(x: number, y: number, t: number): PointerGesture[] {
    const out: PointerGesture[] = []
    const away = this._lastMoveAt > 0 && t - this._lastMoveAt > 60_000
    const prev = this.pos
    if (prev && Math.hypot(x - prev.x, y - prev.y) > 0.02) this.lingerFired = false
    this.pos = { x, y }
    this._lastMoveAt = t
    this.hist.push({ x, y, t })
    this.hist = this.hist.filter(s => t - s.t <= 1500)
    const nowInside = inRect(this.r.face, x, y)
    const region = this.r.eyes.some(e => inRect(e, x, y)) ? 'eyes' : inRect(this.r.mouth, x, y) ? 'mouth' : null
    const wasInside = this.inside
    const wasRegion = this.region
    this.inside = nowInside
    this.region = region
    if (away) { this.hist = [{ x, y, t }]; return ['return'] }

    if (nowInside && !wasInside) out.push('enter')
    if (region && region !== wasRegion) out.push(region)

    // shake
    const recent = this.hist.filter(s => t - s.t <= 1000)
    let len = 0
    let reversals = 0
    let lastSign = 0
    for (let i = 1; i < recent.length; i++) {
      const dx = recent[i].x - recent[i - 1].x
      len += Math.hypot(dx, recent[i].y - recent[i - 1].y)
      if (Math.abs(dx) > 0.01) {
        const s = Math.sign(dx)
        if (lastSign && s !== lastSign) reversals++
        lastSign = s
      }
    }
    const shaking = len >= 2 && reversals >= 3
    if (shaking) {
      this.lastShakeOk = t
      if (this.shakeStart < 0) { this.shakeStart = t; out.push('shake') }
      if (!this.dizzyFired && t - this.shakeStart >= 2000) { this.dizzyFired = true; out.push('dizzy') }
      if (!this.annoyedFired && t - this.shakeStart >= 4000) { this.annoyedFired = true; out.push('annoyed') }
    } else if (this.shakeStart >= 0 && t - this.lastShakeOk > 600) {
      this.shakeStart = -1; this.dizzyFired = false; this.annoyedFired = false
    }

    // circle
    if (this.shakeStart < 0) {
      const [cx, cy] = this.r.center
      let sum = 0
      for (let i = 1; i < this.hist.length; i++) {
        const a = this.hist[i - 1], b = this.hist[i]
        if (Math.hypot(a.x - cx, a.y - cy) < 0.08 || Math.hypot(b.x - cx, b.y - cy) < 0.08) continue
        let d = Math.atan2(b.y - cy, b.x - cx) - Math.atan2(a.y - cy, a.x - cx)
        if (d > Math.PI) d -= 2 * Math.PI
        if (d < -Math.PI) d += 2 * Math.PI
        sum += d
      }
      if (Math.abs(sum) >= 2 * Math.PI) { out.push('circle'); this.hist = [{ x, y, t }] }
    }

    // approach
    const [cx, cy] = this.r.center
    const dist = Math.hypot(x - cx, y - cy)
    if (dist > 0.5) this.approachArmed = true
    if (this.approachArmed && this.shakeStart < 0 && recent.length > 2) {
      const first = recent[0]
      const span = (t - first.t) / 1000
      const d0 = Math.hypot(first.x - cx, first.y - cy)
      const speed = span > 0 ? len / span : 0
      if (span >= 0.6 && d0 - dist > 0.1 && speed >= 0.05 && speed <= 0.4 && dist < 0.35) {
        this.approachArmed = false
        out.push('approach')
      }
    }
    return out
  }

  leave(_t: number): PointerGesture[] {
    this.pos = null
    this.lingerFired = false
    this.inside = false
    this.region = null
    this.hist = []
    return ['leave']
  }

  tick(t: number): PointerGesture[] {
    if (this.pos && this.inside && !this.lingerFired && t - this._lastMoveAt >= 3000) {
      this.lingerFired = true
      return ['linger']
    }
    return []
  }
}
