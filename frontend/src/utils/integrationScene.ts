import type { Button, Scene } from '@/types'
import type { IntegrationScene } from '@/data/integrationGuides'

/** Id prefix that marks a scene as created from an integration guide. */
export const INTEGRATION_SCENE_PREFIX = 'integration-scene:'

/** Deterministic id so "already added" can be detected later. */
export function integrationSceneId(sceneKey: string): string {
  return `${INTEGRATION_SCENE_PREFIX}${sceneKey}`
}

/** A scene from an integration's starter layout (5 columns, as many rows as needed). */
export function buildIntegrationScene(def: IntegrationScene, now = Date.now()): Scene {
  const cols = 5
  const buttons: Button[] = def.buttons.map((b, index) => ({
    id: `button-${now}-${index}`,
    label: b.label,
    icon: b.icon,
    icon_type: 'fontawesome',
    action: b.action as Button['action'],
    shape: 'rounded',
    position: { row: Math.floor(index / cols), col: index % cols },
    size: { rows: 1, cols: 1 },
    style: { backgroundColor: b.style?.backgroundColor ?? def.color, textColor: b.style?.textColor ?? '#ffffff' },
    tooltip: b.tooltip ?? b.label,
    enabled: true,
  }))
  const rows = Math.max(3, Math.ceil(buttons.length / cols))
  return {
    id: integrationSceneId(def.sceneKey),
    name: def.name,
    icon: def.icon,
    color: def.color,
    pages: [{ id: `page-${now}`, name: 'Page 1', buttons, grid_config: { rows, cols } }],
    autoCreated: false,
  }
}
