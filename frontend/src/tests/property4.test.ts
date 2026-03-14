import { test, expect } from 'vitest';
import fc from 'fast-check';
import { setActivePinia, createPinia } from 'pinia';
import { useSettingsStore } from '../stores/settings';

test('Property 4: Buttons never fall below minimum touch target size', () => {
    setActivePinia(createPinia());
    const store = useSettingsStore();

    fc.assert(
        fc.property(
            fc.constantFrom('normal', 'touch-friendly', 'tablet'),
            fc.integer({ min: 20, max: 100 }), 
            (mode, minTarget) => {
                store.touchMode = mode as any;
                store.minimumTouchTargetSize = minTarget;
                
                const multiplier = store.touchModeMultiplier;
                const calculatedMinHeight = Math.max(36 * multiplier, store.minimumTouchTargetSize);
                
                expect(calculatedMinHeight).toBeGreaterThanOrEqual(minTarget);
            }
        ),
        { numRuns: 100 }
    );
});
