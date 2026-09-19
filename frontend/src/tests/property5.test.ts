import { test, expect } from 'vitest';
import fc from 'fast-check';
import { setActivePinia, createPinia } from 'pinia';
import { useSettingsStore } from '../stores/settings';

test('Property 5: background round-trip', () => {
    setActivePinia(createPinia());
    const store = useSettingsStore();

    fc.assert(
        fc.property(
            fc.constantFrom('default', 'particles', 'waves'),
            (background) => {
                store.background = background;
                store.saveSettings();

                // mutate state manually to ensure loadSettings restores it
                store.background = background === 'default' ? 'particles' : 'default';
                store.loadSettings();

                expect(store.background).toBe(background);
            }
        ),
        { numRuns: 100 }
    );
});
