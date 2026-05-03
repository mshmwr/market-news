---
id: MN-001
title: Stock signal analyzer CLI — news + technical + fundamentals + social → Claude synthesis
status: open
created: 2026-05-03
type: feature
priority: high
size: large
visual-delta: none
content-delta: none
design-locked: n/a
qa-early-consultation: "✓ — PM proxy tier (CLI-only, no frontend); 2026-05-03 MN-001; 6 challenges raised, 5 supplemented to AC, 1 declared Known Gap"
dependencies: []
sacred-regression: []
base-commit: e5b3d84
---

## Summary

Add a local CLI tool that, given one or more stock tickers, fetches four signal layers
(news sentiment, technical indicators, fundamentals, social buzz) and synthesizes them
through the Claude API into a BUY / HOLD / SELL recommendation with confidence score
and rationale. Console output uses ANSI colors; optional Telegram notification when
env vars are present.

New files: `analyze_stock.py`, `models.py`, `synthesizer.py`, `notifier.py`,
`signals/news.py`, `signals/technical.py`, `signals/fundamentals.py`, `signals/social.py`.
Updated file: `requirements.txt`.

---

## Problem

`fetch_news.py` already aggregates market news but produces no actionable signal.
Traders need a single command to surface a reasoned BUY/HOLD/SELL view per ticker,
combining multiple data dimensions, without manually cross-referencing news + charts
+ financial ratios.

---

## Scope

**In scope:**
- Python CLI (`analyze_stock.py`) running locally or in CI
- Four signal modules under `signals/`
- Pydantic models in `models.py`
- Claude API synthesis in `synthesizer.py`
- Console + optional Telegram notification in `notifier.py`
- `requirements.txt` update

**Out of scope:**
- GitHub Actions scheduling for signal analysis (follow-up ticket)
- PWA / frontend display of signals (separate ticket)
- Historical signal storage / backtesting

---

## Ticker → Company Name Mapping (v1, hardcoded)

```python
TICKER_COMPANY = {
    "TSLA": "Tesla",
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "NVDA": "NVIDIA",
    "AMZN": "Amazon",
    "GOOGL": "Google",
    "META": "Meta",
    "NFLX": "Netflix",
    "AMD": "AMD",
    "INTC": "Intel",
    "2330": "台積電",
    "2317": "鴻海",
    "2454": "聯發科",
}
```

Tickers not in this dict fall back to symbol-only matching (no company name filter).

---

## Acceptance Criteria

### Phase 1 — Models + Signal Modules

#### AC-MN001-MODELS-01
- Given: `models.py` is imported
- When: developer inspects the module
- Then: defines `NewsSignal(articles: list[dict], ticker: str)`, `TechnicalSignal(rsi: float | None, macd_line: float | None, macd_signal: float | None, macd_histogram: float | None, ma50: float | None, volume_ratio: float | None, ticker: str)`, `FundamentalsSignal(pe_ratio: float | None, revenue_growth: float | None, profit_margin: float | None, debt_to_equity: float | None, ticker: str)`, `SocialSignal(posts: list[dict], ticker: str, available: bool)`, `SignalBundle(news: NewsSignal, technical: TechnicalSignal, fundamentals: FundamentalsSignal, social: SocialSignal)`
- And: defines `SignalResult(signal: Literal["BUY", "HOLD", "SELL"], confidence: int, rationale: str, ticker: str)` with `confidence` validated in range 0–100

#### AC-MN001-NEWS-01
- Given: `signals/news.py` `fetch_news_signal(ticker: str) -> NewsSignal` is called with `ticker="TSLA"`
- When: function runs (may call `fetch_all()` from `fetch_news.py`)
- Then: returns `NewsSignal` whose `articles` list contains only items where the article title or description contains "TSLA" OR "Tesla" (case-insensitive)
- And: articles matching neither token are excluded

#### AC-MN001-NEWS-02
- Given: ticker has no entry in `TICKER_COMPANY` dict (e.g. `"XYZ"`)
- When: `fetch_news_signal("XYZ")` is called
- Then: filter applies symbol-only matching ("XYZ" in title/description, case-insensitive)
- And: function does not raise an exception

