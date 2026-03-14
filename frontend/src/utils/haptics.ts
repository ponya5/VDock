export function vibrate(pattern: number | number[] = 50) {
    if (typeof window !== 'undefined' && window.navigator && typeof window.navigator.vibrate === 'function') {
        try {
            window.navigator.vibrate(pattern);
        } catch (e) {
            // Gracefully degrade without throwing
        }
    }
}
