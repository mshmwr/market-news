# MN-004 Design Doc — Signals Display Port to Next.js

**Ticket:** MN-004  
**Phases:** 1 (Data fetching + types) → 2 (Signals UI) → 3 (News UI) → 4 (Translate + theme-color) → 5 (README re-label)  
**Architect:** Senior Architect  
**Date:** 2026-05-09  
**Status:** Ready for Engineer

---

## 0 Pre-Implementation Design Challenge Sheet

| Dimension | Challenge | Verdict |
|-----------|-----------|---------|
| Interface contracts | Next.js Server Component passes fetched data to Client Components as props; serialization must be plain JSON (no Date objects, no class instances) | Accept — all data types are primitives (string, number, boolean, null); TypeScript interfaces enforce this |
| Refactorability | If data source changes from raw.githubusercontent.com to an internal API route, fetch helpers must be swapped in one place | Accept — `fetchSignals()` / `fetchNews()` in `frontend/lib/data.ts` are the single fetch boundary; no inline fetch calls in components |
| Test seam | Signal card filter state lives in client-side React; testable via Playwright with role selectors | Accept — all interactive state in Client Components; server-rendered data is prop-drilled; both layers testable independently |
| Blast radius | `frontend/app/page.tsx` replacement touches only the home route; no other Next.js routes exist | Accept — single route; no shared route-level layout changes beyond adding one `<meta>` tag |
| Spec vs codebase drift | MN-003 scaffold has no component library; all component paths in this design are new; no rename risk | Accept — `frontend/components/` directory is empty except `realtime/types.ts`; all new files |

All 5 dimensions: accept.

---

## 1 Technical Option Analysis

### Decision 1: Data fetch location — Server Component vs API route

**Option A (conservative):** Create `/api/signals` and `/api/news` API routes with ISR; page fetches from its own API.  
**Trade-off:** Two-hop: Client → Next.js API → GitHub CDN. Unnecessary indirection when the Server Component can fetch directly.

**Option B (middle ground — CHOSEN):** Fetch directly in the Server Component (`frontend/app/page.tsx`) from `raw.githubusercontent.com` with `fetch(..., { next: { revalidate: 300 } })`.  
**When to use:** When the page is the only consumer; data is not shared across routes.  
**Trade-off:** Fetch options are co-located with the page; if a second route needs signals, extract to a shared helper. Currently single-route — acceptable.  
**Recommendation:** Simplest path; one Server Component, two fetch calls, both ISR-cached. API routes added only when a second consumer appears.

**Chosen:** Option B. Rationale: BQ-004-01 mandates raw.githubusercontent.com with ISR `revalidate: 300`; API routes add indirection with no current benefit.

---

### Decision 2: Client / Server Component split

**Option A (conservative):** Make `page.tsx` fully a Client Component with `useEffect` fetching.  
**Trade-off:** Loses ISR; data not pre-rendered; slower initial paint; duplicates GH Pages' client-only approach.

**Option B (middle ground — CHOSEN):** `page.tsx` is a Server Component (default in App Router). Interactive sub-components (TabNav, SignalFilters, SignalSort, SignalCard expand/collapse, NewsFilters) are Client Components marked with `'use client'`.  
**When to use:** Standard App Router pattern for data-driven pages.  
**Trade-off:** Props passed from Server to Client must be serializable (primitives only — no Date, no functions). `generated_at` is a string; components format it client-side.

**Chosen:** Option B. Rationale: Maximizes ISR benefit (HTML pre-rendered with data); only interactive leaf nodes are Client Components.

---

### Decision 3: State management for tab + filter state

**Option A (conservative):** URL search params (`?tab=signals&cat=台股`).  
**Trade-off:** Shareable links; browser back/forward works. Adds URL manipulation complexity; AC-MN004-NEWS-02 only requires session-persistence, not URL persistence.

**Option B (middle ground — CHOSEN):** React `useState` in a Client Component wrapper at the page level. Tab and filter state live in a single `<PageClient>` component that receives server-fetched data as props.  
**When to use:** Session-only state (no need for URL sharing or back button).  
**Trade-off:** State lost on hard reload; acceptable for filter/tab preferences.

**Chosen:** Option B. Rationale: Minimal complexity; matches AC requirement (session-persistence only); simpler than URL state for the current feature scope.

---

## 2 Component Tree

