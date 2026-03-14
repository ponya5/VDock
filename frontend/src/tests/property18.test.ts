import { test, expect } from 'vitest';
import fc from 'fast-check';
import { useParallax } from '../composables/useParallax';
import { ref } from 'vue';

test('Property 18: useParallax degrades gracefully without device motion', () => {
    fc.assert(
        fc.property(
            fc.boolean(),
            (deviceOrientationSupported) => {
                const globalOrig = (global as any).DeviceOrientationEvent;
                const windowOrig = typeof window !== 'undefined' ? (window as any).DeviceOrientationEvent : undefined;
                
                if (!deviceOrientationSupported) {
                    delete (global as any).DeviceOrientationEvent;
                    if (typeof window !== 'undefined') {
                        delete (window as any).DeviceOrientationEvent;
                    }
                } else {
                    (global as any).DeviceOrientationEvent = class {};
                    if (typeof window !== 'undefined') {
                        (window as any).DeviceOrientationEvent = class {};
                    }
                }

                const target = ref(document.createElement('div'));
                
                expect(() => {
                    const { tiltX, tiltY } = useParallax(target);
                    expect(tiltX.value).toBe(0);
                    expect(tiltY.value).toBe(0);
                }).not.toThrow();
                
                if (globalOrig !== undefined) {
                    (global as any).DeviceOrientationEvent = globalOrig;
                }
                if (typeof window !== 'undefined' && windowOrig !== undefined) {
                    (window as any).DeviceOrientationEvent = windowOrig;
                }
            }
        ),
        { numRuns: 100 }
    );
});
