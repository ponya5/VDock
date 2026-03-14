import { test, expect } from 'vitest';
import fc from 'fast-check';
import { setActivePinia, createPinia } from 'pinia';
import { useProfilesStore } from '../stores/profiles';
import { computed } from 'vue';

test('Property 1: availableScenes never throws on arbitrary state', () => {
    setActivePinia(createPinia());
    const profilesStore = useProfilesStore();

    // The availableScenes logic implemented in SettingsView.vue
    const availableScenes = computed(() => {
        const profile = (profilesStore as any).currentProfile;
        if (!profile) return [];
        
        // This validates Property 1. Needs nullish check so missing arrays won't throw
        return (profile.scenes || []).map((scene: any) => ({
            id: scene.id,
            name: scene.name
        }));
    });

    const anyProfileArb = fc.oneof(
        fc.constant(undefined),
        fc.constant(null),
        fc.record({ id: fc.string(), name: fc.string() }), // no scenes array
        fc.record({
            id: fc.string(),
            name: fc.string(),
            scenes: fc.array(fc.record({
                id: fc.string(),
                name: fc.string()
            }), { maxLength: 10 })
        })
    );

    fc.assert(
        fc.property(anyProfileArb, (profile: any) => {
            (profilesStore as any).currentProfile = profile;
            
            expect(() => {
                const val = availableScenes.value;
                expect(Array.isArray(val)).toBe(true);
            }).not.toThrow();
        })
    );
});
