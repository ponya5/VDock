import { test, expect } from 'vitest';
import fc from 'fast-check';
import { vibrate } from '../utils/haptics';

test('Property 12: haptics.vibrate never throws', () => {

    fc.assert(
        fc.property(
            fc.boolean(), // has navigator object
            fc.boolean(), // has vibrate function
            fc.boolean(), // vibrate throws exception
            fc.oneof(fc.integer({ min: 1, max: 1000 }), fc.array(fc.integer({ min: 1, max: 1000 }))),
            (hasNavigator, hasVibrate, throwsError, pattern) => {
                
                // Set up mock window/navigator
                const mockWindow: any = {};
                if (hasNavigator) {
                    mockWindow.navigator = {};
                    if (hasVibrate) {
                        mockWindow.navigator.vibrate = () => {
                            if (throwsError) throw new Error('Mock hardware error');
                            return true;
                        };
                    }
                }
                
                // Override global window for this test execution
                const oldWindow = (global as any).window;
                (global as any).window = mockWindow;

                expect(() => vibrate(pattern)).not.toThrow();

                // Restore
                (global as any).window = oldWindow;
            }
        ),
        { numRuns: 100 }
    );
});
