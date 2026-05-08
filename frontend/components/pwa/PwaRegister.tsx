'use client';

// MN-005: Service worker registration — side-effect only, renders null.
// Runs after mount (useEffect) so no SSR window.navigator access.
import { useEffect } from 'react';

export default function PwaRegister() {
  useEffect(() => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').catch(() => {
        // SW registration failure is non-fatal — app functions without it.
      });
    }
  }, []);

  return null;
}
