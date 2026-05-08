'use client';

// MN-004: 4-category news filter pills.
// Called from PageClient; onCatChange receives the category or '全部' or '取消全選'.

import { NEWS_CATEGORIES } from '@/lib/constants';
import type { NewsCategory } from '@/lib/types';

interface Props {
  selected: Set<string>;
  onCatChange: (cat: string) => void;
}

const CAT_ACTIVE: Record<string, { bg: string; color: string }> = {
  '台股':   { bg: '#2e7d32', color: '#fff' },
  '美股':   { bg: '#1565c0', color: '#fff' },
  '加密貨幣': { bg: '#e65100', color: '#fff' },
  '宏觀':   { bg: '#6a1b9a', color: '#fff' },
};

export default function NewsFilters({ selected, onCatChange }: Props) {
  const allOn = NEWS_CATEGORIES.every((c) => selected.has(c));

  return (
    <div className="flex gap-2 flex-wrap items-center">
      <button
        onClick={() => onCatChange('全部')}
        className={`px-4 py-1.5 rounded-full border text-[13px] font-medium cursor-pointer transition-all ${
          allOn
            ? 'bg-gray-900 text-white border-transparent'
            : 'border-gray-300 bg-white text-gray-700 hover:border-gray-500'
        }`}
      >
        全部
      </button>
      {NEWS_CATEGORIES.map((cat: NewsCategory) => {
        const isActive = selected.has(cat);
        const activeStyle = CAT_ACTIVE[cat];
        return (
          <button
            key={cat}
            onClick={() => onCatChange(cat)}
            className="px-4 py-1.5 rounded-full border text-[13px] font-medium cursor-pointer transition-all"
            style={
              isActive && activeStyle
                ? { background: activeStyle.bg, color: activeStyle.color, borderColor: 'transparent' }
                : { background: '#fff', color: '#555', borderColor: '#ccc' }
            }
          >
            {cat}
          </button>
        );
      })}
      <button
        onClick={() => onCatChange('取消全選')}
        className="px-4 py-1.5 rounded-full border text-[13px] font-medium cursor-pointer border-gray-300 bg-white text-gray-500 hover:border-gray-500 transition-all"
      >
        全部取消
      </button>
    </div>
  );
}
