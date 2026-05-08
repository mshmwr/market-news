// MN-004: Market Overview panel — server-renderable (no client state).
// Computes BUY/HOLD/SELL sentiment, index signals, sector BUY heat from signals array.

import type { SignalResult } from '@/lib/types';
import { TICKER_CATEGORY } from '@/lib/constants';

interface Props {
  signals: SignalResult[];
}

export default function MarketOverview({ signals }: Props) {
  if (signals.length === 0) return null;

  // Exclude index tickers from sentiment counts
  const stocks = signals.filter(
    (s) => TICKER_CATEGORY[s.ticker] !== '指數',
  );
  const counts = { BUY: 0, HOLD: 0, SELL: 0 };
  for (const s of stocks) {
    if (s.signal in counts) counts[s.signal as keyof typeof counts]++;
  }
  const total = stocks.length || 1;
  const bp = (counts.BUY / total) * 100;
  const hp = (counts.HOLD / total) * 100;
  const sp = (counts.SELL / total) * 100;

  // Sector BUY heat
  const catBuy: Record<string, { buy: number; total: number }> = {};
  for (const s of stocks) {
    const cat = TICKER_CATEGORY[s.ticker];
    if (!cat) continue;
    if (!catBuy[cat]) catBuy[cat] = { buy: 0, total: 0 };
    catBuy[cat].total++;
    if (s.signal === 'BUY') catBuy[cat].buy++;
  }
  const topCats = Object.entries(catBuy)
    .filter(([, v]) => v.buy > 0)
    .sort((a, b) => b[1].buy - a[1].buy)
    .slice(0, 5);

  // Index signals
  const vix = signals.find((s) => s.ticker === '^VIX');
  const spy = signals.find((s) => s.ticker === 'SPY');
  const qqq = signals.find((s) => s.ticker === 'QQQ');
  const tnx = signals.find((s) => s.ticker === '^TNX');
  const vixVal = vix?.fundamentals_data?.current_price;
  const tnxVal = tnx?.fundamentals_data?.current_price;
  const vixColor =
    vixVal == null
      ? '#888'
      : vixVal > 30
        ? '#c62828'
        : vixVal > 20
          ? '#e65100'
          : vixVal > 15
            ? '#f57f17'
            : '#2e7d32';

  const sigBadgeClass = (signal: string) => {
    if (signal === 'BUY') return 'bg-green-100 text-green-800';
    if (signal === 'SELL') return 'bg-red-100 text-red-700';
    return 'bg-yellow-100 text-yellow-700';
  };

  return (
    <div className="rounded-xl bg-white p-4 shadow-sm mb-3">
      <div className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">
        📡 市場總覽
      </div>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {/* Sentiment */}
        <div>
          <div className="text-[10px] font-semibold text-gray-300 uppercase tracking-wide mb-1">
            整體情緒（{total} 檔）
          </div>
          <div className="flex h-1.5 rounded overflow-hidden gap-px mb-2">
            <div style={{ flex: bp, background: '#2e7d32', borderRadius: '3px 0 0 3px' }} />
            <div style={{ flex: hp, background: '#f57f17' }} />
            <div style={{ flex: sp, background: '#c62828', borderRadius: '0 3px 3px 0' }} />
          </div>
          <div className="flex flex-col gap-0.5 text-[11px]">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-green-700 inline-block" />
              BUY {counts.BUY}（{bp.toFixed(0)}%）
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full inline-block" style={{ background: '#f57f17' }} />
              HOLD {counts.HOLD}（{hp.toFixed(0)}%）
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-red-700 inline-block" />
              SELL {counts.SELL}（{sp.toFixed(0)}%）
            </div>
          </div>
        </div>

        {/* Index signals */}
        <div>
          <div className="text-[10px] font-semibold text-gray-300 uppercase tracking-wide mb-1">
            大盤指標
          </div>
          <div className="flex flex-col gap-1 text-[11px]">
            {vixVal != null && (
              <div className="flex justify-between">
                <span className="text-gray-400">VIX</span>
                <span className="font-semibold" style={{ color: vixColor }}>
                  {vixVal.toFixed(1)}
                </span>
              </div>
            )}
            {tnxVal != null && (
              <div className="flex justify-between">
                <span className="text-gray-400">10Y殖利率</span>
                <span className="font-semibold">{tnxVal.toFixed(2)}%</span>
              </div>
            )}
            {spy && (
              <div className="flex justify-between items-center">
                <span className="text-gray-400">SPY</span>
                <span className={`text-[10px] font-semibold px-1.5 py-px rounded ${sigBadgeClass(spy.signal)}`}>
                  {spy.signal}
                </span>
              </div>
            )}
            {qqq && (
              <div className="flex justify-between items-center">
                <span className="text-gray-400">QQQ</span>
                <span className={`text-[10px] font-semibold px-1.5 py-px rounded ${sigBadgeClass(qqq.signal)}`}>
                  {qqq.signal}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Sector heat */}
        <div className="col-span-2 sm:col-span-1">
          <div className="text-[10px] font-semibold text-gray-300 uppercase tracking-wide mb-1">
            板塊熱度（BUY）
          </div>
          {topCats.length === 0 ? (
            <div className="text-[11px] text-gray-300">暫無 BUY 訊號</div>
          ) : (
            <div className="flex flex-col gap-1">
              {topCats.map(([cat, v]) => (
                <div key={cat} className="flex items-center gap-1.5 text-[11px]">
                  <span className="w-14 text-gray-500 shrink-0">{cat}</span>
                  <div className="flex-1 h-1 bg-gray-100 rounded">
                    <div
                      className="h-full bg-green-700 rounded"
                      style={{ width: `${((v.buy / v.total) * 100).toFixed(0)}%` }}
                    />
                  </div>
                  <span className="text-gray-400 min-w-[28px] text-right">
                    {v.buy}/{v.total}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
