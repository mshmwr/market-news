'use client';

// MN-004: Expandable signal card.
// Expand on click (mobile/touch) or mouseenter (hover-capable device).
// window.matchMedia called only inside event handlers — SSR safe.
// Ticker/rationale rendered via React text nodes — no dangerouslySetInnerHTML.

import { useState, useRef } from 'react';
import type { SignalResult } from '@/lib/types';
import { TICKER_CATEGORY } from '@/lib/constants';

interface Props {
  signal: SignalResult;
}

const BORDER_COLOR: Record<string, string> = {
  BUY: '#2e7d32',
  HOLD: '#f9a825',
  SELL: '#c62828',
};
const BADGE_BG: Record<string, string> = {
  BUY: '#e8f5e9',
  HOLD: '#fff8e1',
  SELL: '#ffebee',
};
const BADGE_COLOR: Record<string, string> = {
  BUY: '#2e7d32',
  HOLD: '#f9a825',
  SELL: '#c62828',
};

// SOT sync: keys must mirror SignalCatFilter.tsx CAT_ACTIVE_STYLE.
// Missing key = badge silently hidden on card (cat truthy but catStyle undefined → render gate fails).
const CAT_STYLE: Record<string, { bg: string; color: string }> = {
  '半導體': { bg: '#e3f2fd', color: '#1565c0' },
  '晶圓':   { bg: '#e1f5fe', color: '#01579b' },
  '光電':   { bg: '#f3e5f5', color: '#6a1b9a' },
  '雷射':   { bg: '#fce4ec', color: '#ad1457' },
  '電子':   { bg: '#fce4ec', color: '#880e4f' },
  '消費電子': { bg: '#fff3e0', color: '#bf360c' },
  '材料':   { bg: '#efebe9', color: '#5d4037' },
  'AI/雲端': { bg: '#e8eaf6', color: '#283593' },
  'AI資料': { bg: '#ede7f6', color: '#4527a0' },
  '資安':   { bg: '#ffebee', color: '#c62828' },
  'EV':     { bg: '#e8f5e9', color: '#2e7d32' },
  '無人機': { bg: '#e0f7fa', color: '#00695c' },
  '量子':   { bg: '#f3e5f5', color: '#4a148c' },
  '太空':   { bg: '#e8eaf6', color: '#1a237e' },
  '加密貨幣': { bg: '#fff3e0', color: '#e65100' },
  'ETF':    { bg: '#f5f5f5', color: '#555' },
  '台股ETF': { bg: '#e0f2f1', color: '#00695c' },
  '指數':   { bg: '#efebe9', color: '#4e342e' },
  '通訊':   { bg: '#e8f4fd', color: '#0277bd' },
  '原物料': { bg: '#fff8e1', color: '#f57f17' },
};

function fmt(v: number | undefined | null, digits = 1): string {
  return v != null ? (+v).toFixed(digits) : 'N/A';
}
function fmtPct(v: number | undefined | null): string {
  return v != null ? (v * 100).toFixed(1) + '%' : 'N/A';
}
function fmtDelta(v: number | undefined | null): string {
  return v != null ? (v >= 0 ? '+' : '') + (+v).toFixed(1) + '%' : 'N/A';
}
function fmtDate(ts: number): string {
  const d = new Date(ts * 1000);
  return `${d.getMonth() + 1}/${d.getDate()}`;
}

