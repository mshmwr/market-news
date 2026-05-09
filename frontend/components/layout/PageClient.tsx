'use client';

// MN-004: Client-side interactive shell.
// Receives server-fetched data as props (all plain JSON — no Date objects).
// Owns: currentTab, newsFilter, signalActionFilter, signalSort, sigCatFilter.
// Tab/filter state persists across tab switches (AC-MN004-NEWS-02 requirement).

import { useState } from 'react';
import type { SignalResult, NewsItem as NewsItemType } from '@/lib/types';
import { NEWS_CATEGORIES, SIG_CATS } from '@/lib/constants';
import { TICKER_CATEGORY } from '@/lib/constants';
import TabNav, { type TabId } from '@/components/layout/TabNav';
import TranslateButton from '@/components/layout/TranslateButton';
import MarketOverview from '@/components/signals/MarketOverview';
import SignalCard from '@/components/signals/SignalCard';
import SignalFilters from '@/components/signals/SignalFilters';
import SignalSort, { type SortOrder } from '@/components/signals/SignalSort';
import NewsItemRow from '@/components/news/NewsItem';
import NewsFilters from '@/components/news/NewsFilters';

type ActionFilter = 'all' | 'BUY' | 'HOLD' | 'SELL';

interface Props {
  signals: SignalResult[];
  news: NewsItemType[];
  generatedAt: string | null;
  newsError: boolean;
  digestHtml: string | null;
}

