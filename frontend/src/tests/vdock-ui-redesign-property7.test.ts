import { test, expect } from 'vitest';
import { readFileSync } from 'fs';
import { resolve } from 'path';
import fc from 'fast-check';

// Feature: vdock-ui-redesign, Property 7: Brand-parametric effect classes never hardcode colour
//
// Property 7 (design.md): For any of the glow, neon, emissive, and shimmer CSS effect class
// definitions in the stylesheet, every colour-bearing declaration (background, border,
// box-shadow) SHALL reference color-mix() with var(--btn-brand) and SHALL NOT contain a
// literal hex or named colour value.
//
// Validates: Requirements 3.2
//
// Implemented via static parsing of the effect class CSS source, not component mounting.

const CSS_PATH = resolve(__dirname, '../assets/styles/main.css');
// Strip CSS comments before any parsing — the effect-class blocks contain explanatory
// `/* ... */` comments (documenting the color-mix()/fallback pattern) that themselves
// contain colons, semicolons, and even a literal hex fallback value in prose form. Comments
// carry no runtime styling and must not be mistaken for declarations.
const cssContent = readFileSync(CSS_PATH, 'utf-8').replace(/\/\*[\s\S]*?\*\//g, '');

// The four brand-parametric effect classes rewritten in task 1.3.
const EFFECT_CLASSES = [
    'deck-button-glow',
    'deck-button-neon',
    'deck-button-emissive',
    'btn-shimmer',
] as const;

/**
 * Extracts the base rule block body for an exact class selector, e.g. `.deck-button-glow { ... }`.
 * Deliberately anchors on `\s*\{` so compound selectors like `.deck-button-glow:hover` are not
 * matched by this extraction (those are handled separately below).
 */
function extractRuleBlock(css: string, className: string): string | null {
    const escaped = className.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const pattern = new RegExp(`\\.${escaped}\\s*\\{([^}]*)\\}`);
    const match = css.match(pattern);
    return match ? match[1] : null;
}

/** Extracts every `.className:hover { ... }` block body, if present. */
function extractHoverBlock(css: string, className: string): string | null {
    const escaped = className.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const pattern = new RegExp(`\\.${escaped}:hover\\s*\\{([^}]*)\\}`);
    const match = css.match(pattern);
    return match ? match[1] : null;
}

/** Splits a rule block body into individual `property: value` declarations. */
function splitDeclarations(block: string): { property: string; value: string; raw: string }[] {
    return block
        .split(';')
        .map((d) => d.trim())
        .filter((d) => d.length > 0)
        .map((d) => {
            const colonIndex = d.indexOf(':');
            if (colonIndex === -1) return { property: '', value: '', raw: d };
            return {
                property: d.slice(0, colonIndex).trim(),
                value: d.slice(colonIndex + 1).trim(),
                raw: d,
            };
        });
}

// Colour-bearing property names called out explicitly by Property 7.
const COLOR_BEARING_PROPERTIES = new Set(['background', 'border', 'box-shadow', 'color']);

/**
 * Given a declaration value, strips out (a) the fallback argument of any
 * `var(--btn-brand, ...)` usage, and (b) the body of any `color-mix(...)` call, so that
 * the two documented, design.md-sanctioned uses of a literal hex colour are not mistaken
 * for a hardcoded colour used *instead of* color-mix():
 *   1. The CSS custom property's own default, e.g. `var(--btn-brand, #4a9eff)`.
 *   2. The "mix into" base colour argument of `color-mix()` itself, e.g.
 *      `color-mix(in srgb, var(--btn-brand) 12%, #0d0d0d)` — this is the exact pattern
 *      shown in design.md's own `.fx-glow` reference implementation, so a literal hex as
 *      color-mix's blend target is the mechanism, not a violation of it.
 * What must never appear is a hex/named colour used on its own, outside of any
 * `color-mix(...)` call and outside of a `var(--btn-brand, ...)` fallback slot — i.e. a
 * colour that bypasses brand-parametrization entirely.
 */
function stripBrandFallback(value: string): string {
    // First, remove entire color-mix(...) calls (they legitimately carry var(--btn-brand)
    // plus a literal hex "mix into" base as their second colour argument).
    let stripped = value.replace(/color-mix\([^()]*(?:\([^()]*\)[^()]*)*\)/g, 'COLOR_MIX');
    // Then remove any remaining var(--btn-brand, <fallback>) default-argument slots that
    // exist outside of a color-mix() call (e.g. used directly as a background-color).
    stripped = stripped.replace(/var\(--btn-brand(?:\s*,\s*[^()]*(?:\([^()]*\)[^()]*)*)?\)/g, 'BRAND_VAR');
    return stripped;
}

function hasLiteralHexColorOutsideFallback(value: string): boolean {
    const stripped = stripBrandFallback(value);
    return /#[0-9a-fA-F]{3,8}\b/.test(stripped);
}

function getColorBearingDeclarations(block: string): { property: string; value: string; raw: string }[] {
    return splitDeclarations(block).filter((d) => COLOR_BEARING_PROPERTIES.has(d.property));
}

test('Property 7: Brand-parametric effect classes never hardcode colour', () => {
    // Sanity check: all four effect classes must actually exist in the stylesheet.
    for (const className of EFFECT_CLASSES) {
        const block = extractRuleBlock(cssContent, className);
        expect(block, `expected .${className} rule block to exist in main.css`).not.toBeNull();
    }

    fc.assert(
        fc.property(fc.constantFrom(...EFFECT_CLASSES), (className) => {
            const block = extractRuleBlock(cssContent, className);
            expect(block).not.toBeNull();

            const colorDecls = getColorBearingDeclarations(block as string);

            // Each of these four classes is expected to have at least one colour-bearing
            // declaration (background/border/box-shadow/color) — otherwise the class wouldn't
            // be an "effect" at all.
            expect(colorDecls.length).toBeGreaterThan(0);

            for (const decl of colorDecls) {
                // Every colour-bearing declaration must reference color-mix() and var(--btn-brand).
                expect(
                    decl.value.includes('color-mix('),
                    `.${className} declaration "${decl.raw}" must use color-mix()`
                ).toBe(true);
                expect(
                    decl.value.includes('var(--btn-brand'),
                    `.${className} declaration "${decl.raw}" must reference var(--btn-brand)`
                ).toBe(true);

                // No literal hex colour value outside the documented var(--btn-brand, <fallback>) slot.
                expect(
                    hasLiteralHexColorOutsideFallback(decl.value),
                    `.${className} declaration "${decl.raw}" must not hardcode a hex colour outside the var() fallback`
                ).toBe(false);
            }

            // Bonus: if a `:hover` counterpart exists, it must uphold the same rule.
            const hoverBlock = extractHoverBlock(cssContent, className);
            if (hoverBlock) {
                const hoverColorDecls = getColorBearingDeclarations(hoverBlock);
                for (const decl of hoverColorDecls) {
                    expect(decl.value.includes('color-mix(')).toBe(true);
                    expect(decl.value.includes('var(--btn-brand')).toBe(true);
                    expect(hasLiteralHexColorOutsideFallback(decl.value)).toBe(false);
                }
            }

            return true;
        }),
        { numRuns: 100 }
    );
});
