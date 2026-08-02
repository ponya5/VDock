import { ref } from 'vue'

interface TouchDragPayload {
  type: 'action' | 'button'
  data: unknown
}

const activeTouchDrag = ref<TouchDragPayload | null>(null)
let dragGhostElement: HTMLElement | null = null
let longPressTimer: ReturnType<typeof setTimeout> | null = null
let touchMoveHandler: ((event: TouchEvent) => void) | null = null
let touchEndHandler: ((event: TouchEvent) => void) | null = null

function clearLongPressTimer() {
  if (longPressTimer) {
    clearTimeout(longPressTimer)
    longPressTimer = null
  }
}

function removeTouchDragListeners() {
  if (touchMoveHandler) {
    document.removeEventListener('touchmove', touchMoveHandler)
    touchMoveHandler = null
  }
  if (touchEndHandler) {
    document.removeEventListener('touchend', touchEndHandler)
    touchEndHandler = null
  }
}

function cleanupTouchDragGhost() {
  if (dragGhostElement) {
    dragGhostElement.remove()
    dragGhostElement = null
  }
}

export function useTouchActionDrag() {
  function isTouchDragActive(): boolean {
    return activeTouchDrag.value !== null
  }

  function cancelTouchDrag() {
    clearLongPressTimer()
    removeTouchDragListeners()
    cleanupTouchDragGhost()
    activeTouchDrag.value = null
  }

  function beginTouchDragFromElement(
    sourceElement: HTMLElement,
    payload: TouchDragPayload,
    touch: Touch
  ) {
    cancelTouchDrag()
    activeTouchDrag.value = payload

    const sourceRect = sourceElement.getBoundingClientRect()
    dragGhostElement = sourceElement.cloneNode(true) as HTMLElement
    dragGhostElement.style.cssText = `
      position: fixed;
      left: ${touch.clientX - sourceRect.width / 2}px;
      top: ${touch.clientY - sourceRect.height / 2}px;
      width: ${sourceRect.width}px;
      height: ${sourceRect.height}px;
      opacity: 0.8;
      pointer-events: none;
      z-index: 10000;
      border-radius: inherit;
    `
    document.body.appendChild(dragGhostElement)

    touchMoveHandler = (event: TouchEvent) => {
      event.preventDefault()
      if (!dragGhostElement || event.touches.length === 0) return

      const activeTouch = event.touches[0]
      dragGhostElement.style.left = `${activeTouch.clientX - sourceRect.width / 2}px`
      dragGhostElement.style.top = `${activeTouch.clientY - sourceRect.height / 2}px`

      dragGhostElement.style.display = 'none'
      const elementUnderTouch = document.elementFromPoint(activeTouch.clientX, activeTouch.clientY)
      dragGhostElement.style.display = ''

      document.querySelectorAll('.drop-target-active, .is-highlighted').forEach((element) => {
        element.classList.remove('drop-target-active', 'is-highlighted')
      })

      const placeholderElement = elementUnderTouch?.closest('.button-placeholder') as HTMLElement | null
      if (placeholderElement) {
        placeholderElement.classList.add('drop-target-active', 'is-highlighted')
      }
    }

    touchEndHandler = (event: TouchEvent) => {
      const endedTouch = event.changedTouches[0]
      if (!endedTouch || !activeTouchDrag.value) {
        cancelTouchDrag()
        return
      }

      if (dragGhostElement) {
        dragGhostElement.style.display = 'none'
      }

      const dropElement = document.elementFromPoint(endedTouch.clientX, endedTouch.clientY)
      const payloadSnapshot = activeTouchDrag.value

      document.dispatchEvent(
        new CustomEvent('vdock-touch-drop', {
          detail: {
            payload: payloadSnapshot,
            dropElement,
            clientX: endedTouch.clientX,
            clientY: endedTouch.clientY
          }
        })
      )

      cancelTouchDrag()
    }

    document.addEventListener('touchmove', touchMoveHandler, { passive: false })
    document.addEventListener('touchend', touchEndHandler, { passive: true })
  }

  function bindTouchDragSource(
    sourceElement: HTMLElement,
    payload: TouchDragPayload,
    longPressDurationMs = 400
  ) {
    let touchStartedOnSource = false

    const handleTouchStart = (event: TouchEvent) => {
      if (event.touches.length !== 1) return
      touchStartedOnSource = true
      const touch = event.touches[0]

      clearLongPressTimer()
      longPressTimer = setTimeout(() => {
        if (!touchStartedOnSource) return
        beginTouchDragFromElement(sourceElement, payload, touch)
      }, longPressDurationMs)
    }

    const handleTouchEnd = () => {
      touchStartedOnSource = false
      if (!isTouchDragActive()) {
        clearLongPressTimer()
      }
    }

    const handleTouchMove = (event: TouchEvent) => {
      if (!longPressTimer || event.touches.length === 0) return

      const touch = event.touches[0]
      const sourceRect = sourceElement.getBoundingClientRect()
      const movedOutsideSource =
        touch.clientX < sourceRect.left - 10 ||
        touch.clientX > sourceRect.right + 10 ||
        touch.clientY < sourceRect.top - 10 ||
        touch.clientY > sourceRect.bottom + 10

      if (movedOutsideSource) {
        clearLongPressTimer()
      }
    }

    sourceElement.addEventListener('touchstart', handleTouchStart, { passive: true })
    sourceElement.addEventListener('touchend', handleTouchEnd, { passive: true })
    sourceElement.addEventListener('touchcancel', handleTouchEnd, { passive: true })
    sourceElement.addEventListener('touchmove', handleTouchMove, { passive: true })

    return () => {
      sourceElement.removeEventListener('touchstart', handleTouchStart)
      sourceElement.removeEventListener('touchend', handleTouchEnd)
      sourceElement.removeEventListener('touchcancel', handleTouchEnd)
      sourceElement.removeEventListener('touchmove', handleTouchMove)
      cancelTouchDrag()
    }
  }

  return {
    isTouchDragActive,
    cancelTouchDrag,
    bindTouchDragSource
  }
}
