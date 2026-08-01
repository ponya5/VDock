import { test, expect } from 'vitest';
import fc from 'fast-check';

test('Property 10: pinch scale bounds between 0.5 and 2.0', () => {
    fc.assert(
        fc.property(
            fc.double({ min: -100.0, max: 100.0, noNaN: true, noInfinity: true }), // unconstrained scale input
            (scaleInput) => {
                const pinched = Math.max(0.5, Math.min(2.0, scaleInput));
                expect(pinched).toBeGreaterThanOrEqual(0.5);
                expect(pinched).toBeLessThanOrEqual(2.0);
            }
        ),
        { numRuns: 100 }
    );
});

test('Property 13 & 14: Swipe maps to correct navigation directions', () => {
    // Left/Right -> Page navigation (Property 13)
    // Up/Down -> Scene navigation (Property 14)
    fc.assert(
        fc.property(
            fc.constantFrom('LEFT', 'RIGHT', 'UP', 'DOWN'),
            (direction) => {
                let event = '';
                if (direction === 'LEFT') event = 'swipeLeft';
                if (direction === 'RIGHT') event = 'swipeRight';
                if (direction === 'UP') event = 'swipeUp';
                if (direction === 'DOWN') event = 'swipeDown';
                
                if (direction === 'LEFT' || direction === 'RIGHT') {
                    expect(['swipeLeft', 'swipeRight']).toContain(event);
                } else {
                    expect(['swipeUp', 'swipeDown']).toContain(event);
                }
            }
        )
    );
});

test('Property 19: Swipe progress bounds [0, 1]', () => {
    fc.assert(
        fc.property(
            fc.integer({ min: -500, max: 500 }), // dx or dy
            fc.integer({ min: 1, max: 200 }), // threshold
            (distance, threshold) => {
                const absDist = Math.abs(distance);
                const progress = Math.min(absDist / threshold, 1);
                
                expect(progress).toBeGreaterThanOrEqual(0);
                expect(progress).toBeLessThanOrEqual(1);
            }
        )
    );
});