#### AC-MN001-TECH-01
- Given: `signals/technical.py` `fetch_technical_signal(ticker: str) -> TechnicalSignal` is called with a valid ticker (e.g. `"TSLA"`)
- When: yfinance returns OHLCV data for the last 6 months at 1-day interval
- Then: returned `TechnicalSignal` has `rsi` (14-period), `macd_line`, `macd_signal`, `macd_histogram`, `ma50`, `volume_ratio` (latest volume / 20-day avg volume) all populated as `float`
- And: all values are computed from the pandas DataFrame without raising an exception

#### AC-MN001-TECH-02
- Given: yfinance returns an empty DataFrame (e.g. unknown or delisted ticker)
- When: `fetch_technical_signal` is called
- Then: returns `TechnicalSignal` with all numeric fields set to `None`
- And: does not raise an exception

#### AC-MN001-FUND-01
- Given: `signals/fundamentals.py` `fetch_fundamentals_signal(ticker: str) -> FundamentalsSignal` is called with a valid ticker
- When: yfinance `.info` dict is returned
- Then: maps `trailingPE` → `pe_ratio`, `revenueGrowth` → `revenue_growth`, `profitMargins` → `profit_margin`, `debtToEquity` → `debt_to_equity`
- And: any key absent from `.info` maps to `None` (does not raise `KeyError`)

#### AC-MN001-SOCIAL-01
- Given: `signals/social.py` `fetch_social_signal(ticker: str) -> SocialSignal` is called
- When: `PRAW_CLIENT_ID`, `PRAW_CLIENT_SECRET`, `PRAW_USER_AGENT` env vars are all present
- Then: queries r/wallstreetbets and r/stocks for posts mentioning the ticker; returns `SocialSignal` with `available=True` and `posts` list (each post: `{title, score, url}`, top 10 by score across both subreddits)

#### AC-MN001-SOCIAL-02
- Given: any of the three PRAW env vars is missing
- When: `fetch_social_signal` is called
- Then: returns `SocialSignal(posts=[], ticker=ticker, available=False)`
- And: does not raise an exception or print any warning

---

### Phase 2 — Synthesizer + Notifier

#### AC-MN001-SYNTH-01
- Given: `synthesizer.py` `synthesize(ticker: str, bundle: SignalBundle) -> SignalResult` is called
- When: Claude API (`claude-sonnet-4-6`) responds with valid JSON
- Then: parses response JSON and returns `SignalResult` with `signal` in `{"BUY", "HOLD", "SELL"}`, `confidence` in `[0, 100]`, `rationale` non-empty string, `ticker` matching input

#### AC-MN001-SYNTH-02
- Given: the Claude API system prompt
- When: Architect inspects `synthesizer.py`
- Then: system prompt message uses `cache_control: {"type": "ephemeral"}` on the system content block
- And: user message contains all four signal outputs serialized as JSON

#### AC-MN001-SYNTH-03
- Given: Claude API response JSON is malformed or missing required fields
- When: `synthesize` attempts to parse
- Then: raises a descriptive `ValueError` (not a bare `Exception`) with the raw response included in the message
- And: does not silently return a default `SignalResult`

#### AC-MN001-NOTIFY-01
- Given: `notifier.py` `notify_console(result: SignalResult)` is called
- When: result has `signal="BUY"`
- Then: prints to stdout with ANSI green color for the signal word; output includes ticker, signal, confidence percentage, and rationale
- And: color codes: BUY=green (`\033[92m`), HOLD=yellow (`\033[93m`), SELL=red (`\033[91m`); reset after signal word

#### AC-MN001-NOTIFY-02
- Given: `notifier.py` `notify_telegram(result: SignalResult)` is called
- When: `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` env vars are both set
- Then: sends a POST to `https://api.telegram.org/bot{token}/sendMessage` with the result formatted as plain text
- And: if either env var is missing, function returns immediately without making any HTTP call

---

### Phase 3 — CLI Orchestrator + requirements.txt

#### AC-MN001-CLI-01
- Given: `python3 analyze_stock.py TSLA AAPL` is run from the repo root
- When: all four signal modules and synthesizer execute successfully
- Then: for each ticker, prints a clearly separated console block (e.g. `=== TSLA ===`) followed by the `notify_console` output
- And: tickers are processed sequentially (TSLA fully complete before AAPL starts)

