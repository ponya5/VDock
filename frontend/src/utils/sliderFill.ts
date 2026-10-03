/** Range inputs draw their own fill via a --fill custom property (see settings.css). */
export function sliderFill(value: number, min: number, max: number) {
  const pct = max > min ? ((value - min) / (max - min)) * 100 : 0
  return { '--fill': `${Math.min(100, Math.max(0, pct))}%` }
}
