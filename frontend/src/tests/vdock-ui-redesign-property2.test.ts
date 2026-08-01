import { test, expect } from 'vitest';
import fc from 'fast-check';
import { presetRegistry, findPresetsByKeyword } from '../data/presets';

// Feature: vdock-ui-redesign, Property 2: Preset keyword discoverability
//
// For any preset with a non-empty `keywords` array, searching the Preset_Registry by
// any element of that array, or by the preset's `name`, SHALL include that preset in
// the result set.
//
// Validates: Requirements 1.6

test('Feature: vdock-ui-redesign, Property 2: Preset keyword discoverability', () => {
    const presetsWithKeywords = presetRegistry.filter(
        (preset) => Array.isArray(preset.keywords) && preset.keywords.length > 0
    );

    // Guard: the property is only meaningful if there is at least one preset with
    // keywords to exercise. If this fails, task 3.3 (seeding presets with keywords)
    // has not been completed yet.
    expect(presetsWithKeywords.length).toBeGreaterThan(0);

    const presetArb = fc.constantFrom(...presetsWithKeywords);

    fc.assert(
        fc.property(presetArb, (preset) => {
            // Pick either the preset's own name or one of its keywords as the query.
            const candidateQueries = [preset.name, ...(preset.keywords ?? [])];
            for (const query of candidateQueries) {
                const results = findPresetsByKeyword(presetRegistry, query);
                expect(results.some((p) => p.id === preset.id)).toBe(true);
            }
        }),
        { numRuns: 100 }
    );
});
