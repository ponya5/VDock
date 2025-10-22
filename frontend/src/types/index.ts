// Type definitions for VDock

export type ActionType = 
  | 'url'
  | 'program'
  | 'command'
  | 'hotkey'
  | 'multi_action'
  | 'macro'
  | 'system_control'
  | 'system_metric'
  // Individual performance metrics
  | 'metric_memory'
  | 'metric_cpu_usage'
  | 'metric_cpu_temperature'
  | 'metric_cpu_frequency'
  | 'metric_cpu_power'
  | 'metric_internet_speed'
  | 'metric_harddisk'
  | 'metric_gpu_temperature'
  | 'metric_gpu_frequency'
  | 'metric_gpu_usage'
  | 'metric_gpu_memory_freq'
  | 'metric_gpu_memory_usage'
  // Individual time options
  | 'time_world_clock'
  | 'time_timer'
  | 'time_countdown'
  // Weather
  | 'weather'
  | 'cross_platform'
  | 'folder'
  | 'plugin'
  // Navigation
  | 'next_page'
  | 'previous_page'
  | 'home_page'
  // Screenshot
  | 'screenshot'
  // UI Control
  | 'ui_control'

export type ButtonShape = 'rectangle' | 'rounded' | 'circle' | 'hexagon' | 'diamond' | 'octagon'

export type ButtonEffect = 'none' | 'glass' | 'neumorphism' | 'gradient' | 'glow' | '3d'

export type ButtonAnimation = 'none' | 'pulse' | 'shimmer' | 'bounce' | 'rotate'

export interface MacroStep {
  type: 'hotkey' | 'delay' | 'text' | 'click'
  keys?: string[]
  text?: string
  delay?: number
  position?: { x: number; y: number }
}

export type PerformanceMetric = 
  | 'memory'
  | 'cpu_usage'
  | 'cpu_temperature'
  | 'cpu_frequency'
  | 'cpu_package_power'
  | 'internet_speed'
  | 'harddisk'
  | 'gpu_temperature'
  | 'gpu_core_frequency'
  | 'gpu_core_usage'
  | 'gpu_memory_frequency'
  | 'gpu_memory_usage'

export type TimeOptionType = 'world_time' | 'timer' | 'countdown'

export interface ButtonAction {
  type: ActionType
  config: Record<string, any>
  macro_steps?: MacroStep[]
  performance_metrics?: PerformanceMetric[]
  time_option?: TimeOptionType
  timer_duration?: number
  countdown_target?: string
  timezone?: string
  weather_location?: string
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
  triggeredByApp?: string // App executable name that triggers this scene
  autoCreated?: boolean // Whether this scene was auto-created by app integration
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

export interface RunningApp {
  name: string
  exe: string
  pid: number
  path?: string
}

export interface AppIntegration {
  appExe: string
  appName: string
  enabled: boolean
  sceneId?: string
  sceneName?: string
  autoCreateScene: boolean
}

export interface SystemMetricData {
  type: 'cpu' | 'memory' | 'disk' | 'network' | 'temperature' | 'battery' | 'processes'
  value?: number
  unit?: string
  status?: 'normal' | 'warning' | 'critical'
  details?: any
  timestamp?: string
}

export interface ServerConfig {
  host: string
  port: number
  require_auth: boolean
  allow_lan: boolean
  use_ssl: boolean
  enable_plugins: boolean
}

