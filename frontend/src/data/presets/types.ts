// Preset registry types for VDock UI Redesign — Phase 2 (Preset registry)
// See design.md, section "1. Preset registry" and "2. Button layer model".
//
// NOTE on EffectType / IconLoop:
// These are defined here (rather than in `@/types`) because task 3.1 (Preset registry)
// lands before task 5.1 (Button layer model, which introduces `ButtonLayers`,
// `IconType`, `IconLoop`, and `BehaviourType` in `frontend/src/types/index.ts`).
// When task 5.1 adds `IconLoop` to `@/types`, these two type aliases should be
// consolidated into a single source of truth (most likely `@/types`, re-exported here)
// rather than duplicated. Keep this file's definitions in sync with design.md section
// 4.2 (effects) and 4.4 (icon loops) until that consolidation happens.

import type { ButtonAction, EffectType, IconLoop } from '@/types'

/**
 * Preset category. Every preset registered in the Preset_Registry must use one of
 * these values (Property 1: Preset categories are always valid).
 */
export type PresetCategory = 'recent' | 'ai' | 'dev' | 'media' | 'social' | 'news' | 'system'

/**
 * A single entry in the Preset_Registry. Data-driven replacement for the ~640-line
 * switch statement in `createPreconfiguredButton` (DashboardView.vue).
 *
 * See design.md, section "1. Preset registry".
 */
export interface ButtonPreset {
  id: string
  name: string
  category: PresetCategory
  brand: { primary: string; glow?: string; text?: string }
  icon: { type: 'logo' | 'fontawesome' | 'gif' | 'lottie'; value: string }
  effect?: EffectType // layer 2 — animation inside the button
  loop?: IconLoop // per-icon animation
  action: ButtonAction
  keywords?: string[] // "chatgpt" also matches "gpt", "openai"
}