function formatGeneratedAt(raw: string | null): string {
  if (!raw) return '';
  const d = new Date(raw);
  if (isNaN(d.getTime())) return ''; // AC-MN004-SIG-01 — never show "Invalid Date"
  return '訊號更新於 ' + d.toLocaleString('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatNewsUpdated(news: NewsItemType[]): string {
  if (news.length === 0) return '';
  const latestTs = news[0].published_ts;
  if (!latestTs) return '';
  return '更新於 ' + new Date(latestTs * 1000).toLocaleString('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function PageClient({ signals, news, generatedAt, newsError, digestHtml }: Props) {
  const [currentTab, setCurrentTab] = useState<TabId>('news');

  // News filter — persists across tab switches
  const [newsFilter, setNewsFilter] = useState<Set<string>>(new Set(NEWS_CATEGORIES));

  // Signal filters
  const [signalActionFilter, setSignalActionFilter] = useState<ActionFilter>('all');
  const [signalSort, setSignalSort] = useState<SortOrder>('desc');
  const [sigCatFilter, setSigCatFilter] = useState<Set<string>>(new Set(SIG_CATS));

  // --- News filter handlers ---
  function handleNewsCatChange(cat: string) {
    setNewsFilter((prev) => {
      const next = new Set(prev);
      if (cat === '全部') {
        NEWS_CATEGORIES.forEach((c) => next.add(c));
      } else if (cat === '取消全選') {
        next.clear();
      } else {
        next.has(cat) ? next.delete(cat) : next.add(cat);
        if (next.size === 0) NEWS_CATEGORIES.forEach((c) => next.add(c));
      }
      return next;
    });
  }

  // --- Signal cat filter handlers ---
  function handleSigCatChange(cat: string) {
    setSigCatFilter((prev) => {
      const next = new Set(prev);
      if (cat === '全部') {
        SIG_CATS.forEach((c) => next.add(c));
      } else if (cat === '取消全選') {
        next.clear();
      } else {
        next.has(cat) ? next.delete(cat) : next.add(cat);
      }
      return next;
    });
  }

  function handleSortToggle() {
    setSignalSort((s) => (s === 'desc' ? 'asc' : s === 'asc' ? 'none' : 'desc'));
  }

  // --- Derived signal list ---
  let filteredSignals = signals.filter(
    (s) => sigCatFilter.has(TICKER_CATEGORY[s.ticker] ?? ''),
  );
  if (signalActionFilter !== 'all') {
    filteredSignals = filteredSignals.filter((s) => s.signal === signalActionFilter);
  }
  if (signalSort === 'desc') {
    filteredSignals = [...filteredSignals].sort((a, b) => b.confidence - a.confidence);
  } else if (signalSort === 'asc') {
    filteredSignals = [...filteredSignals].sort((a, b) => a.confidence - b.confidence);
  }

  // --- Derived news list ---
  const filteredNews = news.filter((a) => newsFilter.has(a.category));

  const generatedAtFormatted = formatGeneratedAt(generatedAt);
  const newsUpdatedFormatted = formatNewsUpdated(news);

  return (
    <div className="min-h-screen bg-[#f5f5f7] text-gray-900">
      {/* Sticky header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 sticky top-0 z-10">
        <div className="flex justify-between items-baseline mb-3">
          <h1 className="text-[18px] font-semibold">每日市場新聞</h1>
          <div className="flex gap-2 items-center">
            <TranslateButton />
          </div>
        </div>
        <div className="mb-3">
          <TabNav currentTab={currentTab} onTabChange={setCurrentTab} />
        </div>
        {/* News filters — visible only on news tab */}
        {currentTab === 'news' && (
          <NewsFilters selected={newsFilter} onCatChange={handleNewsCatChange} />
        )}
      </header>

      <main className="max-w-[800px] mx-auto mt-6 px-4 pb-12">
        {/* === SIGNALS TAB === */}
        {currentTab === 'signals' && (
          <section>
            <div className="flex items-baseline gap-3 mb-3">
              <h2 className="text-[16px] font-semibold text-gray-900">股票訊號</h2>
              <SignalSort sort={signalSort} onToggle={handleSortToggle} />
              {generatedAtFormatted && (
                <span className="text-[12px] text-gray-400">{generatedAtFormatted}</span>
              )}
            </div>

            <div className="mb-3">
              <SignalFilters
                actionFilter={signalActionFilter}
                sigCatFilter={sigCatFilter}
                onActionChange={setSignalActionFilter}
                onCatChange={handleSigCatChange}
              />
            </div>

            {signals.length === 0 ? (
              <p className="text-[14px] text-gray-400 py-4">訊號暫未生成</p>
            ) : (
              <>
                <p className="text-[11px] text-gray-400 mb-2.5 leading-relaxed">
                  信心度 = AI 對訊號方向的把握程度（0–100%）；數值越高代表新聞、技術面、基本面指向越一致。點擊卡片可展開詳細數據。
                </p>
                <MarketOverview signals={signals} />
                <div className="flex flex-col gap-2.5">
                  {filteredSignals.map((s) => (
                    <SignalCard key={s.ticker} signal={s} />
                  ))}
                  {filteredSignals.length === 0 && (
                    <p className="text-[14px] text-gray-400 py-2">沒有符合條件的訊號</p>
                  )}
                </div>
              </>
            )}
          </section>
        )}

        {/* === NEWS TAB === */}
        {currentTab === 'news' && (
          <section>
            <div className="flex items-center gap-2 mb-3">
              {newsUpdatedFormatted && (
                <span className="text-[12px] text-gray-400">{newsUpdatedFormatted}</span>
              )}
            </div>

            {newsError ? (
              <p className="text-[14px] text-gray-400 py-4">載入失敗</p>
            ) : filteredNews.length === 0 ? (
              <p className="text-[14px] text-gray-400 py-4">沒有符合條件的新聞</p>
            ) : (
              <div className="flex flex-col gap-px bg-gray-200 rounded-xl overflow-hidden">
                {filteredNews.map((article, i) => (
                  <NewsItemRow key={`${article.link}-${i}`} article={article} />
                ))}
              </div>
            )}
          </section>
        )}

        {/* === DIGEST TAB === */}
        {currentTab === 'digest' && (
          <section>
            {digestHtml ? (
              <div
                className="bg-white rounded-xl p-2 sm:p-4 overflow-hidden"
                dangerouslySetInnerHTML={{ __html: digestHtml }}
              />
            ) : (
              <p className="text-[14px] text-gray-400 py-4">
                電子報尚未產生 / Newsletter not generated yet.
              </p>
            )}
          </section>
        )}
      </main>
    </div>
  );
}
