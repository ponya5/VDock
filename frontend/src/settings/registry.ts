// DL-146: the single source for Settings navigation - sections, pages, panel
// anchors, search entries and legacy deep-link ids. SettingsView, the search box
// and the deep-link resolver all read from here; panels never know where they live.

export type SectionId = 'overview' | 'appearance' | 'agents' | 'integrations' | 'devices' | 'system'
type Icon = [string, string]

export interface SettingsPage {
  id: string
  name: string
  /** Topbar heading and blurb. */
  title: string
  blurb: string
  /** Panel component names the view mounts for this page, in order. */
  panels: string[]
  /** `id`s inside the panels that search and `?anchor=` can scroll to. */
  anchors: string[]
  /** `data-tour` value kept on the sub-tab for the tutorial. */
  tour?: string
  /** Every control saves on change (or through its own API), so the topbar Apply is redundant. */
  autosaves?: true
}

export interface SettingsSection {
  id: SectionId
  name: string
  icon: Icon
  /** `data-tour` value kept on the sidebar item for the tutorial. */
  tour?: string
  pages: SettingsPage[]
}

export interface SearchEntry {
  label: string
  keywords: string
  /** `guide` opens the standalone guide window instead of a settings page. */
  section: SectionId | 'guide'
  page?: string
  anchor?: string
  icon: Icon
}

export interface SettingsRoute {
  section: SectionId
  page: string
  anchor?: string
}

export const SECTIONS: SettingsSection[] = [
  // Pages arrive with the Overview panel; until then the section has none and is not listed.
  { id: 'overview', name: 'Overview', icon: ['fas', 'gauge-high'], pages: [] },
  {
    id: 'appearance', name: 'Appearance', icon: ['fas', 'palette'], tour: 'nav-appearance',
    pages: [
      { id: 'buttons', name: 'Buttons', title: 'Buttons', blurb: 'Sizing, motion and press feedback for every deck key.', panels: ['AppearanceButtons'], anchors: ['sizing', 'touch', 'design', 'motion', 'feedback'] },
      { id: 'layout', name: 'Layout & sidebar', title: 'Layout & sidebar', blurb: 'The docked sidebar and dashboard font.', panels: ['AppearanceLayout'], anchors: ['typography', 'sidebar'] },
      { id: 'background', name: 'Background', title: 'Background', blurb: 'Dashboard wallpaper and per-scene overrides.', panels: ['AppearanceBackground'], anchors: ['dashboard-bg', 'scene-bg'] },
      { id: 'screensaver', name: 'Screen saver', title: 'Screen saver', blurb: 'Idle screen widgets, timing and its own backdrop.', panels: ['ScreensaverPanel'], anchors: ['ss-general', 'ss-spectrum', 'ss-background', 'ss-widgets'], tour: 'subtab-screensaver' },
    ],
  },
  {
    id: 'agents', name: 'Agents & automation', icon: ['fas', 'robot'], tour: 'nav-integration',
    pages: [
      { id: 'scenes', name: 'Scene switching', title: 'Scene switching', blurb: 'Scenes that follow the app in focus.', panels: ['SceneSwitchingPanel'], anchors: ['auto-switch', 'running-apps'] },
      { id: 'alerts', name: 'Agent alerts', title: 'Agent alerts', blurb: 'Banner, glow, deck chips and toasts when something needs you.', panels: ['AgentAlertsPanel', 'NotificationsPanel'], anchors: ['agent-alerts', 'notifications'] },
      { id: 'triggers', name: 'Triggers', title: 'Triggers', blurb: 'Automatic rules: when something happens (a time, an app opens, an AI agent needs you, a script calls in), VDock switches scene, shows a notification or runs an action.', panels: ['TriggersPanel'], anchors: [], autosaves: true },
      { id: 'mcp', name: 'MCP server', title: 'MCP server', blurb: 'Let local agents act on the deck.', panels: ['McpPanel'], anchors: ['mcp-server'], autosaves: true },
    ],
  },
  {
    id: 'integrations', name: 'Integrations', icon: ['fas', 'plug'], tour: 'nav-templates',
    pages: [
      { id: 'templates', name: 'App templates', title: 'App templates', blurb: 'Drop-in scenes for popular apps.', panels: ['TemplatesPanel'], anchors: [], autosaves: true },
    ],
  },
  {
    id: 'devices', name: 'Devices & network', icon: ['fas', 'mobile-screen-button'], tour: 'nav-server',
    pages: [
      { id: 'connect', name: 'Connect a device', title: 'Connect a device', blurb: 'Turn a phone or tablet into a second deck.', panels: ['ConnectPanel'], anchors: [], tour: 'nav-connect', autosaves: true },
      { id: 'security', name: 'Security', title: 'Security', blurb: 'Require a deck password on every device.', panels: ['SecurityPanel'], anchors: ['security'], autosaves: true },
      { id: 'ports', name: 'Ports & host', title: 'Ports & host', blurb: 'Ports and the interface the server binds to.', panels: ['PortsPanel'], anchors: ['connection'], autosaves: true },
    ],
  },
  {
    id: 'system', name: 'System', icon: ['fas', 'screwdriver-wrench'], tour: 'nav-logs',
    pages: [
      { id: 'logs', name: 'Logs', title: 'Session logs', blurb: 'Backend and frontend logs for troubleshooting.', panels: ['LogsPanel'], anchors: [], autosaves: true },
      { id: 'startup', name: 'Startup', title: 'Startup', blurb: 'Launcher behaviour, settings navigation and recent actions.', panels: ['StartupPanel', 'RecentActionsPanel'], anchors: ['startup', 'recent-actions'] },
      { id: 'about', name: 'About', title: 'About VDock', blurb: 'Version, help and project links.', panels: ['AboutPanel'], anchors: ['features', 'build'], tour: 'nav-about', autosaves: true },
    ],
  },
]