```
frontend/app/page.tsx                  [SERVER COMPONENT — ISR revalidate:300]
  └── fetches: signals.json, news.json from raw.githubusercontent.com
  └── renders: <PageClient signals={...} news={...} generatedAt={...} />

frontend/components/layout/PageClient.tsx  ['use client' — owns all interactive state]
  ├── state: currentTab, newsFilter (Set<string>), signalActionFilter, signalSort, sigCatFilter (Set<string>)
  ├── renders (tab=news):
  │   ├── <TabNav />                   [tab switching buttons]
  │   ├── <NewsFilters />              [4 category pills]
  │   └── <NewsList articles={filtered} />
  │       └── <NewsItem />*            [article row — no state]
  └── renders (tab=signals):
      ├── <TabNav />
      ├── <SignalFilters />            [BUY/HOLD/SELL + category pills]
      ├── <SignalSort />               [confidence sort button]
      ├── <MarketOverview />           [BUY/HOLD/SELL bar, index panel, sector panel]
      └── <SignalList signals={sorted+filtered} />
          └── <SignalCard />*          [expandable card — local expand state]

frontend/app/layout.tsx                [ROOT LAYOUT — add theme-color meta]
```

**Props interface summary:**

| Component | Key Props | Client? |
|-----------|-----------|---------|
| `PageClient` | `signals: SignalResult[]`, `news: NewsItem[]`, `generatedAt: string \| null` | Yes |
| `TabNav` | `currentTab`, `onTabChange` | Yes (via PageClient) |
| `NewsFilters` | `selected: Set<string>`, `onChange` | Yes |
| `NewsList` | `articles: NewsItem[]` | No (pure display) |
| `NewsItem` | `article: NewsItem` | No |
| `SignalFilters` | `actionFilter`, `sigCatFilter`, `onActionChange`, `onCatChange` | Yes |
| `SignalSort` | `sort: 'desc' \| 'asc' \| 'none'`, `onToggle` | Yes |
| `MarketOverview` | `signals: SignalResult[]` | No (computed display) |
| `SignalCard` | `signal: SignalResult` | Yes (expand state) |

---

## 3 TypeScript Types (`frontend/lib/types.ts`)

```typescript
export type SignalAction = 'BUY' | 'HOLD' | 'SELL';

export interface TechnicalData {
  rsi?: number;
  macd_line?: number;
  macd_signal?: number;
  macd_histogram?: number;
  ma50?: number;
  volume_ratio?: number;
}

export interface FundamentalsData {
  pe_ratio?: number;
  forward_pe?: number;
  price_to_book?: number;
  revenue_growth?: number;
  profit_margin?: number;
  debt_to_equity?: number;
  target_mean_price?: number;
  current_price?: number;
  fifty_two_week_low?: number;
  fifty_two_week_high?: number;
  trailing_eps?: number;
  book_value?: number;
  peg_ratio?: number;
  short_name?: string;
  recommendation_key?: string;
  number_of_analyst_opinions?: number;
  sector?: string;
}

export interface UndervaluationData {
  upside_pct?: number;
  week52_position_pct?: number;
  graham_number?: number;
  price_vs_graham_pct?: number;
  relative_pe?: number;
  sector_pe_avg?: number;
  peg_ratio?: number;
}

export interface SourceItem {
  title?: string;
  url: string;
  published_ts?: number;
}

export interface SocialPost {
  title?: string;
  url: string;
}

export interface SignalResult {
  ticker: string;
  name?: string;
  signal: SignalAction;
  confidence: number;
  rationale: string;
  bull_case?: string;
  bear_case?: string;
  sources?: SourceItem[];
  social_posts?: SocialPost[];
  technical_data?: TechnicalData;
  fundamentals_data?: FundamentalsData;
  undervaluation_data?: UndervaluationData;
}

export interface SignalsResponse {
  generated_at: string;
  signals: SignalResult[];
}

export interface NewsItem {
  title: string;
  description?: string;
  link: string;
  source: string;
  category: '台股' | '美股' | '加密貨幣' | '宏觀';
  published_ts: number;
}
```

---

## 4 Data Fetch Layer (`frontend/lib/data.ts`)

```typescript
import type { SignalsResponse, NewsItem } from './types';

const RAW_BASE = 'https://raw.githubusercontent.com/mshmwr/market-news/main/docs';
const REVALIDATE = 300; // 5 minutes — signals update daily, news every 30 min

export async function fetchSignals(): Promise<SignalsResponse | null> {
  try {
    const res = await fetch(`${RAW_BASE}/signals.json`, {
      next: { revalidate: REVALIDATE },
    });
    if (!res.ok) return null;
    return (await res.json()) as SignalsResponse;
  } catch {
    return null;
  }
}

export async function fetchNews(): Promise<NewsItem[]> {
  try {
    const res = await fetch(`${RAW_BASE}/news.json`, {
      next: { revalidate: REVALIDATE },
    });
    if (!res.ok) return [];
    return (await res.json()) as NewsItem[];
  } catch {
    return [];
  }
}
```