export default function SignalCard({ signal: s }: Props) {
  const [expanded, setExpanded] = useState(false);
  const cat = TICKER_CATEGORY[s.ticker] || '';
  const catStyle = CAT_STYLE[cat];
  const borderColor = BORDER_COLOR[s.signal] ?? '#888';
  const badgeBg = BADGE_BG[s.signal] ?? '#f5f5f5';
  const badgeColor = BADGE_COLOR[s.signal] ?? '#555';
  const hoverRef = useRef(false);

  const handleMouseEnter = () => {
    // matchMedia only called inside event handler — not at module scope
    if (typeof window !== 'undefined' && window.matchMedia('(hover: hover)').matches) {
      hoverRef.current = true;
      setExpanded(true);
    }
  };
  const handleMouseLeave = () => {
    if (hoverRef.current) {
      hoverRef.current = false;
      setExpanded(false);
    }
  };
  const handleClick = () => {
    if (typeof window !== 'undefined' && !window.matchMedia('(hover: hover)').matches) {
      setExpanded((e) => !e);
    }
  };

  const t = s.technical_data ?? {};
  const f = s.fundamentals_data ?? {};
  const uv = s.undervaluation_data ?? {};

  const uvItems: string[] = [];
  if (uv.upside_pct != null) uvItems.push('目標價漲幅: ' + fmtDelta(uv.upside_pct));
  if (uv.week52_position_pct != null) uvItems.push('52週位置: ' + fmt(uv.week52_position_pct) + '%');
  if (uv.graham_number != null) uvItems.push('Graham值: ' + fmt(uv.graham_number, 2));
  if (uv.price_vs_graham_pct != null) uvItems.push('vs Graham: ' + fmtDelta(uv.price_vs_graham_pct));
  if (uv.relative_pe != null) uvItems.push('同業相對P/E: ' + fmt(uv.relative_pe, 2) + 'x');

  const techItems = [
    'RSI: ' + fmt(t.rsi),
    'MACD: ' + fmt(t.macd_line, 2),
    'MA50: ' + fmt(t.ma50, 2),
    '成交量比: ' + fmt(t.volume_ratio, 2) + 'x',
  ];
  const fundItems = [
    '本益比: ' + fmt(f.pe_ratio),
    '預期本益比: ' + fmt(f.forward_pe),
    'P/B: ' + fmt(f.price_to_book),
    '收益成長: ' + fmtPct(f.revenue_growth),
    '利潤率: ' + fmtPct(f.profit_margin),
    '負債比: ' + fmt(f.debt_to_equity),
    ...(f.recommendation_key
      ? ['法人評等: ' + f.recommendation_key + (f.number_of_analyst_opinions ? ` (${f.number_of_analyst_opinions}人)` : '')]
      : []),
  ];

  return (
    <div
      className="rounded-xl bg-white px-3.5 py-2.5 cursor-pointer min-w-0"
      style={{ borderLeft: `4px solid ${borderColor}` }}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onClick={handleClick}
    >
      {/* Summary row */}
      <div className="flex items-center gap-2 min-w-0">
        {cat && catStyle && (
          <span
            className="text-[10px] px-1.5 py-px rounded-lg font-medium shrink-0"
            style={{ background: catStyle.bg, color: catStyle.color }}
          >
            {cat}
          </span>
        )}
        <div className="flex-1 min-w-0 flex flex-col gap-px overflow-hidden">
          <span className="text-[14px] font-semibold text-gray-900 whitespace-nowrap overflow-hidden text-ellipsis">
            {s.ticker}
          </span>
          {s.name && (
            <span className="text-[11px] text-gray-400 whitespace-nowrap overflow-hidden text-ellipsis">
              {s.name}
            </span>
          )}
        </div>
        <span className="text-[12px] text-gray-500 shrink-0">
          {s.confidence != null ? `${s.confidence}%` : ''}
        </span>
        <span
          className="text-[11px] font-semibold px-2 py-px rounded-lg shrink-0"
          style={{ background: badgeBg, color: badgeColor }}
        >
          {s.signal}
        </span>
      </div>

      {/* Details (expanded) */}
      {expanded && (
        <div className="mt-2 pt-2 border-t border-gray-100">
          <p className="text-[12px] text-gray-600 leading-relaxed mb-2 overflow-wrap-anywhere">
            {s.rationale}
          </p>

          {(s.bull_case || s.bear_case) && (
            <div className="flex flex-col gap-1.5 mb-2">
              {s.bull_case && (
                <div className="text-[11px] leading-relaxed px-2 py-1.5 rounded-md bg-green-50 border-l-[3px] border-green-400 text-green-900 overflow-wrap-anywhere">
                  <span className="font-semibold mr-1">🐂 多方:</span>
                  {s.bull_case}
                </div>
              )}
              {s.bear_case && (
                <div className="text-[11px] leading-relaxed px-2 py-1.5 rounded-md bg-red-50 border-l-[3px] border-red-400 text-red-900 overflow-wrap-anywhere">
                  <span className="font-semibold mr-1">🐻 空方:</span>
                  {s.bear_case}
                </div>
              )}
            </div>
          )}

          {/* Technical data */}
          <div className="mb-2">
            <div className="text-[10px] font-semibold text-gray-300 uppercase tracking-wide mb-1">
              📊 技術指標
            </div>
            <div className="flex flex-wrap gap-1">
              {techItems.map((item) => (
                <span key={item} className="text-[10px] px-1.5 py-px rounded-full bg-gray-100 text-gray-500">
                  {item}
                </span>
              ))}
            </div>
          </div>

          {/* Fundamentals */}
          <div className="mb-2">
            <div className="text-[10px] font-semibold text-gray-300 uppercase tracking-wide mb-1">
              📈 基本面
            </div>
            <div className="flex flex-wrap gap-1">
              {fundItems.map((item) => (
                <span key={item} className="text-[10px] px-1.5 py-px rounded-full bg-gray-100 text-gray-500">
                  {item}
                </span>
              ))}
            </div>
          </div>

          {/* Undervaluation */}
          {uvItems.length > 0 && (
            <div className="mb-2">
              <div className="text-[10px] font-semibold text-gray-300 uppercase tracking-wide mb-1">
                💹 低估指標
              </div>
              <div className="flex flex-wrap gap-1">
                {uvItems.map((item) => (
                  <span key={item} className="text-[10px] px-1.5 py-px rounded-full bg-gray-100 text-gray-500">
                    {item}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Reference news */}
          {s.sources && s.sources.length > 0 && (
            <div className="mb-2">
              <div className="text-[10px] font-semibold text-gray-300 uppercase tracking-wide mb-1">
                參考新聞
              </div>
              {s.sources.map((src, i) => (
                <div key={i} className="flex items-baseline gap-1.5">
                  <a
                    href={src.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[11px] text-blue-500 hover:underline overflow-hidden text-ellipsis whitespace-nowrap flex-1 min-w-0"
                    onClick={(e) => e.stopPropagation()}
                  >
                    {src.title || src.url}
                  </a>
                  {src.published_ts && (
                    <span className="text-[10px] text-gray-300 shrink-0">
                      {fmtDate(src.published_ts)}
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Reddit posts */}
          {s.social_posts && s.social_posts.length > 0 && (
            <div>
              <div className="text-[10px] font-semibold text-gray-300 uppercase tracking-wide mb-1">
                Reddit 討論
              </div>
              {s.social_posts.map((p, i) => (
                <div key={i} className="flex items-baseline">
                  <a
                    href={p.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[11px] text-blue-500 hover:underline overflow-hidden text-ellipsis whitespace-nowrap"
                    onClick={(e) => e.stopPropagation()}
                  >
                    {p.title || p.url}
                  </a>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
