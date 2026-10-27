/**
 * DL-155 — Wingy's "scenes": cartoon hands that slide in from the sides of the
 * face box and do something (type on a laptop, cheer, clap, cover the eyes,
 * wave). Pure geometry: given a scene, its slide-in progress p (0..1, springy)
 * and the clock, handPoses() says where each hand is and how its fingers curl.
 * RobotHands.vue only draws what this returns.
 */
export type SceneId = 'typing' | 'cheer' | 'clap' | 'cover' | 'hello'

export interface SceneDef {
  /** 0..1 — how far the face lifts/shrinks to make room (the laptop sits below it). */
  lift: number
  laptop: boolean
}

export const SCENES = {
  typing: { lift: 1, laptop: true },
  cheer: { lift: 0, laptop: false },
  clap: { lift: 0, laptop: false },
  cover: { lift: 0, laptop: false },
  hello: { lift: 0, laptop: false },
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
    case 'hello': {
      const hidden: HandPose = { x: -100, y: 0, rot: 0, mirror: false, curl: OPEN, thumb: -40, visible: false }
      return [
        hidden,
        { x: lerp(260, 172, u), y: lerp(120, 66, u), rot: -70 + Math.sin(s * 10) * 18, mirror: true, curl: OPEN, thumb: -40, visible: true },
      ]
    }
  }
}
