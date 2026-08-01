/**
 * Brand tint resolution for the `--btn-brand` CSS custom property.
 *
 * Phase 1 (Foundations) mechanism: `DeckButton.vue` sets `--btn-brand` from
 * `button.style.glowColor` when present, and leaves it unset otherwise. When
 * unset, the CSS fallback syntax `var(--btn-brand, <default>)` used by the
 * `.deck-button-glow` / `.deck-button-neon` / `.deck-button-emissive` /
 * `.btn-shimmer` effect classes in `main.css` resolves to that effect's
 * documented hardcoded default colour.
 *
 * Full precedence (`layers.effect.tint` -> preset `brand.primary` -> hardcoded
 * default) lands in later phases (presetToButton / resolveButtonVisual). This
 * helper only resolves the current explicit-source step so it can be unit
 * tested independently of the component.
 */

/**
 * Resolve the value that should be assigned to the `--btn-brand` CSS custom
 * property from an optional glow colour source.
 *
 * - Returns the trimmed colour string when it is a non-empty string.
 * - Returns `undefined` for any other input (undefined, null, empty/whitespace
 *   string, or any non-string value), signalling that `--btn-brand` should be
 *   left unset so CSS's fallback chain can resolve the effect's default.
 *
 * This function never throws, regardless of the input provided.
 */
export function resolveBrandTint(glowColor?: unknown): string | undefined {
  if (typeof glowColor !== 'string') {
    return undefined
  }

  const trimmed = glowColor.trim()
  return trimmed.length > 0 ? trimmed : undefined
}
