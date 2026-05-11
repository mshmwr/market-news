'use client';

// Google Translate Element widget (in-page JS overlay).
// Replaces the old translate.goog proxy approach — `*.vercel.app` is rejected
// by translate.goog (HTTP 400), so we embed Google's widget directly instead.
//
// Flow: widget loads in background on every page mount. It reads the
// `googtrans` cookie and applies translation if present. Button just toggles
// the cookie and reloads so the widget picks it up.

import { useEffect, useState } from 'react';

declare global {
  interface Window {
    googleTranslateElementInit?: () => void;
    google?: { translate: { TranslateElement: new (opts: object, id: string) => unknown } };
  }
}

const WIDGET_SRC = '//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit';
const TARGET_LANG = 'zh-TW';

function isTranslated(): boolean {
  if (typeof document === 'undefined') return false;
  return document.cookie.split(';').some((c) => c.trim().startsWith('googtrans=') && c.includes(TARGET_LANG));
}

export default function TranslateButton() {
  const [translated, setTranslated] = useState(false);

  useEffect(() => {
    setTranslated(isTranslated());

    // Hide Google's injected top banner; the translation itself still applies.
    const style = document.createElement('style');
    style.textContent = `
      .skiptranslate.goog-te-banner-frame,
      .goog-te-banner-frame { display: none !important; }
      body { top: 0 !important; position: static !important; }
      #goog-gt-tt, .goog-te-balloon-frame { display: none !important; }
      .goog-text-highlight { background: none !important; box-shadow: none !important; }
    `;
    document.head.appendChild(style);

    // Lazy-load widget script once per page.
    if (!document.querySelector(`script[src="${WIDGET_SRC}"]`)) {
      window.googleTranslateElementInit = () => {
        if (!window.google?.translate) return;
        new window.google.translate.TranslateElement(
          {
            pageLanguage: 'auto',
            includedLanguages: 'zh-TW,zh-CN,en,ja,ko',
            autoDisplay: false,
          },
          'google_translate_element',
        );
      };
      const s = document.createElement('script');
      s.src = WIDGET_SRC;
      s.async = true;
      document.body.appendChild(s);
    }
  }, []);

  function handleClick() {
    const host = window.location.hostname;
    const expire = 'expires=Thu, 01 Jan 1970 00:00:00 GMT';

    // Clear any prior cookie variants (root + dotted-host).
    document.cookie = `googtrans=; ${expire}; path=/`;
    document.cookie = `googtrans=; ${expire}; path=/; domain=.${host}`;

    if (!translated) {
      document.cookie = `googtrans=/auto/${TARGET_LANG}; path=/`;
      document.cookie = `googtrans=/auto/${TARGET_LANG}; path=/; domain=.${host}`;
    }

    window.location.reload();
  }

  return (
    <>
      <button
        type="button"
        onClick={handleClick}
        className="fixed bottom-5 left-5 z-30 px-4 py-2 rounded-full bg-[#1d1d1f] text-white text-[13px] shadow-lg hover:bg-[#3a3a3c] whitespace-nowrap"
      >
        {translated ? '🌐 原文' : '🌐 翻譯'}
      </button>
      <div id="google_translate_element" className="hidden" />
    </>
  );
}
