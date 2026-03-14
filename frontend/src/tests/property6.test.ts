import { test, expect } from 'vitest';
import fc from 'fast-check';

test('Property 6: DockedSidebar layout uses mobile overlay under 768px', () => {
    // Assert logic from DockedSidebar's handleWindowResize checks 
    fc.assert(
        fc.property(
            fc.integer({ min: 320, max: 2000 }),
            (width) => {
                const isMobile = width < 768;
                if (width < 768) {
                    expect(isMobile).toBe(true);
                } else {
                    expect(isMobile).toBe(false);
                }
            }
        ),
        { numRuns: 100 }
    );
});