---

## 5 TICKER_CATEGORY Map

Ported from `docs/index.html` (lines 371–381). Must be a shared constant in `frontend/lib/constants.ts`:

```typescript
export const TICKER_CATEGORY: Record<string, string> = {
  NVDA: '半導體', AMD: '半導體', ASML: '半導體', INTC: '半導體',
  TSM: '半導體', MU: '半導體', SNDK: '半導體', LWLG: '半導體', '2454.TW': '半導體',
  LITE: '光電', '2308.TW': '電子',
  GOOGL: 'AI/雲端', MSFT: 'AI/雲端', AMZN: 'AI/雲端', META: 'AI/雲端', PLTR: 'AI/雲端',
  CRWD: '資安', TSLA: 'EV', ONDS: '無人機',
  'BTC-USD': '加密貨幣', 'ETH-USD': '加密貨幣',
  SPY: 'ETF', QQQ: 'ETF', SOXX: 'ETF', IBB: 'ETF',
  '^GSPC': '指數', '^VIX': '指數', '^TNX': '指數',
  NOK: '通訊', 'CL=F': '原物料',
};

export const NEWS_CATEGORIES = ['台股', '美股', '加密貨幣', '宏觀'] as const;
export const SIG_CATS = [...new Set(Object.values(TICKER_CATEGORY))].sort();
```

---

## 6 Signal Card Visual Spec

Ported from production CSS (faithful port per BQ-004-04):

| State | Left border color | Badge bg | Badge text |
|-------|------------------|----------|------------|
| BUY | `#2e7d32` | `#e8f5e9` | `#2e7d32` |
| HOLD | `#f9a825` | `#fff8e1` | `#f9a825` |
| SELL | `#c62828` | `#ffebee` | `#c62828` |

Card structure (collapsed):
- Category badge (sector tag, 10px, colored per TICKER_CATEGORY)
- Ticker symbol (14px, bold)
- Company name (11px, muted)
- Confidence percentage (12px)
- Signal badge (BUY/HOLD/SELL, 11px, colored)

Card structure (expanded — on click/hover):
- Rationale paragraph (12px, line-height 1.5)
- Bull/bear debate rows (if `bull_case`/`bear_case` present)
- Technical data chips: RSI, MACD, MA50, volume ratio
- Fundamentals chips: PE, forward PE, P/B, revenue growth, profit margin, debt/equity, analyst rating
- Reference news links (11px, truncated)
- Reddit posts (if `social_posts` present)

Expand/collapse logic:
- Desktop (hover: hover): `mouseenter` → expand, `mouseleave` → collapse
- Mobile (touch): `click` → toggle
- `window.matchMedia` only in event handler or `useEffect` (not SSR-safe at module scope)

---

## 7 Market Overview Panel

Computed from `signals` array at render time (no separate fetch):

1. **Sentiment bar**: count BUY/HOLD/SELL among non-index stocks; render three colored flex segments
2. **Index panel**: find `^VIX`, `SPY`, `QQQ`, `^TNX` in signals array; display VIX value with color threshold (`>30` red, `>20` orange, `>15` amber, else green); SPY/QQQ show signal badge
3. **Sector BUY heat**: group non-index stocks by category; compute buy/total ratio; show top-5 categories

Hidden when `signals` array is empty.

---

## 8 Translate Button

Client Component in header area. On click: opens `https://market-news-sigma-vercel-app.translate.goog/?_x_tr_sl=auto&_x_tr_tl=zh-TW&_x_tr_hl=zh-TW` in new tab. If `location.hostname.endsWith('.translate.goog')` is true (user already on translated page), button is hidden.

Must be a Client Component (accesses `window.location.hostname`).

---

## 9 File Change List

| File | Action | Notes |
|------|--------|-------|
| `frontend/lib/types.ts` | Create | SignalResult, NewsItem, SignalsResponse interfaces |
| `frontend/lib/data.ts` | Create | fetchSignals(), fetchNews() with ISR revalidate:300 |
| `frontend/lib/constants.ts` | Create | TICKER_CATEGORY, NEWS_CATEGORIES, SIG_CATS |
| `frontend/app/page.tsx` | Modify (replace) | Server Component; ISR fetch; renders PageClient |
| `frontend/app/layout.tsx` | Modify | Add `<meta name="theme-color" content="#1d1d1f">` |
| `frontend/app/globals.css` | Modify | Add signal card CSS vars / Tailwind safelist if needed |
| `frontend/components/layout/PageClient.tsx` | Create | 'use client'; owns all interactive state |
| `frontend/components/layout/TabNav.tsx` | Create | Tab switching; called from PageClient |
| `frontend/components/layout/TranslateButton.tsx` | Create | 'use client'; translate.goog anchor |
| `frontend/components/signals/SignalCard.tsx` | Create | 'use client'; expandable card |
| `frontend/components/signals/MarketOverview.tsx` | Create | Server-renderable display component |
| `frontend/components/signals/SignalFilters.tsx` | Create | 'use client'; BUY/HOLD/SELL + category pills |
| `frontend/components/signals/SignalSort.tsx` | Create | 'use client'; sort toggle button |
| `frontend/components/news/NewsItem.tsx` | Create | Pure display component |
| `frontend/components/news/NewsFilters.tsx` | Create | 'use client'; 4-category pills |
| `README.md` | Modify | Re-label: Vercel=Production, GH Pages=Legacy |
| `ssot/system-overview.md` | Modify | Update Data Flow diagram + Changelog for MN-004 |

