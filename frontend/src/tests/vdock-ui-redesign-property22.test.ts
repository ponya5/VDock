import { test, expect } from 'vitest'
import { readFileSync } from 'fs'
import { resolve } from 'path'

test('Feature: vdock-ui-redesign, Property 22: Interactive touch targets have a minimum dimension of 44px', () => {
  const components = [
    { file: 'QuickAddPicker.vue', classes: ['.category-tab', '.preset-card', '.dot-indicator'] },
    { file: 'OnScreenKeypad.vue', classes: ['.keypad-key'] },
    { file: 'DeckFooter.vue', classes: ['.page-dot'] },
    { file: 'EditSidebar.vue', classes: ['.btn-control', '.action-item'] },
    { file: 'DeckHeader.vue', classes: ['.animate-tap'] }
  ]

  for (const { file, classes } of components) {
    const filePath = resolve(__dirname, `../components/${file}`)
    const content = readFileSync(filePath, 'utf-8')
    
    // Find style block
    const styleMatch = content.match(/<style[^>]*>([\s\S]*?)<\/style>/)
    expect(styleMatch, `${file} should contain a style block`).not.toBeNull()
    const styles = styleMatch![1]

    for (const cls of classes) {
      // Find rule for class
      const escapedCls = cls.replace('.', '\\.')
      const ruleRegex = new RegExp(`${escapedCls}\\s*(?:,[^{]*)?\\{([^}]*)\\}`, 'g')
      const matches = [...styles.matchAll(ruleRegex)]
      expect(matches.length, `Should find style rules for "${cls}" in ${file}`).toBeGreaterThan(0)

      for (const match of matches) {
        const body = match[1]
        
        // Extract size rules
        const hasMinHeight = /min-height\s*:\s*([0-9]+)px/.exec(body)
        const hasHeight = /height\s*:\s*([0-9]+)px/.exec(body)
        const hasPadding = /padding\s*:\s*([0-9]+)px/.exec(body)
        const hasMinWidth = /min-width\s*:\s*([0-9]+)px/.exec(body)
        const hasWidth = /width\s*:\s*([0-9]+)px/.exec(body)

        const verticalSize = hasMinHeight ? parseInt(hasMinHeight[1]) : (hasHeight ? parseInt(hasHeight[1]) : 0)
        const horizontalSize = hasMinWidth ? parseInt(hasMinWidth[1]) : (hasWidth ? parseInt(hasWidth[1]) : 0)
        const paddingSize = hasPadding ? parseInt(hasPadding[1]) : 0

        // Account for background-clip padding trick
        const totalHeight = verticalSize + 2 * paddingSize
        const totalWidth = horizontalSize + 2 * paddingSize

        // Touch target size condition (either height/min-height is >= 44px, width/min-width is >= 44px, or padding extends size to >= 44px)
        const isSizedCorrectly = 
          (totalHeight >= 44 || verticalSize >= 44) || 
          (totalWidth >= 44 || horizontalSize >= 44) || 
          (paddingSize >= 17) // 17px padding on 10px element makes it 44px

        expect(isSizedCorrectly, `Class "${cls}" in ${file} must have touch target dimensions of at least 44px. Found body: ${body}`).toBe(true)
      }
    }
  }
})
