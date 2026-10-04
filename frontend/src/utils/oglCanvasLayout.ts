/** After OGL `Renderer.setSize`, inline canvas styles match the drawing buffer in px and shrink in nested layouts. */
export function stretchOglCanvasToContainer(canvas: HTMLCanvasElement): void {
  canvas.style.width = '100%'
  canvas.style.height = '100%'
  canvas.style.display = 'block'
}

export function syncEmbeddedPreviewCanvases(root: HTMLElement): void {
  root.querySelectorAll('canvas').forEach(stretchOglCanvasToContainer)
}
