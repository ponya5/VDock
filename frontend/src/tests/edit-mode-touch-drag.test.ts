// DL-055: touch reorder in edit mode. HTML5 drag never fires on touchscreens,
// so DeckGrid.startTouchDrag is the only way to move buttons on the panel —
// but it used to be unreachable once edit mode was active because DeckButton
// only emitted longPress when NOT editing, and slider faces stole the gesture.
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const button = readFileSync(
  resolve(__dirname, '../components/DeckButton.vue'),
  'utf-8'
)
const grid = readFileSync(
  resolve(__dirname, '../components/DeckGrid.vue'),
  'utf-8'
)
const slider = readFileSync(
  resolve(__dirname, '../components/SliderButtonFace.vue'),
  'utf-8'
)
const actions = readFileSync(
  resolve(__dirname, '../composables/useButtonActions.ts'),
  'utf-8'
)
const gestures = readFileSync(
  resolve(__dirname, '../composables/useGestures.ts'),
  'utf-8'
)

describe('edit-mode touch drag', () => {
  it('emits the grab gesture in edit mode, not only in view mode', () => {
    // The old `if (!props.isEditMode)` gate made startTouchDrag unreachable
    // while already editing — the emit must now be unconditional (emitGrab).
    const lp = button.slice(
      button.indexOf('useLongPress(buttonRef'),
      button.indexOf('useLongPress(buttonRef') + 300
    )
    expect(lp).toContain('onLongPress: emitGrab')
    expect(lp).not.toContain('!props.isEditMode')
    const grab = button.slice(
      button.indexOf('function emitGrab'),
      button.indexOf('function emitGrab') + 500
    )
    expect(grab).toContain("emit('longPress'")
  })

  it('grabs on press-and-move, not just hold-and-wait', () => {
    // Immediate drags must start the reorder — cancelling on early movement
    // reads as "touch doesn't work" on the panel.
    expect(button).toContain('handleEditModeMove')
    expect(button).toMatch(/pointermove.*handleEditModeMove/)
  })

  it('never treats overlay controls (delete/edit/copy) as drag handles', () => {
    expect(button).toContain('overlayControlSelector')
  })

  it('does not open the button editor when already in edit mode', () => {
    const fn = actions.slice(
      actions.indexOf('function handleDeckButtonLongPress'),
      actions.indexOf('function handleDeckButtonLongPress') + 600
    )
    expect(fn).toMatch(/isEditMode\) return/)
  })

  it('keeps the slider face inert in edit mode', () => {
    // Otherwise touching a slider to move it fires a real volume_set and
    // pointer capture steals the drag gesture.
    expect(slider).toMatch(/onPointerDown[\s\S]*isEditMode/)
  })

  it('still routes the grab into startTouchDrag', () => {
    expect(grid).toMatch(/handleButtonLongPress[\s\S]*startTouchDrag/)
  })

  it('does not count a drag landing on a button as a tap (double-tap guard)', () => {
    const dt = gestures.slice(gestures.indexOf('useDoubleTap'))
    expect(dt).toContain('pointerdown')
    expect(dt).toContain('threshold')
  })
})