/** Anchors that exist on a page but deliberately have no search entry. */
export const NOT_SEARCHABLE: string[] = ['features', 'build']

export const SEARCH: SearchEntry[] = [
  { label: 'Auto Scene Switching', keywords: 'auto scene switching monitored applications follow app focus', section: 'agents', page: 'scenes', anchor: 'auto-switch', icon: ['fas', 'shuffle'] },
  { label: 'Running Applications', keywords: 'running apps processes filter search dev tools', section: 'agents', page: 'scenes', anchor: 'running-apps', icon: ['fas', 'desktop'] },
  { label: 'Agent Attention Alerts', keywords: 'agent alerts waiting glow banner chips dock notification permission idle', section: 'agents', page: 'alerts', anchor: 'agent-alerts', icon: ['fas', 'user-clock'] },
  { label: 'Agent Hooks', keywords: 'agent hooks install claude codex cursor status', section: 'agents', page: 'alerts', anchor: 'agent-alerts', icon: ['fas', 'plug-circle-check'] },
  { label: 'Notifications', keywords: 'notifications toast toasts popups alerts errors', section: 'agents', page: 'alerts', anchor: 'notifications', icon: ['fas', 'bell'] },
  { label: 'Triggers & Schedules', keywords: 'triggers schedules automation time app foreground agent webhook scene switch pause resume', section: 'agents', page: 'triggers', icon: ['fas', 'bolt'] },
  { label: 'MCP Server', keywords: 'mcp server agents model context protocol tools press button enable disable', section: 'agents', page: 'mcp', anchor: 'mcp-server', icon: ['fas', 'robot'] },
  { label: 'Connect a device', keywords: 'connect device phone tablet qr lan wifi pair second deck allow lan deck address', section: 'devices', page: 'connect', icon: ['fas', 'mobile-screen-button'] },
  { label: 'Deck Password', keywords: 'password authentication auth login lock secure require unlock', section: 'devices', page: 'security', anchor: 'security', icon: ['fas', 'lock'] },
  { label: 'Ports & Host', keywords: 'server host port connection frontend backend address bind', section: 'devices', page: 'ports', anchor: 'connection', icon: ['fas', 'server'] },
  { label: 'Touch Mode', keywords: 'touch mode finger tablet target size', section: 'appearance', page: 'buttons', anchor: 'touch', icon: ['fas', 'hand-pointer'] },
  { label: 'Button Size & Transparency', keywords: 'button size labels tooltips transparency display', section: 'appearance', page: 'buttons', anchor: 'sizing', icon: ['fas', 'table-cells-large'] },
  { label: 'Button Behaviour', keywords: 'button animation icon loop effect style apply all key design', section: 'appearance', page: 'buttons', anchor: 'design', icon: ['fas', 'sliders'] },
  { label: 'Motion & Animation', keywords: 'motion animation press idle icon tilt wiggle', section: 'appearance', page: 'buttons', anchor: 'motion', icon: ['fas', 'wand-magic-sparkles'] },
  { label: 'Press Sound', keywords: 'sound audio click feedback labels tooltips', section: 'appearance', page: 'buttons', anchor: 'feedback', icon: ['fas', 'volume-high'] },
  { label: 'Typography', keywords: 'font typography typeface text dashboard', section: 'appearance', page: 'layout', anchor: 'typography', icon: ['fas', 'font'] },
  { label: 'Docked Sidebar', keywords: 'sidebar docked width column', section: 'appearance', page: 'layout', anchor: 'sidebar', icon: ['fas', 'table-columns'] },
  { label: 'Background', keywords: 'background animation particles waves aurora image wallpaper gradient scene override', section: 'appearance', page: 'background', anchor: 'dashboard-bg', icon: ['fas', 'image'] },
  { label: 'Per-scene Background', keywords: 'scene background override wallpaper per scene', section: 'appearance', page: 'background', anchor: 'scene-bg', icon: ['fas', 'images'] },
  { label: 'Screensaver Delay', keywords: 'screensaver idle timeout sleep', section: 'appearance', page: 'screensaver', anchor: 'ss-general', icon: ['fas', 'moon'] },
  { label: 'Screensaver Background', keywords: 'screensaver backdrop background image idle', section: 'appearance', page: 'screensaver', anchor: 'ss-background', icon: ['fas', 'image'] },
  { label: 'Screensaver Widgets', keywords: 'screensaver widgets weather news stocks crypto world clock now playing system stats', section: 'appearance', page: 'screensaver', anchor: 'ss-widgets', icon: ['fas', 'grip'] },
  { label: 'Spectrum Screensaver', keywords: 'spectrum visualizer audio skin winamp aurora ember scope shuffle media controls fullscreen', section: 'appearance', page: 'screensaver', anchor: 'ss-spectrum', icon: ['fas', 'wave-square'] },
  { label: 'Weather Widget Size', keywords: 'screensaver weather size scale small screen touch', section: 'appearance', page: 'screensaver', anchor: 'ss-widgets', icon: ['fas', 'cloud-sun'] },
  { label: 'Weather Widget Location', keywords: 'weather location city temperature geolocation', section: 'appearance', page: 'screensaver', anchor: 'ss-widgets', icon: ['fas', 'cloud-sun'] },
  { label: 'App Templates', keywords: 'templates presets apps buttons app paths executable', section: 'integrations', page: 'templates', icon: ['fas', 'layer-group'] },
  { label: 'Session Logs', keywords: 'logs errors troubleshoot debug export download', section: 'system', page: 'logs', icon: ['fas', 'file-lines'] },
  { label: 'Startup', keywords: 'launcher terminal close debug startup', section: 'system', page: 'startup', anchor: 'startup', icon: ['fas', 'power-off'] },
  { label: 'Open Settings in New Tab', keywords: 'settings browser tab window navigation external', section: 'system', page: 'startup', anchor: 'startup', icon: ['fas', 'up-right-from-square'] },
  { label: 'Recent Actions', keywords: 'recent actions history picker clear', section: 'system', page: 'startup', anchor: 'recent-actions', icon: ['fas', 'clock-rotate-left'] },
  { label: 'About VDock', keywords: 'version about info build tutorial', section: 'system', page: 'about', icon: ['fas', 'circle-info'] },
  { label: 'User Guide', keywords: 'help guide tutorial how to documentation swipe gestures troubleshooting', section: 'guide', icon: ['fas', 'circle-question'] },
]

