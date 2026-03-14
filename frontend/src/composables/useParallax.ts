import { ref, unref, watch, type MaybeRef } from 'vue';

export interface ParallaxOptions {
  maxTilt?: number;
  perspective?: number;
}

export function useParallax(target: MaybeRef<HTMLElement | null | undefined>, options: ParallaxOptions = {}) {
  const maxTilt = options.maxTilt ?? 15;
  const perspective = options.perspective ?? 1000;
  
  const tiltX = ref(0);
  const tiltY = ref(0);
  
  const onMouseMove = (e: MouseEvent) => {
    const el = unref(target);
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    
    tiltX.value = ((y - centerY) / centerY) * -maxTilt;
    tiltY.value = ((x - centerX) / centerX) * maxTilt;
    
    el.style.transform = `perspective(${perspective}px) rotateX(${tiltX.value}deg) rotateY(${tiltY.value}deg)`;
  };
  
  const onMouseLeave = () => {
    tiltX.value = 0;
    tiltY.value = 0;
    const el = unref(target);
    if (el) el.style.transform = `perspective(${perspective}px) rotateX(0deg) rotateY(0deg)`;
  };
  
  const onDeviceOrientation = (e: DeviceOrientationEvent) => {
    if (e.beta === null || e.gamma === null) return;
    
    const el = unref(target);
    if (!el) return;
    
    const beta = Math.max(-45, Math.min(45, e.beta));
    const gamma = Math.max(-45, Math.min(45, e.gamma));
    
    tiltX.value = (beta / 45) * maxTilt;
    tiltY.value = (gamma / 45) * maxTilt;
    
    el.style.transform = `perspective(${perspective}px) rotateX(${tiltX.value}deg) rotateY(${tiltY.value}deg)`;
  };

  const cleanup = () => {
    const el = unref(target);
    if (el) {
      el.removeEventListener('mousemove', onMouseMove);
      el.removeEventListener('mouseleave', onMouseLeave);
      el.style.transform = '';
    }
    if (typeof window !== 'undefined') {
      window.removeEventListener('deviceorientation', onDeviceOrientation);
    }
  };

  watch(() => unref(target), (el, _, onCleanup) => {
    cleanup();
    if (el) {
      el.addEventListener('mousemove', onMouseMove);
      el.addEventListener('mouseleave', onMouseLeave);
      el.style.transform = `perspective(${perspective}px) rotateX(0deg) rotateY(0deg)`;
    }
    if (typeof window !== 'undefined' && (window as any).DeviceOrientationEvent) {
      window.addEventListener('deviceorientation', onDeviceOrientation);
    }
    onCleanup(cleanup);
  }, { immediate: true });

  return { tiltX, tiltY };
}
