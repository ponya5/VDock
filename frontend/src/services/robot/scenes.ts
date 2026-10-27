/**
 * DL-155 — Wingy's "scenes": cartoon hands that slide in from the sides of the
 * face box and do something (type on a laptop, cheer, clap, cover the eyes,
 * wave). Pure geometry: given a scene, its slide-in progress p (0..1, springy)
 * and the clock, handPoses() says where each hand is and how its fingers curl.
 * RobotHands.vue only draws what this returns.
 */
export type SceneId =
  | 'typing' | 'cheer' | 'clap' | 'cover' | 'hello'
  | 'inspect' | 'call' | 'notes' | 'relax' | 'sneakers' | 'chin'

export interface SceneDef {
  /** 0..1 — how far the face lifts/shrinks to make room (the laptop sits below it). */
  lift: number
  laptop: boolean
  /** Drawn by RobotScenery (outline storyboard style) instead of the glove hands. */
  toon?: boolean
  /** Where the face goes while the scene is up (viewBox units / scale delta). */
  fx?: number
  fy?: number
  fs?: number
  hideFace?: boolean
}

export const SCENES = {
  typing: { lift: 0, laptop: true, toon: true, fx: 24, fy: -4, fs: -0.18 },
  cheer: { lift: 0, laptop: false, toon: true, fy: -6 },
  clap: { lift: 0, laptop: false },
  cover: { lift: 0, laptop: false },
  hello: { lift: 0, laptop: false, toon: true, fx: 20, fs: -0.1 },
  inspect: { lift: 0, laptop: false, toon: true, fx: -24, fy: -6 },
  call: { lift: 0, laptop: false, toon: true, fy: -14, fs: -0.12 },
  notes: { lift: 0, laptop: false, toon: true, fx: 8, fy: -22, fs: -0.12 },
  relax: { lift: 0, laptop: false, toon: true, fx: -14 },
  sneakers: { lift: 0, laptop: false, toon: true, hideFace: true },
  chin: { lift: 0, laptop: false, toon: true, fx: 18, fs: -0.1 },
} as const satisfies Record<SceneId, SceneDef>
export const SCENE_IDS = Object.keys(SCENES) as SceneId[]

export interface HandPose {
  x: number
  y: number
  /** Degrees; fingers point along +x before rotation. */
  rot: number
  /** Mirrored right hand (arm enters from the right edge). */
  mirror: boolean
  /** Curl in degrees for index, middle, ring, pinky. */
  curl: [number, number, number, number]
  /** Thumb angle in degrees (negative = up). */
  thumb: number
  visible: boolean
}

const lerp = (a: number, b: number, u: number) => a + (b - a) * u
const OPEN: [number, number, number, number] = [4, 2, 4, 8]
const clamp01 = (v: number) => Math.min(1.15, Math.max(0, v))

/** Left hand first, then right. `p` may overshoot past 1 for the springy landing. */
export function handPoses(scene: SceneId, p: number, tMs: number): [HandPose, HandPose] {
  const u = clamp01(p)
  const s = tMs / 1000
  switch (scene) {
    case 'typing': {
      const tap = (phase: number) => 12 + 26 * Math.max(0, Math.sin(s * 13 + phase))
      const L: HandPose = {
        x: lerp(-70, 66, u), y: lerp(190, 138, u) + Math.sin(s * 13) * 0.8, rot: 38, mirror: false,
        curl: [tap(0), tap(1.7), tap(3.1), tap(4.4)], thumb: -28, visible: true,
      }
      const R: HandPose = {
        x: lerp(270, 134, u), y: lerp(190, 138, u) + Math.sin(s * 13 + 2) * 0.8, rot: 38, mirror: true,
        curl: [tap(2.3), tap(0.8), tap(3.9), tap(5.2)], thumb: -28, visible: true,
      }
      return [L, R]
    }
    case 'cheer': {
      const wave = Math.sin(s * 9) * 14
      return [
        { x: lerp(-60, 28, u), y: lerp(150, 34, u), rot: -62 + wave, mirror: false, curl: OPEN, thumb: -40, visible: true },
        { x: lerp(260, 172, u), y: lerp(150, 34, u), rot: -62 - wave, mirror: true, curl: OPEN, thumb: -40, visible: true },
      ]
    }
    case 'clap': {
      const gap = 6 + 16 * Math.abs(Math.sin(s * 8))
      return [
        { x: lerp(-60, 100 - gap - 14, u), y: lerp(150, 128, u), rot: -86, mirror: false, curl: OPEN, thumb: -30, visible: true },
        { x: lerp(260, 100 + gap + 14, u), y: lerp(150, 128, u), rot: -86, mirror: true, curl: OPEN, thumb: -30, visible: true },
      ]
    }
    case 'cover': {
      const peek = 0.5 + 0.5 * Math.sin(s * 2.4)
      return [
        { x: lerp(-50, 64, u), y: lerp(100, 76 - peek * 4, u), rot: -90, mirror: false, curl: [10, 8, 10, 14], thumb: -20, visible: true },
        { x: lerp(250, 136, u), y: lerp(100, 76 - peek * 4, u), rot: -90, mirror: true, curl: [10, 8, 10, 14], thumb: -20, visible: true },
      ]
    }
    case 'inspect': case 'call': case 'notes': case 'relax': case 'sneakers': case 'chin': {
      const none: HandPose = { x: -100, y: 0, rot: 0, mirror: false, curl: OPEN, thumb: -40, visible: false }
      return [none, none]
    }
    case 'hello': {
      const hidden: HandPose = { x: -100, y: 0, rot: 0, mirror: false, curl: OPEN, thumb: -40, visible: false }
      return [
        hidden,
        { x: lerp(260, 172, u), y: lerp(120, 66, u), rot: -70 + Math.sin(s * 10) * 18, mirror: true, curl: OPEN, thumb: -40, visible: true },
      ]
    }
  }
}
