import { describe, test, expect } from 'vitest';
import fc from 'fast-check';
import { readFileSync } from 'fs';
import { resolveBrandTint } from '../utils/brandTint';

// Feature: vdock-ui-redesign, Property 6: Brand tint resolves with correct precedence and fallback
// Validates: Requirements 3.1, 3.4
//
// Full statement (design.md): "For any button, resolving --btn-brand SHALL yield
// layers.effect.tint when it is set to a colour value, otherwise the owning preset's
// brand.primary when available, otherwise the documented default hardcoded colour for
// that effect type — and this resolution SHALL never throw regardless of which sources
// are present or absent."
//
// Scope note: the full layers.effect.tint / preset brand.primary precedence chain lands
// in later tasks (3.6 presetToButton, 5.1/5.2 ButtonLayers/resolveButtonVisual). This
// test covers the CURRENT mechanism implemented in task 1.3: DeckButton.vue resolves
// --btn-brand from `button.style.glowColor` via `resolveBrandTint`, leaving it unset when
// absent so CSS's `var(--btn-brand, <default>)` fallback chain supplies the effect's
// documented default. It also statically verifies that fallback chain exists in main.css
// for glow/neon/emissive/shimmer.

describe('Feature: vdock-ui-redesign, Property 6: Brand tint resolves with correct precedence and fallback', () => {
  test('resolveBrandTint never throws and resolves to the trimmed colour or undefined, for any input', () => {
    fc.assert(
      fc.property(
        fc.oneof(
          fc.string(),
          fc.constant(undefined),
          fc.constant(null),
          fc.integer(),
          fc.boolean(),
          fc.object(),
          fc.array(fc.string())
        ),
        (input) => {
          let result: string | undefined;
          expect(() => {
            result = resolveBrandTint(input as any);
          }).not.toThrow();

          if (typeof input === 'string' && input.trim().length > 0) {
            expect(result).toBe(input.trim());
          } else {
            expect(result).toBeUndefined();
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  test('resolveBrandTint precedence: a set colour value always wins over being unset', () => {
    fc.assert(
      fc.property(
        fc.string({ minLength: 1 }).filter((s) => s.trim().length > 0),
        (glowColor) => {
          // When a colour source is present, it must be yielded verbatim (trimmed).
          expect(resolveBrandTint(glowColor)).toBe(glowColor.trim());
          // When absent, resolution must explicitly fall back to undefined
          // (letting CSS's own var(--btn-brand, <default>) fallback take over).
          expect(resolveBrandTint(undefined)).toBeUndefined();
        }
      ),
      { numRuns: 100 }
    );
  });

  test('main.css provides a hardcoded default fallback for --btn-brand on glow, neon, emissive, and shimmer effects', () => {
    const css = readFileSync(
      new URL('../assets/styles/main.css', import.meta.url),
      'utf-8'
    );

    // Each brand-parametric effect must reference var(--btn-brand, <hardcoded default>)
    // so resolution never throws/breaks even when no colour source is present.
    const fallbackPattern = /var\(--btn-brand,\s*[^)]+\)/;

    const effectBlocks: Record<string, RegExp> = {
      glow: /\.deck-button-glow\s*{[^}]*}/,
      neon: /\.deck-button-neon\s*{[^}]*}/,
      emissive: /\.deck-button-emissive\s*{[^}]*}/,
      shimmer: /\.btn-shimmer\s*{[^}]*}/
    };

    for (const [effectName, blockPattern] of Object.entries(effectBlocks)) {
      const match = css.match(blockPattern);
      expect(match, `expected to find a CSS block for effect "${effectName}"`).not.toBeNull();
      const block = match![0];
      expect(
        fallbackPattern.test(block),
        `expected effect "${effectName}" to reference var(--btn-brand, <default>) as a fallback`
      ).toBe(true);
    }
  });
});
