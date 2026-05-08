---
id: MN-004
title: Signals Display Port to Next.js
status: open
created: 2026-05-09
type: feature
priority: high
size: L
visual-delta: yes
content-delta: yes
design-locked: false
qa-early-consultation: pending
worktree: .claude/worktrees/MN-004-signals-port-nextjs
branch: MN-004-signals-port-nextjs
dependencies: MN-003 (closed 2026-05-09)
---

## Summary

Port the full production display from `docs/index.html` to the Next.js app under `frontend/`. This is the feature-parity gate that allows GH Pages (`docs/index.html`) to retire and Vercel to become the primary production URL. Data sources are the existing `docs/signals.json` and `docs/news.json` JSON files updated by GitHub Actions cron; the Next.js app reads them via ISR so updates propagate without a redeploy.

## Scope

**Source of truth for production behaviour:** `docs/index.html` + `docs/signals.json` + `docs/news.json`.

**Data schemas confirmed from live JSON:**

- `docs/signals.json`: `{ generated_at: ISO8601, signals: [{ ticker, name, signal, confidence, rationale, bull_case?, bear_case?, sources[], social_posts[], technical_data{rsi,macd_line,macd_signal,macd_histogram,ma50,volume_ratio}, fundamentals_data{pe_ratio,forward_pe,price_to_book,revenue_growth,profit_margin,debt_to_equity,target_mean_price,current_price,fifty_two_week_low,fifty_two_week_high,trailing_eps,book_value,peg_ratio,short_name,recommendation_key,number_of_analyst_opinions,sector}, undervaluation_data{upside_pct,week52_position_pct,graham_number,price_vs_graham_pct,relative_pe,sector_pe_avg,peg_ratio} }] }`
- `docs/news.json`: `[{ title, description, link, source, category, published_ts }]`
- `docs/screen-latest.json`: `{ date, candidates: [{ ticker, name, score, reason }] }` (screener card — PENDING BQ-004-05 for scope decision)

**Files to create (frontend/src):**
- `frontend/app/page.tsx` — replace placeholder; main page with tabs
- `frontend/app/api/signals/route.ts` — ISR-backed data route (or direct fetch in page; see BQ-004-01)
- `frontend/app/api/news/route.ts` — ISR-backed data route (or direct fetch; see BQ-004-01)
- `frontend/components/signals/` — SignalCard, MarketOverview, SignalFilters, SignalSort
- `frontend/components/news/` — NewsItem, NewsFilters
- `frontend/components/layout/` — TabNav, Header, Toast
- `frontend/lib/types.ts` — shared TypeScript types derived from confirmed JSON schemas

**Files to modify:**
- `frontend/app/layout.tsx` — add PWA metadata (manifest link, theme-color) if BQ-004-03 resolves to "port PWA"
- `frontend/app/globals.css` — extend with any global CSS not expressible in Tailwind

**Files NOT modified in this ticket:**
- All Python files, `.github/workflows/`, `docs/index.html` (stays live during MN-004 development)
- `docs/signals.json`, `docs/news.json` (write target of Actions; read-only for Next.js)
- Auth, paywall, WebSocket (SP-prefix scope / future ticket)

**Out of scope:**
- Real-time price feed (WebSocket/polling — `RealtimePrice` stub; deferred per MN-003 BQ-003-03)
- Feedback button Firebase integration (SP scope or separate ticket)
- Google Analytics / tracking

## Blocking Questions

**BQ-004-01 — Data fetching strategy** [OPEN — requires user answer]
How does the Next.js app read `signals.json` and `news.json`?

- **Option A (recommended): `raw.githubusercontent.com` fetch at request time with ISR `revalidate`**
  Next.js Server Component fetches `https://raw.githubusercontent.com/mshmwr/market-news/main/docs/signals.json` (public repo, no auth). Next.js caches the response and revalidates every N seconds. When GitHub Actions commits updated JSON, the next revalidation cycle serves fresh data without rebuild or redeploy. Clean separation: the JSON files live in the repo as they do today; no copy step needed.
  Risk: GitHub CDN latency (~200 ms); cache-miss cold start may add latency on first visitor after revalidation window. `revalidate: 300` (5 min) recommended — signals update once daily, news every 30 min.

