import { ref, unref, watch, type MaybeRef } from 'vue';

export interface SwipeOptions {
  threshold?: number;
  onSwipeEnd?: (direction: 'LEFT' | 'RIGHT' | 'UP' | 'DOWN', progress: number) => void;
  onSwipeStart?: () => void;
  onSwipe?: (direction: 'LEFT' | 'RIGHT' | 'UP' | 'DOWN', progress: number) => void;
}

export function useSwipe(target: MaybeRef<HTMLElement | null | undefined>, options: SwipeOptions = {}) {
  const threshold = options.threshold ?? 50;
  const isSwiping = ref(false);
  const direction = ref<'LEFT' | 'RIGHT' | 'UP' | 'DOWN' | null>(null);
  const progress = ref(0);

  let startX = 0;
  let startY = 0;

  const onPointerDown = (e: PointerEvent) => {
    if (!e.isPrimary) return;
    startX = e.clientX;
    startY = e.clientY;
    isSwiping.value = true;
    direction.value = null;
    progress.value = 0;
    options.onSwipeStart?.();
  };

  const onPointerMove = (e: PointerEvent) => {
    if (!isSwiping.value || !e.isPrimary) return;
    
    const dx = e.clientX - startX;
    const dy = e.clientY - startY;
    const absX = Math.abs(dx);
    const absY = Math.abs(dy);

    if (absX > absY) {
      direction.value = dx > 0 ? 'RIGHT' : 'LEFT';
      progress.value = Math.min(absX / threshold, 1);
    } else {
      direction.value = dy > 0 ? 'DOWN' : 'UP';
      progress.value = Math.min(absY / threshold, 1);
    }
    
    options.onSwipe?.(direction.value, progress.value);
  };

  const onPointerUp = (e: PointerEvent) => {
    if (!isSwiping.value || !e.isPrimary) return;
    isSwiping.value = false;
    if (direction.value && progress.value >= 1) {
      options.onSwipeEnd?.(direction.value, progress.value);
    }
    progress.value = 0;
  };

  const cleanup = () => {
    const el = unref(target);
    if (!el) return;
    el.removeEventListener('pointerdown', onPointerDown as EventListener);
    el.removeEventListener('pointermove', onPointerMove as EventListener);
    el.removeEventListener('pointerup', onPointerUp as EventListener);
    el.removeEventListener('pointercancel', onPointerUp as EventListener);
  };

  watch(() => unref(target), (el, _, onCleanup) => {
    cleanup();
    if (el) {
      el.addEventListener('pointerdown', onPointerDown as EventListener);
      el.addEventListener('pointermove', onPointerMove as EventListener);
      el.addEventListener('pointerup', onPointerUp as EventListener);
      el.addEventListener('pointercancel', onPointerUp as EventListener);
    }
    onCleanup(cleanup);
  }, { immediate: true });

  return { isSwiping, direction, progress };
}

export interface LongPressOptions {
  delay?: number;
  threshold?: number;
  onLongPress?: () => void;
  onCancel?: () => void;
}

export function useLongPress(target: MaybeRef<HTMLElement | null | undefined>, options: LongPressOptions = {}) {
  const delay = options.delay ?? 500;
  const threshold = options.threshold ?? 10;
  
  let timer: ReturnType<typeof setTimeout> | null = null;
  let startX = 0;
  let startY = 0;
  let isPressed = false;

  const cancel = () => {
    if (timer) {
      clearTimeout(timer);
      timer = null;
    }
    if (isPressed) {
      options.onCancel?.();
    }
    isPressed = false;
  };

  const onPointerDown = (e: PointerEvent) => {
    if (!e.isPrimary) return;
    startX = e.clientX;
    startY = e.clientY;
    isPressed = true;
    
    timer = setTimeout(() => {
      if (isPressed) {
        options.onLongPress?.();
        isPressed = false;
      }
    }, delay);
  };

  const onPointerMove = (e: PointerEvent) => {
    if (!isPressed || !e.isPrimary) return;
    const dx = Math.abs(e.clientX - startX);
    const dy = Math.abs(e.clientY - startY);
    if (dx > threshold || dy > threshold) {
      cancel();
    }
  };

  const onPointerUp = () => cancel();

  watch(() => unref(target), (el, _, onCleanup) => {
    if (el) {
      el.addEventListener('pointerdown', onPointerDown as EventListener);
      el.addEventListener('pointermove', onPointerMove as EventListener);
      el.addEventListener('pointerup', onPointerUp as EventListener);
      el.addEventListener('pointercancel', onPointerUp as EventListener);
      el.addEventListener('contextmenu', (e) => e.preventDefault());
    }
    onCleanup(() => {
      if (el) {
        el.removeEventListener('pointerdown', onPointerDown as EventListener);
        el.removeEventListener('pointermove', onPointerMove as EventListener);
        el.removeEventListener('pointerup', onPointerUp as EventListener);
        el.removeEventListener('pointercancel', onPointerUp as EventListener);
      }
      cancel();
    });
  }, { immediate: true });
}

