'use client';

// Google Translate proxy button (translate.goog).
// Hostname encoding rule: original `.` → `-`, original `-` → `--`.
// The Vercel host `market-news-sigma.vercel.app` has hyphens, so they must be
// doubled — the previous single-hyphen form decoded to `market.news.sigma...`
// which doesn't exist and Google returned HTTP 400.

import { useEffect, useState } from 'react';

const TRANSLATE_URL =
  'https://market--news--sigma-vercel-app.translate.goog/?_x_tr_sl=auto&_x_tr_tl=zh-TW&_x_tr_hl=zh-TW';

export default function TranslateButton() {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
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
      className="fixed bottom-5 left-5 z-30 px-4 py-2 rounded-full bg-[#1d1d1f] text-white text-[13px] shadow-lg hover:bg-[#3a3a3c] whitespace-nowrap no-underline"
    >
      🌐 翻譯
    </a>
  );
}