- **Option B: Copy JSON into `frontend/public/` on each Actions run**
  Add a step to `update-news.yml` and `update-signals.yml` that copies `docs/*.json` → `frontend/public/*.json` and commits. Next.js serves them as static files from Vercel CDN. Fastest client-side fetch; no external HTTP call from server. Risk: doubles commit noise; `git diff --stat` on every news run touches two directories; complicates the Actions workflow.

- **Option C: Relative path read at build time (`fs.readFileSync`)**
  Works only for `next build` triggered on JSON change — requires a Vercel build hook or manual redeploy whenever JSON updates. Breaks the "no redeploy" ISR goal. Not recommended.

PM recommendation: **Option A** — cleanest architecture, zero Actions workflow change, standard Next.js ISR pattern.

---

**BQ-004-02 — Manual refresh button** [OPEN — requires user answer]
The production HTML has a 🔄 button for news (triggers Cloudflare Worker at `market-news-trigger.rsp93050420.workers.dev`) and a 🔄 button for signals (triggers Worker at `/signals` endpoint), both with polling until fresh data appears.

Options:
- **Option A (recommended): Drop the manual refresh buttons entirely**
  Next.js ISR auto-revalidates on a timer; users who want fresh data can hard-reload (CMD+Shift+R). The Worker is a workaround for GH Pages' inability to push updates — unnecessary on Vercel ISR. Simpler, no Cloudflare dependency.
- **Option B: Port the refresh buttons**
  Client component calls Worker URL via `fetch` POST, then polls the data API route until `generated_at` changes. Preserves power-user feature. Requires Client Component wrapper around a mostly-server-rendered page — adds complexity.

PM recommendation: **Option A** — drop the buttons. Vercel ISR makes them redundant; if user wants them back, a separate ticket is appropriate.

---

**BQ-004-03 — PWA manifest + service worker** [OPEN — requires user answer]
`docs/index.html` registers a service worker (`sw.js`) and links `manifest.json` (PWA install, home-screen icon, theme color). GH Pages serves these as static files.

Options:
- **Option A (recommended): Defer PWA to a later ticket**
  Next.js PWA integration (e.g. `next-pwa` or manual `public/sw.js`) adds scope and edge cases (caching strategy, iOS quirks). MN-004's goal is feature parity on the data/UI layer; PWA is a separate progressive enhancement.
- **Option B: Port PWA in MN-004**
  Add `manifest.json` + `public/sw.js` (or `next-pwa`) in this ticket. Adds ~1 phase of work.

PM recommendation: **Option A** — defer PWA. Add meta `theme-color` and `<link rel="manifest">` stub only; full SW registration in a dedicated MN-005.

---

**BQ-004-04 — News category tab layout vs. redesign** [OPEN — requires user answer]
Production uses 4 pill-filter buttons (台股/美股/加密貨幣/宏觀) on the news tab, and separate category-filter pills on the signals tab (semiconductor, AI/cloud, EV, etc.). The tab itself is a two-tab bar (新聞 / 股票訊號).

Options:
- **Option A (recommended): Faithful port — preserve identical tab/filter UX**
  Exactly match the production layout: 2 tabs, same 4 news categories, same signal categories derived from TICKER_CATEGORY map. Only difference is React components instead of vanilla JS.
- **Option B: Redesign / simplify**
  Collapse tabs, redesign filter layout, etc. Increases scope substantially; risk of parity regression.

PM recommendation: **Option A** — faithful port. Redesign is a separate ticket after Vercel is production.

---

**BQ-004-05 — Screener card (`screen-latest.json`)** [OPEN — requires user answer]
`docs/index.html` fetches `screen-latest.json` (undervaluation screener candidates with rank, ticker, name, score, reason). The file is produced by a separate workflow not yet ticketed.

Options:
- **Option A (recommended): Exclude screener from MN-004 scope**
  The screener JSON source is not produced by any MN-series workflow — it's a future feature. `docs/index.html` already handles 404 gracefully (screener card hidden). MN-004 Next.js page should do the same: if `screen-latest.json` fetch fails, screener card is simply not rendered. No dedicated screener component needed.
- **Option B: Port screener card in MN-004**
  Build the ScreenerCard component and fetch `screen-latest.json`. Risk: creates dependency on a file that may not exist on Vercel at all (it lives in `docs/`, not `frontend/public/`).

