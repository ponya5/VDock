import { test, expect } from 'vitest';
import fc from 'fast-check';
import { presetRegistry, presetToButton } from '../data/presets';

// Feature: vdock-ui-redesign, Property 3: presetToButton is pure and correctly derived
//
// For any registered preset and any valid empty grid position, calling
// presetToButton(preset, position) SHALL return a Button whose icon is correctly
// derived from preset.icon, whose brand tint (style.glowColor) is derived from
// preset.brand.primary (unless the preset supplies its own tint via brand.glow),
// and whose action deep-equals preset.action, SHALL assign a freshly generated id
// not equal to any previously generated id in the same test run, and SHALL NOT
// mutate the preset object or any registry entry as a side effect.
//
// SCOPE NOTE: presetToButton currently returns a Button built from the existing
// `icon`/`icon_type` and `style.glowColor` fields rather than a `layers` field,
// per its own doc comment (ButtonLayers lands in task 5.1). This test verifies
// the current, existing-fields-based contract.
//
// Validates: Requirements 1.7, 8.7

test('Feature: vdock-ui-redesign, Property 3: presetToButton is pure and correctly derived', () => {
    expect(presetRegistry.length).toBeGreaterThan(0);

    const positionArb = fc.record({
        row: fc.nat({ max: 20 }),
        col: fc.nat({ max: 20 })
    });

    const seenIds = new Set<string>();

    fc.assert(
        fc.property(fc.constantFrom(...presetRegistry), positionArb, (preset, position) => {
            // Snapshot the preset and the entire registry before calling presetToButton,
            // so we can assert neither was mutated as a side effect.
            const presetBefore = structuredClone(preset);
            const registryBefore = structuredClone(presetRegistry);

            const button = presetToButton(preset, position);

            // --- No mutation of preset or registry ---------------------------------
            expect(preset).toEqual(presetBefore);
            expect(presetRegistry).toEqual(registryBefore);

            // --- Position is placed correctly ---------------------------------------
            expect(button.position).toEqual({ row: position.row, col: position.col });

            // --- Icon correctly derived from preset.icon -----------------------------
            if (preset.icon.type === 'logo') {
                expect(button.icon_type).toBe('custom');
                expect(button.icon).toBe(preset.icon.value);
            } else if (preset.icon.type === 'fontawesome') {
                expect(button.icon_type).toBe('fontawesome');
                expect(button.icon).toEqual(preset.icon.value.split(':'));
            } else {
                // 'gif' | 'lottie' fallback
                expect(button.icon_type).toBe('custom');
                expect(button.icon).toBe(preset.icon.value);
            }

            // --- Brand tint derived from preset.brand.primary (unless overridden) ---
            const expectedGlow = preset.brand.glow ?? preset.brand.primary;
            expect(button.style?.glowColor).toBe(expectedGlow);

            // --- action deep-equals preset.action, but is not the same reference -----
            expect(button.action).toEqual(preset.action);
            expect(button.action).not.toBe(preset.action);
            if (button.action && preset.action) {
                expect(button.action.config).not.toBe(preset.action.config);
            }

            // --- id is freshly generated and unique across calls in this run ---------
            expect(typeof button.id).toBe('string');
            expect(button.id.length).toBeGreaterThan(0);
            expect(seenIds.has(button.id)).toBe(false);
            seenIds.add(button.id);
        }),
        { numRuns: 100 }
    );
});