/** Pre-registry `?tab=` ids and the page each opened. */
export const LEGACY_TABS: Record<string, { section: SectionId; page?: string }> = {
  appearance: { section: 'appearance' },
  templates: { section: 'integrations', page: 'templates' },
  server: { section: 'devices', page: 'ports' },
  integration: { section: 'agents' },
  connect: { section: 'devices', page: 'connect' },
  logs: { section: 'system', page: 'logs' },
  about: { section: 'system', page: 'about' },
}

/** Pre-registry `?sub=` ids that changed name; the rest (`buttons`, `alerts`, ...) kept theirs. */
export const LEGACY_SUBS: Record<string, string> = { apps: 'scenes' }

/** Sections that have pages - the ones the sidebar lists. */
export const NAV_SECTIONS: SettingsSection[] = SECTIONS.filter((s) => s.pages.length > 0)

/** Where Settings opens when nothing says otherwise: Overview once it has pages. */
export const LANDING: SectionId = NAV_SECTIONS[0].id

export function findSection(id: string | undefined): SettingsSection | undefined {
  return NAV_SECTIONS.find((s) => s.id === id)
}

export function findPage(section: SettingsSection, id: string | undefined): SettingsPage | undefined {
  return section.pages.find((p) => p.id === id)
}

function str(value: unknown): string | undefined {
  return typeof value === 'string' ? value : undefined
}

