/**
 * DL-153 — tiny damped-spring integrator for the robot face. Every animated
 * face value is a Spring; retargeting keeps velocity, so expressions blend
 * mid-motion instead of snapping. Fixed 4 ms substeps make the result
 * independent of the display's frame rate; dt is clamped so a hidden tab
 * returning with a multi-second gap can't fling anything.
 */
export interface SpringConfig { stiffness: number; damping: number }

export const SPRINGS = {
  /** lids, blinks — fast, no overshoot */
  snappy: { stiffness: 700, damping: 55 },
  /** sizes, mouth — smooth with a hint of life */
  soft: { stiffness: 170, damping: 22 },
  /** eye look / head — slight lag + overshoot */
  look: { stiffness: 140, damping: 15 },
  /** props, accessories, glyph pops */
  bouncy: { stiffness: 320, damping: 12 },
  /** opacities */
  fade: { stiffness: 260, damping: 32 },
} as const satisfies Record<string, SpringConfig>

export interface Spring { value: number; velocity: number; target: number; config: SpringConfig }

export const MAX_DT_MS = 50
const SUBSTEP_MS = 4

export function createSpring(value: number, config: SpringConfig = SPRINGS.soft): Spring {
  return { value, velocity: 0, target: value, config }
}

export function stepSpring(s: Spring, dtMs: number): void {
  let remaining = Math.min(Math.max(dtMs, 0), MAX_DT_MS)
  const { stiffness, damping } = s.config
  while (remaining > 0) {
    const h = Math.min(SUBSTEP_MS, remaining) / 1000
    const accel = stiffness * (s.target - s.value) - damping * s.velocity
    s.velocity += accel * h
    s.value += s.velocity * h
    remaining -= SUBSTEP_MS
  }
}

export function isSettled(s: Spring, eps = 0.001): boolean {
  return Math.abs(s.target - s.value) < eps && Math.abs(s.velocity) < eps * 10
}