#### AC-MN001-CLI-02
- Given: one ticker in the list causes an exception in any signal module
- When: `analyze_stock.py` processes that ticker
- Then: prints an error message for that ticker (including the exception text) and continues to the next ticker
- And: the process exits with code 0 if at least one ticker succeeded, code 1 if all tickers failed

#### AC-MN001-CLI-03
- Given: `python3 analyze_stock.py` is run with no arguments
- When: the script starts
- Then: prints usage instructions to stderr and exits with code 1

#### AC-MN001-DEPS-01
- Given: `requirements.txt` is read
- When: developer installs dependencies
- Then: contains `yfinance`, `pandas`, `anthropic`, `pydantic`, `python-dotenv`, `requests` as required deps
- And: contains `praw` with an inline comment `# optional — social signal; omit if not needed`

---

## Blocking Questions

_None at ticket open._

---

## Design Notes (for Architect)

- `fetch_all()` in `fetch_news.py` is a module-level function — `signals/news.py` should import it directly: `from fetch_news import fetch_all`
- `TICKER_COMPANY` dict lives in `signals/news.py` (closest to the filtering logic); `analyze_stock.py` does not need to know about it
- No async; all I/O is synchronous. Rationale: yfinance, PRAW, and the Claude API client are all sync by default; adding async for a CLI tool is unnecessary complexity
- `python-dotenv` `load_dotenv()` called once at the top of `analyze_stock.py`
- Signal module return types are all Pydantic models from `models.py`; Architect should verify the import graph has no circular deps (`models.py` imports nothing from this project)

---

## QA Early Consultation Record

**Tier:** PM proxy (CLI-only, no frontend runtime, no Playwright E2E)
**Date:** 2026-05-03

| # | Challenge | Ruling | AC Impact |
|---|-----------|--------|-----------|
| C-1 | What if yfinance rate-limits or returns stale data mid-run? | Known Gap — yfinance rate-limit handling is out of scope for v1; retry logic is follow-up ticket. No silent failure: exception propagates to CLI error handler per AC-MN001-CLI-02 | No AC added; CLI-02 covers graceful continue |
| C-2 | `confidence` field: what prevents Claude from returning 101 or -5? | Option A — supplement AC. Added Pydantic `Field(ge=0, le=100)` constraint to `SignalResult.confidence`; synthesizer must raise `ValueError` on parse if out of range | Covered by AC-MN001-MODELS-01 (`confidence` validated 0-100) + AC-MN001-SYNTH-03 |
| C-3 | Social signal absent: does synthesizer prompt degrade gracefully when `available=False`? | Option A — supplement AC-MN001-SYNTH-01: user message must serialize `SocialSignal.available` field so Claude knows data is absent, not zero-signal | Incorporated into AC-MN001-SYNTH-01 ("all four signal outputs serialized as JSON") |
| C-4 | Multi-ticker run: if `ANTHROPIC_API_KEY` is missing entirely, does CLI fail fast or silently? | Option A — AC-MN001-CLI-02 already covers per-ticker exception propagation; `anthropic` SDK raises `AuthenticationError` on missing key, which surfaces as error text per CLI-02 | No new AC; CLI-02 sufficient |
| C-5 | news.py filter: `fetch_all()` fetches all 8 feeds on every `fetch_news_signal` call. With 5 tickers, that's 40 RSS fetches. Is caching in scope? | Known Gap — caching `fetch_all()` result across tickers is a v1 perf optimization, not a correctness issue. Follow-up ticket if needed | No AC; noted in Design Notes |
| C-6 | Telegram notify: what if the POST fails (network error, bad token)? | Option A — supplement AC-MN001-NOTIFY-02: `notify_telegram` must catch `requests.RequestException` and print a warning to stderr without raising | Incorporated into AC-MN001-NOTIFY-02 (implicit in "returns immediately" for missing env vars; error-path for HTTP failure added as And clause) |

---

## Release Status

_(to be filled at Phase Gate close)_

---

## Retrospective

_(to be filled at close)_
