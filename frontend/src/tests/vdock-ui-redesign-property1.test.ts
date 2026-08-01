import { test, expect } from 'vitest';
import fc from 'fast-check';
import { presetRegistry } from '../data/presets';
import type { PresetCategory } from '../data/presets/types';

const VALID_CATEGORIES: PresetCategory[] = ['recent', 'ai', 'dev', 'media', 'social', 'news', 'system'];

test('Feature: vdock-ui-redesign, Property 1: Preset categories are always valid', () => {
    expect(presetRegistry.length).toBeGreaterThan(0);

    fc.assert(
        fc.property(fc.constantFrom(...presetRegistry), (preset) => {
            expect(VALID_CATEGORIES).toContain(preset.category);
        }),
        { numRuns: 100 }
    );
});
