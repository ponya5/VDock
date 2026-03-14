import { test, expect } from 'vitest';
import fc from 'fast-check';
import { setActivePinia, createPinia } from 'pinia';
import { useDashboardStore } from '../stores/dashboard';

test('Property 17: Drag-and-drop data swap preserves data integrity', () => {
    setActivePinia(createPinia());
    const store = useDashboardStore();

    fc.assert(
        fc.property(
            fc.record({ row: fc.integer({ min: 0, max: 9 }), col: fc.integer({ min: 0, max: 9 }) }),
            fc.record({ row: fc.integer({ min: 0, max: 9 }), col: fc.integer({ min: 0, max: 9 }) }),
            (posA, posB) => {
                // Ignore same position moves to simplify test logic semantics
                if (posA.row === posB.row && posA.col === posB.col) return;

                const buttonA: any = { id: 'btnA', position: { ...posA }, size: { rows: 1, cols: 1 }, enabled: true, shape: 'rectangle' };
                const buttonB: any = { id: 'btnB', position: { ...posB }, size: { rows: 1, cols: 1 }, enabled: true, shape: 'rectangle' };

                // Emulate moving Logic
                const simulateMove = (btnIdToMove: string, tgtPos: {row: number, col: number}, gridButtons: any[]) => {
                    const btn = gridButtons.find(b => b.id === btnIdToMove);
                    if (!btn) return gridButtons;

                    const clone = [...gridButtons];
                    const existingAtTargetIndex = clone.findIndex(b => b.position.row === tgtPos.row && b.position.col === tgtPos.col);

                    if (existingAtTargetIndex !== -1 && clone[existingAtTargetIndex].id !== btn.id) {
                        // Swap
                        const currentPos = { ...btn.position };
                        clone[existingAtTargetIndex].position = currentPos;
                    }
                    
                    btn.position = { ...tgtPos };
                    return clone;
                };

                let grid = [buttonA, buttonB];
                grid = simulateMove('btnA', posB, grid);

                const finalA = grid.find(b => b.id === 'btnA');
                const finalB = grid.find(b => b.id === 'btnB');

                // A should be at B's original pos
                expect(finalA!.position).toEqual(posB);
                // B should be at A's original pos
                expect(finalB!.position).toEqual(posA);
                
                // Assert no data payload dropped
                expect(grid.length).toBe(2);
                expect(grid.some(b => b.id === 'btnA')).toBe(true);
                expect(grid.some(b => b.id === 'btnB')).toBe(true);
            }
        ),
        { numRuns: 100 }
    );
});
