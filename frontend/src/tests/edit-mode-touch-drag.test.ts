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

  // DL-110: a ghost must never outlive its drag — mice can't fire touchend,
  // and cancelled/backgrounded touches never emit it either.
  it('cleans up the ghost on cancel, pointer release, blur and unmount', () => {
    expect(grid).toContain("document.addEventListener('touchcancel'")
    expect(grid).toContain("document.addEventListener('pointercancel'")
    expect(grid).toContain("document.addEventListener('pointerup'")
    expect(grid).toContain("window.addEventListener('blur'")
    // cancel path must not execute a drop
    expect(grid).toMatch(/onTouchCancelDrag[\s\S]*?finishDrag\(false\)/)
    // unmount shares the same cleanup
    const unmount = grid.slice(grid.indexOf('onUnmounted'))
    expect(unmount).toContain('finishDrag(false)')
  })

  it('never starts the touch-ghost for a mouse pointer', () => {
    const handler = grid.slice(
      grid.indexOf('function handleButtonLongPress'),
      grid.indexOf('function handleButtonLongPress') + 700
    )
    expect(handler).toContain("pointerType === 'mouse'")
    expect(handler).toContain('isEditMode')
    // DeckButton must actually report the pointer type
    expect(button).toContain('downPointerType = event.pointerType')
    expect(button).toMatch(/emit\('longPress', props\.button, downPointerType/)
    expect(button).toMatch(/pointerType === 'mouse'/)
  })

  it('the sidebar action drag cancels on touchcancel too', () => {
    const drag = readFileSync(
      resolve(__dirname, '../composables/useTouchActionDrag.ts'),
      'utf-8'
    )
    expect(drag).toContain("document.addEventListener('touchcancel'")
    expect(drag).toContain("document.addEventListener('pointercancel'")
    expect(drag).toContain("window.addEventListener('blur'")
  })

  it('hides the header reveal FAB while editing (it overlapped Delete Page)', () => {
    const view = readFileSync(
      resolve(__dirname, '../views/DashboardView.vue'),
      'utf-8'
    )
    const fab = view.slice(
      view.indexOf('header-reveal-fab') - 300,
      view.indexOf('header-reveal-fab')
    )
    expect(fab).toContain('!isEditMode')
  })
})
