// DL-026: deck-style key designs (deckkey/statuskey/fullart/folder), the
// ButtonDesignPicker swatch grid, and Button Size resizing the actual button
// box — not just icon/label — via width/height% + place-self on the grid item.
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const types = readFileSync(resolve(__dirname, '../types/index.ts'), 'utf-8')
const deckButton = readFileSync(resolve(__dirname, '../components/DeckButton.vue'), 'utf-8')
const mainCss = readFileSync(resolve(__dirname, '../assets/styles/main.css'), 'utf-8')
const picker = readFileSync(resolve(__dirname, '../components/ButtonDesignPicker.vue'), 'utf-8')
const editor = readFileSync(resolve(__dirname, '../components/ButtonEditor.vue'), 'utf-8')
const settingsView = readFileSync(resolve(__dirname, '../views/SettingsView.vue'), 'utf-8')
const buttonActions = readFileSync(resolve(__dirname, '../composables/useButtonActions.ts'), 'utf-8')

describe('deck-key design effects', () => {
  it('registers the four new effect types', () => {
    for (const fx of ["'deckkey'", "'statuskey'", "'fullart'", "'folder'"]) {
      expect(types).toContain(fx)
    }
  })

  it('maps each effect to a deck-button class', () => {
    for (const fx of ['deckkey', 'statuskey', 'fullart', 'folder']) {
      expect(deckButton).toContain(`'deck-button-${fx}'`)
      expect(mainCss).toContain(`.deck-button-${fx}`)
    }
  })

  it('lets the CSS classes own the card surface (rich-card branch)', () => {
    // The rich-style branch must list all four so inline defaults don't fight
    // the class-based gradients/shadows.
    expect(deckButton).toMatch(/vis\.effect\.type === 'deckkey'/)
    expect(deckButton).toMatch(/vis\.effect\.type === 'statuskey'/)
    expect(deckButton).toMatch(/vis\.effect\.type === 'fullart'/)
    expect(deckButton).toMatch(/vis\.effect\.type === 'folder'/)
  })

  it('peeks at the target page for goto_page folder buttons', () => {
    expect(deckButton).toContain("action?.type !== 'goto_page'")
    expect(deckButton).toContain('folderTargetPage')
    expect(deckButton).toContain('folderCells')
    expect(deckButton).toContain('folderBadgeCount')
    expect(deckButton).toContain('folder-badge')
  })
})

describe('button size resizes the button box', () => {
  it('scales the grid item itself via width/height% + place-self', () => {
    expect(deckButton).toContain('boxScale')
    expect(deckButton).toContain('baseStyle.width')
    expect(deckButton).toContain('baseStyle.height')
    expect(deckButton).toContain("placeSelf = 'center'")
  })

  it('tracks the raw slider, not the touch-mode-multiplied prop', () => {
    // ×2 touch mode must not permanently overflow every button into its
    // neighbours — the box follows settingsStore.buttonSize alone.
    expect(deckButton).toContain('settingsStore.buttonSize')
  })

  it('caps growth so buttons stay inside the grid gap', () => {
    expect(deckButton).toMatch(/Math\.min\(sizeScale, 1\.1\)/)
  })
})

describe('button design picker', () => {
  it('offers all ten card designs as swatches', () => {
    const found = ['none', 'glass', 'glowglass', 'gem', 'neonrim', 'watermark', 'deckkey', 'statuskey', 'fullart', 'folder']
      .filter(v => picker.includes(`value: '${v}'`))
    expect(found).toHaveLength(10)
  })

  it('keeps animated/overlay effects in a secondary select', () => {
    expect(picker).toContain('overlay-select')
    expect(picker).toContain("'fire'")
    expect(picker).toContain("'aurora'")
  })

  it('is wired into the Button Editor and the global Settings preview', () => {
    expect(editor).toContain('<ButtonDesignPicker v-model="buttonDesign"')
    expect(editor).toContain("import ButtonDesignPicker from './ButtonDesignPicker.vue'")
    expect(settingsView).toContain('<ButtonDesignPicker v-model="previewEffect"')
  })

  it('writes layers.effect so the choice cannot be shadowed by style.effect', () => {
    expect(editor).toContain('editedButton.value.layers = {')
    expect(editor).toContain('delete editedButton.value.style.effect')
  })

  it('applies the chosen default design to newly created buttons', () => {
    expect(buttonActions).toContain('resolveDefaultEffect')
    expect(buttonActions).toContain('buttonDefaultEffect')
  })
})