PM recommendation: **Option A** — exclude screener. Port it when the screener workflow is formalized.

---

**BQ-004-06 — GH Pages retirement timing** [OPEN — requires user answer]
MN-003 set the retirement gate as "MN-004 reaching feature parity." Once MN-004 merges, when does `docs/index.html` officially retire?

Options:
- **Option A: Retire immediately on MN-004 merge**
  Add a Phase in MN-004 that updates README to label Vercel as "Production" and GH Pages as "Archived / Legacy". `docs/index.html` stays in the repo (no deletion) but is no longer the canonical production URL.
- **Option B (recommended): Retire only after user observes parity for N days**
  MN-004 ships Vercel as production but keeps GH Pages running in parallel. User monitors both for N days (suggested: 7). PM opens a separate MN-005 retirement ticket at user's explicit approval. Lower risk — GH Pages is a zero-cost fallback during the observation window.

PM recommendation: **Option B** — hold retirement for user observation. Less risky; GH Pages costs nothing to keep. Include a Phase in MN-004 that re-labels README (Vercel = "Production", GH Pages = "Legacy / retiring") but does NOT remove `docs/index.html`.

---

**BQ-004-07 — Google Translate proxy link** [OPEN — requires user answer]
Production HTML has a 🌐 翻譯 button that opens the page via Google Translate proxy URL.

Options:
- **Option A (recommended): Port the translate button**
  Simple: one `<a>` that opens `https://market-news-sigma-vercel-app.translate.goog/...?_x_tr_sl=auto&...`. Verified the pattern works for Vercel URLs. Low effort, preserves feature.
- **Option B: Drop the translate button**
  Modern browsers offer native translation; the button is a convenience shortcut.

PM recommendation: **Option A** — port it; it's a one-liner anchor, no risk.

## Acceptance Criteria

**Note: ACs below are drafted for BQ recommendations (A or B as noted above). ACs will be revised after BQ answers confirmed.**

### Phase 1 — Data fetching + JSON API layer

**AC-MN004-DATA-01**
- Given: Next.js app is deployed on Vercel with no `.env.local` override
- When: the page server-renders
- Then: `signals.json` data is fetched from `https://raw.githubusercontent.com/mshmwr/market-news/main/docs/signals.json` (or project-internal path, per BQ-004-01 ruling) with ISR `revalidate: 300`; the fetch does not block at build time and does not require any Vercel env var

**AC-MN004-DATA-02**
- Given: `signals.json` fetch returns a valid JSON object
- When: the page renders
- Then: `generated_at` (ISO8601 string), `signals` (array of signal objects) are parsed and available to child components; each signal object has at minimum `ticker`, `signal`, `confidence`, `rationale` fields accessible without TypeScript error

**AC-MN004-DATA-03**
- Given: either `signals.json` or `news.json` fetch returns a non-2xx response or throws a network error
- When: the page renders
- Then: the affected section displays a placeholder ("訊號暫未生成" for signals; loading error state for news); the other section continues to render normally; no uncaught runtime exception; `npx tsc --noEmit` passes

### Phase 2 — Signals section UI

**AC-MN004-SIG-01**
- Given: `signals.json` is valid and contains at least one signal
- When: user selects the "股票訊號" tab
- Then: a "股票訊號" heading is visible; below it the `generated_at` timestamp is displayed formatted as "訊號更新於 YYYY/MM/DD HH:MM" (Taiwan locale); below that the signal cards grid renders

**AC-MN004-SIG-02**
- Given: a signal card for ticker X is rendered
- When: signal value is BUY, HOLD, or SELL
- Then: the card displays ticker symbol, company name (if present in `name` field), confidence percentage, signal badge; the card left-border accent color is green (`#2e7d32`) for BUY, amber (`#f9a825`) for HOLD, red (`#c62828`) for SELL; ticker text is set via safe DOM text assignment (not innerHTML interpolation)

**AC-MN004-SIG-03**
- Given: the signals tab is active and at least one signal is loaded
- When: user clicks the BUY / HOLD / SELL / 全部 filter button
- Then: only cards matching the selected signal type are shown; all other cards are removed from the rendered output; clicking 全部 restores all cards

