// Type definitions for VDock

export type ActionType = 
  | 'url'
  | 'program'
  | 'command'
  | 'hotkey'
  | 'multi_action'
  | 'system_control'
  | 'cross_platform'
  | 'folder'
  | 'plugin'

export type ButtonShape = 'rectangle' | 'rounded' | 'circle' | 'hexagon' | 'diamond' | 'octagon'

export type ButtonEffect = 'none' | 'glass' | 'neumorphism' | 'gradient' | 'glow' | '3d'

export type ButtonAnimation = 'none' | 'pulse' | 'shimmer' | 'bounce' | 'rotate'

export interface ButtonAction {
  type: ActionType
  config: Record<string, any>
}

export interface ButtonPosition {
  row: number
  col: number
}

export interface ButtonSize {
  rows: number
  cols: number
}

export interface ButtonStyle {
  backgroundColor?: string
  borderColor?: string
  borderWidth?: number
  textColor?: string
  fontSize?: number
  iconSize?: number
  opacity?: number
  enhanced?: boolean
  effect?: ButtonEffect
  animation?: ButtonAnimation
  gradient?: string
  glowColor?: string
  shadowIntensity?: number
  [key: string]: any
}

export interface Button {
  id: string
  label: string
  secondary_label?: string
  icon?: string | string[]
  icon_type?: 'fontawesome' | 'material' | 'custom'
  media_url?: string // For video/gif files
  media_type?: 'video' | 'gif' | 'image'
  action?: ButtonAction
  shape: ButtonShape
  position: ButtonPosition
  size: ButtonSize
  style?: ButtonStyle
  tooltip?: string
  enabled: boolean
}

export interface GridConfig {
  rows: number
  cols: number
}

export interface Background {
  type: 'solid' | 'gradient' | 'image'
  color?: string
  gradient?: {
    from: string
    to: string
    direction?: string
  }
  image?: string
}

export interface Page {
  id: string
  name: string
  buttons: Button[]
  grid_config: GridConfig
  background?: Background
}

export interface Scene {
  id: string
  name: string
  icon?: string
  color?: string
  pages: Page[]
  isActive?: boolean
  buttonSize?: number // Size multiplier for scene buttons
  created_at?: string
  updated_at?: string
}

export interface Profile {
  id: string
  name: string
  description: string
  icon?: string
  avatar?: string // URL or path to avatar image/gif
  scenes: Scene[]
  dockedButtons?: Button[] // Buttons that persist across all scenes
  theme: string
  settings?: ProfileSettings
  created_at?: string
  updated_at?: string
}

export interface ProfileSettings {
  defaultGridRows?: number
  defaultGridCols?: number
  buttonSize?: number
  showLabels?: boolean
  showTooltips?: boolean
  animationsEnabled?: boolean
}

export interface Theme {
  id: string
  name: string
  colors: Record<string, string>
}

export interface PluginInfo {
  id: string
  name: string
  version: string
  author: string
  description: string
  actions: string[]
}

export interface ActionResult {
  success: boolean
  message: string
  data?: Record<string, any>
}

export interface ServerConfig {
  host: string
  port: number
  require_auth: boolean
  allow_lan: boolean
  use_ssl: boolean
  enable_plugins: boolean
}

