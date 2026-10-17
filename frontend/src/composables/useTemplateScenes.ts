import type { Button, Scene } from '@/types'
import type { AppTemplate } from '@/data/appTemplates'
import { useDashboardStore } from '@/stores/dashboard'

/** Adds a template as a new scene on the loaded profile; null when no profile is loaded. */
export function addTemplateScene(template: AppTemplate): Scene | null {
  const dashboard = useDashboardStore()
  if (!dashboard.currentProfile) return null
  const buttons: Button[] = template.buttons.map((b, index) => ({
    id: `button-${Date.now()}-${index}`,
    label: b.label, icon: b.icon, icon_type: 'fontawesome', action: b.action as Button['action'], shape: 'rounded',
    position: { row: Math.floor(index / 5), col: index % 5 }, size: { rows: 1, cols: 1 },
    style: { backgroundColor: b.style?.backgroundColor ?? template.color, textColor: b.style?.textColor ?? '#ffffff' },
    tooltip: b.tooltip ?? b.label, enabled: true
  }))
  const scene: Scene = {
    id: `scene-${Date.now()}-${template.id}`, name: template.name, icon: template.icon[1] ?? 'layer-group',
    color: template.color, pages: [{ id: `page-${Date.now()}-${template.id}`, name: 'Page 1', buttons, grid_config: { rows: 4, cols: 5 } }],
    appId: template.id, autoCreated: false
  }
  dashboard.addScene(scene)
  return scene
}
