import { test, expect } from 'vitest';
import fc from 'fast-check';
import { setActivePinia, createPinia } from 'pinia';
import { useSettingsStore } from '../stores/settings';

test('Property 16: Sidebar open/close (dockedSidebarEnabled) maintains state correctly across toggles and loads', () => {
    setActivePinia(createPinia());
    const settingsStore = useSettingsStore();

    // Mock localStorage
    const mockStorage: Record<string, string> = {};
    Object.defineProperty(window, 'localStorage', {
        value: {
            getItem: (key: string) => mockStorage[key] || null,
            setItem: (key: string, value: string) => { mockStorage[key] = value; },
            removeItem: (key: string) => { delete mockStorage[key]; },
            clear: () => {
                for (let key in mockStorage) {
                    delete mockStorage[key];
                }
            }
        },
        writable: true
    });

    const toggleSequenceArb = fc.array(fc.boolean(), { minLength: 1, maxLength: 50 });

    fc.assert(
        fc.property(toggleSequenceArb, (actions) => {
            localStorage.clear();
            settingsStore.dockedSidebarEnabled = true;
            settingsStore.saveSettings();

            for (const state of actions) {
                settingsStore.dockedSidebarEnabled = state;
                settingsStore.saveSettings();
                
                // Induce failure state before reloading round-trip
                settingsStore.dockedSidebarEnabled = !state; 
                
                // Load from storage round-trip validation
                settingsStore.loadSettings();
                
                expect(settingsStore.dockedSidebarEnabled).toBe(state);
            }
        })
    );
});
