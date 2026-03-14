import { test, expect, vi } from 'vitest';
import fc from 'fast-check';
import { useSwipe, useLongPress } from '../composables/useGestures';
import { ref } from 'vue';

class MockPointerEvent extends Event {
    clientX: number;
    clientY: number;
    isPrimary: boolean;
    pointerId: number;
    constructor(type: string, dict: any = {}) {
        super(type);
        this.clientX = dict.clientX || 0;
        this.clientY = dict.clientY || 0;
        this.isPrimary = dict.isPrimary !== false;
        this.pointerId = dict.pointerId || 1;
    }
}
if (typeof global.PointerEvent === 'undefined') {
    (global as any).PointerEvent = MockPointerEvent;
} else if (typeof window !== 'undefined' && !(window as any).PointerEvent) {
    (window as any).PointerEvent = MockPointerEvent;
}

test('Property 9: Swipe gesture requires minimum threshold', () => {
    fc.assert(
        fc.property(
            fc.integer({ min: 0, max: 49 }),
            fc.integer({ min: 50, max: 500 }),
            fc.constantFrom('LEFT', 'RIGHT', 'UP', 'DOWN'),
            (underDx, overDx, direction) => {
                let dx = 0, dy = 0;
                if (direction === 'LEFT') dx = -underDx;
                if (direction === 'RIGHT') dx = underDx;
                if (direction === 'UP') dy = -underDx;
                if (direction === 'DOWN') dy = underDx;

                const target = ref(document.createElement('div'));
                let fired = false;
                
                useSwipe(target, {
                    threshold: 50,
                    onSwipeEnd: () => { fired = true; }
                });

                target.value.dispatchEvent(new MockPointerEvent('pointerdown', { clientX: 100, clientY: 100, isPrimary: true }));
                target.value.dispatchEvent(new MockPointerEvent('pointermove', { clientX: 100 + dx, clientY: 100 + dy, isPrimary: true }));
                target.value.dispatchEvent(new MockPointerEvent('pointerup', { isPrimary: true }));
                
                expect(fired).toBe(false);

                if (direction === 'LEFT') dx = -overDx;
                if (direction === 'RIGHT') dx = overDx;
                if (direction === 'UP') dy = -overDx;
                if (direction === 'DOWN') dy = overDx;
                
                target.value.dispatchEvent(new MockPointerEvent('pointerdown', { clientX: 100, clientY: 100, isPrimary: true }));
                target.value.dispatchEvent(new MockPointerEvent('pointermove', { clientX: 100 + dx, clientY: 100 + dy, isPrimary: true }));
                target.value.dispatchEvent(new MockPointerEvent('pointerup', { isPrimary: true }));
                
                expect(fired).toBe(true);
            }
        ),
        { numRuns: 100 }
    );
});

test('Property 11: Long-press cancels if pointer moves past threshold', () => {
    vi.useFakeTimers();
    fc.assert(
        fc.property(
            fc.integer({ min: 11, max: 100 }), // distance > 10px
            (distance) => {
                const target = ref(document.createElement('div'));
                let fired = false;
                let cancelled = false;
                
                useLongPress(target, {
                    delay: 500,
                    threshold: 10,
                    onLongPress: () => { fired = true; },
                    onCancel: () => { cancelled = true; }
                });

                target.value.dispatchEvent(new MockPointerEvent('pointerdown', { clientX: 100, clientY: 100, isPrimary: true }));
                target.value.dispatchEvent(new MockPointerEvent('pointermove', { clientX: 100 + distance, clientY: 100, isPrimary: true }));
                
                vi.advanceTimersByTime(501);
                
                expect(fired).toBe(false);
                expect(cancelled).toBe(true);
                
                // Reset
                fired = false;
                cancelled = false;
                
                // Test no move
                target.value.dispatchEvent(new MockPointerEvent('pointerdown', { clientX: 100, clientY: 100, isPrimary: true }));
                vi.advanceTimersByTime(501);
                
                expect(fired).toBe(true);
                expect(cancelled).toBe(false);
            }
        ),
        { numRuns: 100 }
    );
    vi.useRealTimers();
});