**AC-MN004-SIG-04**
- Given: signals are displayed
- When: user clicks the "信心度 ↓" sort button
- Then: cards are sorted descending by confidence percentage; clicking again sorts ascending; clicking a third time removes sort (original order); button label updates to reflect current sort state

**AC-MN004-SIG-05**
- Given: a signal card is rendered
- When: user clicks (touch) or hovers (pointer device) the card
- Then: the card expands to show rationale text, bull/bear debate rows (if `bull_case`/`bear_case` present), technical data chips (RSI, MACD, MA50, volume ratio), fundamentals chips (PE, forward PE, P/B, revenue growth, profit margin, debt/equity, analyst rating), and reference news links; collapsing hides the expanded content

**AC-MN004-SIG-06**
- Given: the Market Overview panel is computed from loaded signals
- When: signals tab renders
- Then: the panel shows overall BUY/HOLD/SELL counts + percentage bar, key index signals (VIX value with color coding, SPY/QQQ signal badges), and top sector BUY counts; the panel is hidden if the signal array is empty

### Phase 3 — News section UI

**AC-MN004-NEWS-01**
- Given: `news.json` is valid and contains at least one article
- When: the "新聞" tab is active (default tab on load)
- Then: the news section renders articles; the most-recent article's `published_ts` is formatted and shown as "更新於 YYYY/MM/DD HH:MM" (Taiwan locale); each article shows title (as link), source badge, category badge, relative time string

**AC-MN004-NEWS-02**
- Given: news articles span categories 台股, 美股, 加密貨幣, 宏觀
- When: user clicks a category filter pill
- Then: articles are filtered to show only the selected category; active pill has dark background; clicking 全部 restores all categories; deselecting all categories shows no articles (not an error state)

**AC-MN004-NEWS-03**
- Given: an article has a `link` field
- When: user clicks the article title
- Then: the link opens in a new tab with `rel="noopener noreferrer"`; the `link` value is rendered via a safe `href` attribute (not innerHTML)

**AC-MN004-NEWS-04**
- Given: `news.json` fetch returns 404 or network error
- When: the news tab renders
- Then: a "載入失敗" message is displayed in place of the news list; no uncaught JS exception; signals tab is unaffected

### Phase 4 — GH Pages retirement labeling (README update)

**AC-MN004-RETIRE-01**
- Given: MN-004 is merged and Vercel is serving the full signals + news display
- When: `README.md` is read
- Then: the Vercel URL (`https://market-news-sigma.vercel.app`) is labeled "Production"; the GH Pages URL (`https://mshmwr.github.io/market-news/`) is labeled "Legacy (retiring — see MN-005)"; the README does NOT claim GH Pages is current production

**AC-MN004-RETIRE-02**
- Given: MN-004 is merged
- When: `docs/index.html` is checked
- Then: the file still exists at `docs/index.html` (not deleted, not redirected); GH Pages continues to serve it unmodified; retirement (file removal or redirect) is deferred to MN-005

## QA Early Consultation

pending — to be completed before Engineer release

## AC vs Sacred Cross-Check

MN-001/002/003 (all closed): no visual Sacred clauses that conflict with MN-004 AC. AC-MN004-DATA-03 placeholder text "訊號暫未生成" matches MN-002 AC-MN002-HTML-04 (same placeholder string — intentional carry-forward, not conflict).
AC vs Sacred cross-check: no conflict.

## Binary-Criterion AC Scan

All Then/And clauses anchored to: DOM state (text content, element visibility, color value), tab/filter interaction observable state, HTTP 200/4xx response, TypeScript compiler error count (`npx tsc --noEmit`), file existence. Zero subjective bars.
Binary-criterion AC scan: 14 clauses checked / 0 subjective.

## Phase Gate Status

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1 — Data fetching + JSON API layer | open | Pending BQ-004-01 ruling |
| Phase 2 — Signals section UI | open | Pending BQ-004-04 + visual-delta Designer spec |
| Phase 3 — News section UI | open | Pending BQ-004-04 ruling |
| Phase 4 — GH Pages retirement labeling | open | Pending BQ-004-06 ruling |

## Release Status

open — BQ answers required before Architect release

---

_Ticket opened: 2026-05-09 by PM_