function locateAnchor(anchor: string): SettingsRoute | undefined {
  for (const section of NAV_SECTIONS) {
    const page = section.pages.find((p) => p.anchors.includes(anchor))
    if (page) return { section: section.id, page: page.id, anchor }
  }
  return undefined
}

/**
 * Resolves a settings URL query into a concrete section + page. Understands the
 * current `?section=&page=&anchor=` form and the legacy `?tab=&sub=` form; anything
 * unknown lands on the first section.
 */
export function resolveRoute(query: Record<string, unknown>): SettingsRoute {
  const anchor = str(query.anchor)
  const legacy = LEGACY_TABS[str(query.tab) ?? '']
  const section = findSection(str(query.section) ?? legacy?.section)
  if (!section) {
    return (anchor && locateAnchor(anchor)) || fallbackRoute(findSection(LANDING)!)
  }
  const sub = str(query.sub)
  const wanted = str(query.page) ?? (sub && (LEGACY_SUBS[sub] ?? sub)) ?? legacy?.page
  const page = findPage(section, wanted) ?? section.pages[0]
  const owns = anchor && page.anchors.includes(anchor)
  return { section: section.id, page: page.id, ...(owns ? { anchor } : {}) }
}

function fallbackRoute(section: SettingsSection): SettingsRoute {
  return { section: section.id, page: section.pages[0].id }
}

/** Case-insensitive search over label and keywords; label hits rank first. */
export function searchSettings(q: string): SearchEntry[] {
  const needle = q.trim().toLowerCase()
  if (!needle) return []
  const labelHits = SEARCH.filter((e) => e.label.toLowerCase().includes(needle))
  const keywordHits = SEARCH.filter((e) => !labelHits.includes(e) && e.keywords.toLowerCase().includes(needle))
  return [...labelHits, ...keywordHits]
}