export interface PinchOptions {
  onPinch?: (scale: number) => void;
  onPinchStart?: () => void;
  onPinchEnd?: () => void;
}

export function usePinch(target: MaybeRef<HTMLElement | null | undefined>, options: PinchOptions = {}) {
  let initialDistance = 0;
  const activePointers = new Map<number, PointerEvent>();

  const getDistance = (p1: PointerEvent, p2: PointerEvent) => {
    const dx = p1.clientX - p2.clientX;
    const dy = p1.clientY - p2.clientY;
    return Math.sqrt(dx * dx + dy * dy);
  };

  const onPointerDown = (e: PointerEvent) => {
    activePointers.set(e.pointerId, e);
    if (activePointers.size === 2) {
      const pointers = Array.from(activePointers.values());
      initialDistance = getDistance(pointers[0], pointers[1]);
      options.onPinchStart?.();
    }
  };

  const onPointerMove = (e: PointerEvent) => {
    if (!activePointers.has(e.pointerId)) return;
    activePointers.set(e.pointerId, e);
    
    if (activePointers.size === 2) {
      const pointers = Array.from(activePointers.values());
      const currentDistance = getDistance(pointers[0], pointers[1]);
      const scale = currentDistance / initialDistance;
      options.onPinch?.(scale);
    }
  };

  const onPointerUp = (e: PointerEvent) => {
    const wasPinching = activePointers.size === 2;
    activePointers.delete(e.pointerId);
    if (wasPinching && activePointers.size < 2) {
      options.onPinchEnd?.();
    }
  };

  watch(() => unref(target), (el, _, onCleanup) => {
    if (el) {
      el.addEventListener('pointerdown', onPointerDown as EventListener);
      el.addEventListener('pointermove', onPointerMove as EventListener);
      el.addEventListener('pointerup', onPointerUp as EventListener);
      el.addEventListener('pointercancel', onPointerUp as EventListener);
    }
    onCleanup(() => {
      if (el) {
        el.removeEventListener('pointerdown', onPointerDown as EventListener);
        el.removeEventListener('pointermove', onPointerMove as EventListener);
        el.removeEventListener('pointerup', onPointerUp as EventListener);
        el.removeEventListener('pointercancel', onPointerUp as EventListener);
      }
    });
  }, { immediate: true });
}

export interface DoubleTapOptions {
  delay?: number;
  onDoubleTap?: (e: PointerEvent) => void;
}

export function useDoubleTap(target: MaybeRef<HTMLElement | null | undefined>, options: DoubleTapOptions = {}) {
  const delay = options.delay ?? 300;
  let lastTapTime = 0;
  let tapCount = 0;

  const onClick = (e: PointerEvent) => {
    const now = Date.now();
    if (now - lastTapTime < delay) {
      tapCount++;
    } else {
      tapCount = 1;
    }
    lastTapTime = now;

    if (tapCount === 2) {
      options.onDoubleTap?.(e);
      tapCount = 0;
    }
  };

  watch(() => unref(target), (el, _, onCleanup) => {
    if (el) {
      el.addEventListener('pointerup', onClick as EventListener);
    }
    onCleanup(() => {
      if (el) el.removeEventListener('pointerup', onClick as EventListener);
    });
  }, { immediate: true });
}
