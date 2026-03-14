import { test, expect } from 'vitest';
import fc from 'fast-check';
import { setActivePinia, createPinia } from 'pinia';
import { useSettingsStore } from '../stores/settings';

test('Property 5: background preference round-trip', () => {
    setActivePinia(createPinia());
    const store = useSettingsStore();

    fc.assert(
        fc.property(
            fc.constantFrom('none', 'particles', 'waves'),
            (preference) => {
                store.backgroundPreference = preference;
                store.saveSettings();
                
                // mutate state manually to ensure loadSettings restores it
                store.backgroundPreference = preference === 'none' ? 'particles' : 'none';
                store.loadSettings();
                
                expect(store.backgroundPreference).toBe(preference);
            }
        ),
        { numRuns: 100 }
    );
});
