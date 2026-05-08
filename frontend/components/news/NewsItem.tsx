// MN-004: Single article row — server-renderable, no client state.
// Link rendered via href attribute; title via React text node (not innerHTML).

import type { NewsItem as NewsItemType } from '@/lib/types';

interface Props {
  article: NewsItemType;
}

const CAT_BADGE: Record<string, { bg: string; color: string }> = {
  '台股':   { bg: '#e8f5e9', color: '#2e7d32' },
  '美股':   { bg: '#e3f2fd', color: '#1565c0' },
  '加密貨幣': { bg: '#fff3e0', color: '#e65100' },
  '宏觀':   { bg: '#f3e5f5', color: '#6a1b9a' },
};

function formatTime(ts: number): string {
  const diff = Math.floor(Date.now() / 1000 - ts);
  const d = new Date(ts * 1000);
  const datePart = d.toLocaleDateString('zh-TW', { month: 'numeric', day: 'numeric' });
  if (diff < 60) return '剛剛';
  if (diff < 3600) return `${Math.floor(diff / 60)} 分鐘前 · ${datePart}`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} 小時前 · ${datePart}`;
  return d.toLocaleDateString('zh-TW', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function NewsItem({ article }: Props) {
  const catStyle = CAT_BADGE[article.category] ?? { bg: '#f0f0f0', color: '#555' };

  return (
    <div className="bg-white px-[18px] py-[14px] flex flex-col gap-1.5 hover:bg-gray-50">
      <a
        href={article.link}
        target="_blank"
        rel="noopener noreferrer"
        className="text-[15px] font-medium text-gray-900 no-underline leading-snug hover:text-blue-600"
      >
        {article.title}
      </a>
      <div className="flex gap-2 items-center">
        <span className="text-[11px] px-2 py-px rounded-full font-medium bg-gray-100 text-gray-500">
          {article.source}
        </span>
        <span
          className="text-[11px] px-2 py-px rounded-full font-medium"
          style={{ background: catStyle.bg, color: catStyle.color }}
        >
          {article.category}
        </span>
        <span className="text-[12px] text-gray-400 ml-auto whitespace-nowrap">
          {formatTime(article.published_ts)}
        </span>
      </div>
    </div>
  );
}