---

## 10 Implementation Order

### Phase 1 — Types + data fetch (no UI changes)

1. Create `frontend/lib/types.ts` — all TypeScript interfaces
2. Create `frontend/lib/constants.ts` — TICKER_CATEGORY, NEWS_CATEGORIES, SIG_CATS
3. Create `frontend/lib/data.ts` — fetchSignals(), fetchNews()
4. Run `npx tsc --noEmit` — must exit 0

### Phase 2 — Signals section UI

5. Create `frontend/components/signals/MarketOverview.tsx`
6. Create `frontend/components/signals/SignalCard.tsx` ('use client')
7. Create `frontend/components/signals/SignalFilters.tsx` ('use client')
8. Create `frontend/components/signals/SignalSort.tsx` ('use client')
9. Run `npx tsc --noEmit`

### Phase 3 — News section UI

10. Create `frontend/components/news/NewsItem.tsx`
11. Create `frontend/components/news/NewsFilters.tsx` ('use client')
12. Run `npx tsc --noEmit`

### Phase 4 — Page client + layout integration

13. Create `frontend/components/layout/TranslateButton.tsx` ('use client')
14. Create `frontend/components/layout/PageClient.tsx` ('use client') — integrate all components
15. Modify `frontend/app/page.tsx` — ISR fetch + render PageClient
16. Modify `frontend/app/layout.tsx` — add theme-color meta
17. Run `npx tsc --noEmit` then `npm run build`

### Phase 5 — README + ssot update

18. Modify `README.md`
19. Modify `ssot/system-overview.md`

---

## 11 Route Impact Table

| Route | Component | Visual change | Shared primitive touched |
|-------|-----------|---------------|--------------------------|
| `/` (home) | `page.tsx` | Yes — full replace of placeholder shell | theme-color meta (new, no existing consumer) |

Single route; no shared primitive that other routes consume.

---

## 12 Boundary Contracts / AC Compliance Map

| AC | Design Section | Engineer signal |
|----|---------------|-----------------|
| AC-MN004-DATA-01 | §3 types.ts | All fields typed; `npx tsc --noEmit` exit 0 |
| AC-MN004-DATA-02 | §4 data.ts | `next: { revalidate: 300 }` in each fetch call |
| AC-MN004-DATA-03 | §4 data.ts | try/catch returns null/[] on any error |
| AC-MN004-SIG-01 | §6 + PageClient | generated_at formatted with locale string; Invalid Date guard |
| AC-MN004-SIG-02 | §6 visual spec table | Tailwind or CSS class per signal action; JSX text nodes only |
| AC-MN004-SIG-03 | §2 PageClient state | signalActionFilter state in PageClient; filtered list passed to SignalCard |
| AC-MN004-SIG-04 | §2 SignalSort | sort: 'desc'|'asc'|'none' cycle; label updates |
| AC-MN004-SIG-05 | §6 expand/collapse | 'use client'; matchMedia in event handler only |
| AC-MN004-SIG-06 | §7 MarketOverview | rendered only when signals.length > 0 |
| AC-MN004-NEWS-01 | §2 NewsItem | target="_blank" rel="noopener noreferrer" |
| AC-MN004-NEWS-02 | §2 PageClient state | newsFilter Set<string> persists across tab switch |
| AC-MN004-NEWS-03 | §4 data.ts | fetchNews() returns [] on error; news section shows 載入失敗 |
| AC-MN004-NEWS-04 | §4 data.ts | ISR fetch in Server Component; npm run build exit 0 |
| AC-MN004-TRANSLATE-01 | §8 TranslateButton | theme-color meta in layout.tsx; translate anchor in header |
| AC-MN004-RETIRE-01 | §9 README | Vercel=Production, GH Pages=Legacy text |
| AC-MN004-RETIRE-02 | scope | docs/index.html untouched |
