'use client';

// MN-004: Google Translate proxy button.
// Opens the page via translate.goog proxy. Hidden when already on a translated page.
// window.location accessed only at click time — SSR safe.

import { useState, useEffect } from 'react';

const TRANSLATE_URL =
  'https://market-news-sigma-vercel-app.translate.goog/?_x_tr_sl=auto&_x_tr_tl=zh-TW&_x_tr_hl=zh-TW';

export default function TranslateButton() {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    // Hide button when already on a translated page
    if (typeof window !== 'undefined' && window.location.hostname.endsWith('.translate.goog')) {
      setVisible(false);
    }
  }, []);

  if (!visible) return null;

  return (
    <a
      href={TRANSLATE_URL}
      target="_blank"
      rel="noopener noreferrer"
      className="text-[12px] px-2.5 py-1 rounded-full border border-gray-300 bg-white text-gray-500 hover:border-gray-500 whitespace-nowrap no-underline"
    >
      🌐 翻譯
    </a>
  );
}
