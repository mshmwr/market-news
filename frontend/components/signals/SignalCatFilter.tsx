'use client';

import { SIG_CATS } from '@/lib/constants';

interface Props {
  sigCatFilter: Set<string>;
  onCatChange: (cat: string) => void;
}

const CAT_ACTIVE_STYLE: Record<string, { bg: string; color: string; border: string }> = {
  '半導體': { bg: '#e3f2fd', color: '#1565c0', border: '#1565c0' },
  '晶圓':   { bg: '#e1f5fe', color: '#01579b', border: '#01579b' },
  '光電':   { bg: '#f3e5f5', color: '#6a1b9a', border: '#6a1b9a' },
  '雷射':   { bg: '#fce4ec', color: '#ad1457', border: '#ad1457' },
  '電子':   { bg: '#fce4ec', color: '#880e4f', border: '#880e4f' },
  '消費電子': { bg: '#fff3e0', color: '#bf360c', border: '#bf360c' },
  '材料':   { bg: '#efebe9', color: '#5d4037', border: '#5d4037' },
  'AI/雲端': { bg: '#e8eaf6', color: '#283593', border: '#283593' },
  'AI資料': { bg: '#ede7f6', color: '#4527a0', border: '#4527a0' },
  '資安':   { bg: '#ffebee', color: '#c62828', border: '#c62828' },
  'EV':     { bg: '#e8f5e9', color: '#2e7d32', border: '#2e7d32' },
  '無人機': { bg: '#e0f7fa', color: '#00695c', border: '#00695c' },
  '量子':   { bg: '#f3e5f5', color: '#4a148c', border: '#4a148c' },
  '太空':   { bg: '#e8eaf6', color: '#1a237e', border: '#1a237e' },
  '加密貨幣': { bg: '#fff3e0', color: '#e65100', border: '#e65100' },
  'ETF':    { bg: '#f5f5f5', color: '#555',    border: '#888' },
  '台股ETF': { bg: '#e0f2f1', color: '#00695c', border: '#00695c' },
  '指數':   { bg: '#efebe9', color: '#4e342e', border: '#4e342e' },
  '通訊':   { bg: '#e8f4fd', color: '#0277bd', border: '#0277bd' },
  '原物料': { bg: '#fff8e1', color: '#f57f17', border: '#f57f17' },
};

export default function SignalCatFilter({ sigCatFilter, onCatChange }: Props) {
  const allCatsOn = SIG_CATS.every((c) => sigCatFilter.has(c));

  return (
    <div className="flex flex-wrap gap-1.5">
      <button
        onClick={() => onCatChange('全部')}
        className={`px-3 py-1 rounded-full border text-[12px] cursor-pointer transition-all ${
          allCatsOn
            ? 'bg-gray-900 text-white border-transparent'
            : 'border-gray-300 bg-white text-gray-500 hover:border-gray-500'
        }`}
      >
        全部
      </button>
      {SIG_CATS.map((cat) => {
        const isActive = sigCatFilter.has(cat);
        const activeStyle = CAT_ACTIVE_STYLE[cat];
        return (
          <button
            key={cat}
            onClick={() => onCatChange(cat)}
            className="px-3 py-1 rounded-full border text-[12px] cursor-pointer transition-all"
            style={
              isActive && activeStyle
                ? { background: activeStyle.bg, color: activeStyle.color, borderColor: activeStyle.border }
                : { background: '#fff', color: '#555', borderColor: '#ccc' }
            }
          >
            {cat}
          </button>
        );
      })}
      <button
        onClick={() => onCatChange('取消全選')}
        className="px-3 py-1 rounded-full border text-[12px] cursor-pointer text-gray-300 border-gray-200 hover:text-red-600 hover:border-red-400 transition-all"
      >
        取消全選
      </button>
    </div>
  );
}
