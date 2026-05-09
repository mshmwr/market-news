---
id: MN-008
title: Richer Daily Digest — TW/US split, market-moving news, NIM reliability
status: in-progress
created: 2026-05-09
type: feature
priority: high
size: M
visual-delta: none
content-delta: yes
qa-early-consultation: skipped — single-file additive change to existing digest pipeline; failure modes degrade to empty narrative + raw lists (already validated in MN-007)
supersedes: MN-007 (extends — 4 → 6 sections + reliability fixes)
---

## Why

User feedback after MN-007 first run:
1. "內容不夠豐富，我也想要台美股和地緣政治資訊" — current Top-5 Shortlist is mostly US (selection by confidence rank); Taiwan stocks invisible despite being in `signals.json`.
2. "還有影響股票市場的資訊" — no section covering macro / earnings / market-moving headlines.
3. MN-007 first run: 4/4 NIM calls hit 180s timeout; second run: 2/4 returned 0 chars (max_tokens=4096 exhausted by reasoning on multi-line prompts).

## Scope

Files touched:
- `digest.py`:
  - Split signals → `_split_signals_by_region(signals)` returning `(us_top5, tw_top4)`.
  - Add `_fetch_market_news(articles, limit=8)` — pull latest items from `fetch_news.py` categories `美股` + `台股` (CNBC + MarketWatch + 經濟日報 + ETtoday財經).
  - Bump `_fetch_geopolitical()` limit 5 → 8.
  - Single shared `fetch_all_news()` call — geo + market-moving share the same fetch.
  - Bump NIM `max_tokens` 4096 → 8192 to stop reasoning model truncating content on long prompts.
  - Add `label` arg to `_call_nim()` so per-section failures are identifiable.
  - Switch error prints from stderr → stdout with `flush=True` so GH Actions captures them.
  - Region-aware `_narrative_stocks(top, region_label)` produces separate US / TW narratives.
  - New `_narrative_market_news()` builder.
  - Render six sections in this order: US stocks → TW stocks → F&G → market-moving → geo → FOMC.
  - ThreadPoolExecutor `max_workers` 4 → 6.
- `docs/tickets/MN-008-*.md` — this ticket.

## Acceptance Criteria

1. **Six sections render.** Email contains six h2 headings: US Stock Shortlist, TW Stock Shortlist, Fear & Greed Index, 影響股票市場的新聞, Geopolitical Risk Pulse, FOMC / Fed Updates.
2. **TW stocks visible.** TW shortlist contains all `*.TW` tickers from `signals.json`, sorted BUY-first by confidence (currently 4 tickers).
3. **Market-moving news populated.** Section lists ≥5 headlines from CNBC / MarketWatch / 經濟日報 / ETtoday財經 with `[category · source]` annotation.
4. **NIM reliability.** ≥5 of 6 narrative slots return non-empty content within the 300s per-call timeout under normal NIM latency. Total wall-time ≤6 minutes (parallelism keeps total ≈ max single-call time).
5. **Graceful degradation preserved.** Missing `NVIDIA_API_KEY` → all narratives empty, raw lists still render, exit 0.
6. **No new env vars.** Reuses `NVIDIA_API_KEY` + `RESEND_API_KEY`.

## Out of Scope

- Realtime price quotes (deferred to later MN-XXX).
- Sector heatmap or breadth indicators.
- VIX / TAIEX index quotes.
- Description excerpts in news lists (titles only, kept compact for email rendering).
